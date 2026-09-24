#include "fastmath/fastmath.hpp"

#include <cassert>
#include <cmath>
#include <stdexcept>
#include <vector>

int main() {
  assert(fastmath::add(10, 20) == 30);

  const std::vector<double> lhs{1.0, 2.0, 3.0};
  const std::vector<double> rhs{4.0, 5.0, 6.0};
  assert(std::abs(fastmath::dot_product(lhs, rhs) - 32.0) < 1e-12);

  bool rejected_mismatched_lengths = false;
  try {
    static_cast<void>(fastmath::dot_product({1.0}, {1.0, 2.0}));
  } catch (const std::invalid_argument&) {
    rejected_mismatched_lengths = true;
  }
  assert(rejected_mismatched_lengths);
}

