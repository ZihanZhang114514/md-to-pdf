@echo off
rem Drag a .md file onto this .bat to convert it to PDF next to the source file.
setlocal
if "%~1"=="" (
  echo Drag a .md file onto this .bat to convert it to PDF.
  pause
  exit /b 1
)
set "IN=%~f1"
set "OUT=%~dpn1.pdf"
set "TITLE=%~n1"
echo Input : "%IN%"
echo Output: "%OUT%"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0md2pdf.ps1" -InputPath "%IN%" -OutputPath "%OUT%" -Title "%TITLE%"
if errorlevel 1 ( echo FAILED & pause & exit /b 1 )
echo OK: "%OUT%"
pause
