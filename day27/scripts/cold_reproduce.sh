#!/bin/sh
set -eu

IMAGE="faultline:0.27.0-rc1"
BUILD_LOG="$(mktemp)"
trap 'rm -f "$BUILD_LOG"' EXIT

docker version >/dev/null
echo "docker preflight: PASS"

if ! docker build --pull --quiet --tag "$IMAGE" . >"$BUILD_LOG" 2>&1; then
  cat "$BUILD_LOG"
  exit 1
fi
echo "clean image build: PASS"

docker run --rm --entrypoint python "$IMAGE" \
  day27/scripts/reproduce_headlines.py
