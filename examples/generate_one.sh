#!/usr/bin/env bash
# Make a single B1 video (no keys required).
set -e
cd "$(dirname "$0")/.."
python -m app.main one --level B1
