"""
Vendas SINTÉTICAS da rede fictícia – para mostrar como o potencial vira decisão.

Importante: estes números são INVENTADOS (com semente fixa, reprodutíveis).
Não existem vendas públicas por loja e categoria; simulamos para demonstrar
a análise de "gap de sortimento" que se faria com os dados reais da empresa.

História simulada: a rede hoje usa o MESMO planograma em todas as lojas (o mix
médio da cidade). Por isso as vendas de cada loja ficam no meio do caminho entre
o que a vizinhança quer (potencial local) e o que a gôndola oferece (mix padrão):

    vendas[cat] = captura × potencial_total × (α·mix_local[cat] + (1-α)·mix_padrão[cat])
                  × sazonalidade[mês, cat] × ruído

- captura: fatia do mercado da área que a loja pega (menor com mais concorrentes);
- α = 0,55: quanto a demanda local "vence" a gôndola padrão.
A diferença entre mix_local e mix vendido é a OPORTUNIDADE de ajuste do mix.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config

ALFA = 0.55
CAPTURA_BASE = 0.07        # 7% do potencial da área se não houvesse concorrente
EFEITO_CONCORRENTE = 0.12  # cada concorrente reduz a captura


def sazonalidade(mes: int, categoria: str) -> float:
    """Dezembro mais forte pra todo mundo; verão puxa bebidas; inverno puxa café/laticínios."""
    s = 1.0 + (0.15 if mes == 12 else 0) + (0.04 if mes == 11 else 0) - (0.05 if mes == 2 else 0)
    if categoria == "Bebidas alcoólicas":
        s *= 1.25 if mes in (12, 1, 2) else (0.85 if mes in (6, 7) else 1.0)
    if categoria == "Café e bebidas não alcoólicas" and mes in (1, 2, 12):
        s *= 1.08
    if categoria == "Laticínios e frios" and mes in (6, 7):
        s *= 1.06
    return s


def gerar_vendas(pot: pd.DataFrame, perfil: pd.DataFrame, mix_padrao: pd.Series,
                 ano: int = 2025) -> pd.DataFrame:
    rng = np.random.default_rng(config.SEMENTE)
    linhas = []
    for loja, grupo in pot.groupby("loja_id"):
        total = grupo["total"].sum()
        conc = perfil.loc[loja, "concorrentes"]
        if pd.isna(conc):  # desconhecido: usa a mediana das outras lojas
            conc = perfil["concorrentes"].median()
        captura = CAPTURA_BASE / (1 + EFEITO_CONCORRENTE * conc) * rng.lognormal(0, 0.10)
        for _, r in grupo.iterrows():
            mix = ALFA * r["share"] + (1 - ALFA) * mix_padrao[r["categoria"]]
            for mes in range(1, 13):
                v = captura * total * mix * sazonalidade(mes, r["categoria"]) * rng.lognormal(0, 0.05)
                linhas.append({"loja_id": loja, "mes": f"{ano}-{mes:02d}",
                               "categoria": r["categoria"], "vendas": round(v, 2)})
    return pd.DataFrame(linhas)


def gap_sortimento(pot: pd.DataFrame, vendas: pd.DataFrame) -> pd.DataFrame:
    """
    Compara o peso de cada categoria no POTENCIAL da área com o peso nas VENDAS.
    gap > 0: a vizinhança quer mais daquilo do que a loja vende -> ampliar espaço.
    oportunidade_rs: quanto a categoria venderia/mês se o mix de vendas
    acompanhasse o potencial (mantendo o faturamento total).
    """
    v = vendas.groupby(["loja_id", "categoria"])["vendas"].sum().rename("vendas_ano").reset_index()
    v["share_vendas"] = v["vendas_ano"] / v.groupby("loja_id")["vendas_ano"].transform("sum")
    g = pot.merge(v, on=["loja_id", "categoria"])
    g["gap_pp"] = 100 * (g["share"] - g["share_vendas"])
    g["oportunidade_rs_mes"] = (g["share"] - g["share_vendas"]) * \
        g.groupby("loja_id")["vendas_ano"].transform("sum") / 12
    # Regra de decisão: diferença RELATIVA de pelo menos 5% entre potencial e vendas.
    g["gap_rel"] = g["share"] / g["share_vendas"] - 1
    g["acao"] = np.select([g["gap_rel"] >= 0.05, g["gap_rel"] <= -0.05],
                          ["Ampliar", "Reduzir"], "Manter")
    return g
