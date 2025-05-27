@echo off
title HJKS Scraper - Auto Runner
setlocal enabledelayedexpansion

:: Define Python path
set "USERPROFILE_PATH=%USERPROFILE%"
set "PYTHON_PATH=%USERPROFILE_PATH%\Miniconda3\envs\jepx_scraper\python.exe"

:: Set the start and end dates (format: yyyy-MM-dd)
set "START_DATE=2025-05-26"
set "END_DATE=2020-04-01"

:: Convert END_DATE to no-dash format once（这是常量）
set "END_NO_DASH=%END_DATE:-=%"

:: Initialize current date
set "CURRENT_DATE=%START_DATE%"

echo.
echo ================= HJKS Spot Curve Auto Runner =================
echo Python: %PYTHON_PATH%
echo Start:  %START_DATE%
echo End:    %END_DATE%
echo ----------------------------------------------------------------------

:loop
:: Format CURRENT_DATE for Python call: yyyy/MM/dd
for /f %%i in ('powershell -nologo -command "(Get-Date '!CURRENT_DATE!').ToString('yyyy/MM/dd')"') do (
    set "DATE_FOR_PYTHON=%%i"
)

echo Running: %PYTHON_PATH% run_jepx_curve.py !DATE_FOR_PYTHON!
%PYTHON_PATH% run_jepx_curve.py !DATE_FOR_PYTHON!

:: Move to previous day
for /f %%i in ('powershell -nologo -command "(Get-Date '!CURRENT_DATE!').AddDays(-1).ToString('yyyy-MM-dd')"') do (
    set "CURRENT_DATE=%%i"
)

:: Convert CURRENT_DATE to no-dash format for comparison
set "CURRENT_NO_DASH=!CURRENT_DATE:-=!"

:: Check loop continuation
if !CURRENT_NO_DASH! GEQ %END_NO_DASH% (
    goto loop
)

echo.
echo All Done!
pause
exit
