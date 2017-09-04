#!/usr/bin/env python3

import fileinput
import json

def log_lvl_to_str(lvl):
    if not isinstance(lvl, int) and not (isinstance(lvl, str) and lvl.isdigit()):
        return "unknown"

    ilvl = int(lvl)

    if ilvl == 0:
        return "crit"
    elif ilvl == 1:
        return "err"
    elif ilvl == 2:
        return "warn"
    elif ilvl == 3:
        return "info"
    elif ilvl == 4:
        return "debug"
    return "unknown"

for line in fileinput.input():
    try:
        js = json.loads(line)
    except json.JSONDecodeError:
        print(line)
        continue

    ts = js.get("time_iso8601", "timestamp-unknown")
    app = js.get("app", "app-unknown")
    lvl = log_lvl_to_str(js.get("lvl", ""))
    msg = js.get("msg", "").strip()

    keys = ("time_iso8601", "app", "lvl", "msg", "ver")
    for k in keys:
        if k in js:
            del js[k]

    rem = (", ".join("{!s}={!r}".format(k, v) for (k, v) in
                     js.items())).strip()

    print("%s %s %s %s %s" % (ts, lvl, app, msg, rem))
