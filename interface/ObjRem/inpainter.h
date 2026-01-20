#pragma once
#include <string>

#include <opencv2/core.hpp>       
#include <opencv2/imgcodecs.hpp>  
#include <opencv2/imgproc.hpp>    
#include <opencv2/photo.hpp>      

struct RectROI {
    int x, y, width, height;
};

class PatchRemover {
public:
    PatchRemover();
    
    void setImage(const cv::Mat& image);

    void setSelection(int x, int y, int width, int height);
    void process();
    bool save(const std::string& outputPath);
    
    // Optional: Return result back to Python as Mat
    cv::Mat getResult() const;

private:
    cv::Mat srcImage;
    cv::Mat mask;
    cv::Mat result;
    RectROI selection;
};