@echo off
rem ============================================================
rem  hermes.cmd — main entry point (Windows)
rem
rem  Location (canonical): the root of this repo, e.g.
rem    C:\Users\%USERNAME%\paperclip-hermes-paperclip-adapter-integration-...\hermes.cmd
rem
rem  Paperclip's adapter calls this file via resolveSpawnTarget.
rem  It delegates all the logic to launch_hermes.py in the same folder.
rem
rem  Any other hermes.cmd (in a PATH bin folder, etc.) is a thin shim
rem  that calls launch_hermes.py from THIS folder.
rem ============================================================
if "%~1"=="--version" (
  wsl bash -lc "hermes --version"
  goto :eof
)
python "%~dp0launch_hermes.py" %*
