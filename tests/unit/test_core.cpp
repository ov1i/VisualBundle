#include <gtest/gtest.h>
#include <opencv2/opencv.hpp>
#include <cstdio>
#include "../../interface/ObjRem/inpainter.h"

class PatchRemoverTest : public ::testing::Test {
protected:
    const std::string TEST_IMG_PATH = "gtest_dummy_input.png";
    const std::string TEST_OUT_PATH = "gtest_dummy_output.png";

    // Helper to generate a standardized test image in memory
    cv::Mat createDummyMat() {
        cv::Mat dummy = cv::Mat(100, 100, CV_8UC3, cv::Scalar(0, 255, 0)); // Green
        cv::rectangle(dummy, cv::Rect(40, 40, 20, 20), cv::Scalar(255, 0, 0), -1); // Blue box
        return dummy;
    }

    void SetUp() override {
        // We still save a file for the file-loading tests
        cv::Mat dummy = createDummyMat();
        if (!cv::imwrite(TEST_IMG_PATH, dummy)) {
            throw std::runtime_error("Failed to create dummy test image.");
        }
    }

    void TearDown() override {
        std::remove(TEST_IMG_PATH.c_str());
        std::remove(TEST_OUT_PATH.c_str());
    }
};


// 1. Test loading directly from cv::Mat (No File I/O)
TEST_F(PatchRemoverTest, LoadFromMemorySuccess) {
    PatchRemover remover;
    cv::Mat input = createDummyMat();
    
    // Should accept a valid matrix
    ASSERT_NO_THROW(remover.setImage(input));
    
    // Should run process without error
    remover.setSelection(40, 40, 20, 20);
    ASSERT_NO_THROW(remover.process());
}

// 2. Test that getResult returns the processed data
TEST_F(PatchRemoverTest, GetResultReturnsValidMat) {
    PatchRemover remover;
    remover.setImage(createDummyMat());
    remover.setSelection(40, 40, 20, 20);
    remover.process();

    cv::Mat result = remover.getResult();
    
    // Result should not be empty
    ASSERT_FALSE(result.empty());
    // Result should match input dimensions
    EXPECT_EQ(result.rows, 100);
    EXPECT_EQ(result.cols, 100);
}

// 3. Test Deep Copy Safety
// If we modify the input matrix AFTER passing it to C++, the C++ internal copy should remain safe.
TEST_F(PatchRemoverTest, InternalImageIsDeepCopy) {
    PatchRemover remover;
    cv::Mat original = createDummyMat();
    
    // Pass to tool
    remover.setImage(original);
    
    // Now destroy/modify the original external matrix
    original.setTo(cv::Scalar(0, 0, 0)); // Turn it black
    
    // Run process on the internal copy
    remover.setSelection(40, 40, 20, 20);
    remover.process();
    
    // The result should NOT be a black image (it should be green/inpainted)
    cv::Mat result = remover.getResult();
    cv::Scalar meanColor = cv::mean(result);
    
    // Green channel (index 1) should still be high (~255), not 0
    EXPECT_GT(meanColor[1], 100.0); 
}

// 4. Test Safety: Passing Empty Matrix
TEST_F(PatchRemoverTest, ThrowsOnEmptyMatInput) {
    PatchRemover remover;
    cv::Mat empty;
    
    // Should throw runtime_error
    EXPECT_THROW(remover.setImage(empty), std::runtime_error);
}

// 5. Test processing without loading anything
TEST_F(PatchRemoverTest, ThrowsProcessWithoutImage) {
    PatchRemover remover;
    EXPECT_THROW(remover.process(), std::runtime_error);
}