@echo off
rem ============================================================
rem  Put this in: C:\Users\%USERNAME%\bin\hermes.cmd
rem  (the bin folder must be on the Windows PATH)
rem
rem  This file lets you call hermes from a Windows command line.
rem  Paperclip calls dist\hermes.exe directly, not through this file.
rem ============================================================
if "%~1"=="" (
  wsl hermes
  goto :eof
)
python "C:\Users\%USERNAME%\paperclip-hermes-paperclip-adapter-integration\launch_hermes.py" %*
