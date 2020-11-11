#!/usr/bin/env python2
# coding=utf8

from __future__ import print_function
import argparse
import time
import urllib2
import json
import re
import sys

BASE_URL = "https://api.github.com"
RECORDS_PER_REQUEST = 100
OUTPUT_FILE = "stale-branches.txt"

link_url_regex = re.compile(r"(?<=\<).+(?=\>)")
IGNORED_BRANCHES = ["master", "develop"]


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def auth_value(user, passwd):
    auth_str = "%s:%s" % (user, passwd)

    return "Basic " + auth_str.encode("base64").rstrip("\n")


def extract_links(l):
    next_link = None
    last_link = None
    spl = l.split(",")

    for s in spl:
        if 'rel="next"' in s:
            m = link_url_regex.search(s)
            next_link = m.group()

        if 'rel="last"' in s:
            m = link_url_regex.search(s)
            last_link = m.group()

    return (next_link, last_link)


def http_get_retry(req):
    MAX_TRIES = 10
    RETRY_SLEEP_TIMEOUT_SEC = 3

    for i in range(MAX_TRIES):
        try:
            return urllib2.urlopen(req)
        except urllib2.URLError as e:
            print("github request failed (try %s/%s): %s" % (
                  i+1, MAX_TRIES, e))

            if i < MAX_TRIES - 1:
                print("retrying in %s seconds" % (RETRY_SLEEP_TIMEOUT_SEC))
                time.sleep(RETRY_SLEEP_TIMEOUT_SEC)
            else:
                raise(e)

def http_get(url, base64auth):
    all_data = []
    hdrs = {'Content-Type': 'application/json',
            'Authorization': base64auth,
            'Accept': 'application/vnd.github.v3+json',
           }

    while True:
        eprint("HTTP-GET %s" % url)

        req = urllib2.Request(url, headers=hdrs)
        resp = http_get_retry(req)

        data = json.loads(resp.read())
        all_data += data

        link_str = resp.info().get("Link")
        if link_str is None:
            return data

        url, last_url = extract_links(link_str)
        if url == last_url:
            return all_data

    return all_data


def closed_prs(repo, base64auth):
    url = (BASE_URL + "/repos/%s/pulls?state=closed&per_page=%s" %
           (repo, RECORDS_PER_REQUEST))
    return http_get(url, base64auth)


def branches(repo, base64auth):
    res = {}
    url = (BASE_URL + "/repos/%s/branches?per_page=%s" %
           (repo, RECORDS_PER_REQUEST))
    branches_json = http_get(url, base64auth)

    for br in branches_json:
        res[br["name"]] = True

    return res


def open_prs(repo, base64auth):
    url = (BASE_URL + "/repos/%s/pulls?state=open&per_page=%s" %
           (repo, RECORDS_PER_REQUEST))
    return http_get(url, base64auth)


def merged_pr_branches(user, token, repo):
    del_branches = {}
    base64auth = auth_value(user, token)

    existing_branches = branches(repo, base64auth)
    eprint("Found %s branches" % len(existing_branches))

    cprs = closed_prs(repo, base64auth)
    eprint("Found %s closed PRs" % len(cprs))
    for pr in cprs:
        branch = pr["head"]["ref"]
        if branch in IGNORED_BRANCHES:
            continue
        if branch in existing_branches:
            del_branches[branch] = True

    # the same branch name can be used for multiple PRs, remove branches from
    # the list that are used in open PRs from the map
    oprs = open_prs(repo, base64auth)
    eprint("Found %s open PRs" % len(oprs))
    for pr in oprs:
        branch = pr["head"]["ref"]
        if branch in del_branches:
            del del_branches[branch]

    eprint("Found the following %s stale branches:" % len(del_branches))
    with open(OUTPUT_FILE, "w") as f:
        for b in del_branches:
            print(b)
            f.write(b+"\n")

    eprint("stale branches were written to %s" % OUTPUT_FILE)


def setup_parser():
    descr = "list undeleted branches of merged PRs"

    epilog = """
Names of branches are written to STDOUT and to the file
%s.
Status messages are printed to STDERR.
""" % OUTPUT_FILE

    p = argparse.ArgumentParser(description=descr, epilog=epilog)

    p.add_argument("-u", "--user", help="github username", type=str,
                   default="sisubot")
    p.add_argument("-a", "--api-token",
                   help="github API access token (https://github.com/settings/tokens)",
                   type=str, required=True)

    p.add_argument("repository",
                   help="github repository: <OWNER>/<REPOSITORY>",
                   type=str, nargs=1)

    args = p.parse_args()

    merged_pr_branches(args.user, args.api_token, args.repository[0])


if __name__ == "__main__":
    setup_parser()
