#!/usr/bin/env bash
# Runs the end-to-end ML pipeline. Dependencies are installed separately
# from requirements.txt (per assessment instructions, not installed here).
set -euo pipefail

PYTHON="$(command -v python3 || command -v python)"
"$PYTHON" -m src.main --config "${CONFIG_PATH:-config.yaml}" "$@"