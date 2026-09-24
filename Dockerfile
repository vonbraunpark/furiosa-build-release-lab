FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
       build-essential \
       ca-certificates \
       cmake \
    && apt-get clean

WORKDIR /src
COPY . .

RUN cmake -S . -B /build \
      -DFASTMATH_BUILD_PYTHON=OFF \
      -DFASTMATH_BUILD_TESTS=ON \
      -DFASTMATH_BUILD_NATIVE_PACKAGE=OFF \
      -DFASTMATH_BUILD_CLI=ON \
      -DCMAKE_BUILD_TYPE=Release \
    && cmake --build /build --parallel \
    && ctest --test-dir /build --output-on-failure

FROM ubuntu:24.04 AS runtime

ARG DEBIAN_FRONTEND=noninteractive
ARG REPOSITORY_URL="https://github.com/local/furiosa-build-release-lab"
ARG VCS_REF="unknown"

LABEL org.opencontainers.image.title="furiosa-build-release-lab" \
      org.opencontainers.image.description="Versioned C++ build and release lab runtime" \
      org.opencontainers.image.source="${REPOSITORY_URL}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.licenses="MIT"

RUN apt-get update \
    && apt-get install --yes --no-install-recommends libstdc++6 \
    && apt-get clean

COPY --from=builder /build/fastmath_cli /usr/local/bin/fastmath-cli

USER 65532:65532
ENTRYPOINT ["/usr/local/bin/fastmath-cli"]
