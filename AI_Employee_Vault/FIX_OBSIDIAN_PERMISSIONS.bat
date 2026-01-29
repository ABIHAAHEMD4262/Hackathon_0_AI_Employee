@echo off
echo Fixing Obsidian Vault Permissions...
echo.

REM Get the directory where this batch file is located
set "VAULT_DIR=%~dp0"

REM Remove any trailing backslash
if "%VAULT_DIR:~-1%"=="\" set "VAULT_DIR=%VAULT_DIR:~0,-1%"

echo Vault Directory: %VAULT_DIR%
echo.

REM Take ownership of the .obsidian folder
echo Taking ownership of .obsidian folder...
takeown /F "%VAULT_DIR%\.obsidian" /R /D Y >nul 2>&1

REM Grant full permissions to current user
echo Granting permissions...
icacls "%VAULT_DIR%\.obsidian" /grant "%USERNAME%":F /T /Q >nul 2>&1
icacls "%VAULT_DIR%" /grant "%USERNAME%":F /T /Q >nul 2>&1

echo.
echo Done! Try opening the vault in Obsidian now.
echo.
echo If you still get errors, try:
echo 1. Run this script as Administrator (right-click -> Run as administrator)
echo 2. Close Obsidian completely before opening the vault
echo 3. Copy the AI_Employee_Vault folder to a location like Documents
echo.
pause
