# Compatibility and ABI policy

## Supported build matrix

| Surface | Environments | Required checks |
| --- | --- | --- |
| Native C++ | Ubuntu 22.04/24.04 × GCC/Clang | Configure, build, unit test, install |
| Installed CMake package | Same native matrix | External consumer configure, link, run |
| Python extension | CPython 3.10-3.13 | Wheel build, clean install, behavior test |
| Release wheel | manylinux_2_28 x86_64 | auditwheel repair and installed test |
| Ubuntu package | Ubuntu 24.04 amd64 | Install, consumer test, removal test |

All matrix entries are required; `fail-fast: false` preserves evidence from the
other environments when one entry fails.

## ABI stability

The shared library exports only the two functions declared with `FASTMATH_API`.
Hidden default visibility prevents implementation details and standard-library
helpers from accidentally becoming public ABI.

Before the first version tag, CI compares exported ELF symbols with
`abi/fastmath-0.1.0.symbols`. After a `v*` tag exists, CI builds that tag and the
current source with debug information, creates Libabigail corpora, and runs
`abidiff`. Removed symbols, changed public signatures, and other incompatible
changes fail the workflow. Additive changes remain visible in the report and
require review before a minor-version release.

Changing or removing an existing public ABI requires a new SONAME major and a
major SemVer release.
