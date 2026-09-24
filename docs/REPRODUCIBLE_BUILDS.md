# Reproducible build policy

## Guarantee under test

The reproducibility workflow builds the wheel and DEB twice from the same
commit using the same Ubuntu runner, compiler, Python interpreter, and installed
build tools. The two builds use different absolute source and build directories.
Every published package must have an identical SHA-256 digest.

This proves path- and time-independent output in a fixed toolchain. It does not
claim that different compiler, Python, CMake, or dependency versions produce
identical bytes; those differences are covered by compatibility testing rather
than the reproducibility guarantee.

## Normalization

- `SOURCE_DATE_EPOCH` is set to the source commit timestamp.
- `TZ=UTC`, `LC_ALL=C.UTF-8`, and `PYTHONHASHSEED=0` normalize process state.
- Compiler file and debug path prefixes are mapped away from temporary paths.
- Both builds share one installed toolchain but use isolated source and build
  directories.

## Evidence and failure analysis

`reproducibility.json` is the machine-readable result and
`reproducibility.md` is the review summary. Both contain each artifact's two
SHA-256 values. If any artifact differs, the workflow runs `diffoscope` and
uploads text and HTML reports while failing the required check.

Run locally after installing CMake, CPack, a compiler, Python build dependencies,
and optionally diffoscope:

```bash
./scripts/build_reproducible.sh reproducibility-report
```
