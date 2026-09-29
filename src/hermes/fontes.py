"""
Download das fontes públicas.

Cada função baixa UM arquivo para `dados/brutos/`, só se ele ainda não existir
(cache simples). Assim o pipeline pode ser rodado várias vezes sem baixar tudo
de novo. Também registramos em `dados/brutos/_origem.json` a URL e a data de
cada download, para o app conseguir mostrar a procedência de cada dado.
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime
from pathlib import Path

import requests

from . import config

CABECALHO = {"User-Agent": "Mozilla/5.0 (projeto-portfolio-hermes; dados publicos)"}
ARQ_ORIGEM = config.DADOS_BRUTOS / "_origem.json"


def _registrar_origem(nome: str, url: str, arquivo: Path) -> None:
    """Guarda de onde veio cada arquivo e quando foi baixado."""
    origem = json.loads(ARQ_ORIGEM.read_text("utf-8")) if ARQ_ORIGEM.exists() else {}
    origem[nome] = {
        "url": url,
        "arquivo": arquivo.name,
        "baixado_em": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "tamanho_mb": round(arquivo.stat().st_size / 1e6, 1),
    }
    ARQ_ORIGEM.write_text(json.dumps(origem, ensure_ascii=False, indent=2), "utf-8")


def baixar(url: str, destino: Path, nome: str, tentativas: int = 3) -> Path:
    """Baixa `url` para `destino` em streaming (arquivos grandes não estouram a memória)."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists() and destino.stat().st_size > 0:
        print(f"  ✓ {destino.name} já existe – pulando download")
        return destino
    for tentativa in range(1, tentativas + 1):
        try:
            print(f"  ↓ baixando {nome} ({url})")
            with requests.get(url, headers=CABECALHO, stream=True, timeout=120) as r:
                r.raise_for_status()
                total = int(r.headers.get("content-length", 0))
                baixado = 0
                tmp = destino.with_suffix(destino.suffix + ".part")
                with open(tmp, "wb") as f:
                    for bloco in r.iter_content(chunk_size=1 << 20):
                        f.write(bloco)
                        baixado += len(bloco)
                        if total:
                            print(f"\r    {baixado / 1e6:,.0f} de {total / 1e6:,.0f} MB", end="")
                print()
                tmp.replace(destino)
            _registrar_origem(nome, url, destino)
            return destino
        except Exception as erro:  # rede instável: tenta de novo
            print(f"    falhou (tentativa {tentativa}): {erro}")
            time.sleep(5 * tentativa)
    raise RuntimeError(f"Não consegui baixar {url}")


def achar_arquivo_na_pasta(url_pasta: str, padrao: str) -> str:
    """
    O FTP do IBGE é uma página HTML com a lista de arquivos. Os nomes mudam
    quando o IBGE republica (a data entra no nome), então procuramos pelo
    padrão e pegamos a versão mais recente (maior nome em ordem alfabética).
    """
    html = requests.get(url_pasta, headers=CABECALHO, timeout=60).text
    achados = sorted(set(re.findall(padrao, html)))
    if not achados:
        raise FileNotFoundError(f"Nenhum arquivo com padrão {padrao} em {url_pasta}")
    return url_pasta + achados[-1]


def get_json(url: str, nome: str, destino: Path) -> list | dict:
    """Consulta uma API que devolve JSON (SIDRA) e guarda a resposta em disco."""
    if destino.exists():
        print(f"  ✓ {destino.name} já existe – pulando consulta")
        return json.loads(destino.read_text("utf-8"))
    print(f"  ↓ consultando {nome} ({url})")
    r = requests.get(url, headers=CABECALHO, timeout=120)
    r.raise_for_status()
    dados = r.json()
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(dados, ensure_ascii=False), "utf-8")
    _registrar_origem(nome, url, destino)
    return dados


# ---------------------------------------------------------------------------
# Um atalho por fonte
# ---------------------------------------------------------------------------
def baixar_malha_setores() -> Path:
    return baixar(config.URL_MALHA_SETORES, config.DADOS_BRUTOS / "SP_setores_CD2022.gpkg",
                  "Censo 2022 – malha de setores (SP)")


def _local_ou_url(destino: Path, pasta: str, padrao: str) -> str:
    """Se o arquivo já foi baixado, nem consulta a pasta do IBGE (funciona offline)."""
    return "" if destino.exists() else achar_arquivo_na_pasta(pasta, padrao)


def baixar_demografia() -> tuple[Path, Path]:
    url = _local_ou_url(config.DADOS_BRUTOS / "censo_demografia.zip",
                        config.PASTA_AGREGADOS_SETOR, config.PADRAO_DEMOGRAFIA)
    url_dic = _local_ou_url(config.DADOS_BRUTOS / "censo_agregados_dicionario.xlsx",
                            config.PASTA_AGREGADOS, config.PADRAO_DICIONARIO_AGREGADOS)
    zip_ = baixar(url, config.DADOS_BRUTOS / "censo_demografia.zip",
                  "Censo 2022 – agregados de demografia")
    dic = baixar(url_dic, config.DADOS_BRUTOS / "censo_agregados_dicionario.xlsx",
                 "Censo 2022 – dicionário dos agregados")
    return zip_, dic


def baixar_renda() -> tuple[Path, Path]:
    url = _local_ou_url(config.DADOS_BRUTOS / "censo_renda.zip", config.PASTA_RENDA, config.PADRAO_RENDA)
    url_dic = _local_ou_url(config.DADOS_BRUTOS / "censo_renda_dicionario.xlsx",
                            config.PASTA_RENDA, config.PADRAO_DICIONARIO_RENDA)
    zip_ = baixar(url, config.DADOS_BRUTOS / "censo_renda.zip",
                  "Censo 2022 – rendimento do responsável")
    dic = baixar(url_dic, config.DADOS_BRUTOS / "censo_renda_dicionario.xlsx",
                 "Censo 2022 – dicionário do rendimento")
    return zip_, dic


def baixar_od() -> Path:
    return baixar(config.URL_OD, config.DADOS_BRUTOS / "pesquisa_od_2023.zip",
                  "Pesquisa Origem-Destino 2023 (Metrô-SP)")


def baixar_pof() -> list:
    classes = ",".join(c[0] for c in config.CLASSES_POF)
    itens = sorted({i for v in config.CATEGORIAS_LOJA.values() for i in v}
                   | {i for v in config.ITENS_FORA_DE_CASA_TRABALHADOR.values() for i in v}
                   | {"103625", "103626", "103692"})
    url = (f"https://apisidra.ibge.gov.br/values/t/{config.SIDRA_POF_TABELA}/n3/35"
           f"/v/{config.SIDRA_POF_VARIAVEL}/p/all/c339/7999,{classes}/c12190/{','.join(itens)}")
    return get_json(url, "POF 2017-2018 – despesa com alimentação (SIDRA 6972, SP)",
                    config.DADOS_BRUTOS / "pof_6972_sp.json")


def baixar_ipca() -> list:
    url = (f"https://apisidra.ibge.gov.br/values/t/{config.SIDRA_IPCA_TABELA}/n1/all"
           f"/v/{config.SIDRA_IPCA_VARIAVEL}/p/{config.IPCA_MES_POF},{config.IPCA_MES_CENSO}")
    return get_json(url, "IPCA – número-índice (SIDRA 1737)",
                    config.DADOS_BRUTOS / "ipca_1737.json")
