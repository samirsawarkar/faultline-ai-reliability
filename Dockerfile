# syntax=docker/dockerfile:1.7
# Multi-architecture manifest digest for python:3.12.4-slim-bookworm.
FROM python:3.12.4-slim-bookworm@sha256:a3e58f9399353be051735f09be0316bfdeab571a5c6a24fd78b92df85bcb2d85

ARG PIP_VERSION=26.0.1

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONHASHSEED=0 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SOURCE_DATE_EPOCH=0

WORKDIR /workspace

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        git=1:2.39.5-0+deb12u3 \
        make=4.3-4.1 \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir "pip==${PIP_VERSION}"

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home --uid 10001 faultline
COPY --chown=faultline:faultline . .
RUN chown faultline:faultline /workspace
USER faultline

# A successful image build is itself a clean-room reproduction gate.
RUN make PY=python reproduce

CMD ["make", "PY=python", "reproduce-fast"]
