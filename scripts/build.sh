#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# ==========================================
# 1. SETUP ARGUMENTS & MODE
# ==========================================
# Default: Build only the Python Library
BUILD_MODE="Library Only"
CMAKE_FLAGS="-DBUILD_TESTING=OFF"
TARGET_FLAG="--target ObjectRemover_core" # Only build the lib by default

# Check if user passed "test" as an argument
if [[ "$1" == "test" ]]; then
    BUILD_MODE="Library + Unit Tests"
    CMAKE_FLAGS="-DBUILD_TESTING=ON"
    TARGET_FLAG="" # Build everything (lib + tests)
fi

echo "=============================================="
echo "   Compiling ObjectRemover                    "
echo "   Mode: $BUILD_MODE                          "
echo "=============================================="

# ==========================================
# 2. PREPARE BUILD ENVIRONMENT
# ==========================================
mkdir -p .build
cd .build

# ==========================================
# 3. CONFIGURE CMAKE
# ==========================================
echo "[INFO] Configuring Project..."
# We pass the CMAKE_FLAGS determined above
cmake -DCMAKE_BUILD_TYPE=Release $CMAKE_FLAGS ..

# ==========================================
# 4. COMPILE
# ==========================================
echo "[INFO] Building... (This may take time for OpenCV)"
NUM_CORES=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)

# We use the TARGET_FLAG determined above
cmake --build . --config Release --parallel "$NUM_CORES" $TARGET_FLAG

# ==========================================
# 5. BRANCH: TEST OR FREEZE
# ==========================================
if [[ "$1" == "test" ]]; then
    # --- TEST MODE ---
    echo "=============================================="
    echo "   Running Google Tests...                    "
    echo "=============================================="
    
    # Run the test executable
    if [ -f "./bin/unit_tests" ]; then
        ./bin/unit_tests
    elif [ -f "./unit_tests" ]; then
        ./unit_tests
    else
        echo "[ERROR] unit_tests executable not found!"
        exit 1
    fi

else
    # --- RELEASE MODE (FREEZE) ---
    # Only copy to freezed_libs if we are NOT testing
    echo "=============================================="
    echo "   Freezing Library...                        "
    echo "=============================================="

    # Go up to the root directory relative to .build
    TARGET_DIR="../freezed_libs"

    # Create directory if it doesn't exist
    mkdir -p "$TARGET_DIR"

    # Copy Linux/Mac Shared Objects
    find . -maxdepth 2 -name "ObjectRemover_core*.so" -exec cp {} "$TARGET_DIR/ObjectRemover_core.so" \; -exec echo "   [+] Copied {}" \;

    # Copy Windows Python DLLs
    find . -maxdepth 2 -name "ObjectRemover_core*.pyd" -exec cp {} "$TARGET_DIR/ObjectRemover_core.pyd" \; -exec echo "   [+] Copied {}" \;

    # Copy Mac Dynamic Libs
    find . -maxdepth 2 -name "ObjectRemover_core*.dylib" -exec cp {} "$TARGET_DIR/ObjectRemover_core.dylib" \; -exec echo "   [+] Copied {}" \;
    
    echo "   [INFO] Library frozen to freezed_libs/"
fi

echo "=============================================="
echo "   Build Success!                             "
echo "   Artifacts are located in: .build/          "
echo "=============================================="