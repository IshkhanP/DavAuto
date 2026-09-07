@echo off
REM BlackSharkCars one-shot runner (Windows)
REM Usage: run.bat           -> asks Docker or local
REM        run.bat docker     -> Docker mode
REM        run.bat local      -> local mode
REM        run.bat tests      -> run tests only

setlocal
if /I "%1"=="docker" (
    python run.py --docker
    exit /b %ERRORLEVEL%
)
if /I "%1"=="local" (
    python run.py --local
    exit /b %ERRORLEVEL%
)
if /I "%1"=="tests" (
    python run.py --tests
    exit /b %ERRORLEVEL%
)
python run.py
exit /b %ERRORLEVEL%