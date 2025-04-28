@echo off
title HJKS Scraper - Auto Runner
set "USERPROFILE_PATH=%USERPROFILE%"
set "PYTHON_PATH=%USERPROFILE_PATH%\Miniconda3\envs\hjks_scraper\python.exe"

cd /d "%~dp0"
echo [%date% %time%] Running HJKS Scraper...

"%PYTHON_PATH%" hjks_scraper.py

echo.
echo Script finished. Window will close in 15 seconds...
timeout /t 15 /nobreak
exit
