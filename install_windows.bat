@echo off
REM ============================================
REM Portal RFID - Biamar UR4
REM Script de Instalacao para Windows
REM ============================================

echo ============================================
echo Portal RFID - Biamar UR4
echo Instalacao para Windows
echo ============================================
echo.

REM Verificar se Python esta instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo.
    echo Instale Python 3.8 ou superior:
    echo https://www.python.org/downloads/
    echo.
    echo Marque a opcao "Add Python to PATH" durante a instalacao
    pause
    exit /b 1
)

echo [OK] Python encontrado: 
python --version
echo.

REM Criar ambiente virtual
echo Criando ambiente virtual Python...
if exist venv (
    echo Removendo ambiente virtual antigo...
    rmdir /s /q venv
)

python -m venv venv
if errorlevel 1 (
    echo [ERRO] Falha ao criar ambiente virtual
    pause
    exit /b 1
)

echo [OK] Ambiente virtual criado
echo.

REM Ativar ambiente virtual e instalar dependencias
echo Instalando dependencias Python...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias
    pause
    exit /b 1
)

echo [OK] Dependencias instaladas
echo.

REM Criar diretorios necessarios
echo Criando diretorios necessarios...
if not exist database mkdir database
if not exist logs mkdir logs

echo [OK] Diretorios criados
echo.

REM Inicializar banco de dados
echo Inicializando banco de dados...
python -c "from backend.models import init_db; init_db()"

if errorlevel 1 (
    echo [AVISO] Erro ao inicializar banco (pode ser ignorado)
)

echo.
echo ============================================
echo Instalacao concluida com sucesso!
echo ============================================
echo.
echo Para iniciar o sistema:
echo   start_windows.bat
echo.
echo Para parar o sistema:
echo   stop_windows.bat
echo.
echo Pressione qualquer tecla para sair...
pause >nul
