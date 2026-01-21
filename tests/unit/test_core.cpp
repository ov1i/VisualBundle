#include <gtest/gtest.h>
#include <opencv2/opencv.hpp>
#include <chrono>
#include <thread>
#include "../../interface/ObjRem/inpainter.h"

class PatchRemoverTest : public ::testing::Test {
protected:
    // Helper to generate a standardized test image in memory
    cv::Mat createDummyMat(int width=100, int height=100) {
        // Green background
        cv::Mat dummy = cv::Mat(height, width, CV_8UC3, cv::Scalar(0, 255, 0)); 
        // Blue box in center to remove
        cv::rectangle(dummy, cv::Rect(width/2 - 10, height/2 - 10, 20, 20), cv::Scalar(255, 0, 0), -1); 
        return dummy;
    }
};

// 1. Basic Load Test
TEST_F(PatchRemoverTest, LoadFromMemorySuccess) {
    PatchRemover remover;
    cv::Mat input = createDummyMat();
    ASSERT_NO_THROW(remover.setImage(input));
}

// 2. TIMEOUT TEST (Critical for Infinite Loop Detection)
TEST_F(PatchRemoverTest, ProcessTerminatesInReasonableTime) {
    PatchRemover remover;
    cv::Mat input = createDummyMat(100, 100); // Small image
    remover.setImage(input);
    remover.setSelection(40, 40, 20, 20); // 20x20 hole

    auto start = std::chrono::high_resolution_clock::now();
    
    // This should finish almost instantly for 100x100. 
    // If infinite loop exists, this will hang.
    ASSERT_NO_THROW(remover.process());

    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> elapsed = end - start;

    // Fail if it takes longer than 2.0 seconds (It should take < 0.1s)
    EXPECT_LT(elapsed.count(), 2.0) << "Algorithm took too long! Infinite loop suspected.";
}

// 3. Convergence Test
// Ensure the hole is actually filled (no black/empty pixels left in the target area)
TEST_F(PatchRemoverTest, HoleIsActuallyFilled) {
    PatchRemover remover;
    cv::Mat input = createDummyMat();
    remover.setImage(input);
    
    // Select the blue box
    cv::Rect roi(40, 40, 20, 20);
    remover.setSelection(roi.x, roi.y, roi.width, roi.height);
    remover.process();

    cv::Mat result = remover.getResult();
    
    // Check the ROI area in the result. It should NOT be black (0,0,0) or pure blue (255,0,0).
    // It should be filled with Green (0,255,0) from the background.
    cv::Mat roiResult = result(roi);
    cv::Scalar meanColor = cv::mean(roiResult);

    // BGR channel check: Green should be dominant
    EXPECT_GT(meanColor[1], 200.0) << "Inpainted area should be Green (Background), but it isn't.";
    EXPECT_LT(meanColor[0], 50.0)  << "Inpainted area still has Blue (Object), removal failed.";
}

// 4. Structure Propagation Test (The Criminisi 'Smart' Test)
// We draw a white line on a black background, cut a hole in the line, 
// and see if the algorithm reconnects it.
TEST_F(PatchRemoverTest, ReconnectsBrokenLine) {
    cv::Mat img = cv::Mat::zeros(100, 100, CV_8UC3); // Black
    
    // Draw horizontal white line
    cv::line(img, cv::Point(0, 50), cv::Point(100, 50), cv::Scalar(255, 255, 255), 3);
    
    PatchRemover remover;
    remover.setImage(img);
    
    // Cut a hole in the middle of the line
    int holeSize = 10;
    remover.setSelection(50 - holeSize/2, 50 - holeSize/2, holeSize, holeSize);
    remover.process();
    
    cv::Mat result = remover.getResult();
    
    // Check the center pixel. It should be White (reconnected), not Black.
    cv::Vec3b centerPixel = result.at<cv::Vec3b>(50, 50);
    
    // Check intensity (255 = white)
    int intensity = (centerPixel[0] + centerPixel[1] + centerPixel[2]) / 3;
    EXPECT_GT(intensity, 100) << "Failed to reconnect the white line. Structure propagation missing.";
}

// 5. Deep Copy Safety
TEST_F(PatchRemoverTest, InternalImageIsDeepCopy) {
    PatchRemover remover;
    cv::Mat original = createDummyMat();
    remover.setImage(original);
    
    // Destroy external matrix
    original.setTo(cv::Scalar(0, 0, 0)); 
    
    remover.setSelection(40, 40, 20, 20);
    remover.process();
    
    cv::Mat result = remover.getResult();
    cv::Scalar meanColor = cv::mean(result);
    EXPECT_GT(meanColor[1], 100.0) << "C++ logic relied on external memory pointer!";
}

// 6. Exception Safety
TEST_F(PatchRemoverTest, ThrowsOnEmptyMatInput) {
    PatchRemover remover;
    cv::Mat empty;
    EXPECT_THROW(remover.setImage(empty), std::runtime_error);
}

TEST_F(PatchRemoverTest, ThrowsProcessWithoutImage) {
    PatchRemover remover;
    EXPECT_THROW(remover.process(), std::runtime_error);
}