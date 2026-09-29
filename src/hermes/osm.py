"""
OpenStreetMap – a área REAL de 15 minutos a pé e os concorrentes.

Por que não um círculo de raio fixo? Porque ninguém anda em linha reta: rios,
avenidas, linhas de trem e quarteirões grandes mudam muito a área alcançável.
Usamos a malha de ruas e calçadas do OpenStreetMap (via biblioteca osmnx):

1. baixamos a rede de caminhada ao redor da loja (raio de 2,5 km);
2. achamos o nó da rede mais próximo da loja;
3. pegamos todos os trechos de rua alcançáveis andando até 1.200 m
   (15 min × 4,8 km/h) – isso é uma ISÓCRONA;
4. transformamos esses trechos num polígono (buffer de 30 m + união).

Com o mesmo polígono, consultamos no OSM os supermercados e lojas de
conveniência que já existem ali (concorrência).

Velocidade: baixar a malha de ruas pelo Overpass é pesado e os servidores
públicos vivem lentos. Por isso a isócrona é pedida primeiro ao **Valhalla**
(motor de rotas open source que roda sobre os mesmos dados do OSM, servidor
público da FOSSGIS): ele devolve o polígono pronto em ~1 segundo. O cálculo
"na mão" com osmnx fica como plano B – e é ele que o notebook mostra passo a passo.
"""
from __future__ import annotations

import geopandas as gpd
import networkx as nx
import pandas as pd
from shapely.geometry import Point, Polygon

from . import config


# O servidor principal do Overpass (API que entrega os dados do OSM) vive
# sobrecarregado. Tentamos os espelhos públicos em sequência até um responder.
# Ordem: os que responderam no teste primeiro (são lentos, mas respondem).
ESPELHOS_OVERPASS = [
    "https://overpass.private.coffee/api",
    "https://overpass.kumi.systems/api",
    "https://overpass-api.de/api",
]


def _com_espelhos(funcao, *args, timeout: int = 90, espelhos=None, **kwargs):
    """Executa uma consulta ao OSM tentando cada espelho do Overpass."""
    import osmnx as ox

    ox.settings.requests_timeout = timeout
    ox.settings.overpass_rate_limit = False  # espelhos nem sempre têm o endpoint /status
    ox.settings.use_cache = True           # respostas ficam em ./cache (rodar de novo é instantâneo)
    ultimo_erro = None
    for url in (espelhos or ESPELHOS_OVERPASS):
        ox.settings.overpass_url = url
        try:
            return funcao(*args, **kwargs)
        except Exception as erro:
            if "InsufficientResponse" in type(erro).__name__:
                raise  # resposta válida, só que vazia – não adianta trocar de servidor
            print(f"      servidor {url.split('/')[2]} falhou ({type(erro).__name__}); tentando outro…")
            ultimo_erro = erro
    raise OSMIndisponivel("Nenhum servidor do OpenStreetMap respondeu.") from ultimo_erro


class OSMIndisponivel(RuntimeError):
    """Todos os servidores do OSM falharam – o pipeline usa o plano B."""


# Plano B: sem a rede de ruas, usamos um círculo "descontado". Em cidades, o
# caminho a pé é em média ~30% maior que a linha reta (fator de circuidade),
# então 1.200 m de caminhada ≈ 1.200 / 1,3 ≈ 920 m em linha reta.
FATOR_CIRCUIDADE = 1.3


def isocrona_aproximada(lat: float, lon: float) -> Polygon:
    ponto = gpd.GeoSeries([Point(lon, lat)], crs=config.CRS_WGS84).to_crs(config.CRS_METRICO).iloc[0]
    return ponto.buffer(distancia_caminhada_m() / FATOR_CIRCUIDADE)


def distancia_caminhada_m() -> float:
    p = config.PREMISSAS
    return p["minutos_caminhada"] / 60 * p["velocidade_km_h"] * 1000


URL_VALHALLA = "https://valhalla1.openstreetmap.de/isochrone"


def isocrona_valhalla(lat: float, lon: float) -> Polygon:
    """Isócrona a pé pronta, calculada pelo Valhalla sobre a malha do OSM."""
    import requests
    from shapely.geometry import shape

    p = config.PREMISSAS
    corpo = {
        "locations": [{"lat": lat, "lon": lon}],
        "costing": "pedestrian",
        "costing_options": {"pedestrian": {"walking_speed": p["velocidade_km_h"]}},
        "contours": [{"time": p["minutos_caminhada"]}],
        "polygons": True,
        "denoise": 0.5,
        "generalize": 15,
    }
    try:
        r = requests.post(URL_VALHALLA, json=corpo, timeout=60,
                          headers={"User-Agent": "hermes-portfolio (dados publicos)"})
        r.raise_for_status()
        geom = shape(r.json()["features"][0]["geometry"])
    except Exception as erro:
        raise OSMIndisponivel(f"Valhalla falhou: {erro}") from erro
    if geom.geom_type == "MultiPolygon":
        geom = max(geom.geoms, key=lambda g: g.area)
    if geom.geom_type == "LineString":  # contorno sem polígono
        geom = Polygon(geom.coords)
    poli = gpd.GeoSeries([Polygon(geom.exterior)], crs=config.CRS_WGS84).to_crs(config.CRS_METRICO).iloc[0]
    return poli


def isocrona(lat: float, lon: float, salvar_grafo=None) -> tuple[Polygon, str]:
    """
    Tenta, em ordem: (1) Valhalla, rápido; (2) osmnx + Overpass, lento.
    Devolve o polígono e o método usado. Se os dois falharem, levanta OSMIndisponivel.
    """
    try:
        return isocrona_valhalla(lat, lon), "valhalla_osm"
    except OSMIndisponivel as erro:
        print(f"      {erro} – tentando pela malha de ruas (osmnx)…")
    return isocrona_osmnx(lat, lon, salvar_grafo=salvar_grafo), "ruas_osm"


def isocrona_osmnx(lat: float, lon: float, buffer_m: float = 30, salvar_grafo=None) -> Polygon:
    """Polígono (CRS métrico) alcançável a pé a partir do ponto.

    `salvar_grafo`: caminho .graphml opcional para guardar a rede de ruas
    (o notebook usa isso para mostrar o passo a passo de uma loja).
    """
    import osmnx as ox

    alcance = distancia_caminhada_m()
    # Andando 1.200 m pelas ruas, ninguém se afasta mais que 1.200 m em linha reta;
    # baixamos um quadrado de 1.500 m de "raio" (folga para achar a esquina da loja).
    G = _com_espelhos(ox.graph_from_point, (lat, lon), dist=alcance + 300,
                      network_type="walk", simplify=True, timeout=120,
                      espelhos=ESPELHOS_OVERPASS[:2])
    G = ox.project_graph(G, to_crs=config.CRS_METRICO)
    if salvar_grafo:
        ox.save_graphml(G, salvar_grafo)
    ponto = gpd.GeoSeries([Point(lon, lat)], crs=config.CRS_WGS84).to_crs(config.CRS_METRICO).iloc[0]
    origem = ox.distance.nearest_nodes(G, X=ponto.x, Y=ponto.y)
    sub = nx.ego_graph(G, origem, radius=alcance, distance="length")
    arestas = ox.graph_to_gdfs(sub, nodes=False, fill_edge_geometry=True)
    poligono = arestas.buffer(buffer_m).union_all()
    # "Tapa" buracos internos (quarteirões) – interessa a mancha contínua.
    if poligono.geom_type == "MultiPolygon":
        poligono = max(poligono.geoms, key=lambda g: g.area)
    return Polygon(poligono.exterior)


def concorrentes(poligono_metrico: Polygon) -> gpd.GeoDataFrame:
    """Supermercados e lojas de conveniência do OSM dentro da isócrona."""
    import osmnx as ox

    poli_wgs = gpd.GeoSeries([poligono_metrico], crs=config.CRS_METRICO).to_crs(config.CRS_WGS84).iloc[0]
    try:
        # Consulta leve (só pontos de comércio): 60 s por servidor bastam.
        f = _com_espelhos(ox.features_from_polygon, poli_wgs,
                          tags={"shop": ["supermarket", "convenience"]}, timeout=60)
    except OSMIndisponivel:
        raise  # servidor fora: quem chamou decide (não é "zero concorrentes")
    except Exception:  # resposta vazia -> osmnx levanta erro = nenhum concorrente
        return gpd.GeoDataFrame({"nome": [], "tipo": []}, geometry=[], crs=config.CRS_METRICO)
    f = f.to_crs(config.CRS_METRICO)
    out = gpd.GeoDataFrame(
        {
            "nome": f.get("name", pd.Series(index=f.index, dtype=str)).fillna("(sem nome)").values,
            "tipo": f["shop"].values,
        },
        geometry=f.geometry.centroid.values,
        crs=config.CRS_METRICO,
    )
    return out[out.within(poligono_metrico)].reset_index(drop=True)


def concorrentes_vazio() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame({"nome": [], "tipo": []}, geometry=[], crs=config.CRS_METRICO)
