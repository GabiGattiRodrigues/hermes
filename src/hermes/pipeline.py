"""
Pipeline completo do Hermes:  python -m hermes.pipeline

1. baixa as fontes públicas (só na primeira vez);
2. calcula as isócronas de 15 min e os concorrentes (OSM);
3. monta setores do Censo, empregos da OD e gastos da POF;
4. calcula perfil, potencial, índice de afinidade e grupos de lojas;
5. gera as vendas sintéticas e o gap de sortimento;
6. salva tudo, leve, em dados/processados/ (é isso que o app lê).
"""
from __future__ import annotations

import json
from datetime import datetime

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point

from . import analise, censo, config, fontes, od, osm, pof, vendas

OUT = config.DADOS_PROCESSADOS


def etapa(txt: str) -> None:
    print(f"\n=== {txt} ===")


def lojas_gdf() -> gpd.GeoDataFrame:
    df = pd.DataFrame(config.LOJAS, columns=["loja_id", "nome", "lat", "lon"])
    return gpd.GeoDataFrame(df, geometry=[Point(xy) for xy in zip(df.lon, df.lat)],
                            crs=config.CRS_WGS84)


def calcular_isocronas(lojas: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Isócronas + concorrentes. O OSM é a parte mais lenta e instável, então:
    - cada loja é salva assim que fica pronta (dados/brutos/osm/AGxx.gpkg);
    - se os servidores do OSM não responderem, a loja recebe a área APROXIMADA
      (plano B, ver osm.isocrona_aproximada) e o pipeline segue até o fim;
    - na próxima rodada, só as lojas aproximadas tentam o OSM de novo.
    """
    pasta = config.DADOS_BRUTOS / "osm"
    pasta.mkdir(parents=True, exist_ok=True)
    polys, concs = [], []
    for i, r in enumerate(lojas.itertuples()):
        arq = pasta / f"{r.loja_id}.gpkg"
        salvo = gpd.read_file(arq, layer="isocrona") if arq.exists() else None
        # Arquivos de versões antigas não têm "metodo"/"conc_ok" – só eram gravados
        # quando o OSM funcionava, então valem como completos.
        metodo = salvo["metodo"].iloc[0] if salvo is not None and "metodo" in salvo else "ruas_osm"
        conc_ok = bool(salvo["conc_ok"].iloc[0]) if salvo is not None and "conc_ok" in salvo else True
        area_ok = salvo is not None and metodo != "aproximada"
        if area_ok and conc_ok:
            p = salvo.geometry.iloc[0]
            c = gpd.read_file(arq, layer="concorrentes")
            n_conc = int((c["nome"] != "_vazio").sum())
            print(f"  ✓ {r.loja_id} {r.nome} (já calculada)")
        else:
            print(f"  • {r.loja_id} {r.nome}")
            if area_ok:
                p = salvo.geometry.iloc[0]
            else:
                grafo = config.DADOS_BRUTOS / "grafo_exemplo_AG01.graphml"
                try:
                    p, metodo = osm.isocrona(r.lat, r.lon,
                                             salvar_grafo=None if grafo.exists() else grafo)
                except osm.OSMIndisponivel:
                    p, metodo = osm.isocrona_aproximada(r.lat, r.lon), "aproximada"
                    print("      rotas fora do ar -> área aproximada (círculo de 920 m); "
                          "tento de novo na próxima rodada")
            try:
                c = osm.concorrentes(p)
                n_conc, conc_ok = len(c), True
            except osm.OSMIndisponivel:
                c, n_conc, conc_ok = osm.concorrentes_vazio(), None, False
            gpd.GeoDataFrame({"loja_id": [r.loja_id], "metodo": [metodo], "conc_ok": [conc_ok]},
                             geometry=[p], crs=config.CRS_METRICO).to_file(arq, layer="isocrona")
            (c if len(c) else gpd.GeoDataFrame({"nome": ["_vazio"], "tipo": [""]},
                                               geometry=[p.centroid], crs=config.CRS_METRICO)) \
                .to_file(arq, layer="concorrentes")
            print(f"      área {p.area / 1e6:.2f} km² · "
                  f"{'?' if n_conc is None else n_conc} concorrentes · método: {metodo}")
        c = c[c["nome"] != "_vazio"].copy()
        c["loja_id"] = r.loja_id
        polys.append({"loja_id": r.loja_id, "metodo_area": metodo,
                      "concorrentes_ok": conc_ok, "geometry": p})
        concs.append(c)
    iso = gpd.GeoDataFrame(polys, crs=config.CRS_METRICO)
    conc = gpd.GeoDataFrame(pd.concat(concs, ignore_index=True), geometry="geometry", crs=config.CRS_METRICO)
    conc = conc.reindex(columns=["loja_id", "nome", "tipo", "geometry"])
    iso.to_file(config.DADOS_BRUTOS / "isocronas_cache.gpkg")
    conc.to_file(config.DADOS_BRUTOS / "concorrentes_cache.gpkg")
    n_aprox = int((iso["metodo_area"] == "aproximada").sum())
    n_sem_conc = int((~iso["concorrentes_ok"]).sum())
    if n_aprox or n_sem_conc:
        print(f"  ⚠ {n_aprox} loja(s) com área aproximada e {n_sem_conc} sem concorrentes – "
              "rode o pipeline de novo mais tarde para completar.")
    return iso, conc


class _Tee:
    """Escreve na tela E num arquivo de log (dados/processados/log_pipeline.txt)."""

    def __init__(self, *alvos):
        self.alvos = alvos

    def write(self, txt):
        for a in self.alvos:
            a.write(txt)
            a.flush()

    def flush(self):
        for a in self.alvos:
            a.flush()


def main() -> None:
    import sys

    config.DADOS_BRUTOS.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    log = open(OUT / "log_pipeline.txt", "w", encoding="utf-8")
    sys.stdout = _Tee(sys.__stdout__, log)
    sys.stderr = _Tee(sys.__stderr__, log)

    etapa("1. Download das fontes públicas")
    gpkg = fontes.baixar_malha_setores()
    zip_demo, dic_ag = fontes.baixar_demografia()
    zip_renda, dic_renda = fontes.baixar_renda()
    zip_od = fontes.baixar_od()
    dados_pof = fontes.baixar_pof()
    dados_ipca = fontes.baixar_ipca()

    etapa("2. Isócronas de 15 min e concorrentes (OpenStreetMap)")
    lojas = lojas_gdf()
    iso, conc = calcular_isocronas(lojas)

    etapa("3. Censo 2022 – setores do município de SP")
    setores, meta_censo = censo.montar_setores(gpkg, zip_demo, zip_renda, dic_ag, dic_renda)
    print(f"  {meta_censo['n_setores']:,} setores · {meta_censo['pop_total']:,.0f} pessoas · "
          f"{meta_censo['setores_sem_renda']:,} setores sem renda divulgada")
    for cod, desc in meta_censo["variaveis"].items():
        print(f"    {cod}: {desc[:110]}")

    etapa("4. POF + IPCA")
    itens_pof, pof_cat = pof.matriz_pof(dados_pof)
    fator = pof.fator_ipca(dados_ipca)
    gasto_trab = pof.gasto_trabalhador(itens_pof)
    print(f"  IPCA jan/2018 -> jul/2022: ×{fator:.3f}")
    print("  gasto/mês por trabalhador (R$ 2018):", gasto_trab.round(2).to_dict())
    setores = analise.adicionar_classe_pof(setores, fator)

    etapa("5. Pesquisa OD 2023 – empregos")
    trab = od.pontos_de_trabalho(zip_od)
    municipio = setores.union_all()
    empregos_cidade = trab[trab.within(municipio)]["peso"].sum()
    trab_lojas = gpd.sjoin(trab, iso[["loja_id", "geometry"]], predicate="within")
    empregos = trab_lojas.groupby("loja_id")["peso"].sum()
    print(f"  {len(trab):,} pessoas com local de trabalho geolocalizado · "
          f"{empregos_cidade:,.0f} empregos estimados na capital")

    etapa("6. Perfil, potencial e afinidade")
    inter = analise.cruzar_setores(setores, iso)
    n_conc = conc.groupby("loja_id").size().reindex(iso["loja_id"]).fillna(0)
    n_conc[~iso.set_index("loja_id")["concorrentes_ok"]] = np.nan  # desconhecido ≠ zero
    perfil = analise.perfil_lojas(inter, iso, empregos, n_conc)
    perfil = perfil.join(iso.set_index("loja_id")[["metodo_area"]])
    dom_lojas = analise.domicilios_por_classe(inter, "loja_id")
    pot = analise.potencial_categorias(dom_lojas, empregos, pof_cat, gasto_trab, fator)
    # Referência: a cidade inteira (todos os setores + todos os empregos da capital)
    dom_cidade = analise.domicilios_por_classe(setores.assign(loja_id="cidade"), "loja_id")
    pot_cidade = analise.potencial_categorias(dom_cidade, pd.Series({"cidade": empregos_cidade}),
                                              pof_cat, gasto_trab, fator)
    share_cidade = pot_cidade.set_index("categoria")["share"]
    pot = analise.indice_afinidade(pot, share_cidade)
    perfil = analise.agrupar_lojas(perfil)
    perfil["potencial_total_mes"] = pot.groupby("loja_id")["total"].sum()
    perfil = perfil.join(lojas.set_index("loja_id")[["nome", "lat", "lon"]])
    print(perfil[["nome", "pop", "empregos", "renda_media_resp", "concorrentes", "perfil"]]
          .round(0).to_string())

    etapa("7. Vendas sintéticas e gap de sortimento")
    vend = vendas.gerar_vendas(pot, perfil, share_cidade)
    gap = vendas.gap_sortimento(pot, vend)

    etapa("8. Salvando saídas leves para o app")
    wgs = config.CRS_WGS84
    lojas_out = lojas.merge(perfil.drop(columns=["nome", "lat", "lon"]).reset_index(), on="loja_id")
    lojas_out.to_file(OUT / "lojas.geojson", driver="GeoJSON")
    iso.to_crs(wgs).to_file(OUT / "isocronas.geojson", driver="GeoJSON")
    conc.to_crs(wgs).to_file(OUT / "concorrentes.geojson", driver="GeoJSON")
    set_out = inter[["loja_id", "CD_SETOR", "fracao", "pop", "domicilios", "renda_resp",
                     "classe_pof", "geometry"]].copy()
    set_out["geometry"] = set_out.geometry.simplify(5)
    set_out.to_crs(wgs).to_file(OUT / "setores_lojas.geojson", driver="GeoJSON")
    trab_out = trab_lojas[["loja_id", "peso", "geometry"]].to_crs(wgs)
    trab_out.to_file(OUT / "empregos_pontos.geojson", driver="GeoJSON")
    pot.to_csv(OUT / "potencial.csv", index=False)
    vend.to_csv(OUT / "vendas_sinteticas.csv", index=False)
    gap.to_csv(OUT / "gap_sortimento.csv", index=False)
    pof_cat.to_csv(OUT / "pof_categorias.csv")
    pot_cidade.to_csv(OUT / "potencial_cidade.csv", index=False)

    origem = json.loads((config.DADOS_BRUTOS / "_origem.json").read_text("utf-8"))
    meta = {
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "origem": origem,
        "censo": meta_censo,
        "fator_ipca": fator,
        "gasto_trabalhador_2018": gasto_trab.to_dict(),
        "empregos_cidade": float(empregos_cidade),
        "od_pessoas_geolocalizadas": int(len(trab)),
        "premissas": config.PREMISSAS,
        "distancia_caminhada_m": osm.distancia_caminhada_m(),
        "nome_rede": config.NOME_REDE,
    }
    (OUT / "metadados.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2, default=str),
                                        "utf-8")
    print(f"  pronto: {OUT}")


if __name__ == "__main__":
    main()
