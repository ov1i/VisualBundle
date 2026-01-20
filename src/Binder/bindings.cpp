#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include "inpainter.h"

namespace py = pybind11;

// --- 1. Type Caster: NumPy <-> cv::Mat ---
// This allows Pybind11 to automatically convert numpy arrays to cv::Mat
// We implement a simplified version for 3-channel (color) images.
namespace pybind11 { namespace detail {

template<> struct type_caster<cv::Mat> {
public:
    PYBIND11_TYPE_CASTER(cv::Mat, _("numpy.ndarray"));

    // Conversion Python -> C++
    bool load(handle src, bool) {
        // Ensure it's a numpy array
        if (!isinstance<array>(src)) return false;
        
        array b = reinterpret_borrow<array>(src);
        buffer_info info = b.request();

        // Check dimensions (we expect HxWx3 for color images)
        if (info.ndim != 3) {
             throw std::runtime_error("Expected a 3D array (Height x Width x Channels)");
             return false;
        }

        int rows = info.shape[0];
        int cols = info.shape[1];
        int type = CV_8UC3; // Assuming standard uint8 BGR/RGB image

        // Create a cv::Mat view of the numpy memory (no copy yet)
        value = cv::Mat(rows, cols, type, info.ptr, info.strides[0]);
        return true;
    }

    // Conversion C++ -> Python
    static handle cast(const cv::Mat& m, return_value_policy, handle) {
        if (m.empty()) return none().release();

        // We only support standard 3-channel byte images here for simplicity
        if (m.type() != CV_8UC3) throw std::runtime_error("Only CV_8UC3 (color) images supported for return");

        // Define shape and strides
        std::vector<ssize_t> shape = { m.rows, m.cols, 3 };
        std::vector<ssize_t> strides = { 
            (ssize_t)m.step[0], 
            (ssize_t)m.step[1], 
            (ssize_t)m.elemSize1() 
        };

        return array(buffer_info(
            m.data,              // Pointer to data
            sizeof(unsigned char), // Size of one element
            format_descriptor<unsigned char>::format(), // Format
            3,                   // Dimensions
            shape,               // Shape
            strides              // Strides
        )).release();
    }
};
}} // namespace pybind11::detail


// --- 2. The Module Definition ---

PYBIND11_MODULE(ObjectRemover_core, m) {
    m.doc() = "C++ Object Removal Backend with Direct NumPy Support";

    py::class_<PatchRemover>(m, "PatchRemover")
        .def(py::init<>())
        // Load from NumPy
        .def("set_image", &PatchRemover::setImage, "Load image from NumPy array")
        
        // Set ROI
        .def("set_selection", &PatchRemover::setSelection)
        
        // Process
        .def("process", &PatchRemover::process)
        
        // Save to disk
        .def("save", &PatchRemover::save)
        
        // NEW: Get result back as NumPy
        .def("get_result", &PatchRemover::getResult, "Get processed image as NumPy array");
}