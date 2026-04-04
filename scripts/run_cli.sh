#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
export http_proxy=
export https_proxy=
export all_proxy=

python src/main.py
