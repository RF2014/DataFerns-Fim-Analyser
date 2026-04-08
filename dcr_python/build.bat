@echo off
REM Build executable for FIM Traffic Analyzer
REM This script will take 3-5 minutes to complete

setlocal enabledelayedexpansion

set VENV_PYTHON=C:\Users\royston.fernandes\Documents\CodeVBA_fim\GUI\.venv\Scripts\python.exe
set DIST_DIR=%~dp0
set SOURCE_DIR=C:\Users\royston.fernandes\Documents\CodeVBA_fim\GUI\dcr_python\src
set BUILD_DIR=%DIST_DIR%build
set DIST_OUTPUT_DIR=%DIST_DIR%dist

echo ======================================================================
echo FIM Traffic Analyzer - Building Executable
echo ======================================================================
echo.
echo This process may take 3-5 minutes. Please wait...
echo.
echo Build will create:
echo   - %DIST_OUTPUT_DIR%\FIM_Analyzer.exe
echo.

if not exist "%VENV_PYTHON%" (
    echo ERROR: Virtual environment not found at:
    echo   %VENV_PYTHON%
    pause
    exit /b 1
)

echo [1/2] Cleaning previous builds...
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
if exist "%DIST_OUTPUT_DIR%" rmdir /s /q "%DIST_OUTPUT_DIR%"

echo [2/2] Building executable with PyInstaller...
echo.

"%VENV_PYTHON%" -m PyInstaller ^
    --name=FIM_Analyzer ^
    --onefile ^
    --windowed ^
    --icon=NONE ^
    --add-data "%SOURCE_DIR%;src" ^
    --collect-all PyQt5 ^
    --collect-all matplotlib ^
    --collect-all pandas ^
    --collect-all numpy ^
    --collect-all openpyxl ^
    --collect-all holidays ^
    --hidden-import=PyQt5 ^
    --hidden-import=matplotlib.backends.backend_qt5agg ^
    --distpath "%DIST_OUTPUT_DIR%" ^
    --workpath "%BUILD_DIR%" ^
    --specpath "%DIST_DIR%" ^
    "%SOURCE_DIR%\ui\fim_loader.py"

if %ERRORLEVEL% neq 0 (
    echo.
    echo ======================================================================
    echo ERROR: Build failed!
    echo ======================================================================
    pause
    exit /b 1
)

echo.
echo ======================================================================
echo BUILD SUCCESSFUL!
echo ======================================================================
echo.

if exist "%DIST_OUTPUT_DIR%\FIM_Analyzer.exe" (
    for %%A in ("%DIST_OUTPUT_DIR%\FIM_Analyzer.exe") do set SIZE=%%~zA
    echo Executable created: %DIST_OUTPUT_DIR%\FIM_Analyzer.exe
    echo Size: !SIZE! bytes
    echo.
    echo You can now distribute this EXE to any Windows computer.
    echo No Python installation required!
) else (
    echo ERROR: Executable was not created!
    pause
    exit /b 1
)

echo.
echo Creating README...

(
echo FIM TRAFFIC ANALYZER - STANDALONE EXECUTABLE
echo =============================================
echo.
echo QUICK START:
echo 1. Double-click FIM_Analyzer.exe to launch the application
echo 2. No installation required - runs directly from this folder
echo 3. No Python or other dependencies needed
echo.
echo SYSTEM REQUIREMENTS:
echo - Windows 7 or later
echo - 512 MB available disk space
echo - No other software required
echo.
echo FEATURES:
echo - Load and analyze FIM (traffic counting) data files
echo - Generate statistical reports
echo - Export analysis to Excel and PDF formats
echo - Date/time range filtering for targeted analysis
echo - Automatic French public holiday detection
echo - Night/day and working day traffic calculations
echo.
echo USAGE:
echo 1. Launch FIM_Analyzer.exe
echo 2. Click "Load FIM File" to select a .fim data file
echo 3. Click "Analyse" to generate analysis
echo 4. Select date/time range for analysis (if needed)
echo 5. Choose export format (Excel or PDF)
echo 6. Results are saved to the selected location
echo.
echo TROUBLESHOOTING:
echo - First launch may take 10-20 seconds (normal - Python initialization)
echo - Windows may show security warning on first run
echo   Click "More info" then "Run anyway" to proceed
echo - Ensure .fim file is valid before loading
echo.
echo VERSION: 1.0
echo BUILT: December 2025
) > "%DIST_OUTPUT_DIR%\README.txt"

echo README created: %DIST_OUTPUT_DIR%\README.txt
echo.
echo Ready to distribute FIM_Analyzer.exe to any Windows computer!
echo.
pause
