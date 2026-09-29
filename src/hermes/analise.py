"""
Análises do Hermes: do mapa ao mix de produtos.

Passos:
1. `cruzar_setores`   – que pedaço de cada setor censitário cai na isócrona da loja;
2. `perfil_lojas`     – quem mora e quem trabalha na área de cada loja;
3. `potencial_categorias` – quanto dinheiro por categoria circula ali (R$/mês);
4. `indice_afinidade` – o mix da área comparado ao da cidade (100 = igual à cidade);
5. `agrupar_lojas`    – k-means para achar "tipos" de loja.
"""
from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd

from . import config, pof


# ---------------------------------------------------------------------------
# 1. Interseção setor × isócrona (ponderação por área)
# ---------------------------------------------------------------------------
def cruzar_setores(setores: gpd.GeoDataFrame, isocronas: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Um setor pode estar só PARCIALMENTE dentro da área da loja. Assumimos que as
    pessoas estão espalhadas de forma uniforme dentro do setor, então se 40% da
    área do setor cai na isócrona, contamos 40% da população dele.
    (Hipótese clássica de "interpolação por área"; setores são pequenos, o erro é baixo.)
    """
    inter = gpd.overlay(setores, isocronas[["loja_id", "geometry"]], how="intersection",
                        keep_geom_type=True)
    area_setor = setores.set_index("CD_SETOR").geometry.area
    inter["fracao"] = (inter.geometry.area / inter["CD_SETOR"].map(area_setor)).clip(0, 1)
    return inter


def adicionar_classe_pof(setores: pd.DataFrame, fator_ipca: float) -> pd.DataFrame:
    """
    Renda do responsável (R$ jul/2022) -> renda FAMILIAR em R$ de jan/2018 -> classe POF.
        renda_familia_2018 = renda_resp × fator_renda_familia ÷ IPCA(jul22/jan18)
    """
    s = setores.copy()
    s["renda_familia_2018"] = s["renda_resp"] * config.PREMISSAS["fator_renda_familia"] / fator_ipca
    s["classe_pof"] = s["renda_familia_2018"].map(pof.classe_pof)
    return s


# ---------------------------------------------------------------------------
# 2. Perfil de cada loja
# ---------------------------------------------------------------------------
def perfil_lojas(inter: pd.DataFrame, isocronas: gpd.GeoDataFrame, empregos: pd.Series,
                 n_concorrentes: pd.Series) -> pd.DataFrame:
    cols = ["pop", "domicilios", "pop_0_14", "pop_15_29", "pop_30_59", "pop_60_mais"]
    w = inter[cols].multiply(inter["fracao"], axis=0)
    w["loja_id"] = inter["loja_id"].values
    # renda média ponderada pelo nº de domicílios
    w["renda_x_dom"] = inter["renda_resp"] * inter["domicilios"] * inter["fracao"]
    w["dom_com_renda"] = inter["domicilios"].where(inter["renda_resp"].notna()) * inter["fracao"]
    p = w.groupby("loja_id").sum(numeric_only=True)

    p["renda_media_resp"] = p["renda_x_dom"] / p["dom_com_renda"]
    area = isocronas.set_index("loja_id").geometry.area / 1e6
    p["area_km2"] = area
    p["densidade_hab_km2"] = p["pop"] / p["area_km2"]
    total_idade = p[["pop_0_14", "pop_15_29", "pop_30_59", "pop_60_mais"]].sum(axis=1)
    for c in ["pop_0_14", "pop_15_29", "pop_30_59", "pop_60_mais"]:
        p["pct_" + c.removeprefix("pop_")] = p[c] / total_idade
    p["empregos"] = empregos.reindex(p.index).fillna(0)
    p["empregos_por_morador"] = p["empregos"] / p["pop"].replace(0, np.nan)
    # Concorrentes desconhecidos (OSM fora do ar) ficam vazios; quem usa trata.
    p["concorrentes"] = n_concorrentes.reindex(p.index)
    return p.drop(columns=["renda_x_dom", "dom_com_renda"])


# ---------------------------------------------------------------------------
# 3. Potencial de gasto por categoria (R$/mês, a preços de jul/2022)
# ---------------------------------------------------------------------------
def domicilios_por_classe(df: pd.DataFrame, chave: str = "loja_id") -> pd.DataFrame:
    """
    Soma domicílios (já ponderados pela fração do setor) por classe de renda POF.
    Setores sem renda divulgada (sigilo) têm seus domicílios repartidos na mesma
    proporção dos demais setores da mesma área.
    """
    df = df.copy()
    df["dom_w"] = df["domicilios"] * (df["fracao"] if "fracao" in df else 1.0)
    tab = df[df["classe_pof"].notna()].pivot_table(
        index=chave, columns="classe_pof", values="dom_w", aggfunc="sum", fill_value=0)
    total = df.groupby(chave)["dom_w"].sum()
    escala = (total / tab.sum(axis=1)).reindex(tab.index).fillna(1.0)
    return tab.multiply(escala, axis=0)


def potencial_categorias(dom_classe: pd.DataFrame, empregos: pd.Series, pof_cat: pd.DataFrame,
                         gasto_trab: pd.Series, fator_ipca: float) -> pd.DataFrame:
    """
    potencial_moradores[cat]     = Σ_classes domicílios(classe) × gasto POF(classe, cat)
    potencial_trabalhadores[cat] = empregos × gasto por trabalhador(cat)
    Tudo × IPCA para trazer de jan/2018 a jul/2022.
    """
    pof_cat = pof_cat.reindex(dom_classe.columns).fillna(0)
    mor = dom_classe.fillna(0) @ pof_cat * fator_ipca
    trab = pd.DataFrame(0.0, index=mor.index, columns=mor.columns)
    for cat, valor in gasto_trab.items():
        trab[cat] = empregos.reindex(mor.index).fillna(0) * valor * fator_ipca
    longo = (mor.stack().rename("moradores").to_frame()
             .join(trab.stack().rename("trabalhadores")))
    longo.index.names = ["loja_id", "categoria"]
    longo["total"] = longo["moradores"] + longo["trabalhadores"]
    longo["share"] = longo["total"] / longo.groupby(level=0)["total"].transform("sum")
    return longo.reset_index()


# ---------------------------------------------------------------------------
# 4. Índice de afinidade
# ---------------------------------------------------------------------------
def indice_afinidade(pot: pd.DataFrame, share_cidade: pd.Series) -> pd.DataFrame:
    """
    índice = (peso da categoria na área da loja) ÷ (peso da categoria na cidade) × 100
    120 = a área gasta 20% a mais do que a média da cidade naquela categoria.
    """
    pot = pot.copy()
    pot["share_cidade"] = pot["categoria"].map(share_cidade)
    pot["indice"] = 100 * pot["share"] / pot["share_cidade"]
    return pot


# ---------------------------------------------------------------------------
# 5. Agrupamento das lojas por perfil
# ---------------------------------------------------------------------------
VARS_CLUSTER = ["renda_media_resp", "pct_0_14", "pct_60_mais", "empregos_por_morador",
                "densidade_hab_km2"]
ROTULOS = {
    "corporativa": ("Corporativa (quem trabalha)", "Business district (workers)"),
    "misto": ("Misto (mora e trabalha)", "Mixed (live & work)"),
    "residencial": ("Residencial consolidado", "Established residential"),
    "familiar": ("Periferia familiar", "Family outskirts"),
    "extra": ("Outro perfil", "Other profile"),
}


def agrupar_lojas(perfil: pd.DataFrame, k: int = config.N_CLUSTERS) -> pd.DataFrame:
    """
    k-means nas variáveis de perfil (padronizadas; empregos e densidade em log,
    porque variam em ordens de grandeza). Depois damos NOME a cada grupo olhando
    o centro dele – o algoritmo só devolve números 0, 1, 2…
    """
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    X = perfil[VARS_CLUSTER].copy()
    X["empregos_por_morador"] = np.log1p(X["empregos_por_morador"].fillna(0))
    X["densidade_hab_km2"] = np.log1p(X["densidade_hab_km2"])
    X = X.fillna(X.median())
    Z = StandardScaler().fit_transform(X)
    km = KMeans(n_clusters=k, n_init=20, random_state=config.SEMENTE).fit(Z)
    centros = pd.DataFrame(km.cluster_centers_, columns=VARS_CLUSTER)

    # Nomeação: o algoritmo só devolve 0, 1, 2…; damos nome olhando o centro de cada grupo.
    # 1) mais empregos por morador -> "Corporativa"
    # 2) dos que sobram, mais crianças (0-14) -> "Periferia familiar"
    # 3) dos que sobram, o de mais empregos por morador -> "Misto"; o seguinte -> "Residencial"
    nomes, livres = {}, set(range(k))
    g = centros["empregos_por_morador"].idxmax(); nomes[g] = "corporativa"; livres.discard(g)
    if livres:
        g = centros.loc[sorted(livres), "pct_0_14"].idxmax(); nomes[g] = "familiar"; livres.discard(g)
    ordem = centros.loc[sorted(livres), "empregos_por_morador"].sort_values(ascending=False).index
    for g, chave in zip(ordem, ["misto", "residencial"] + ["extra"] * k):
        nomes[g] = chave

    out = perfil.copy()
    out["cluster"] = km.labels_
    out["perfil_chave"] = out["cluster"].map(nomes)
    out["perfil"] = out["perfil_chave"].map(lambda c: ROTULOS[c][0])
    out["perfil_en"] = out["perfil_chave"].map(lambda c: ROTULOS[c][1])
    return out
