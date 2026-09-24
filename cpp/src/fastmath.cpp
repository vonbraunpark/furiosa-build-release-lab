#include "fastmath/fastmath.hpp"

#include <numeric>
#include <stdexcept>

namespace fastmath {

int add(const int lhs, const int rhs) { return lhs + rhs; }

double dot_product(const std::vector<double>& lhs,
                   const std::vector<double>& rhs) {
  if (lhs.size() != rhs.size()) {
    throw std::invalid_argument("dot_product inputs must have equal lengths");
  }

  return std::inner_product(lhs.begin(), lhs.end(), rhs.begin(), 0.0);
}

}  // namespace fastmath

