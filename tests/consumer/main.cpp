#include <fastmath/fastmath.hpp>

#include <cmath>
#include <vector>

int main() {
  if (fastmath::add(10, 20) != 30) {
    return 1;
  }

  const std::vector<double> lhs{1.0, 2.0, 3.0};
  const std::vector<double> rhs{4.0, 5.0, 6.0};
  return std::abs(fastmath::dot_product(lhs, rhs) - 32.0) < 1e-12 ? 0 : 2;
}
