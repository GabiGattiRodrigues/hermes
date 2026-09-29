"""
Pesquisa Origem-Destino 2023 (Metrô-SP) – quem TRABALHA perto de cada loja.

O Censo diz onde as pessoas moram, mas não onde elas passam o dia. A Pesquisa
OD entrevista ~30 mil domicílios da Região Metropolitana e registra, para cada
pessoa, a COORDENADA do local de trabalho. Cada entrevistado tem um peso de
expansão (FE_PESS) = quantas pessoas reais ele representa.

Somando os pesos dos locais de trabalho que caem dentro da área de 15 min da
loja, temos uma estimativa de quantos empregos existem ali.

Campos usados do banco (Banco2023_divulgacao_190225.dbf):
- F_PESS   = 1 no primeiro registro de cada pessoa (o banco tem uma linha por VIAGEM)
- FE_PESS  = fator de expansão da pessoa
- SETOR1   = setor de atividade do trabalho principal (0/vazio = não trabalha)
- CO_TR1_X / CO_TR1_Y = coordenadas do trabalho principal (Córrego Alegre UTM 23S)
"""
from __future__ import annotations

import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd

from . import config

CAMPOS = ["F_PESS", "FE_PESS", "SETOR1", "CO_TR1_X", "CO_TR1_Y"]


def extrair_dbf(caminho_zip: Path) -> Path:
    """Extrai só o .dbf do banco de microdados (o zip tem também relatórios e mapas)."""
    destino_dir = caminho_zip.parent / "od2023"
    with zipfile.ZipFile(caminho_zip) as z:
        nome = next(n for n in z.namelist()
                    if n.lower().endswith(".dbf") and "banco" in n.lower())
        destino = destino_dir / Path(nome).name
        if not destino.exists():
            destino_dir.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(z.read(nome))
    return destino


def pontos_de_trabalho(caminho_zip: Path) -> gpd.GeoDataFrame:
    """Um ponto por pessoa que trabalha, com o peso de expansão."""
    from dbfread import DBF

    dbf = extrair_dbf(caminho_zip)
    linhas = [{c: r.get(c) for c in CAMPOS}
              for r in DBF(str(dbf), encoding="latin-1", load=False)
              if r.get("F_PESS") == 1]
    df = pd.DataFrame(linhas)
    df = df[df["SETOR1"].notna() & ~df["SETOR1"].astype(str).str.strip().isin(["", "0"])]
    df = df[df["CO_TR1_X"].fillna(0).astype(float).gt(0) & df["CO_TR1_Y"].fillna(0).astype(float).gt(0)]
    gdf = gpd.GeoDataFrame(
        df[["FE_PESS", "SETOR1"]].rename(columns={"FE_PESS": "peso", "SETOR1": "setor_atividade"}),
        geometry=gpd.points_from_xy(df["CO_TR1_X"].astype(float), df["CO_TR1_Y"].astype(float)),
        crs=config.CRS_OD,
    )
    return gdf.to_crs(config.CRS_METRICO)
