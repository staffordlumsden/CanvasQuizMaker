@echo off
setlocal
set "REPO_ROOT=%~dp0"
"%REPO_ROOT%.venv\Scripts\python.exe" "%REPO_ROOT%text2qti_web.py"
