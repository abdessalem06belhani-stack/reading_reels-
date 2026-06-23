#!/usr/bin/env bash
# Generate today's content for every account in config/accounts.yaml.
set -e
cd "$(dirname "$0")/.."
python -m app.main accounts
