"""
Configuração central do projeto Hermes.

Tudo o que é "decisão" do projeto mora aqui: caminhos, URLs das fontes públicas,
as lojas (fictícias) da rede e as PREMISSAS usadas nas contas. A ideia é que
qualquer pessoa consiga abrir este arquivo e entender, sem ler o resto do código,
de onde vêm os dados e quais hipóteses foram assumidas.
"""
from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parents[2]          # pasta do projeto (…/hermes)
DADOS_BRUTOS = RAIZ / "dados" / "brutos"             # downloads originais (não vão pro git)
DADOS_PROCESSADOS = RAIZ / "dados" / "processados"  # saídas leves usadas pelo app

# Município de São Paulo no código do IBGE (7 dígitos).
COD_MUN_SP = "3550308"

# Sistemas de coordenadas:
# - WGS84 (lat/lon) é o que mapas web usam;
# - SIRGAS 2000 / UTM 23S (EPSG:31983) é métrico, bom pra calcular áreas em m²;
# - a Pesquisa OD publica coordenadas em Córrego Alegre / UTM 23S (EPSG:22523).
CRS_WGS84 = "EPSG:4326"
CRS_METRICO = "EPSG:31983"
CRS_OD = "EPSG:22523"

# ---------------------------------------------------------------------------
# Fontes públicas (todas abertas, sem login)
# ---------------------------------------------------------------------------
# Censo 2022 – malha de setores censitários JÁ com os atributos básicos
# (população, domicílios, média de moradores). Arquivo do estado de SP.
URL_MALHA_SETORES = (
    "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/"
    "malha_com_atributos/setores/gpkg/UF/SP/SP_setores_CD2022.gpkg"
)
# Censo 2022 – pastas dos agregados. Os nomes dos arquivos trazem a data de
# publicação (ex.: ..._20260508.zip), então o código lista a pasta e acha o
# arquivo pelo padrão do nome em vez de fixar o nome exato.
PASTA_AGREGADOS_SETOR = (
    "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/"
    "Agregados_por_Setor_csv/"
)
PASTA_AGREGADOS = (
    "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/"
)
PADRAO_DICIONARIO_AGREGADOS = r"dicionario_de_dados_agregados_por_setores_censitarios[^\"]*\.xlsx"
PADRAO_DEMOGRAFIA =r"Agregados_por_setores_demografia_BR[^\"]*\.zip"
PASTA_RENDA = (
    "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/"
    "Agregados_por_Setores_Censitarios_Rendimento_do_Responsavel/"
)
PADRAO_RENDA = r"Agregados_por_setores_renda_responsavel_BR[^\"]*_csv\.zip"
PADRAO_DICIONARIO_RENDA = r"dicionario_de_dados_renda_responsavel[^\"]*\.xlsx"

# Pesquisa Origem-Destino 2023 do Metrô-SP (microdados, ~200 MB).
URL_OD = "https://transparencia.metrosp.com.br/sites/default/files/Site_190225_PesquisaOD2023.zip"

# POF 2017-2018 via API do SIDRA/IBGE.
# Tabela 6972: despesa monetária e não monetária média mensal FAMILIAR com
# alimentação, por classe de rendimento e tipo de despesa. n3/35 = estado de SP.
SIDRA_POF_TABELA = 6972
SIDRA_POF_VARIAVEL = 1201  # valor em R$ por família/mês (a preços de 15/jan/2018)

# IPCA (tabela 1737, variável 2266 = número-índice) para levar a renda do
# Censo (jul/2022) aos preços da POF (jan/2018).
SIDRA_IPCA_TABELA = 1737
SIDRA_IPCA_VARIAVEL = 2266
IPCA_MES_POF = "201801"
IPCA_MES_CENSO = "202207"

# Classes de rendimento da POF (classificação C339 da tabela 6972), com os
# limites em R$ de jan/2018 de renda FAMILIAR mensal.
CLASSES_POF = [
    # (código SIDRA, rótulo curto, limite inferior, limite superior)
    ("47558", "até 1.908", 0, 1908),
    ("47559", "1.908 a 2.862", 1908, 2862),
    ("47560", "2.862 a 5.724", 2862, 5724),
    ("47561", "5.724 a 9.540", 5724, 9540),
    ("47562", "9.540 a 14.310", 9540, 14310),
    ("47563", "14.310 a 23.850", 14310, 23850),
    ("47564", "mais de 23.850", 23850, float("inf")),
]

# Tipos de despesa da POF (classificação C12190) e como eles viram
# "categorias de gôndola" da loja. Uma categoria da loja pode juntar vários
# itens da POF.
CATEGORIAS_LOJA = {
    "Mercearia básica": ["103627", "103631", "103640", "103674", "103684", "103685"],
    "Hortifruti": ["103636", "103644", "103649"],
    "Carnes e peixes": ["103654"],
    "Aves e ovos": ["103661"],
    "Laticínios e frios": ["103665"],
    "Padaria e biscoitos": ["103670"],
    "Café e bebidas não alcoólicas": ["103679", "103680", "8862", "8044"],
    "Bebidas alcoólicas": ["103681", "103682"],
    "Pronto para consumo": ["103690"],
    "Outros alimentos": ["103691"],
}
# Itens de alimentação FORA de casa usados para estimar a demanda de quem
# TRABALHA perto da loja (lanche, salgado, bebida pra viagem).
ITENS_FORA_DE_CASA_TRABALHADOR = {
    "Pronto para consumo": ["103695", "103697"],          # sanduíches/salgados + lanches
    "Café e bebidas não alcoólicas": ["103696", "103694"],  # refri/outras + café/leite
}
CATEGORIA_EN = {
    "Mercearia básica": "Dry grocery",
    "Hortifruti": "Fruit & vegetables",
    "Carnes e peixes": "Meat & fish",
    "Aves e ovos": "Poultry & eggs",
    "Laticínios e frios": "Dairy & deli",
    "Padaria e biscoitos": "Bakery & biscuits",
    "Café e bebidas não alcoólicas": "Coffee & soft drinks",
    "Bebidas alcoólicas": "Alcoholic drinks",
    "Pronto para consumo": "Ready-to-eat",
    "Outros alimentos": "Other food",
}

# ---------------------------------------------------------------------------
# Premissas (hipóteses explícitas – mude aqui e rode o pipeline de novo)
# ---------------------------------------------------------------------------
PREMISSAS = {
    # Isócrona: 15 minutos a pé a 4,8 km/h ≈ 1.200 m de caminhada pelas ruas.
    "minutos_caminhada": 15,
    "velocidade_km_h": 4.8,
    # O Censo publica a renda do RESPONSÁVEL pelo domicílio; a POF usa a renda
    # da FAMÍLIA inteira. Esse fator converte uma na outra (hipótese: o
    # responsável responde por ~2/3 da renda da casa).
    "fator_renda_familia": 1.5,
    # Pessoas que trabalham por família (média) – usado para transformar o
    # gasto FAMILIAR com lanche fora de casa em gasto POR TRABALHADOR.
    "trabalhadores_por_familia": 1.6,
    # Parcela do gasto de lanche/bebida do trabalhador que um mercado de
    # proximidade consegue disputar (o resto vai pra padaria, café, restaurante).
    "parcela_trabalhador_mercado": 0.30,
    # Dias úteis: a POF é mensal e já considera o mês inteiro; não ajustamos.
}

# Quantos grupos (clusters) de perfil de loja.
N_CLUSTERS = 4
SEMENTE = 42  # reprodutibilidade das partes aleatórias (vendas sintéticas, k-means)

# ---------------------------------------------------------------------------
# Lojas da rede fictícia "Ágora Express"
# ---------------------------------------------------------------------------
# Rede INVENTADA. Os pontos ficam em bairros reais de SP, escolhidos para ter
# perfis bem diferentes (centro financeiro, bairro residencial, periferia…).
# As coordenadas são aproximadas e não representam nenhuma loja real.
LOJAS = [
    ("AG01", "Faria Lima", -23.5868, -46.6820),
    ("AG02", "Paulista", -23.5614, -46.6559),
    ("AG03", "Largo da Batata", -23.5672, -46.6937),
    ("AG04", "Vila Mariana", -23.5890, -46.6345),
    ("AG05", "Mooca", -23.5570, -46.5990),
    ("AG06", "Tatuapé", -23.5405, -46.5763),
    ("AG07", "Santana", -23.5022, -46.6252),
    ("AG08", "Berrini", -23.6080, -46.6950),
    ("AG09", "República", -23.5432, -46.6425),
    ("AG10", "Perdizes", -23.5360, -46.6780),
    ("AG11", "Lapa", -23.5226, -46.7036),
    ("AG12", "Jabaquara", -23.6460, -46.6410),
    ("AG13", "Itaquera", -23.5420, -46.4710),
    ("AG14", "Capão Redondo", -23.6710, -46.7790),
    ("AG15", "Butantã", -23.5717, -46.7085),
]
NOME_REDE = "Ágora Express"
