@echo off

echo.
echo ==========================================
echo    ThorneForm Cue Designer Build
echo ==========================================
echo.

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

python -m PyInstaller ^
--onefile ^
--windowed ^
--clean ^
--hidden-import=_cffi_backend ^
--icon=icons/app_icon.ico ^
--name "ThorneForm Cue Designer" ^
thorneform_cue_designer.py

echo.
echo ==========================================
echo Build Complete!
echo ==========================================
echo.

pause