@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo  Pokemon Oneshot AllMove Challenge Builder
echo ==========================================
echo.

echo [1/5] Cleaning up previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist release rmdir /s /q release
if exist *.spec del *.spec

echo [2/5] Building executable with PyInstaller...
echo This may take a few minutes...
pyinstaller --onefile --windowed oneshot_allmove_challenge.py

if not exist dist\oneshot_allmove_challenge.exe (
    echo ERROR: Build failed! Check if PyInstaller is installed.
    echo Run: pip install pyinstaller
    pause
    exit /b 1
)

echo [3/5] Creating release folder structure...
mkdir release
mkdir release\saves
mkdir release\lua_interface

echo [4/5] Copying files to release...
copy dist\oneshot_allmove_challenge.exe release\
copy pokemon_moves.csv release\
copy oneshot_allmove_script.lua release\
copy settings.ini release\
copy README.md release\
copy saves\example_challenge.json release\saves\

echo [5/5] Cleaning up build files...
rmdir /s /q build
rmdir /s /q dist
del oneshot_allmove_challenge.spec

echo.
echo ==========================================
echo  BUILD COMPLETE!
echo ==========================================
echo.
echo Release files are ready in 'release' folder:

dir release /b

echo.
echo File sizes:
for %%f in (release\*.exe) do (
    for %%s in (%%f) do echo   %%~nxf: %%~zs bytes
)

echo.
echo You can now:
echo 1. Test the executable: release\oneshot_allmove_challenge.exe
echo 2. Zip the 'release' folder for distribution
echo 3. Upload to GitHub Releases
echo.
pause