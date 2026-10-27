#!/bin/sh
# PandasWise legal-hold gate: refuse to push if held (HOLD_REVIEW) content is in the built output.
cd "$(git rev-parse --show-toplevel)" || exit 1
python3 legal_gate.py --check || { echo "pre-push: legal hold check failed, push refused"; exit 1; }
