@echo off
REM ============================================
REM Portal RFID - Biamar UR4
REM Script para Parar Sistema no Windows
REM ============================================

echo ============================================
echo Portal RFID - Biamar UR4
echo Parando Sistema...
echo ============================================
echo.

REM Parar processos Python relacionados ao projeto
echo Finalizando processos...

REM Parar API
taskkill /FI "WINDOWTITLE eq API - Portal RFID*" /F >nul 2>&1
if not errorlevel 1 (
    echo [OK] API parada
) else (
    echo [INFO] API nao estava rodando
)

REM Parar RFID Reader
taskkill /FI "WINDOWTITLE eq RFID Reader*" /F >nul 2>&1
if not errorlevel 1 (
    echo [OK] RFID Reader parado
) else (
    echo [INFO] RFID Reader nao estava rodando
)

REM Parar processos Python na porta 8000 (backup)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
    if not errorlevel 1 echo [OK] Processo na porta 8000 finalizado
)

echo.
echo ============================================
echo Sistema parado!
echo ============================================
echo.
echo Pressione qualquer tecla para sair...
pause >nul
