#include "inpainter.h"
#include <iostream>
#include <stdexcept>

PatchRemover::PatchRemover() : selection{0,0,0,0} {}

void PatchRemover::setImage(const cv::Mat& image) {
    if (image.empty()) {
        throw std::runtime_error("Received empty image from Python");
    }
    // Deep copy to ensure C++ owns its memory, safe from Python GC
    image.copyTo(srcImage);
    
    // Reset mask
    mask = cv::Mat::zeros(srcImage.size(), CV_8UC1);
}

void PatchRemover::setSelection(int x, int y, int width, int height) {
    if (srcImage.empty()) return;

    x = std::max(0, x);
    y = std::max(0, y);
    width = std::min(width, srcImage.cols - x);
    height = std::min(height, srcImage.rows - y);

    selection = {x, y, width, height};

    mask.setTo(cv::Scalar(0));
    cv::rectangle(mask, cv::Rect(x, y, width, height), cv::Scalar(255), -1);
}

void PatchRemover::process() {
    if (srcImage.empty()) throw std::runtime_error("No image loaded");
    
    cv::Mat denoised;
    // 1. Denoise (Clean up the source so we don't copy noise)
    cv::fastNlMeansDenoisingColored(srcImage, denoised, 3, 3, 7, 21);

    // 2. DILATE THE MASK (Critical Fix)
    // This expands your selection by ~5 pixels in all directions.
    // It ensures we are copying from the 'background' and not the 'object edge'.
    int dilation_size = 5; 
    cv::Mat element = cv::getStructuringElement(
        cv::MORPH_RECT,
        cv::Size(2 * dilation_size + 1, 2 * dilation_size + 1),
        cv::Point(dilation_size, dilation_size)
    );
    cv::Mat dilatedMask;
    cv::dilate(mask, dilatedMask, element);

    // 3. Inpainting
    // We use the DILATED mask now.
    // INPAINT_NS (Navier-Stokes) often handles structural edges slightly better than TELEA
    // Try swapping to cv::INPAINT_NS if TELEA still looks "smudgy".
    cv::inpaint(denoised, dilatedMask, result, 5, cv::INPAINT_TELEA);
}
// void PatchRemover::process() {
//     if (srcImage.empty()) throw std::runtime_error("No image loaded");
    
//     cv::Mat denoised;
//     cv::fastNlMeansDenoisingColored(srcImage, denoised, 3, 3, 7, 21);
//     cv::inpaint(denoised, mask, result, 3, cv::INPAINT_TELEA);
// }

bool PatchRemover::save(const std::string& outputPath) {
    if (result.empty()) return false;
    return cv::imwrite(outputPath, result);
}

cv::Mat PatchRemover::getResult() const {
    if (result.empty()) {
        // Return a copy of src if process hasn't run, or empty
        return srcImage.empty() ? cv::Mat() : srcImage; 
    }
    return result;
}