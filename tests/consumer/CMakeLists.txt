cmake_minimum_required(VERSION 3.20)

project(fastmath_consumer LANGUAGES CXX)

find_package(fastmath 0.1 CONFIG REQUIRED)

add_executable(fastmath_consumer main.cpp)
target_link_libraries(fastmath_consumer PRIVATE fastmath::fastmath)
target_compile_features(fastmath_consumer PRIVATE cxx_std_17)
