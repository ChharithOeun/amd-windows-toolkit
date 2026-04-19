@echo off
REM AMD Windows AI Toolkit — Quick Launcher
REM Run this to check GPU health and see ecosystem status.

echo.
echo  AMD Windows AI Toolkit
echo  ======================
echo.
echo  1. Quick GPU check       (check_gpu.py)
echo  2. Full health report    (doctor.py)
echo  3. One-time setup wizard (setup_env.py)
echo  4. Exit
echo.
set /p choice="  Enter choice [1-4]: "

if "%choice%"=="1" (
    python scripts\check_gpu.py
    pause
    goto :eof
)
if "%choice%"=="2" (
    python scripts\doctor.py
    pause
    goto :eof
)
if "%choice%"=="3" (
    python scripts\setup_env.py
    pause
    goto :eof
)
if "%choice%"=="4" goto :eof

echo  Invalid choice.
pause
