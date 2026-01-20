include(FetchContent)
FetchContent_Declare(
  googletest
  GIT_REPOSITORY https://github.com/google/googletest.git
  GIT_TAG        release-1.12.1
)
FetchContent_MakeAvailable(googletest)

# Define the test executable
# NOTE: We use ${CMAKE_SOURCE_DIR} to ensure we find the files correctly 
# regardless of where this script is running.
add_executable(unit_tests 
    test_core.cpp 
    ${CMAKE_SOURCE_DIR}/src/ObjRem/inpainter.cpp
)

# Link Dependencies
target_link_libraries(unit_tests PRIVATE 
    GTest::gtest_main 
    opencv_core 
    opencv_imgproc 
    opencv_photo 
    opencv_imgcodecs
)

target_include_directories(unit_tests PRIVATE 
    ${CMAKE_SOURCE_DIR}/interface/ObjRem
    ${CMAKE_SOURCE_DIR}/src
    ${opencv_SOURCE_DIR}/include
    ${opencv_SOURCE_DIR}/modules/core/include
    ${opencv_SOURCE_DIR}/modules/imgproc/include
    ${opencv_SOURCE_DIR}/modules/photo/include
    ${opencv_SOURCE_DIR}/modules/imgcodecs/include
    ${opencv_BINARY_DIR}
    ${CMAKE_BINARY_DIR}
)

# Register with CTest
add_test(NAME CoreLogicTest COMMAND unit_tests)