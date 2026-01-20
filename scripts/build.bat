@echo off
setlocal EnableDelayedExpansion

:: ==========================================
:: 1. SETUP ARGUMENTS & MODE
:: ==========================================
set BUILD_MODE=Library Only
set CMAKE_FLAGS=-DBUILD_TESTING=OFF
set TARGET_FLAG=--target ObjectRemover_core

:: Check if user passed "test" as an argument
if /I "%1"=="test" (
    set BUILD_MODE=Library + Unit Tests
    set CMAKE_FLAGS=-DBUILD_TESTING=ON
    set TARGET_FLAG=
)

echo ==============================================
echo    Compiling ObjectRemover (Windows)
echo    Mode: %BUILD_MODE%
echo ==============================================

:: ==========================================
:: 2. PREPARE BUILD ENVIRONMENT
:: ==========================================
if not exist .build mkdir .build
cd .build

:: ==========================================
:: 3. CONFIGURE CMAKE
:: ==========================================
echo [INFO] Configuring Project...
cmake .. -DCMAKE_BUILD_TYPE=Release %CMAKE_FLAGS%

:: ==========================================
:: 4. COMPILE
:: ==========================================
echo [INFO] Building... (This may take time for OpenCV)
cmake --build . --config Release --parallel %NUMBER_OF_PROCESSORS% %TARGET_FLAG%

if %errorlevel% neq 0 (
    echo [ERROR] Build Failed!
    exit /b %errorlevel%
)

:: ==========================================
:: 5. BRANCH: TEST OR FREEZE
:: ==========================================
if /I "%1"=="test" (
    :: --- TEST MODE ---
    echo ==============================================
    echo    Running Google Tests...
    echo ==============================================
    
    :: Check standard Release locations for the test executable
    if exist "Release\unit_tests.exe" (
        "Release\unit_tests.exe"
    ) else if exist "bin\Release\unit_tests.exe" (
        "bin\Release\unit_tests.exe"
    ) else if exist "unit_tests.exe" (
        "unit_tests.exe"
    ) else (
        echo [ERROR] unit_tests.exe not found!
        exit /b 1
    )

) else (
    :: --- RELEASE MODE (FREEZE) ---
    echo ==============================================
    echo    Freezing Library...
    echo ==============================================

    set "TARGET_DIR=..\freezed_libs"
    if not exist "!TARGET_DIR!" mkdir "!TARGET_DIR!"

    :: Loop through potential .pyd files and copy them
    :: We look in Release folder which is standard for Windows CMake builds
    for /r %%f in (ObjectRemover_core*.pyd) do (
        echo    [+] Copied %%f
        copy /Y "%%f" "!TARGET_DIR!\ObjectRemover_core.pyd" >nul
    )

    echo    [INFO] Library frozen to freezed_libs\
)

echo ==============================================
echo    Build Success!
echo    Artifacts are located in: .build\
echo ==============================================

cd ..
pause