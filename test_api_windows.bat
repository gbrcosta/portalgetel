@echo off
REM ============================================
REM Teste de API - Portal RFID Biamar
REM ============================================

echo ============================================
echo Testando API do Portal RFID...
echo ============================================
echo.

REM Verificar se curl existe (Windows 10+)
where curl >nul 2>&1
if errorlevel 1 (
    echo [ERRO] curl nao encontrado
    echo No Windows 10/11, curl ja vem instalado
    echo Tente atualizar o Windows ou instale: https://curl.se/
    pause
    exit /b 1
)

echo [1/3] Testando endpoint raiz...
curl -s http://localhost:8000/ >nul 2>&1
if errorlevel 1 (
    echo [ERRO] API nao esta respondendo
    echo Execute: start_windows.bat
    echo.
    pause
    exit /b 1
) else (
    echo [OK] API respondendo
    curl -s http://localhost:8000/
    echo.
)

echo.
echo [2/3] Testando health check...
curl -s http://localhost:8000/health
echo.

echo.
echo [3/3] Endpoints disponiveis:
echo   Dashboard stats: http://localhost:8000/api/dashboard/stats
echo   Tags: http://localhost:8000/api/tags
echo   Sessoes: http://localhost:8000/api/sessions
echo   Documentacao: http://localhost:8000/docs
echo.

echo ============================================
echo Teste concluido!
echo ============================================
echo.
pause
