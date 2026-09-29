@echo off
REM ================================================================
REM  Hermes - roda o pipeline: baixa os dados publicos e gera
REM  dados\processados (o que o app e o notebook usam).
REM ================================================================
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONPATH=%~dp0src
set PIP_NO_CACHE_DIR=1

REM Se a instalacao anterior nao terminou (marcador ausente), recria o ambiente do zero.
REM Ambiente ja existe sem marcador: se as bibliotecas principais importam, so marca como ok.
if exist .venv\Scripts\python.exe if not exist .venv\instalado.ok (
  .venv\Scripts\python.exe -c "import geopandas, osmnx, streamlit, dbfread, sklearn, folium, plotly" 2>nul && echo ok> .venv\instalado.ok
)
REM Se ainda assim nao tem marcador, a instalacao anterior ficou pela metade: recria do zero.
if exist .venv if not exist .venv\instalado.ok (
  echo Instalacao anterior incompleta - recriando o ambiente .venv ...
  rmdir /s /q .venv
)
if not exist .venv\Scripts\python.exe (
  echo [1/3] Criando ambiente virtual...
  py -3 -m venv .venv 2>/dev/null || python -m venv .venv
)
call .venv\Scripts\activate.bat

if not exist .venv\instalado.ok (
  echo [2/3] Instalando bibliotecas - pode levar uns 10 minutos na primeira vez...
  python -m pip install --upgrade pip
  pip install -r requirements.txt
  if errorlevel 1 (
    echo.
    echo ERRO na instalacao das bibliotecas. Tire um print desta tela.
    pause
    exit /b 1
  )
  echo ok> .venv\instalado.ok
)

echo [3/3] Rodando o pipeline...
python -m hermes.pipeline
echo.
echo Fim. O log completo esta em dados\processados\log_pipeline.txt
pause
