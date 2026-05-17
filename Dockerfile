FROM ghcr.io/astral-sh/uv:0.9.17-trixie-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
  UV_LINK_MODE=copy \
  UV_PYTHON_PREFERENCE=only-managed \
  UV_NO_DEV=1 \
  UV_PYTHON_INSTALL_DIR=/python

RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* ;

RUN uv python install 3.14.2 ;

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
  --mount=type=bind,source=uv.lock,target=uv.lock \
  --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
  uv sync --frozen --no-install-project ;

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen ;

################################################################################

FROM debian:trixie-slim AS development

ENV PYTHONUNBUFFERED=1


RUN groupadd --gid 1000 python \
  && useradd --uid 1000 --gid python --shell /bin/bash --create-home python ;


RUN apt-get update \
  && apt-get install -y --no-install-recommends ca-certificates \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* ;


COPY --from=builder --chown=python:python /python /python
COPY --from=builder --chown=python:python /app /app

ENV PATH="/app/.venv/bin:${PATH}"

USER python
ENTRYPOINT []
WORKDIR /app

ENV SSL_CERT_FILE=/app/.venv/lib/python3.14/site-packages/certifi/cacert.pem
ENV REQUESTS_CA_BUNDLE=/app/.venv/lib/python3.14/site-packages/certifi/cacert.pem
ENV HTTpx_CA_BUNDLE=/app/.venv/lib/python3.14/site-packages/certifi/cacert.pem


CMD ["uvicorn", "--host", "0.0.0.0", "--port", "8001", "main:app", "--reload"]
