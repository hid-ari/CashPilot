#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python -m pip install --upgrade pip
python -m pip install buildozer cython
buildozer android debug
