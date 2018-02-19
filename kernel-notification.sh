#!/usr/bin/env bash

# The script reads  kernel messages from journald and sends them via mail to
# $MAILTO if they contain the expression $grep_expr.
# It's intented to run via cron to get mail notifications about intereresting
# kernel events.
# The scripts uses journald cursors the prevent sending out the same message
# multiples times. It requires write permissions in $run_dir and read
# permissions for kernel logs.
# The parameters to the mail program are adapted for the
# mail version "mail (GNU # Mailutils)".

# vi:set tabstop=8 sts=8 shiftwidth=8 expandtab tw=80

set -eu -o pipefail

run_dir="/var/run/kernel_notifications"
cursor_file="$run_dir/last_cursor"
grep_expr="BUG|Call Trace|WARNING|protection fault"

if [[ ! -v MAILTO || -z "$MAILTO"  ]]; then
	echo "\$MAILTO environment variable not set"
	exit 1
fi

mkdir -p "$run_dir"

args="-q -k --show-cursor"
if [ -f "$cursor_file" ]; then
	cursor=$(cat "$cursor_file")
	args="$args --after-cursor=$cursor"
fi

set +e
log="$(journalctl $args)"
rv=$?
set -e

if [ -z "$log" ] || ! echo "$log" | grep -q "\-\- cursor:"; then
	echo "no new kernel messages"
	exit 0
fi

if [ $rv -ne 0 ]; then
	echo "journalctl exited with code $rv"
	exit $rv
fi

cursor="$(echo "$log" | tail -n 1 | sed 's/-- cursor: //g')"

issues="$(echo "$log" | grep -nE "$grep_expr" || true )"

if [ -z "$issues" ]; then
	echo "no important kernel messages"
	echo "$cursor" > "$cursor_file"
	exit 0
fi

mail_tmpfile="$(mktemp "kernlog-$HOSTNAME.XXX.txt")"
trap 'rm -rf "$mail_tmpfile"' EXIT

echo "$log" | perl -pe 'use MIME::QuotedPrint; $_=MIME::QuotedPrint::decode($_);' > "$mail_tmpfile"

fqdn="$(hostname -f)"
echo -e "Found critical kernel log messages on $fqdn.\n"\
	"Kernel logs are attached."\
	| mail --encoding="quoted-printable" --content-type="text/plain" -A "$mail_tmpfile" -s "kernel errors on $fqdn" "$MAILTO"

echo "send kernel log messages to $MAILTO"

echo "$cursor" > "$cursor_file"
