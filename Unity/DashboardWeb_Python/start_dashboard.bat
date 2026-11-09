@echo off
REM ===========================================================================
REM  Iniciador do Dashboard Web da Esteira (Gemeo Digital)
REM
REM  Basta dar DOIS CLIQUES neste arquivo. Ele cuida de tudo:
REM    1) encontra o Python instalado;
REM    2) cria o ambiente virtual (.venv) na primeira vez;
REM    3) instala as dependencias (FastAPI e Uvicorn);
REM    4) abre o navegador e inicia o servidor.
REM
REM  Se este .bat nao funcionar, veja as instrucoes manuais no topo de main.py.
REM ===========================================================================

chcp 65001 >nul
title Dashboard Web da Esteira
cd /d "%~dp0"

echo ============================================
echo   Dashboard Web da Esteira - Gemeo Digital
echo ============================================
echo.

REM --- 1) Descobre qual comando de Python existe nesta maquina --------------
REM     Tenta primeiro "python"; se nao houver, tenta o lancador "py".
set "PYTHON=python"
where python >nul 2>nul
if errorlevel 1 set "PYTHON=py"
where %PYTHON% >nul 2>nul
if errorlevel 1 (
    echo [ERRO] Python nao foi encontrado neste computador.
    echo        Instale o Python em https://www.python.org/downloads/
    echo        e marque a opcao "Add Python to PATH" durante a instalacao.
    echo.
    pause
    exit /b 1
)

REM --- 2) Cria o ambiente virtual apenas se ele ainda nao existir -----------
if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Criando ambiente virtual ^(.venv^)...
    %PYTHON% -m venv .venv
)

REM --- 3) Ativa o ambiente e instala as dependencias ------------------------
echo [2/3] Instalando dependencias ^(FastAPI e Uvicorn^)...
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERRO] Nao foi possivel instalar as dependencias.
    echo        Verifique sua conexao com a internet e tente novamente.
    echo.
    pause
    exit /b 1
)

REM --- 4) Abre o navegador e inicia o servidor ------------------------------
REM     Abrimos o navegador num processo separado, com uma pequena espera,
REM     para dar tempo do servidor subir antes de carregar a pagina.
echo [3/3] Iniciando o servidor em http://localhost:8000
echo.
echo  ^>^> Para PARAR o servidor, clique nesta janela e pressione Ctrl + C.
echo.
start "" cmd /c "timeout /t 3 >nul & start http://localhost:8000"
REM --timeout-graceful-shutdown 5: ao apertar Ctrl + C, o servidor espera no
REM maximo 5 segundos as conexoes fecharem e entao desliga (o dashboard mantem
REM uma conexao SSE aberta que, sem esse limite, faria o Ctrl + C travar).
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000 --timeout-graceful-shutdown 5

pause
