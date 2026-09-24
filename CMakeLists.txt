cmake_minimum_required(VERSION 3.20)

project(fastmath VERSION 0.1.0 LANGUAGES CXX)

include(GNUInstallDirs)
include(CMakePackageConfigHelpers)

option(FASTMATH_BUILD_PYTHON "Build the Python extension module" ON)
option(FASTMATH_BUILD_TESTS "Build the C++ tests" ON)
option(FASTMATH_BUILD_NATIVE_PACKAGE "Build and package the shared C++ library" OFF)
option(FASTMATH_BUILD_CLI "Build the fastmath command-line smoke application" OFF)
option(FASTMATH_REPRODUCIBLE "Remove build-path variance from compiled artifacts" OFF)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(FASTMATH_REPRODUCIBLE AND CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  add_compile_options(
    "-ffile-prefix-map=${CMAKE_SOURCE_DIR}=."
    "-ffile-prefix-map=${CMAKE_BINARY_DIR}=."
    "-fdebug-prefix-map=${CMAKE_SOURCE_DIR}=."
    "-fdebug-prefix-map=${CMAKE_BINARY_DIR}=."
  )
endif()

add_library(fastmath_core STATIC cpp/src/fastmath.cpp)
set_target_properties(fastmath_core PROPERTIES POSITION_INDEPENDENT_CODE ON)
target_include_directories(
  fastmath_core
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/cpp/include>
    $<INSTALL_INTERFACE:include>
)
target_compile_features(fastmath_core PUBLIC cxx_std_17)

if(FASTMATH_BUILD_CLI)
  add_executable(fastmath_cli apps/fastmath_cli.cpp)
  target_link_libraries(fastmath_cli PRIVATE fastmath_core)
  target_compile_features(fastmath_cli PRIVATE cxx_std_17)
  target_compile_definitions(
    fastmath_cli
    PRIVATE FASTMATH_VERSION="${PROJECT_VERSION}"
  )
endif()

if(FASTMATH_BUILD_NATIVE_PACKAGE)
  # Keep the Python extension self-contained by linking it to the static
  # target, while publishing a versioned shared library in the Ubuntu package.
  add_library(fastmath_shared SHARED cpp/src/fastmath.cpp)
  set_target_properties(
    fastmath_shared
    PROPERTIES
      OUTPUT_NAME fastmath
      VERSION ${PROJECT_VERSION}
      SOVERSION ${PROJECT_VERSION_MAJOR}
      EXPORT_NAME fastmath
      CXX_VISIBILITY_PRESET hidden
      VISIBILITY_INLINES_HIDDEN YES
  )
  target_compile_definitions(fastmath_shared PRIVATE FASTMATH_BUILDING_LIBRARY)
  target_include_directories(
    fastmath_shared
    PUBLIC
      $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/cpp/include>
      $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
  )
  target_compile_features(fastmath_shared PUBLIC cxx_std_17)
endif()

if(FASTMATH_BUILD_PYTHON)
  find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)
  find_package(pybind11 CONFIG REQUIRED)

  pybind11_add_module(_fastmath MODULE python/bindings.cpp)
  target_link_libraries(_fastmath PRIVATE fastmath_core)
  install(TARGETS _fastmath LIBRARY DESTINATION fastmath)
endif()

if(FASTMATH_BUILD_NATIVE_PACKAGE)
  install(
    TARGETS fastmath_shared
    EXPORT fastmathTargets
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
  )
  install(
    DIRECTORY cpp/include/
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
    FILES_MATCHING PATTERN "*.hpp"
  )
  install(
    EXPORT fastmathTargets
    FILE fastmathTargets.cmake
    NAMESPACE fastmath::
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/fastmath
  )

  configure_package_config_file(
    cmake/fastmathConfig.cmake.in
    ${CMAKE_CURRENT_BINARY_DIR}/fastmathConfig.cmake
    INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/fastmath
  )
  write_basic_package_version_file(
    ${CMAKE_CURRENT_BINARY_DIR}/fastmathConfigVersion.cmake
    VERSION ${PROJECT_VERSION}
    COMPATIBILITY SameMajorVersion
  )
  install(
    FILES
      ${CMAKE_CURRENT_BINARY_DIR}/fastmathConfig.cmake
      ${CMAKE_CURRENT_BINARY_DIR}/fastmathConfigVersion.cmake
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/fastmath
  )

  set(CPACK_GENERATOR "DEB")
  set(CPACK_PACKAGE_NAME "fastmath")
  set(CPACK_PACKAGE_VENDOR "furiosa-build-release-lab")
  set(CPACK_PACKAGE_CONTACT "YoungSeong Park")
  set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "C++17 sample library for build and release infrastructure practice")
  set(CPACK_PACKAGE_VERSION ${PROJECT_VERSION})
  set(CPACK_PACKAGING_INSTALL_PREFIX "/usr")
  set(CPACK_DEBIAN_PACKAGE_SECTION "devel")
  set(CPACK_DEBIAN_PACKAGE_PRIORITY "optional")
  set(CPACK_DEBIAN_PACKAGE_SHLIBDEPS ON)
  set(CPACK_DEBIAN_FILE_NAME DEB-DEFAULT)
  include(CPack)
endif()

if(FASTMATH_BUILD_TESTS)
  include(CTest)
  if(BUILD_TESTING)
    add_executable(fastmath_cpp_tests tests/cpp/test_fastmath.cpp)
    target_link_libraries(fastmath_cpp_tests PRIVATE fastmath_core)
    add_test(NAME fastmath_cpp_tests COMMAND fastmath_cpp_tests)
  endif()
endif()
