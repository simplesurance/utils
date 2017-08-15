#!/usr/bin/env bash

one_file=0
unique=0

set -eu

print_usage() {
    echo "$0 <RESULT-DIR>"
    echo " -1, --one-file         aggregate all logs in all.log file"
}

while [ $# -ge 1 ]; do
        case "$1" in
        -1 | --one-file)
                one_file=1
                shift
                ;;
        -*)
                print_usage
                exit 1
                ;;
        *)
                break
                ;;
        esac
done

if [ $# -ne 1 ]; then
        print_usage
        exit 1
fi


out="$1"

mkdir -p "$out"

file="$out/all.log"

services="$(nomad status | awk '{ print $1 }' | grep -v ID)"
for srv in $services; do
    if [ $one_file -eq 0 ]; then
        file="$out/$srv.log"
    fi

    echo "aggregating $srv logs to $file"

    alloc_ids=$(nomad status $srv| grep "Allocations" -A 1000000| awk '{ print $1 }'|grep -vE 'ID|Allocations')
    for id in $alloc_ids; do
        nomad logs "$id" | ./go-json-logs-to-readable.py > "$out/$srv.log"
    done
done
