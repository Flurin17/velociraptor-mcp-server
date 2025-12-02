FROM debian:bookworm-slim

ARG VELOCIRAPTOR_TAG=v0.75
ARG VELOCIRAPTOR_VERSION=v0.75.1
ARG TARGETARCH
ENV VELOCIRAPTOR_VERSION=${VELOCIRAPTOR_VERSION}

RUN apt-get update \
  && apt-get install -y --no-install-recommends ca-certificates curl \
  && rm -rf /var/lib/apt/lists/* \
  && update-ca-certificates

WORKDIR /opt/velociraptor

RUN set -e; \
  case "${TARGETARCH:-amd64}" in \
    arm64|aarch64) ARCH=arm64 ;; \
    amd64|x86_64) ARCH=amd64 ;; \
    *) echo "Unsupported arch ${TARGETARCH}" && exit 1 ;; \
  esac; \
  echo "Downloading Velociraptor ${VELOCIRAPTOR_VERSION} for ${ARCH} from tag ${VELOCIRAPTOR_TAG}"; \
  curl -L --fail --noproxy '*' -o velociraptor \
    "https://github.com/Velocidex/velociraptor/releases/download/${VELOCIRAPTOR_TAG}/velociraptor-${VELOCIRAPTOR_VERSION}-linux-${ARCH}" \
    && chmod +x velociraptor

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

VOLUME ["/client"]

ENTRYPOINT ["/entrypoint.sh"]
