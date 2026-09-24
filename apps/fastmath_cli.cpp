#include <fastmath/fastmath.hpp>

#include <cmath>
#include <iostream>
#include <string_view>
#include <vector>

int main(int argc, char* argv[]) {
  if (argc == 2 && std::string_view{argv[1]} == "--version") {
    std::cout << "fastmath-cli " << FASTMATH_VERSION << '\n';
    return 0;
  }

  const int sum = fastmath::add(10, 20);
  const double product = fastmath::dot_product(
      std::vector<double>{1.0, 2.0, 3.0},
      std::vector<double>{4.0, 5.0, 6.0});

  if (sum != 30 || std::abs(product - 32.0) >= 1e-12) {
    std::cerr << "fastmath self-test failed\n";
    return 1;
  }

  std::cout << "fastmath self-test passed: add=30 dot_product=32\n";
  return 0;
}
