@echo off
setlocal EnableExtensions
title TradingLog dev launcher

rem ============================================================
rem  TradingLog - one-click dev launcher
rem
rem    backend  : FastAPI project in server/   -> http://127.0.0.1:8000
rem    frontend : Vite dev server              -> http://localhost:5173
rem
rem  Usage : double-click this file, or run start_dev.cmd
rem  Stop  : close the two spawned console windows (or press Ctrl+C there)
rem
rem  IMPORTANT: keep this file ASCII-only.
rem  cmd.exe mis-parses non-ASCII batch files (it mixes byte offsets with
rem  character counts), which silently drops characters from some lines.
rem  All user-facing text below is therefore English on purpose.
rem ============================================================

rem ---------------- switches ----------------
rem backend hot reload: 1 = on (auto restart when a .py file changes), 0 = off
set "BACKEND_RELOAD=1"
rem open the browser once services are up: 1 = yes, 0 = no
set "OPEN_BROWSER=0"

rem always work relative to the folder this script lives in
cd /d "%~dp0"
set "ROOT=%CD%"

echo.
echo ============================================================
echo   TradingLog dev environment
echo ------------------------------------------------------------
echo   project root : %ROOT%
echo   backend      : http://127.0.0.1:8000   (API docs: /docs)
echo   frontend     : http://localhost:5173
echo ============================================================
echo.

rem ---------- 1. project layout + toolchain ----------
if not exist "%ROOT%\package.json" goto :err_no_package
if not exist "%ROOT%\server\pyproject.toml" goto :err_no_server

where uv >nul 2>nul
if errorlevel 1 goto :err_no_uv

where npm >nul 2>nul
if errorlevel 1 goto :err_no_npm

rem ---------- 2. dependencies (auto install on first run) ----------
call :ensure_frontend_deps
if errorlevel 1 goto :err_npm_install

call :ensure_backend_deps
if errorlevel 1 goto :err_uv_sync

rem ---------- 3. port notices ----------
call :port_in_use 8000
if errorlevel 1 goto :port_8000_free
echo [WARN] port 8000 is already in use - the backend may still be running.
echo        Close the old "backend" window first for a clean restart.
echo.
:port_8000_free

call :port_in_use 5173
if errorlevel 1 goto :port_5173_free
echo [WARN] port 5173 is already in use - the frontend may still be running.
echo        Close the old "frontend" window first for a clean restart.
echo.
:port_5173_free

rem ---------- 4. start backend ----------
if "%BACKEND_RELOAD%"=="1" set "RELOAD=true"
echo [start] backend  ^(uv run tradinglog-server^) ...
start "TradingLog backend :8000" /D "%ROOT%\server" cmd /k uv run tradinglog-server

rem ---------- 5. start frontend ----------
echo [start] frontend ^(npm run dev^) ...
start "TradingLog frontend :5173" /D "%ROOT%" cmd /k npm run dev

echo.
echo ------------------------------------------------------------
echo   Both services are now running in their own windows:
echo     * TradingLog backend  :8000
echo     * TradingLog frontend :5173
echo.
echo   Open http://localhost:5173 in your browser.
echo   To stop everything, close those two windows.
echo ------------------------------------------------------------
echo.

if "%OPEN_BROWSER%"=="1" start "" "http://localhost:5173"

echo This window closes itself in 8 seconds ...
timeout /t 8 /nobreak >nul 2>nul
endlocal
exit /b 0


rem ============================================================
rem  subroutines
rem ============================================================

:ensure_frontend_deps
if exist "%ROOT%\node_modules" exit /b 0
echo [deps] node_modules not found, running npm install ...
echo.
call npm install
if errorlevel 1 exit /b 1
echo.
exit /b 0

:ensure_backend_deps
if exist "%ROOT%\server\.venv" exit /b 0
echo [deps] server\.venv not found, running uv sync ...
echo.
pushd "%ROOT%\server"
call uv sync
set "UV_SYNC_RC=%ERRORLEVEL%"
popd
if not "%UV_SYNC_RC%"=="0" exit /b 1
echo.
exit /b 0

:port_in_use
rem returns 0 = port is in use, 1 = port is free
rem NOTE 1: findstr treats a space in the pattern as an OR separator, and /c:
rem         makes the pattern literal (so nothing ever matches). Keep the
rem         regex space-free - ".*" already covers netstat's padding.
rem NOTE 2: do NOT add "-p tcp" here. On Windows that switch omits TCPv6
rem         listeners, and Vite binds [::1]:5173 by default, so the frontend
rem         would never be detected. Plain netstat also lists UDP, but UDP
rem         rows never contain LISTENING, so they cannot false-positive.
netstat -ano | findstr /r ":%~1.*LISTENING" >nul 2>nul
exit /b %ERRORLEVEL%


rem ============================================================
rem  error branches
rem ============================================================

:err_no_package
echo [ERROR] package.json not found in the script folder.
echo         Make sure start_dev.cmd lives in the project root.
echo         current folder: %ROOT%
echo.
pause
exit /b 1

:err_no_server
echo [ERROR] server\pyproject.toml not found - backend project is incomplete.
echo         current folder: %ROOT%
echo.
pause
exit /b 1

:err_no_uv
echo [ERROR] 'uv' was not found on PATH.
echo         The backend is managed by uv, please install it first:
echo         https://docs.astral.sh/uv/getting-started/installation/
echo.
pause
exit /b 1

:err_no_npm
echo [ERROR] 'npm' was not found on PATH.
echo         Please install Node.js first (requires 20.19+ or 22.12+):
echo         https://nodejs.org/
echo.
pause
exit /b 1

:err_npm_install
echo [ERROR] npm install failed. Check your network and Node.js version.
echo.
pause
exit /b 1

:err_uv_sync
echo [ERROR] uv sync failed. Check your network and Python version.
echo.
pause
exit /b 1
