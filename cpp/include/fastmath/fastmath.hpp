#pragma once

#include <vector>

#if defined(_WIN32)
#  if defined(FASTMATH_BUILDING_LIBRARY)
#    define FASTMATH_API __declspec(dllexport)
#  else
#    define FASTMATH_API __declspec(dllimport)
#  endif
#elif defined(__GNUC__) || defined(__clang__)
#  define FASTMATH_API __attribute__((visibility("default")))
#else
#  define FASTMATH_API
#endif

namespace fastmath {

FASTMATH_API int add(int lhs, int rhs);

FASTMATH_API double dot_product(const std::vector<double>& lhs,
                               const std::vector<double>& rhs);

}  // namespace fastmath
