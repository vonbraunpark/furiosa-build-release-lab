#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "fastmath/fastmath.hpp"

namespace py = pybind11;

PYBIND11_MODULE(_fastmath, module) {
  module.doc() = "C++ fastmath functions exposed through pybind11";
  module.def("add", &fastmath::add, py::arg("lhs"), py::arg("rhs"),
             "Add two integers.");
  module.def("dot_product", &fastmath::dot_product, py::arg("lhs"),
             py::arg("rhs"), "Calculate the dot product of two vectors.");
}

