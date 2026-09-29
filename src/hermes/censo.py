"""
Censo 2022 (IBGE) – quem MORA perto de cada loja.

O Censo divulga dados por SETOR CENSITÁRIO: o menor recorte geográfico
publicado, algo como um quarteirão ou poucos quarteirões (~300 domicílios).
Montamos uma tabela com um setor por linha, com:

- população e domicílios (arquivo "básico", que já vem junto da malha);
- população por faixa etária (arquivo "demografia");
- rendimento nominal médio do responsável pelo domicílio (arquivo "renda").

Detalhes que dão trabalho nos arquivos do IBGE (e estão tratados aqui):
- separador ";" e vírgula decimal;
- valores suprimidos por sigilo aparecem como "X" (viram vazio/NaN);
- o código do setor pode vir com sufixo de letra na malha – padronizamos só dígitos;
- os nomes dos arquivos mudam a cada republicação.
"""
from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from . import config

# Faixas etárias do arquivo "demografia" (V01031 a V01041 = 11 classes de idade).
FAIXAS_IDADE = {
    "V01031": "0 a 4", "V01032": "5 a 9", "V01033": "10 a 14", "V01034": "15 a 19",
    "V01035": "20 a 24", "V01036": "25 a 29", "V01037": "30 a 39", "V01038": "40 a 49",
    "V01039": "50 a 59", "V01040": "60 a 69", "V01041": "70 ou mais",
}
GRUPOS_IDADE = {
    "pop_0_14": ["V01031", "V01032", "V01033"],
    "pop_15_29": ["V01034", "V01035", "V01036"],
    "pop_30_59": ["V01037", "V01038", "V01039"],
    "pop_60_mais": ["V01040", "V01041"],
}


def so_digitos(serie: pd.Series) -> pd.Series:
    """'355030801000001P' -> '355030801000001'."""
    return serie.astype(str).str.replace(r"\D", "", regex=True)


def para_numero(serie: pd.Series) -> pd.Series:
    """Converte texto do IBGE ('1.234,5', 'X', '') em número (X/vazio -> NaN)."""
    s = serie.astype(str).str.strip()
    s = s.where(~s.str.upper().isin(["X", "", "NAN", "NONE", "-", "."]))
    # Só troca vírgula decimal quando ela existe; ponto sozinho é decimal do CSV em UTF-8.
    tem_virgula = s.str.contains(",", na=False)
    s = s.where(~tem_virgula, s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    return pd.to_numeric(s, errors="coerce")


# ---------------------------------------------------------------------------
# Dicionário de dados: usamos para (1) confirmar o significado das variáveis
# e (2) achar a variável de renda média sem depender de um código fixo.
# ---------------------------------------------------------------------------
def ler_dicionario(xlsx: Path) -> pd.DataFrame:
    """Lê todas as abas e devolve pares (codigo, descricao) encontrados."""
    linhas = []
    for aba, df in pd.read_excel(xlsx, sheet_name=None, header=None, dtype=str).items():
        for _, row in df.fillna("").iterrows():
            celulas = [str(c).strip() for c in row if str(c).strip()]
            for i, c in enumerate(celulas):
                if re.fullmatch(r"[Vv]\d{4,6}", c):
                    desc = " | ".join(x for x in celulas[i + 1:] if not re.fullmatch(r"[Vv]\d{4,6}", x))
                    linhas.append({"aba": aba, "codigo": c.upper(), "descricao": desc})
    return pd.DataFrame(linhas).drop_duplicates("codigo")


def achar_variavel_renda(dic: pd.DataFrame) -> tuple[str, str]:
    """Procura a variável de 'rendimento nominal médio mensal' do responsável."""
    d = dic.copy()
    d["desc_min"] = d["descricao"].str.lower()
    cand = d[d["desc_min"].str.contains("rendimento") & d["desc_min"].str.contains(r"m[ée]di")
             & ~d["desc_min"].str.contains("vari[aâ]ncia|mediana")]
    if cand.empty:
        raise ValueError("Não achei a variável de renda média no dicionário.")
    linha = cand.iloc[0]
    return linha["codigo"], linha["descricao"]


# ---------------------------------------------------------------------------
# Leitura dos CSVs dentro dos .zip (Brasil inteiro -> filtramos só SP capital)
# ---------------------------------------------------------------------------
def ler_csv_do_zip(caminho_zip: Path, colunas: list[str] | None = None) -> pd.DataFrame:
    """
    Lê o CSV do zip em pedaços (o arquivo do Brasil tem centenas de MB) e
    mantém só os setores do município de São Paulo.
    """
    with zipfile.ZipFile(caminho_zip) as z:
        nome = next(n for n in z.namelist() if n.lower().endswith(".csv"))
        bruto = z.read(nome)
    for enc in ("utf-8-sig", "latin-1"):
        try:
            texto = bruto.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    sep = ";" if texto[:2000].count(";") > texto[:2000].count(",") else ","
    pedacos = []
    for pedaco in pd.read_csv(io.StringIO(texto), sep=sep, dtype=str, chunksize=200_000):
        pedaco.columns = [c.strip().upper() for c in pedaco.columns]
        cod = so_digitos(pedaco["CD_SETOR"])
        pedaco = pedaco[cod.str.startswith(config.COD_MUN_SP)].copy()
        pedaco["CD_SETOR"] = cod[cod.str.startswith(config.COD_MUN_SP)]
        if colunas:
            pedaco = pedaco[["CD_SETOR"] + [c for c in colunas if c in pedaco.columns]]
        pedacos.append(pedaco)
    return pd.concat(pedacos, ignore_index=True)


def ler_malha(gpkg: Path) -> gpd.GeoDataFrame:
    """Malha de setores de SP (estado) -> só município de SP, em CRS métrico."""
    import pyogrio

    campos = list(pyogrio.read_info(gpkg)["fields"])
    col_mun = next(c for c in campos if c.upper() == "CD_MUN")
    gdf = gpd.read_file(gpkg, where=f"{col_mun} = '{config.COD_MUN_SP}'")
    gdf.columns = [c.upper() if c != "geometry" else c for c in gdf.columns]
    gdf["CD_SETOR"] = so_digitos(gdf["CD_SETOR"])
    return gdf.to_crs(config.CRS_METRICO)


def montar_setores(gpkg: Path, zip_demo: Path, zip_renda: Path,
                   dic_agregados: Path, dic_renda: Path) -> tuple[gpd.GeoDataFrame, dict]:
    """Junta malha + demografia + renda num GeoDataFrame, um setor por linha."""
    meta: dict = {"variaveis": {}}

    # 1) Malha com o "básico" (V0001 = pessoas, V0005 = média de moradores, V0007 = domicílios ocupados)
    malha = ler_malha(gpkg)
    for v in ("V0001", "V0005", "V0007"):
        if v in malha.columns:
            malha[v] = para_numero(malha[v])
    dic_ag = ler_dicionario(dic_agregados)
    for v in ["V0001", "V0005", "V0007", *FAIXAS_IDADE]:
        linha = dic_ag[dic_ag["codigo"] == v]
        meta["variaveis"][v] = linha["descricao"].iloc[0] if len(linha) else "(não achada no dicionário)"

    setores = malha[["CD_SETOR", "geometry"]].copy()
    setores["pop"] = malha["V0001"]
    if "V0007" in malha.columns:
        setores["domicilios"] = malha["V0007"]
    else:  # plano B: população ÷ média de moradores
        setores["domicilios"] = malha["V0001"] / malha["V0005"]
    setores["area_km2"] = setores.geometry.area / 1e6

    # 2) Faixas etárias
    demo = ler_csv_do_zip(zip_demo, list(FAIXAS_IDADE))
    for v in FAIXAS_IDADE:
        demo[v] = para_numero(demo[v])
    for grupo, vs in GRUPOS_IDADE.items():
        demo[grupo] = demo[vs].sum(axis=1, min_count=len(vs))
    setores = setores.merge(demo[["CD_SETOR", *GRUPOS_IDADE]], on="CD_SETOR", how="left")

    # 3) Renda média do responsável (código achado pelo dicionário)
    dic_r = ler_dicionario(dic_renda)
    cod_renda, desc_renda = achar_variavel_renda(dic_r)
    meta["variaveis"][cod_renda] = desc_renda
    meta["variavel_renda"] = cod_renda
    renda = ler_csv_do_zip(zip_renda, [cod_renda])
    renda["renda_resp"] = para_numero(renda[cod_renda])
    setores = setores.merge(renda[["CD_SETOR", "renda_resp"]], on="CD_SETOR", how="left")

    # Setores sem ninguém (parques, represas) ficam, mas com população 0.
    setores["pop"] = setores["pop"].fillna(0)
    setores["domicilios"] = setores["domicilios"].fillna(0)

    meta["n_setores"] = int(len(setores))
    meta["pop_total"] = float(setores["pop"].sum())
    meta["setores_sem_renda"] = int(setores["renda_resp"].isna().sum())
    return gpd.GeoDataFrame(setores, geometry="geometry", crs=config.CRS_METRICO), meta
