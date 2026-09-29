"""
POF 2017-2018 (IBGE) – o que cada perfil de família compra.

A Pesquisa de Orçamentos Familiares mede quanto as famílias gastam por mês com
cada tipo de alimento. Usamos a tabela 6972 do SIDRA, recorte estado de SP,
que traz o gasto médio mensal FAMILIAR por CLASSE DE RENDA e por TIPO de
alimento (arroz, carnes, leite, pão, refrigerante…).

Aqui transformamos a resposta da API numa matriz:
    linhas  = classe de renda da POF
    colunas = categoria de gôndola da loja (juntando itens da POF)
    valor   = R$ por família por mês (preços de jan/2018)
"""
from __future__ import annotations

import pandas as pd

from . import config


def _sidra_para_df(dados: list) -> pd.DataFrame:
    """
    A API do SIDRA devolve uma lista em que a 1ª linha é o CABEÇALHO
    (ex.: {"D4C": "Classes de rendimento (Código)", ...}) e as demais são dados.
    Renomeamos as colunas usando esse cabeçalho, para não depender da ordem.
    """
    cab, linhas = dados[0], dados[1:]
    df = pd.DataFrame(linhas).rename(columns=cab)
    df["valor"] = pd.to_numeric(df["Valor"], errors="coerce")  # '-', '..', 'X' -> NaN
    return df


def _coluna(df: pd.DataFrame, trecho: str) -> str:
    return next(c for c in df.columns if trecho.lower() in c.lower() and "(Código)" in c)


def matriz_pof(dados: list) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devolve (itens POF por classe, categorias da loja por classe)."""
    df = _sidra_para_df(dados)
    col_classe = _coluna(df, "rendimento")
    col_item = _coluna(df, "despesa")
    itens = df.pivot_table(index=col_classe, columns=col_item, values="valor", aggfunc="first")
    itens.index.name, itens.columns.name = "classe", "item"
    itens = itens.fillna(0.0)

    cat = pd.DataFrame(index=itens.index)
    for categoria, codigos in config.CATEGORIAS_LOJA.items():
        presentes = [c for c in codigos if c in itens.columns]
        cat[categoria] = itens[presentes].sum(axis=1)
    return itens, cat


def gasto_trabalhador(itens: pd.DataFrame) -> pd.Series:
    """
    Gasto mensal POR TRABALHADOR com lanche/bebida fora de casa que um mercado
    de proximidade consegue disputar. Usa a média do estado (classe 'Total' = 7999):
        gasto da família ÷ trabalhadores por família × parcela disputável
    """
    p = config.PREMISSAS
    media = itens.loc["7999"]
    out = {}
    for categoria, codigos in config.ITENS_FORA_DE_CASA_TRABALHADOR.items():
        familia = media[[c for c in codigos if c in media.index]].sum()
        out[categoria] = familia / p["trabalhadores_por_familia"] * p["parcela_trabalhador_mercado"]
    return pd.Series(out)


def fator_ipca(dados: list) -> float:
    """Quanto os preços subiram entre jan/2018 (POF) e jul/2022 (Censo)."""
    df = _sidra_para_df(dados)
    col_mes = _coluna(df, "mês")
    idx = df.set_index(col_mes)["valor"]
    return float(idx[config.IPCA_MES_CENSO] / idx[config.IPCA_MES_POF])


def classe_pof(renda_familiar_2018: float) -> str | None:
    """Em qual classe de renda da POF cai uma renda familiar (R$ de jan/2018)."""
    if pd.isna(renda_familiar_2018):
        return None
    for codigo, _, lo, hi in config.CLASSES_POF:
        if lo <= renda_familiar_2018 < hi:
            return codigo
    return config.CLASSES_POF[-1][0]
