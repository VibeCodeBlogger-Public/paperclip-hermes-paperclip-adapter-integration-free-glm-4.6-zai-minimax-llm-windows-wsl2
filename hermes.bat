@echo off
rem ============================================================
rem  Location of this file:
rem    C:\Users\<YOUR_USER>\bin\hermes.bat
rem
rem  The folder C:\Users\<YOUR_USER>\bin\ must be added to the
rem  Windows PATH (environment variable).
rem
rem  What this file does:
rem    Forwards the hermes command from Windows into WSL (Ubuntu),
rem    where hermes-agent is actually installed.
rem ============================================================
wsl bash -lc "hermes %*"
