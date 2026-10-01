"""
Hermes – app Streamlit.

Lê só os arquivos leves de dados/processados/ (gerados por `python -m hermes.pipeline`).
Rodar:  streamlit run app/app.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import folium
import geopandas as gpd
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from folium.plugins import HeatMap
import streamlit.components.v1 as components

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(Path(__file__).parent))
from hermes import config  # noqa: E402
from textos import (AFINIDADE, AFINIDADE_EXEMPLO, CASE, CASE_ACHADOS_TIT, CASE_CONCEITOS_TIT,
                    CASE_LOJAS_TIT, CASE_NAVEGAR, CASE_PROBLEMA, CASE_RESUMO, FONTES, KMEANS, KMEANS_K,  # noqa: E402
                    LIMITES, METODO, PREMISSAS_TXT, T)

DADOS = Path(os.environ.get("HERMES_DADOS", RAIZ / "dados" / "processados"))

# Paleta (validada para daltonismo): um tom por perfil de loja, sempre na mesma ordem.
COR_PERFIL = {
    "corporativa": "#2563c9",
    "misto": "#9b4fc4",
    "residencial": "#16967a",
    "familiar": "#e0851f",
    "extra": "#6b7280",
}
AZUL = "#2563c9"
AZUL_CLARO = "#9cc0f0"
CINZA = "#9aa3ad"

st.set_page_config(page_title="Hermes · mapa de lojas", page_icon="🗺️", layout="wide")


# ---------------------------------------------------------------------------
# Dados
# ---------------------------------------------------------------------------
@st.cache_data
def carregar():
    lojas = gpd.read_file(DADOS / "lojas.geojson")
    iso = gpd.read_file(DADOS / "isocronas.geojson")
    conc = gpd.read_file(DADOS / "concorrentes.geojson")
    for col in ("loja_id", "nome", "tipo"):  # arquivo pode vir vazio (OSM fora do ar)
        if col not in conc.columns:
            conc[col] = pd.Series(dtype=str)
    setores = gpd.read_file(DADOS / "setores_lojas.geojson")
    emp = gpd.read_file(DADOS / "empregos_pontos.geojson")
    pot = pd.read_csv(DADOS / "potencial.csv")
    pot_cid = pd.read_csv(DADOS / "potencial_cidade.csv")
    vendas = pd.read_csv(DADOS / "vendas_sinteticas.csv")
    gap = pd.read_csv(DADOS / "gap_sortimento.csv")
    meta = json.loads((DADOS / "metadados.json").read_text("utf-8"))
    return lojas, iso, conc, setores, emp, pot, pot_cid, vendas, gap, meta


lojas, iso, conc, setores, emp, pot, pot_cid, vendas, gap, meta = carregar()

# ---------------------------------------------------------------------------
# Barra lateral: idioma e loja
# ---------------------------------------------------------------------------
IMG = Path(__file__).parent / "assets" / "hermes.png"
with st.sidebar:
    if IMG.exists():
        st.image(str(IMG), width="stretch")
    lang = "en" if st.radio("🌐 Idioma / Language", ["Português", "English"], horizontal=True) == "English" else "pt"


def t(chave: str, **kw) -> str:
    txt = T[chave][lang]
    return txt.format(**kw) if kw else txt


def cat(nome: str) -> str:
    return nome if lang == "pt" else config.CATEGORIA_EN.get(nome, nome)


def brl(v: float, casas: int = 0) -> str:
    s = f"{v:,.{casas}f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".") if lang == "pt" else "BRL " + s


def num(v: float) -> str:
    s = f"{v:,.0f}"
    return s.replace(",", ".") if lang == "pt" else s


col_perfil = "perfil" if lang == "pt" else "perfil_en"
lojas = lojas.sort_values("loja_id")
opcoes = {f"{r.loja_id} · {r.nome}": r.loja_id for r in lojas.itertuples()}
# ---------------------------------------------------------------------------
# Barra lateral: mapa clicável para escolher a loja + perfil do comércio
# ---------------------------------------------------------------------------
REDES = [  # (padrão no nome, bandeira/grupo, formato)
    (r"carrefour|atacad[aã]o", "Grupo Carrefour", "rede"),
    (r"oxxo", "Oxxo", "rede"),
    (r"\bdia\b", "Dia", "rede"),
    (r"p[aã]o de a[cç][uú]car|extra", "GPA (Pão de Açúcar/Extra)", "rede"),
    (r"assa[ií]", "Assaí", "rede"),
    (r"\boba\b", "Oba", "rede"),
    (r"st\.? ?march", "St Marche", "rede"),
    (r"americanas", "Americanas", "rede"),
    (r"ampm|shell select|br mania|^br$", "Conveniência de posto", "posto"),
    (r"sonda|mambo|hirota|futurama|padr[aã]o|pastorinho|econ\b", "Rede regional", "regional"),
]


def classificar(nome: str) -> tuple[str, str]:
    import re
    n = (nome or "").lower()
    if n in ("", "(sem nome)"):
        return ("Sem nome no OSM" if lang == "pt" else "Unnamed in OSM"), "sem_nome"
    for padrao, bandeira, formato in REDES:
        if re.search(padrao, n):
            return bandeira, formato
    return ("Independente" if lang == "pt" else "Independent"), "independente"


def perfil_comercio(loja_id: str) -> dict | None:
    """Resumo do comércio de alimentos (concorrência) dentro da isócrona da loja."""
    lj = lojas.set_index("loja_id").loc[loja_id]
    if pd.isna(lj["concorrentes"]):
        return None
    c = conc[conc["loja_id"] == loja_id].copy()
    c[["bandeira", "formato"]] = [classificar(n) for n in c["nome"]] if len(c) else pd.DataFrame(columns=["a", "b"])
    pt_loja = gpd.GeoSeries.from_xy([lj["lon"]], [lj["lat"]], crs=config.CRS_WGS84).to_crs(config.CRS_METRICO).iloc[0]
    dist = c.to_crs(config.CRS_METRICO).distance(pt_loja) if len(c) else pd.Series(dtype=float)
    n = len(c)
    return {
        "n": n,
        "por10mil": n / lj["pop"] * 1e4 if lj["pop"] else np.nan,
        "pct_redes": (c["formato"].isin(["rede", "posto"]).mean() if n else np.nan),
        "super": int((c["tipo"] == "supermarket").sum()), "conv": int((c["tipo"] == "convenience").sum()),
        "mais_proximo": dist.min() if n else np.nan,
        "tabela": c.assign(dist_m=dist.round(0).values if n else []),
    }


@st.cache_data
def medias_comercio(_lojas_ids: tuple) -> dict:
    vals = [perfil_comercio(l) for l in _lojas_ids]
    vals = [v for v in vals if v]
    return {k: np.nanmean([v[k] for v in vals]) for k in ["n", "por10mil", "pct_redes", "mais_proximo"]}


def _ao_clicar_mapa():
    """Clique numa loja do mapa lateral -> atualiza a loja escolhida na lista."""
    ev = st.session_state.get("mapa_lateral")
    try:
        pontos = ev["selection"]["points"]
    except (KeyError, TypeError):
        return
    if pontos:
        lid = pontos[0]["customdata"][0]
        rotulo = next((k for k, v in opcoes.items() if v == lid), None)
        if rotulo:
            st.session_state["loja_escolhida"] = rotulo


def mapa_lateral(loja_atual: str):
    d = lojas.copy()
    d["sel"] = np.where(d["loja_id"] == loja_atual, 16, 9)
    d["perfil_txt"] = d[col_perfil]
    fig = px.scatter_map(d, lat="lat", lon="lon", color="perfil_chave", color_discrete_map=COR_PERFIL,
                         size="sel", size_max=16, custom_data=["loja_id", "nome", "perfil_txt"],
                         zoom=9.4, center={"lat": -23.585, "lon": -46.625}, height=300)
    fig.update_traces(hovertemplate="<b>%{customdata[0]} · %{customdata[1]}</b><br>%{customdata[2]}<extra></extra>",
                      marker=dict(opacity=0.95))
    # Arrastar = mover o mapa; zoom pelos botões + / − (a rodinha do mouse fica desligada porque,
    # na barra lateral, ela briga com a rolagem da página). uirevision fixo = o zoom e a posição
    # escolhidos pelo usuário não "voltam" quando o app recarrega após um clique.
    fig.update_layout(map_style="carto-positron", margin=dict(l=0, r=0, t=0, b=0), showlegend=False,
                      clickmode="event+select", dragmode="pan", uirevision="mapa_lateral",
                      modebar=dict(orientation="v", bgcolor="rgba(255,255,255,0.85)"))
    return fig


if "loja_escolhida" not in st.session_state:
    st.session_state["loja_escolhida"] = list(opcoes)[0]
with st.sidebar:
    st.caption(t("mapa_lateral"))
    loja_sel = opcoes[st.session_state["loja_escolhida"]]
    st.plotly_chart(mapa_lateral(loja_sel), key="mapa_lateral", on_select=_ao_clicar_mapa,
                    selection_mode="points", config={"displayModeBar": True, "displaylogo": False, "scrollZoom": False,
                            "doubleClick": False,
                            "modeBarButtons": [["zoomInMap", "zoomOutMap", "resetViewMap"]]})
    loja_sel = opcoes[st.selectbox(t("loja"), list(opcoes), key="loja_escolhida")]
    _pc = perfil_comercio(loja_sel)
    st.markdown(f"**{t('comercio_titulo')}**")
    if _pc is None:
        st.caption(t("sem_dados_conc"))
    else:
        _dec = (lambda v: f"{v:.1f}".replace(".", ",")) if lang == "pt" else (lambda v: f"{v:.1f}")
        _red = "–" if np.isnan(_pc["pct_redes"]) else f"{_pc['pct_redes']:.0%}"
        st.markdown(f"{t('estab')}: **{_pc['n']}** ({_pc['super']} super · {_pc['conv']} conv.)  \n"
                    f"{t('por10mil')}: **{_dec(_pc['por10mil'])}**  \n"
                    f"{t('pct_redes')}: **{_red}**")
        st.caption("➡️ " + ("detalhes na aba Raio-X da loja" if lang == "pt" else "details in the Store deep-dive tab"))
    st.markdown("---")
    st.markdown(t("sobre"))

L = lojas.set_index("loja_id").loc[loja_sel]

c_img, c_tit = st.columns([1, 4], vertical_alignment="center")
if IMG.exists():
    c_img.image(str(IMG), width="stretch")
with c_tit:
    st.title(t("titulo"))
    st.caption(t("subtitulo"))
st.info(t("aviso_ficticio", rede=meta.get("nome_rede", "Ágora Express")))

abas = st.tabs([t("aba_case"), t("aba_mapa"), t("aba_loja"), t("aba_comparar"), t("aba_vendas"), t("aba_dados")])

# ---------------------------------------------------------------------------
# 0. O case (contexto, conceitos e principais achados)
# ---------------------------------------------------------------------------
def achados() -> str:
    """Principais achados calculados a partir dos dados (não são texto fixo)."""
    area = iso.to_crs(config.CRS_METRICO).area / 1e6
    circ = np.pi * (meta["distancia_caminhada_m"] / 1000) ** 2
    idx = pot.merge(lojas[["loja_id", "nome", "renda_media_resp"]], on="loja_id")
    pronto = idx[idx.categoria == "Pronto para consumo"].nlargest(3, "indice")
    merc = idx[idx.categoria == "Mercearia básica"]["indice"]
    rica = lojas.loc[lojas["renda_media_resp"].idxmax()]
    pobre = lojas.loc[lojas["renda_media_resp"].idxmin()]
    def ind(loja, c):
        return idx[(idx.loja_id == loja) & (idx.categoria == c)]["indice"].iloc[0]
    top3 = ", ".join(f"{r.nome} ({r.indice:.0f})" for r in pronto.itertuples())
    if lang == "pt":
        def d(v):  # decimal com vírgula
            return f"{v:.1f}".replace(".", ",")
        return (f"- **A área real de 15 min é bem menor que um círculo:** {d(area.min())} a {d(area.max())} km², "
                f"contra {d(circ)} km² de um círculo de {d(meta['distancia_caminhada_m']/1000)} km.\n"
                f"- **Quem trabalha perto puxa o lanche:** o índice de *pronto para consumo* chega a {top3}.\n"
                f"- **A renda muda as bordas do carrinho:** *bebidas alcoólicas* têm índice "
                f"{ind(rica.loja_id, 'Bebidas alcoólicas'):.0f} em {rica.nome} (maior renda) e "
                f"{ind(pobre.loja_id, 'Bebidas alcoólicas'):.0f} em {pobre.nome} (menor renda); *aves e ovos* fazem o "
                f"caminho inverso ({ind(rica.loja_id, 'Aves e ovos'):.0f} × {ind(pobre.loja_id, 'Aves e ovos'):.0f}).\n"
                f"- **O miolo é igual em todo lugar:** a *mercearia básica* varia só entre {merc.min():.0f} e "
                f"{merc.max():.0f}. Dá para ter um miolo padrão e adaptar só as bordas por perfil de loja.")
    return (f"- **The real 15-min area is much smaller than a circle:** {area.min():.1f} to {area.max():.1f} km², "
            f"versus {circ:.1f} km² for a {meta['distancia_caminhada_m']/1000:.1f} km circle.\n"
            f"- **Nearby workers drive snacks:** the *ready-to-eat* index reaches {top3}.\n"
            f"- **Income reshapes the edges of the basket:** *alcoholic drinks* score "
            f"{ind(rica.loja_id, 'Bebidas alcoólicas'):.0f} in {rica.nome} (highest income) and "
            f"{ind(pobre.loja_id, 'Bebidas alcoólicas'):.0f} in {pobre.nome} (lowest); *poultry & eggs* go the other way "
            f"({ind(rica.loja_id, 'Aves e ovos'):.0f} × {ind(pobre.loja_id, 'Aves e ovos'):.0f}).\n"
            f"- **The core is the same everywhere:** *dry grocery* only ranges from {merc.min():.0f} to "
            f"{merc.max():.0f}. A standard core plus profile-specific edges is enough.")


def recomendacao_loja(loja_id: str) -> str:
    """
    Recomendação de sortimento em linguagem de negócio: "se eu abrir um mercado aqui,
    priorizo X, Y e Z porque...". Os motivos saem dos dados: quanto do potencial vem de
    quem trabalha na área e quanto o carrinho das famílias daqui difere do da cidade.
    """
    pt = lang == "pt"
    lj = lojas.set_index("loja_id").loc[loja_id]
    p = pot[pot.loja_id == loja_id].set_index("categoria")
    cid = pot_cid.set_index("categoria")
    sh_mor = p["moradores"] / p["moradores"].sum()             # carrinho só das famílias daqui
    sh_mor_cid = cid["moradores"] / cid["moradores"].sum()     # carrinho das famílias da cidade
    pct_trab = (p["trabalhadores"] / p["total"]).fillna(0)     # quanto do potencial vem de quem trabalha
    def pct(v):
        txt = f"{v * 100:.1f}%"
        return txt.replace(".", ",") if pt else txt

    def motivo(c: str) -> str:
        if pct_trab[c] >= 0.25:
            if pt:
                return (f"{pct(pct_trab[c])} do potencial dessa categoria vem de quem **trabalha** na área "
                        f"(~{num(lj['empregos'] / 1e3)} mil empregos), não de quem mora.")
            return (f"{pct(pct_trab[c])} of this category's potential comes from people who **work** in the area "
                    f"(~{num(lj['empregos'] / 1e3)}k jobs), not residents.")
        mais = sh_mor[c] >= sh_mor_cid[c]
        renda = brl(lj["renda_media_resp"] / 1e3, 1) + (" mil" if pt else "k")
        if pt:
            return (f"o carrinho das famílias daqui (renda média do responsável {renda}) põe **{pct(sh_mor[c])}** "
                    f"do gasto com alimentos nessa categoria, contra {pct(sh_mor_cid[c])} na média de SP.")
        return (f"local families' basket (head-of-household income {renda}) puts **{pct(sh_mor[c])}** of food "
                f"spending in this category, versus {pct(sh_mor_cid[c])} across São Paulo.")

    ordem = p.sort_values("indice", ascending=False)
    prior = ordem[ordem["indice"] >= 105].head(3)
    menos = ordem[ordem["indice"] <= 95].tail(3).iloc[::-1]
    linhas = [("**🛒 Se você for abrir um mercado nesta região, o sortimento deve priorizar:**" if pt else
               "**🛒 If you open a store in this area, the assortment should prioritize:**")]
    for i, (c, r) in enumerate(prior.iterrows(), 1):
        linhas.append(f"{i}. **{cat(c)}** (índice {r['indice']:.0f}) — " + ("porque " if pt else "because ") + motivo(c)
                      if pt else f"{i}. **{cat(c)}** (index {r['indice']:.0f}) — because " + motivo(c))
    if not len(prior):
        linhas.append("- " + ("nenhuma categoria se destaca muito: o mix médio da cidade já atende bem." if pt else
                              "no category stands out much: the city's average mix already fits."))
    if len(menos):
        linhas.append("")
        linhas.append("**↘️ E pode dar menos espaço para:**" if pt else "**↘️ And give less space to:**")
        for c, r in menos.iterrows():
            linhas.append(f"- **{cat(c)}** (índice {r['indice']:.0f}) — " + ("porque " if pt else "because ")
                          + motivo(c) if pt else f"- **{cat(c)}** (index {r['indice']:.0f}) — because " + motivo(c))

    # Contexto: público e concorrência
    ctx = []
    if lj["empregos_por_morador"] >= 2:
        ctx.append("🕛 O público principal é **quem trabalha** na região: pico no almoço e no fim da tarde. Lanche, "
                   "bebida gelada e café perto do caixa." if pt else
                   "🕛 The main audience is **office workers**: peaks at lunch and late afternoon. Snacks, cold drinks "
                   "and coffee near the checkout.")
    elif lj["pct_0_14"] >= lojas["pct_0_14"].median() * 1.2:
        ctx.append("👨‍👩‍👧 Muitas **famílias com crianças**: embalagens maiores, mercearia de reposição e preço visível "
                   "na gôndola." if pt else
                   "👨‍👩‍👧 Many **families with kids**: larger packs, staple groceries and visible shelf prices.")
    else:
        ctx.append("🏠 Público de **moradores** fazendo compra de reposição: frescos todos os dias fazem a loja virar "
                   "hábito." if pt else
                   "🏠 **Residents** doing top-up shopping: fresh produce every day turns the store into a habit.")
    pc = perfil_comercio(loja_id)
    if pc is not None:
        med = medias_comercio(tuple(lojas["loja_id"]))
        d = (lambda v: f"{v:.1f}".replace(".", ",")) if pt else (lambda v: f"{v:.1f}")
        if pc["por10mil"] > med["por10mil"] * 1.2:
            ctx.append(f"🏬 **Muita concorrência mapeada** ({pc['n']} mercados, {d(pc['por10mil'])} por 10 mil moradores; média "
                       f"{d(med['por10mil'])}): diferenciar pelo mix acima e pela conveniência, não por preço." if pt else
                       f"🏬 **High competition** ({pc['n']} stores, {d(pc['por10mil'])} per 10k residents; avg "
                       f"{d(med['por10mil'])}): win on the mix above and on convenience, not price.")
        elif pc["por10mil"] < med["por10mil"] * 0.8:
            ctx.append(f"🏬 **Pouca concorrência mapeada** ({pc['n']} mercados, {d(pc['por10mil'])} por 10 mil moradores; média "
                       f"{d(med['por10mil'])}): espaço para também capturar a compra do mês." if pt else
                       f"🏬 **Low competition** ({pc['n']} stores, {d(pc['por10mil'])} per 10k residents; avg "
                       f"{d(med['por10mil'])}): room to also capture the monthly shop.")
    ctx.append(f"🧩 Modelo de gôndola: perfil **{lj[col_perfil]}** (k-means)." if pt else
               f"🧩 Shelf template: **{lj[col_perfil]}** profile (k-means).")
    linhas.append("")
    linhas.append("**📍 Contexto da região:**" if pt else "**📍 Area context:**")
    linhas += [f"- {c}" for c in ctx]
    return "\n".join(linhas)


def recomendacao_rede() -> pd.DataFrame:
    """Um planograma por perfil: o que ganha e o que perde espaço (média do índice das lojas do perfil)."""
    d = pot.merge(lojas[["loja_id", col_perfil]], on="loja_id")
    m = d.groupby([col_perfil, "categoria"])["indice"].mean().reset_index()
    linhas = []
    for perfil, g in m.groupby(col_perfil):
        g = g.sort_values("indice", ascending=False)
        lojas_p = ", ".join(lojas[lojas[col_perfil] == perfil]["nome"])
        mais = ", ".join(f"{cat(c)} ({v:.0f})" for c, v in g[g.indice >= 103].head(3)[["categoria", "indice"]].values)
        menos = ", ".join(f"{cat(c)} ({v:.0f})" for c, v in g[g.indice <= 97].tail(3)[["categoria", "indice"]].values[::-1])
        linhas.append([perfil, lojas_p, mais or "–", menos or "–"])
    cols = (["Perfil", "Lojas", "Ganha espaço (índice)", "Perde espaço (índice)"] if lang == "pt" else
            ["Profile", "Stores", "Gains space (index)", "Loses space (index)"])
    return pd.DataFrame(linhas, columns=cols)


def conceitos() -> list[tuple[str, str, str, str]]:
    """Cartões didáticos: (título, o que é, exemplo prático com dados reais, por que importa)."""
    lj = lojas.set_index("loja_id")
    fl, cr = lj.loc["AG01"], lj.loc["AG14"]
    circ = np.pi * (meta["distancia_caminhada_m"] / 1000) ** 2
    pfl = pot[pot.loja_id == "AG01"].set_index("categoria")
    pron = pfl.loc["Pronto para consumo"]
    pof_cat = pd.read_csv(DADOS / "pof_categorias.csv", index_col=0)
    pof_cat.index = pof_cat.index.astype(str)
    h_baixa, h_alta = pof_cat.loc["47558", "Hortifruti"], pof_cat.loc["47564", "Hortifruti"]
    gfl = gap[gap.loja_id == "AG01"].set_index("categoria").loc["Pronto para consumo"]
    grupos = lojas.groupby(col_perfil)["nome"].apply(lambda x: ", ".join(x))
    def d(v, c=1):
        txt = f"{v:,.{c}f}"
        return txt.replace(",", "X").replace(".", ",").replace("X", ".") if lang == "pt" else txt
    if lang == "pt":
        return [
            ("🚶 Isócrona (área de 15 min a pé)",
             "Todo lugar onde dá para chegar **andando 15 minutos pelas ruas** a partir da loja. Não é um círculo: "
             "avenidas, rios e quarteirões grandes encurtam o caminho possível.",
             f"Na Faria Lima, a área real tem **{d(fl['area_km2'])} km²**. Um círculo de 1,2 km teria {d(circ)} km², "
             f"quase o dobro, e contaria gente que na prática não vai a pé até a loja.",
             "Define **quem realmente é cliente potencial** da loja."),
            ("🏘️ Setor censitário",
             "O \"pedacinho\" de cidade que o IBGE usa no Censo: mais ou menos um quarteirão, com ~150 casas. "
             "Para cada um sabemos quantas pessoas moram, a idade e a renda.",
             f"A área da Faria Lima cruza vários setores e soma **{num(fl['pop'])} moradores** e "
             f"**{num(fl['domicilios'])} domicílios**. Se só metade de um setor cai na área, contamos só metade dele.",
             "É o **tijolinho** com que montamos o perfil de cada vizinhança."),
            ("💰 Potencial de gasto",
             "Quanto dinheiro as pessoas da área gastam por mês com cada categoria de alimento, **em qualquer lugar** "
             "(não só na nossa loja). Vem da POF, pesquisa do IBGE sobre o orçamento das famílias.",
             f"Uma família de renda mais baixa gasta ~{brl(h_baixa)} por mês com hortifruti, e uma de renda alta "
             f"~{brl(h_alta)} (valores de 2018). Somando todas as famílias e trabalhadores da Faria Lima, o potencial "
             f"total da área é de **{brl(fl['potencial_total_mes'] / 1e6, 1)} milhões por mês**.",
             "Mostra **o tamanho do mercado** em volta de cada loja."),
            ("📐 Índice de afinidade",
             "Compara **o peso de cada categoria no carrinho da vizinhança** com o peso na cidade inteira. "
             "**100 = igual à média de SP**; acima de 100, a vizinhança compra proporcionalmente mais daquilo.",
             f"Na cidade, **{d(pron['share_cidade']*100)}%** do gasto potencial com alimentos vai para *pronto para consumo*. "
             f"Na Faria Lima vai **{d(pron['share']*100)}%**. Então o índice é {d(pron['share']*100)} ÷ "
             f"{d(pron['share_cidade']*100)} × 100 = **{pron['indice']:.0f}**, ou seja, o dobro da média, "
             "puxado por quem trabalha ali e compra lanche.",
             "Diz **o que ganhar e o que perder espaço na gôndola**, e compara lojas grandes e pequenas na mesma régua."),
            ("🧠 Perfil de loja (k-means)",
             "O k-means é um algoritmo que **junta coisas parecidas em grupos**. Aqui ele agrupou as 15 lojas por "
             "renda, idade, empregos e densidade da vizinhança. É como segmentar clientes, só que com lojas.",
             "Ele formou 4 perfis: " + "; ".join(f"**{k}**: {v}" for k, v in grupos.items()) + ".",
             "Em vez de 15 gôndolas diferentes, a rede precisa de **4 modelos**, um por perfil."),
            ("🛒 Mix × vendas (gap)",
             "Compara o que a vizinhança **quer comprar** (potencial) com o que a loja **vende hoje**. Se a categoria pesa "
             "bem mais no potencial do que nas vendas, está faltando espaço para ela.",
             f"Na Faria Lima, *pronto para consumo* é {d(gfl['share']*100)}% do potencial e só "
             f"{d(gfl['share_vendas']*100)}% das vendas (simuladas). Recomendação: **ampliar**, com oportunidade de "
             f"~{brl(gfl['oportunidade_rs_mes'])} por mês.",
             "Transforma a análise em **uma ação concreta** para o time comercial."),
        ]
    return [
        ("🚶 Isochrone (15-min walking area)",
         "Everywhere you can reach **walking 15 minutes along the streets** from the store. It is not a circle: "
         "avenues, rivers and big blocks shorten the possible route.",
         f"In Faria Lima the real area is **{d(fl['area_km2'])} km²**. A 1.2 km circle would cover {d(circ)} km², "
         "almost double, counting people who would never actually walk to the store.",
         "Defines **who is really a potential customer** of the store."),
        ("🏘️ Census tract",
         "The small piece of city IBGE uses in the Census: roughly one block, with ~150 homes. For each one we know "
         "how many people live there, their age and income.",
         f"The Faria Lima area crosses several tracts and adds up to **{num(fl['pop'])} residents** and "
         f"**{num(fl['domicilios'])} households**. If only half a tract falls inside the area, we count only half of it.",
         "It is the **building block** of each neighborhood profile."),
        ("💰 Spending potential",
         "How much money people in the area spend per month on each food category, **anywhere** (not only at our "
         "store). It comes from the POF, IBGE's household budget survey.",
         f"A lower-income family spends ~{brl(h_baixa)} a month on fruit & vegetables, a high-income one "
         f"~{brl(h_alta)} (2018 values). Adding up every family and worker in Faria Lima, the area's total "
         f"potential is **{brl(fl['potencial_total_mes'] / 1e6, 1)} million per month**.",
         "Shows **the size of the market** around each store."),
        ("📐 Affinity index",
         "Compares **each category's weight in the neighborhood's basket** with its weight in the whole city. "
         "**100 = São Paulo average**; above 100, the neighborhood buys proportionally more of it.",
         f"Citywide, **{d(pron['share_cidade']*100)}%** of food spending potential goes to *ready-to-eat*. In "
         f"Faria Lima it is **{d(pron['share']*100)}%**. So the index is {d(pron['share']*100)} ÷ "
         f"{d(pron['share_cidade']*100)} × 100 = **{pron['indice']:.0f}**: double the average, driven by the office "
         "workers buying snacks.",
         "Tells **what should gain or lose shelf space**, putting big and small stores on the same scale."),
        ("🧠 Store profile (k-means)",
         "k-means is an algorithm that **puts similar things into groups**. Here it grouped the 15 stores by the "
         "neighborhood's income, age, jobs and density. Like customer segmentation, but for stores.",
         "It formed 4 profiles: " + "; ".join(f"**{k}**: {v}" for k, v in grupos.items()) + ".",
         "Instead of 15 different shelf layouts, the chain needs **4 templates**, one per profile."),
        ("🛒 Mix × sales (gap)",
         "Compares what the neighborhood **wants to buy** (potential) with what the store **sells today**. If a "
         "category weighs much more in potential than in sales, it lacks shelf space.",
         f"In Faria Lima, *ready-to-eat* is {d(gfl['share']*100)}% of potential but only "
         f"{d(gfl['share_vendas']*100)}% of (simulated) sales. Recommendation: **expand**, an opportunity of "
         f"~{brl(gfl['oportunidade_rs_mes'])} per month.",
         "Turns the analysis into **a concrete action** for the commercial team."),
    ]


def comparativo_lojas() -> pd.DataFrame:
    """Faria Lima × Capão Redondo, lado a lado, em linguagem de negócio."""
    lj = lojas.set_index("loja_id")
    linhas = []
    for lid in ["AG01", "AG14"]:
        r = lj.loc[lid]
        idx = pot[pot.loja_id == lid].sort_values("indice", ascending=False)
        mais = ", ".join(f"{cat(c)} ({v:.0f})" for c, v in idx.head(2)[["categoria", "indice"]].values)
        menos = ", ".join(f"{cat(c)} ({v:.0f})" for c, v in idx.tail(2)[["categoria", "indice"]].values[::-1])
        linhas.append([r["nome"], r[col_perfil], num(r["pop"]), num(r["empregos"]),
                       brl(r["renda_media_resp"]), mais, menos])
    cols = (["Loja", "Perfil (k-means)", "Moradores", "Empregos na área", "Renda média do resp.",
             "Compra MAIS que SP (índice)", "Compra MENOS que SP (índice)"] if lang == "pt" else
            ["Store", "Profile (k-means)", "Residents", "Jobs in the area", "Head-of-hh mean income",
             "Buys MORE than SP (index)", "Buys LESS than SP (index)"])
    return pd.DataFrame(linhas, columns=cols).set_index(cols[0]).T


with abas[0]:
    st.success(CASE_RESUMO[lang])
    emp_fl = num(lojas.set_index("loja_id").loc["AG01", "empregos"])
    st.markdown(CASE_PROBLEMA[lang].format(rede=meta.get("nome_rede", "Ágora Express"), emp_fl=emp_fl))

    st.markdown(f"### {CASE_CONCEITOS_TIT[lang]}")
    rot = ("O que é", "Exemplo prático", "Por que importa") if lang == "pt" else \
          ("What it is", "Practical example", "Why it matters")
    cards = conceitos()
    for i in range(0, len(cards), 2):
        cols = st.columns(2)
        for col, (tit, oque, ex, porque) in zip(cols, cards[i:i + 2]):
            with col.container(border=True):
                st.markdown(f"#### {tit}")
                st.markdown(f"**{rot[0]}:** {oque}")
                # "R$" duas vezes no mesmo texto vira fórmula LaTeX no markdown -> escapar o $
                st.info(f"**{rot[1]}:** {ex}".replace("$", "\\$"))
                st.markdown(f"✅ **{rot[2]}:** {porque}")

    st.markdown(f"### {CASE_LOJAS_TIT[lang]}")
    st.dataframe(comparativo_lojas(), width="stretch")
    st.caption("Mesma rede, mesmo tamanho de loja, vizinhanças opostas: a gôndola ideal muda." if lang == "pt"
               else "Same chain, same store size, opposite neighborhoods: the ideal shelf changes.")

    st.markdown(f"### {CASE_ACHADOS_TIT[lang]}")
    st.markdown(achados())

    st.markdown("### ✅ " + ("Recomendação para a rede" if lang == "pt" else "Recommendation for the chain"))
    st.markdown(
        "**Um miolo comum + 4 planogramas de borda.** A mercearia básica fica igual em todas as lojas; o que muda "
        "por perfil é o espaço das categorias abaixo:" if lang == "pt" else
        "**A common core + 4 edge planograms.** Dry grocery stays the same in every store; what changes by profile "
        "is the space for the categories below:")
    st.dataframe(recomendacao_rede(), hide_index=True, width="stretch")
    st.caption("Índice médio das lojas de cada perfil (100 = média da cidade). A recomendação de cada loja está na "
               "aba 🏪 Raio-X da loja." if lang == "pt" else
               "Average index of the stores in each profile (100 = city average). Each store's recommendation is in "
               "the 🏪 Store deep-dive tab.")
    st.markdown(CASE_NAVEGAR[lang])

# ---------------------------------------------------------------------------
# 1. Mapa
# ---------------------------------------------------------------------------
with abas[1]:
    c1, c2, c3 = st.columns(3)
    ver_renda = c1.toggle(t("cam_renda"), value=True)
    ver_trab = c2.toggle(t("cam_trab"), value=False)
    ver_conc = c3.toggle(t("cam_conc"), value=True)
    st.caption(t("mapa_dica"))

    centro = [L["lat"], L["lon"]]
    m = folium.Map(location=centro, zoom_start=14, tiles=None, control_scale=True)
    folium.TileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles © Esri — Esri, HERE, Garmin, © OpenStreetMap contributors", name="base").add_to(m)

    if ver_renda:
        s = setores[setores["loja_id"] == loja_sel].copy()
        s["renda_resp"] = s["renda_resp"].round(0)
        folium.Choropleth(
            geo_data=s[["CD_SETOR", "geometry"]].to_json(), data=s, columns=["CD_SETOR", "renda_resp"],
            key_on="feature.properties.CD_SETOR", fill_color="Blues", fill_opacity=0.65,
            line_opacity=0.15, nan_fill_color="#e5e7eb", legend_name=t("cam_renda") + " (R$)",
        ).add_to(m)
        folium.GeoJson(
            s[["CD_SETOR", "pop", "renda_resp", "geometry"]].to_json(),
            style_function=lambda f: {"fillOpacity": 0, "weight": 0},
            tooltip=folium.GeoJsonTooltip(["CD_SETOR", "pop", "renda_resp"],
                                          aliases=["Setor", t("moradores"), t("renda") + " (R$)"]),
        ).add_to(m)

    for r in iso.merge(lojas[["loja_id", "perfil_chave", "nome"]], on="loja_id").itertuples():
        cor = COR_PERFIL.get(r.perfil_chave, CINZA)
        destaque = r.loja_id == loja_sel
        folium.GeoJson(
            r.geometry.__geo_interface__,
            style_function=lambda f, cor=cor, d=destaque: {
                "color": cor, "weight": 3 if d else 1.5, "fillColor": cor,
                "fillOpacity": 0.0 if (d and ver_renda) else 0.12},
            tooltip=f"{r.loja_id} · {r.nome}",
        ).add_to(m)

    if ver_trab:
        e = emp[emp["loja_id"] == loja_sel]
        HeatMap([[p.y, p.x, w] for p, w in zip(e.geometry, e["peso"])], radius=18, blur=22,
                min_opacity=0.3).add_to(m)

    if ver_conc:
        for r in conc[conc["loja_id"] == loja_sel].itertuples():
            folium.CircleMarker([r.geometry.y, r.geometry.x], radius=5, color="#374151", weight=1.5,
                                fill=True, fill_color="#ffffff", fill_opacity=1,
                                tooltip=f"{r.nome} ({r.tipo})").add_to(m)

    for r in lojas.itertuples():
        cor = COR_PERFIL.get(r.perfil_chave, CINZA)
        folium.CircleMarker(
            [r.lat, r.lon], radius=9 if r.loja_id == loja_sel else 6, color="#ffffff", weight=2,
            fill=True, fill_color=cor, fill_opacity=1,
            tooltip=f"<b>{r.loja_id} · {r.nome}</b><br>{getattr(r, col_perfil)}",
        ).add_to(m)

    # As abas do Streamlit carregam escondidas (largura 0); o Leaflet então calcula
    # o zoom errado. Quando o mapa ganha tamanho de verdade, recentralizamos.
    mapa_js = m.get_name()
    m.get_root().html.add_child(folium.Element(f"""
    <script>
    (function() {{
      var ajustado = false;
      function ajustar() {{
        if (typeof {mapa_js} === 'undefined') return;
        var el = document.getElementById('{mapa_js}');
        if (!el || el.clientWidth < 50) return;
        {mapa_js}.invalidateSize();
        if (!ajustado) {{ {mapa_js}.setView([{centro[0]}, {centro[1]}], 14, {{reset: true}}); ajustado = true; }}
      }}
      new ResizeObserver(ajustar).observe(document.documentElement);
      window.addEventListener('load', function() {{ setTimeout(ajustar, 300); }});
    }})();
    </script>"""))
    # HTML do folium direto num iframe de altura fixa (mais robusto que o st_folium).
    components.html(m.get_root().render(), height=580)

    legenda = " &nbsp; ".join(
        f"<span style='color:{COR_PERFIL[k]}'>●</span> {lojas.loc[lojas.perfil_chave == k, col_perfil].iloc[0]}"
        for k in COR_PERFIL if (lojas.perfil_chave == k).any())
    st.markdown(f"**{t('legenda_iso')}:** {legenda}", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 2. Raio-X da loja
# ---------------------------------------------------------------------------
with abas[2]:
    st.subheader(f"{loja_sel} · {L['nome']} — {L[col_perfil]}")
    k = st.columns(3) + st.columns(3)  # duas linhas de 3 para os números não serem cortados
    k[0].metric(t("moradores"), num(L["pop"]))
    k[1].metric(t("domicilios"), num(L["domicilios"]))
    k[2].metric(t("empregos"), num(L["empregos"]))
    k[3].metric(t("renda"), brl(L["renda_media_resp"] / 1e3, 1) + (" mil" if lang == "pt" else "k"))
    k[4].metric(t("concorrentes"), "?" if pd.isna(L["concorrentes"]) else int(L["concorrentes"]))
    k[5].metric(t("potencial") + " " + t("por_mes"),
                brl(L["potencial_total_mes"] / 1e6, 1) + (" mi" if lang == "pt" else "M"))

    with st.container(border=True):
        st.markdown("#### 💡 " + ("Recomendação de sortimento para a região" if lang == "pt"
                                 else "Assortment recommendation for the area"))
        st.markdown(recomendacao_loja(loja_sel).replace("$", "\\$"))
        st.caption("Índice = peso da categoria no potencial da área ÷ peso na cidade × 100. Motivos calculados com "
                   "Censo 2022, Pesquisa OD 2023 e POF (dados reais)." if lang == "pt" else
                   "Index = category share of the area's potential ÷ share in the city × 100. Reasons computed from "
                   "the 2022 Census, 2023 OD Survey and POF (real data).")

    c1, c2 = st.columns([1, 1.4])
    with c1:
        faixas = ["0_14", "15_29", "30_59", "60_mais"]
        rot = ["0–14", "15–29", "30–59", "60+"]
        media = lojas[[f"pct_{f}" for f in faixas]].mean()
        fig = go.Figure()
        fig.add_bar(x=rot, y=[L[f"pct_{f}"] * 100 for f in faixas], name=L["nome"], marker_color=AZUL)
        fig.add_bar(x=rot, y=media.values * 100, name="Média das lojas" if lang == "pt" else "Store average",
                    marker_color=AZUL_CLARO)
        fig.update_layout(title=t("idade_titulo"), barmode="group", yaxis_ticksuffix="%", height=360,
                          margin=dict(t=50, b=10), legend=dict(orientation="h", y=-0.15), bargap=0.3)
        st.plotly_chart(fig, width="stretch")
    with c2:
        p = pot[pot["loja_id"] == loja_sel].copy()
        p["rotulo"] = p["categoria"].map(cat)
        p = p.sort_values("indice")
        p["desvio"] = p["indice"] - 100
        fig = go.Figure(go.Bar(
            y=p["rotulo"], x=p["desvio"], base=100, orientation="h",
            marker_color=np.where(p["desvio"] >= 0, AZUL, "#e0851f"),
            text=p["indice"].round(0).astype(int), textposition="outside",
            hovertemplate="%{y}: %{text}<extra></extra>"))
        fig.add_vline(x=100, line_color=CINZA, line_width=1)
        fig.update_layout(title=t("indice_titulo"), height=360, margin=dict(t=50, b=10, l=10),
                          xaxis=dict(range=[min(60, p["indice"].min() - 8), max(140, p["indice"].max() + 12)]))
        st.plotly_chart(fig, width="stretch")
    topo = p.sort_values("indice", ascending=False).iloc[0]
    with st.expander(t("afinidade_titulo"), expanded=True):
        st.markdown(AFINIDADE[lang])
        st.info(f"**{t('exemplo_loja')}:** " + AFINIDADE_EXEMPLO[lang].format(
            loja=L["nome"], cat=cat(topo["categoria"]), s_loja=topo["share"],
            s_cid=topo["share_cidade"], ind=topo["indice"]))

    p = pot[pot["loja_id"] == loja_sel].copy()
    p["rotulo"] = p["categoria"].map(cat)
    longo = p.melt(id_vars="rotulo", value_vars=["moradores", "trabalhadores"], var_name="origem", value_name="rs")
    longo["origem"] = longo["origem"].map({"moradores": t("moradores_s"), "trabalhadores": t("trabalhadores_s")})
    fig = px.bar(longo, y="rotulo", x="rs", color="origem", orientation="h",
                 color_discrete_sequence=[AZUL, "#e0851f"],
                 labels={"rotulo": "", "rs": t("rs_mes"), "origem": ""},
                 category_orders={"rotulo": p.sort_values("total")["rotulo"].tolist()[::-1]})
    fig.update_layout(title=t("quem_gasta"), height=380, margin=dict(t=50, b=10),
                      legend=dict(orientation="h", y=-0.15))
    fig.update_traces(marker_line_color="white", marker_line_width=1)
    st.plotly_chart(fig, width="stretch")

    # --- Perfil dos estabelecimentos (concorrência) ---
    st.subheader(t("comercio_titulo"))
    st.caption(t("comercio_sub"))
    pc = perfil_comercio(loja_sel)
    if pc is None:
        st.warning(t("sem_dados_conc"))
    else:
        med = medias_comercio(tuple(lojas["loja_id"]))
        def dl(v, m, fmt):
            return None if np.isnan(v) or np.isnan(m) else f"{fmt(v - m)} vs {t('media_lojas')}"
        kc = st.columns(4)
        kc[0].metric(t("estab"), pc["n"], dl(pc["n"], med["n"], lambda x: f"{x:+.0f}"), delta_color="off")
        _d1 = (lambda v: f"{v:.1f}".replace(".", ",")) if lang == "pt" else (lambda v: f"{v:.1f}")
        kc[1].metric(t("por10mil"), _d1(pc["por10mil"]),
                     dl(pc["por10mil"], med["por10mil"], lambda x: ("+" if x >= 0 else "") + _d1(x)), delta_color="off")
        kc[2].metric(t("pct_redes"), "–" if np.isnan(pc["pct_redes"]) else f"{pc['pct_redes']:.0%}",
                     dl(pc["pct_redes"], med["pct_redes"], lambda x: f"{x*100:+.0f} p.p."), delta_color="off")
        kc[3].metric(t("mais_proximo"), "–" if np.isnan(pc["mais_proximo"]) else f"{pc['mais_proximo']:.0f} m")
        if pc["n"]:
            tb = pc["tabela"]
            ce1, ce2 = st.columns([1.3, 1])
            with ce1:
                b = tb["bandeira"].value_counts().sort_values()
                fig = go.Figure(go.Bar(y=b.index, x=b.values, orientation="h", marker_color=AZUL,
                                       text=b.values, textposition="outside"))
                fig.update_layout(title=t("bandeiras"), height=60 + 32 * len(b), margin=dict(t=40, b=10, l=10))
                st.plotly_chart(fig, width="stretch")
            with ce2:
                fm = tb["tipo"].map({"supermarket": "Supermercado" if lang == "pt" else "Supermarket",
                                     "convenience": "Conveniência" if lang == "pt" else "Convenience"}).value_counts()
                fig = go.Figure(go.Pie(labels=fm.index, values=fm.values, hole=0.6,
                                       marker=dict(colors=[AZUL, "#e0851f"], line=dict(color="white", width=2))))
                fig.update_layout(title=t("formato"), height=300, margin=dict(t=40, b=10),
                                  legend=dict(orientation="h", y=-0.1))
                st.plotly_chart(fig, width="stretch")
            with st.expander(t("lista_estab")):
                lst = tb[["nome", "bandeira", "tipo", "dist_m"]].sort_values("dist_m").rename(columns={
                    "nome": "Nome" if lang == "pt" else "Name", "bandeira": "Bandeira/grupo" if lang == "pt" else "Banner/group",
                    "tipo": "Tipo (OSM)" if lang == "pt" else "Type (OSM)",
                    "dist_m": "Distância da loja (m)" if lang == "pt" else "Distance from store (m)"})
                st.dataframe(pd.DataFrame(lst), hide_index=True, width="stretch")
        st.caption(t("osm_aviso"))

# ---------------------------------------------------------------------------
# 3. Comparar lojas
# ---------------------------------------------------------------------------
@st.cache_data
def diagnostico_kmeans(tab: pd.DataFrame):
    """Refaz a preparação do k-means (mesma do pipeline) para mostrar silhueta e retrato."""
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    from sklearn.preprocessing import StandardScaler

    vars_ = ["renda_media_resp", "pct_0_14", "pct_60_mais", "empregos_por_morador", "densidade_hab_km2"]
    X = tab[vars_].copy()
    X["empregos_por_morador"] = np.log1p(X["empregos_por_morador"].fillna(0))
    X["densidade_hab_km2"] = np.log1p(X["densidade_hab_km2"])
    Z = pd.DataFrame(StandardScaler().fit_transform(X.fillna(X.median())), columns=vars_, index=tab.index)
    sil = []
    for k in range(2, 7):
        lab = KMeans(n_clusters=k, n_init=20, random_state=config.SEMENTE).fit_predict(Z)
        sil.append({"k": k, "silhueta": round(silhouette_score(Z, lab), 2),
                    "tamanhos": " / ".join(map(str, sorted(np.bincount(lab), reverse=True)))})
    return pd.DataFrame(sil), Z


with abas[3]:
    st.subheader(t("kmeans_titulo"))
    ck1, ck2 = st.columns([1.15, 1])
    with ck1:
        st.markdown(KMEANS[lang])
    with ck2:
        sil, Z = diagnostico_kmeans(pd.DataFrame(lojas.drop(columns="geometry")).set_index("loja_id"))
        st.markdown(f"**{t('kmeans_k')}**")
        sil_show = sil.rename(columns={"silhueta": "silhueta" if lang == "pt" else "silhouette",
                                       "tamanhos": "lojas por grupo" if lang == "pt" else "stores per group"})
        st.dataframe(sil_show, hide_index=True, width="stretch")
        st.caption(KMEANS_K[lang])

    rotulo_var = {
        "renda_media_resp": ("Renda", "Income"), "pct_0_14": ("% crianças", "% children"),
        "pct_60_mais": ("% idosos", "% elderly"), "empregos_por_morador": ("Empregos/morador", "Jobs/resident"),
        "densidade_hab_km2": ("Densidade", "Density"),
    }
    zz = Z.join(lojas.set_index("loja_id")[["perfil_chave", col_perfil]])
    ret = zz.groupby([ "perfil_chave", col_perfil])[list(rotulo_var)].mean().reset_index()
    longo = ret.melt(id_vars=["perfil_chave", col_perfil], var_name="var", value_name="z")
    longo["var"] = longo["var"].map(lambda v: rotulo_var[v][0 if lang == "pt" else 1])
    fig = px.bar(longo, x="var", y="z", color="perfil_chave", barmode="group",
                 color_discrete_map=COR_PERFIL, custom_data=[col_perfil],
                 labels={"var": "", "z": "z-score (0 = média das lojas)" if lang == "pt" else "z-score (0 = store average)"})
    nomes = dict(zip(ret["perfil_chave"], ret[col_perfil]))
    fig.for_each_trace(lambda tr: tr.update(name=nomes.get(tr.name, tr.name)))
    fig.update_traces(marker_line_color="white", marker_line_width=1,
                      hovertemplate="%{customdata[0]}<br>%{x}: %{y:.2f}<extra></extra>")
    fig.add_hline(y=0, line_color=CINZA, line_width=1)
    fig.update_layout(title=t("kmeans_retrato"), height=420, legend=dict(orientation="h", y=-0.15, title=""))
    st.plotly_chart(fig, width="stretch")

    centros = lojas.groupby(col_perfil).agg(
        lojas_=("nome", lambda x: ", ".join(x)),
        renda=("renda_media_resp", "mean"), pct_0_14=("pct_0_14", "mean"),
        pct_60=("pct_60_mais", "mean"), emp=("empregos_por_morador", "mean"),
        dens=("densidade_hab_km2", "mean")).reset_index()
    centros["renda"] = centros["renda"].map(lambda v: brl(v))
    for c in ["pct_0_14", "pct_60"]:
        centros[c] = (centros[c] * 100).round(1).astype(str) + "%"
    centros["emp"] = centros["emp"].round(1)
    centros["dens"] = centros["dens"].map(num)
    centros.columns = ([t("perfil"), "Lojas", "Renda média", "% 0-14", "% 60+", "Empregos/morador", "Hab/km²"]
                       if lang == "pt" else
                       [t("perfil"), "Stores", "Mean income", "% 0-14", "% 60+", "Jobs/resident", "People/km²"])
    st.markdown(f"**{t('kmeans_centros')}**")
    st.dataframe(centros, hide_index=True, width="stretch")
    st.divider()

    c1, c2 = st.columns([1, 1.2])
    with c1:
        d = lojas.copy()
        fig = px.scatter(
            d, x="empregos_por_morador", y="renda_media_resp", size="potencial_total_mes",
            color="perfil_chave", color_discrete_map=COR_PERFIL, text="nome", log_x=True,
            hover_data={"perfil_chave": False, col_perfil: True},
            labels={"empregos_por_morador": t("comp_eixo_x"), "renda_media_resp": t("comp_eixo_y")})
        nomes = dict(zip(d["perfil_chave"], d[col_perfil]))
        fig.for_each_trace(lambda tr: tr.update(name=nomes.get(tr.name, tr.name)))
        fig.update_traces(textposition="top center", textfont_size=10, marker_line_color="white",
                          marker_line_width=1.5)
        fig.update_layout(title=t("comp_scatter"), height=480, legend=dict(orientation="h", y=-0.2, title=""))
        st.plotly_chart(fig, width="stretch")
    with c2:
        h = pot.merge(lojas[["loja_id", "nome"]], on="loja_id")
        h["rotulo"] = h["categoria"].map(cat)
        mat = h.pivot_table(index="nome", columns="rotulo", values="indice")
        fig = px.imshow(mat.round(0), text_auto=True, aspect="auto", zmin=60, zmax=140,
                        color_continuous_scale=[[0, "#e0851f"], [0.5, "#f3f4f6"], [1, AZUL]],
                        labels=dict(color="índice" if lang == "pt" else "index", x="", y=""))
        fig.update_layout(title=t("comp_heat"), height=480, margin=dict(t=50))
        fig.update_xaxes(tickangle=-35)
        st.plotly_chart(fig, width="stretch")

    st.markdown(f"**{t('comp_tabela')}**")
    tab = lojas[["loja_id", "nome", col_perfil, "pop", "empregos", "renda_media_resp", "concorrentes",
                 "potencial_total_mes"]].copy()
    tab.columns = ["ID", t("loja"), t("perfil"), t("moradores"), t("empregos"), t("renda"),
                   t("concorrentes"), t("potencial") + " " + t("rs_mes")]
    st.dataframe(tab.round(0), hide_index=True, width="stretch")

# ---------------------------------------------------------------------------
# 4. Mix × vendas (sintéticas)
# ---------------------------------------------------------------------------
with abas[4]:
    st.warning(t("vendas_aviso"))
    v = vendas[vendas["loja_id"] == loja_sel]
    vm = v.groupby("mes", as_index=False)["vendas"].sum()
    c1, c2 = st.columns([1, 1.3])
    with c1:
        fig = px.line(vm, x="mes", y="vendas", markers=True, labels={"mes": t("mes"), "vendas": t("rs_mes")})
        fig.update_traces(line_color=AZUL, line_width=2, marker_size=8)
        fig.update_layout(title=t("vendas_mes") + f" · {L['nome']}", height=380, yaxis_rangemode="tozero")
        st.plotly_chart(fig, width="stretch")
    with c2:
        g = gap[gap["loja_id"] == loja_sel].copy()
        g["rotulo"] = g["categoria"].map(cat)
        g = g.sort_values("share")
        fig = go.Figure()
        for _, r in g.iterrows():
            fig.add_shape(type="line", x0=r.share_vendas * 100, x1=r.share * 100, y0=r.rotulo, y1=r.rotulo,
                          line=dict(color=CINZA, width=2))
        fig.add_scatter(x=g["share_vendas"] * 100, y=g["rotulo"], mode="markers", name=t("vendas_s"),
                        marker=dict(size=11, color=AZUL_CLARO, line=dict(color="white", width=2)))
        fig.add_scatter(x=g["share"] * 100, y=g["rotulo"], mode="markers", name=t("potencial_s"),
                        marker=dict(size=11, color=AZUL, line=dict(color="white", width=2)))
        fig.update_layout(title=t("mix_titulo"), height=380, xaxis_ticksuffix="%",
                          legend=dict(orientation="h", y=-0.15), margin=dict(t=50))
        st.plotly_chart(fig, width="stretch")

    st.markdown(f"**{t('recomendacao')}**")
    rec = g.sort_values("oportunidade_rs_mes", ascending=False)
    rec = pd.DataFrame({
        t("categoria"): rec["rotulo"],
        t("potencial_s"): (rec["share"] * 100).round(1).astype(str) + "%",
        t("vendas_s"): (rec["share_vendas"] * 100).round(1).astype(str) + "%",
        t("acao"): rec["acao"].map(lambda a: t(a)),
        t("oportunidade"): rec["oportunidade_rs_mes"].round(0),
    })
    st.dataframe(rec, hide_index=True, width="stretch")

# ---------------------------------------------------------------------------
# 5. Dados e método
# ---------------------------------------------------------------------------
with abas[5]:
    st.subheader(t("fontes_titulo"))
    origem = meta.get("origem", {})
    for f in FONTES:
        with st.container(border=True):
            st.markdown(f"**{f['nome'][lang]}**")
            st.markdown(f"- {'O que é' if lang == 'pt' else 'What it is'}: {f['o_que'][lang]}\n"
                        f"- {'Como usamos' if lang == 'pt' else 'How we use it'}: {f['uso'][lang]}\n"
                        f"- Link: [{f['link']}]({f['link']})")
            detalhes = [f"`{origem[k]['arquivo']}` · {origem[k]['tamanho_mb']} MB · "
                        f"{t('baixado')} {origem[k]['baixado_em']}" for k in f["chave"] if k in origem]
            if detalhes:
                st.caption(" | ".join(detalhes))

    st.subheader(t("metodo_titulo"))
    st.markdown(METODO[lang].format(dist=meta["distancia_caminhada_m"],
                                    vel=meta["premissas"]["velocidade_km_h"],
                                    fam=meta["premissas"]["fator_renda_familia"],
                                    ipca=meta["fator_ipca"]))

    st.subheader(t("premissas_titulo"))
    prem = pd.DataFrame([{"": PREMISSAS_TXT[k][lang], "valor" if lang == "pt" else "value": v}
                         for k, v in meta["premissas"].items() if k in PREMISSAS_TXT])
    prem.loc[len(prem)] = ["IPCA jul/2022 ÷ jan/2018", round(meta["fator_ipca"], 3)]
    st.dataframe(prem, hide_index=True, width="stretch")

    vars_ = meta.get("censo", {}).get("variaveis", {})
    if vars_:
        with st.expander("Variáveis do Censo usadas" if lang == "pt" else "Census variables used"):
            st.dataframe(pd.DataFrame(list(vars_.items()), columns=["código", "descrição (IBGE)"]),
                         hide_index=True, width="stretch")

    st.subheader(t("limites_titulo"))
    st.markdown(LIMITES[lang])
    st.caption(f"{'Dados processados em' if lang == 'pt' else 'Data processed on'} {meta['gerado_em']}.")
