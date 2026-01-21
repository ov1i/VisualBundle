#ifndef INPAINTER_H
#define INPAINTER_H

#include <opencv2/opencv.hpp>
#include <string>
#include <vector>

struct InpaintConfig {
    int patchSize = 9;      // 9x9 is a standard sweet spot
    float searchStep = 10;  // Optimization: Don't search every single pixel (speedup)
};

class PatchRemover {
public:
    PatchRemover();
    
    void setImage(const cv::Mat& image);
    void setSelection(int x, int y, int width, int height);
    void process();
    
    cv::Mat getResult() const;
    bool save(const std::string& outputPath);

private:
    cv::Mat srcImage;
    cv::Mat mask;           // 0 = Valid, 255 = Hole (Target)
    cv::Mat result;         // Starts as src, gets filled iteratively
    cv::Mat confidence;     // Stores confidence of pixels (1.0 = known, 0.0 = hole)
    cv::Mat dataTerm;       // Stores structural priority
    cv::Mat priority;       // P = C * D (Final priority)

    cv::Rect selection;
    InpaintConfig config;

    // Helpers
    void initializeMaps();
    bool hasMoreSteps();
    void computePriority(const std::vector<cv::Point>& contour);
    cv::Mat getPatch(const cv::Mat& img, cv::Point p);
    cv::Point findBestMatch(const cv::Mat& targetPatch, const cv::Mat& patchMask);
    void update(cv::Point targetPoint, cv::Point sourcePoint, const cv::Mat& patchMask);
    
    // Math Helpers
    cv::Point2f getGradient(cv::Point p);
    cv::Point2f getNormal(const std::vector<cv::Point>& contour, cv::Point p);
};

#endif // INPAINTER_H