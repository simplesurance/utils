#!/usr/bin/env bash

alloc_id="$1"
script_dir="$(cd "$(dirname "$0")" ; pwd -P)"

cat /var/nomad/alloc/${alloc_id}*/alloc/logs/*.stdout.0 | $script_dir/jsonlogs2txt.py | less -RI
