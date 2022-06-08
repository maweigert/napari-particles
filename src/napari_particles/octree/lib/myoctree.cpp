#include <pybind11/pybind11.h>
namespace py = pybind11;

#include "Vec3.h"
#include "Octree.h"


// int add(int i, int j) {
//     return i + j;
// }

PYBIND11_MODULE(paroctree, m) {
    m.doc() = "pybind11 example plugin"; // optional module docstring

    // m.def("add", &add, "A function that adds two numbers");
    py::class_<Vec3>(m, "Vec3")
        .def(py::init<const float, const float, const float>());

    py::class_<Octree>(m, "Octree")
        .def(py::init<const Vec3&, const Vec3&>());
}


