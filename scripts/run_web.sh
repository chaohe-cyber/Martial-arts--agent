#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
export http_proxy=
export https_proxy=
export all_proxy=

if [[ -x ".venv/bin/python" ]]; then
	.venv/bin/python -m streamlit run src/interface/app.py --server.address 0.0.0.0
else
	streamlit run src/interface/app.py --server.address 0.0.0.0
fi
