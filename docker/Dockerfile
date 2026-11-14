# syntax=docker/dockerfile:1.7
# Two images from one file (see docker-compose.yml):
#   --target client   : Python 3.12 + FLE 0.4.3 + sprites, runs setup/fle_repl.py on :8765
#   --target factorio : factoriotools/factorio:2.0.73 + FLE scenarios/config baked in
#
# Behind a TLS-intercepting proxy? Put its CA (PEM) in an optional build secret "extra_ca"
# (docker-compose.yml wires it to $FLE_EXTRA_CA, default: an empty file). Without it the
# builds use the normal public CA store.

ARG PYTHON_IMAGE=python:3.12-slim
ARG FACTORIO_IMAGE=factoriotools/factorio:2.0.73

# ---------------------------------------------------------------- python + FLE
FROM ${PYTHON_IMAGE} AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
# Optional extra CA (build secret "extra_ca"): appended to certifi + system bundle for this RUN.
RUN --mount=type=secret,id=extra_ca,required=false \
    if [ -s /run/secrets/extra_ca ]; then export PIP_CERT=/run/secrets/extra_ca; fi; \
    pip install "factorio-learning-environment==0.4.3" "a2a-sdk<1"
WORKDIR /app

# ---------------------------------------------------------------- sprites (build-time only)
# `fle sprites` downloads ~370 MB from HuggingFace (Noddybear/fle_images) into .fle/spritemaps;
# fix_sprites.py makes ENTITY sprites usable without the `basisu` tool (gotcha G7).
# Only the generated .fle/sprites (~25 MB) is copied into the final image.
FROM base AS sprites
COPY setup/fix_sprites.py /app/setup/fix_sprites.py
RUN --mount=type=secret,id=extra_ca,required=false \
    if [ -s /run/secrets/extra_ca ]; then \
      B=/tmp/ca.pem; cat "$(python -m certifi)" /run/secrets/extra_ca > $B; \
      export REQUESTS_CA_BUNDLE=$B SSL_CERT_FILE=$B CURL_CA_BUNDLE=$B; fi; \
    fle sprites && python -W ignore setup/fix_sprites.py | tail -2 \
    && test -f .fle/sprites/burner-mining-drill_north.png \
    && echo "sprites: $(ls .fle/sprites | wc -l)" && rm -rf .fle/spritemaps /app/.env

# ---------------------------------------------------------------- FLE server assets
FROM base AS fle-assets
COPY docker/prepare_server_assets.py /tmp/prepare_server_assets.py
RUN python /tmp/prepare_server_assets.py /fle-server

# ---------------------------------------------------------------- client (REPL) image
FROM base AS client
COPY --from=sprites /app/.fle/sprites /app/.fle/sprites
COPY setup/ /app/setup/
# HOME/.fle/sprites is FLE's fallback sprite lookup; make it work for any uid.
RUN mkdir -p /data/saves /data/renders /workspace && chmod 1777 /data /data/saves /data/renders /workspace \
    && ln -s /app/.fle /tmp/.fle
ENV HOME=/tmp \
    FLE_SPRITES_DIR=/app/.fle/sprites \
    FLE_LISTEN_HOST=0.0.0.0 \
    FLE_REPL_PORT=8765 \
    FLE_SERVER_HOST=factorio \
    FLE_RCON_PORT=27015 \
    FLE_SAVES_DIR=/data/saves \
    FLE_FALLBACK_DIR=/data \
    FLE_WORKSPACE=/workspace \
    FLE_CONNECT_RETRIES=40
EXPOSE 8765
HEALTHCHECK --interval=10s --timeout=5s --start-period=120s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if b'\"ok\": true' in urllib.request.urlopen('http://127.0.0.1:8765/status', timeout=4).read() else 1)"
ENTRYPOINT ["python", "-W", "ignore", "/app/setup/fle_repl.py"]

# ---------------------------------------------------------------- factorio server image
FROM ${FACTORIO_IMAGE} AS factorio
USER root
# Base game only (as `fle cluster start` does); FLE scenarios/config/mod-list baked in.
# /opt/factorio/scenarios is a symlink into the /factorio VOLUME in the stock image; replace
# it with a real dir so the scenarios don't depend on volume contents.
RUN rm -rf /opt/factorio/data/elevated-rails /opt/factorio/data/quality /opt/factorio/data/space-age \
    /opt/factorio/scenarios
COPY --from=fle-assets --chown=factorio:factorio /fle-server/scenarios /opt/factorio/scenarios
COPY --from=fle-assets --chown=factorio:factorio /fle-server/config/ /opt/factorio/config/
COPY --from=fle-assets --chown=factorio:factorio /fle-server/mods /opt/factorio/mods
COPY --chmod=0755 docker/factorio-start.sh /usr/local/bin/fle-factorio-start
HEALTHCHECK --interval=5s --timeout=3s --start-period=60s --retries=5 \
    CMD bash -c 'exec 3<>/dev/tcp/127.0.0.1/27015' || exit 1
ENTRYPOINT ["/usr/local/bin/fle-factorio-start"]
