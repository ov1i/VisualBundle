cmake_minimum_required(VERSION 3.14)
project(ObjectRemover)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# ==========================================
# 0. ENABLE OPENMP (Multi-Threading)
# ==========================================
find_package(OpenMP)

if(OpenMP_CXX_FOUND)
    message(STATUS "OpenMP Found. Compiling with Multi-Threading support.")
else()
    message(WARNING "OpenMP NOT found. Compiling in Single-Threaded mode.")
endif()

# ==========================================
# 1. DOWNLOAD & BUILD OPENCV
# ==========================================
message(STATUS "Downloading and compiling OpenCV...")
include(FetchContent)

set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)
set(BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(BUILD_PERF_TESTS OFF CACHE BOOL "" FORCE)
set(BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(BUILD_DOCS OFF CACHE BOOL "" FORCE)
set(BUILD_JAVA OFF CACHE BOOL "" FORCE)
set(BUILD_opencv_python2 OFF CACHE BOOL "" FORCE)
set(BUILD_opencv_python3 OFF CACHE BOOL "" FORCE)
set(WITH_CUDA OFF CACHE BOOL "" FORCE)
set(WITH_GTK OFF CACHE BOOL "" FORCE)
set(WITH_FFMPEG OFF CACHE BOOL "" FORCE)
set(WITH_GSTREAMER OFF CACHE BOOL "" FORCE)
set(WITH_1394 OFF CACHE BOOL "" FORCE)
set(WITH_V4L OFF CACHE BOOL "" FORCE)

set(BUILD_LIST core imgproc photo imgcodecs CACHE STRING "Selected modules" FORCE)

FetchContent_Declare(
  opencv
  GIT_REPOSITORY https://github.com/opencv/opencv.git
  GIT_TAG        4.8.0
)
FetchContent_MakeAvailable(opencv)

# ==========================================
# 2. DOWNLOAD PYBIND11
# ==========================================
message(STATUS "Fetching Pybind11...")
FetchContent_Declare(
  pybind11
  GIT_REPOSITORY https://github.com/pybind/pybind11
  GIT_TAG        v2.11.1
)
FetchContent_MakeAvailable(pybind11)

# ==========================================
# 3. BUILD THE MAIN MODULE
# ==========================================
pybind11_add_module(ObjectRemover_core
    src/Binder/bindings.cpp
    src/ObjRem/inpainter.cpp
)

target_link_libraries(ObjectRemover_core PRIVATE 
    opencv_core 
    opencv_imgproc 
    opencv_photo 
    opencv_imgcodecs
)

# --- LINK OPENMP IF FOUND ---
if(OpenMP_CXX_FOUND)
    target_link_libraries(ObjectRemover_core PRIVATE OpenMP::OpenMP_CXX)
endif()

# Manual Include Paths for Main Module
target_include_directories(ObjectRemover_core PRIVATE 
    interface/ObjRem
    src
    ${opencv_SOURCE_DIR}/include
    ${opencv_SOURCE_DIR}/modules/core/include
    ${opencv_SOURCE_DIR}/modules/imgproc/include
    ${opencv_SOURCE_DIR}/modules/photo/include
    ${opencv_SOURCE_DIR}/modules/imgcodecs/include
    ${opencv_BINARY_DIR}
    ${CMAKE_BINARY_DIR}
)

# ==========================================
# 4. UNIT TESTS
# ==========================================
option(BUILD_TESTING "Build the unit tests" OFF)

if(BUILD_TESTING)
    message(STATUS "Enabled: Building Unit Tests")
    enable_testing()
    # This looks for CMakeLists.txt inside the 'tests' folder
    add_subdirectory(tests/unit)
endif()

message(STATUS "Build setup complete.")