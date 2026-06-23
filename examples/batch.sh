#!/usr/bin/env bash
# Make 5 A2 videos.
set -e
cd "$(dirname "$0")/.."
python -m app.main batch --count 5 --level A2
