@echo off
REM ============================================
REM Portal RFID - Biamar UR4
REM Script de Inicializacao para Windows
REM ============================================

echo ============================================
echo Portal RFID - Biamar UR4
echo Iniciando Sistema...
echo ============================================
echo.

REM Verificar se ambiente virtual existe
if not exist venv (
    echo [ERRO] Ambiente virtual nao encontrado!
    echo Execute primeiro: install_windows.bat
    echo.
    pause
    exit /b 1
)

REM Verificar se ja esta rodando
tasklist /FI "WINDOWTITLE eq API - Portal RFID*" 2>NUL | find /I "cmd.exe" >NUL
if not errorlevel 1 (
    echo [AVISO] Sistema ja esta em execucao!
    echo Para parar, execute: stop_windows.bat
    echo.
    pause
    exit /b 1
)

REM Criar diretorios se nao existirem
if not exist database mkdir database
if not exist logs mkdir logs

REM Iniciar API Backend em nova janela
echo [1/3] Iniciando API Backend...
start "API - Portal RFID Biamar" cmd /k "cd /d "%~dp0" && venv\Scripts\activate && cd backend && python main.py"

timeout /t 3 /nobreak >nul

REM Iniciar Leitor RFID em nova janela (se existir script)
if exist "scripts\rfid_reader.py" (
    echo [2/3] Iniciando Leitor RFID...
    start "RFID Reader - Biamar" cmd /k "cd /d "%~dp0" && venv\Scripts\activate && cd scripts && python rfid_reader.py"
    timeout /t 2 /nobreak >nul
) else (
    echo [2/3] Script RFID nao encontrado (scripts\rfid_reader.py)
    echo      Pule esta etapa se o leitor RFID sera iniciado manualmente
)

REM Aguardar API iniciar
echo [3/3] Aguardando API iniciar...
timeout /t 5 /nobreak >nul

REM Abrir Dashboard no navegador
echo Abrindo Dashboard...
set "DASHBOARD=%~dp0frontend\index.html"
start "" "%DASHBOARD%"

echo.
echo ============================================
echo Sistema iniciado!
echo ============================================
echo.
echo URLs de acesso:
echo   Dashboard: file:///%~dp0frontend\index.html
echo   API: http://localhost:8000
echo   Docs: http://localhost:8000/docs
echo   Health: http://localhost:8000/health
echo.
echo Janelas abertas:
echo   - API Backend
echo   - RFID Reader (se disponivel)
echo   - Dashboard (navegador)
echo.
echo Para parar: stop_windows.bat
echo.
echo Pressione qualquer tecla para sair...
pause >nul
