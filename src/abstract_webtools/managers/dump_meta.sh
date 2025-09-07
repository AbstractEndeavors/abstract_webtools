#!/usr/bin/env bash
# dump_meta.sh
set -euo pipefail
if [ $# -lt 1 ]; then
  echo "Usage: $0 <url>" >&2
  exit 1
fi
python3 meta_dump.py "$1"
