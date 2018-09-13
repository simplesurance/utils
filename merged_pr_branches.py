#!/usr/bin/env python2
# coding=utf8

from __future__ import print_function
import argparse
import urllib2
import json
import re
import sys

BASE_URL = "https://api.github.com"
RECORDS_PER_REQUEST = 100

link_url_regex = re.compile(r"(?<=\<).+(?=\>)")


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


def http_get(url, base64auth):
    all_data = []
    hdrs = {'Content-Type': 'application/json',
            'Authorization': base64auth}

    while True:
        eprint("HTTP-GET %s" % url)

        req = urllib2.Request(url, headers=hdrs)
        resp = urllib2.urlopen(req)
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


def branch_exist(repo, branch, base64auth):
    url = (BASE_URL + "/repos/%s/branches/%s" %
           (repo, branch))
    try:
        http_get(url, base64auth)
        return True
    except urllib2.HTTPError as e:
        if e.code == 404:
            return False
        raise e


def open_prs(repo, base64auth):
    url = (BASE_URL + "/repos/%s/pulls?state=open&per_page=%s" %
           (repo, RECORDS_PER_REQUEST))
    return http_get(url, base64auth)


def merged_pr_branches(user, token, repo):
    branches = {}
    base64auth = auth_value(user, token)

    # see https://developer.github.com/v3/repos/statuses/

    cprs = closed_prs(repo, base64auth)
    eprint("Found %s closed PRs" % len(cprs))
    for pr in cprs:
        branch = pr["head"]["ref"]
        if branch_exist(repo, branch, base64auth):
            branches[branch] = True

    # the same branch name can be used for multiple PRs, remove branches from
    # the list that are used in open PRs from the map
    oprs = open_prs(repo, base64auth)
    eprint("Found %s open PRs" % len(oprs))
    for pr in oprs:
        branch = pr["head"]["ref"]
        if branch in branches:
            del branches[branch]

    eprint("Found %s PRs for deletion" % len(branches))
    for b in branches:
        print(b)


def setup_parser():
    descr = "list undeleted branches of merged PRs"
    epilog = "Status messages are printed to STDERR"
    p = argparse.ArgumentParser(description=descr, epilog=epilog)

    p.add_argument("-u", "--user", help="github username", type=str,
                   default="sisubot")
    p.add_argument("-a", "--auth-token", help="github auth token", type=str,
                   required=True)

    p.add_argument("repository",
                   help="github repository: <OWNER>/<REPOSITORY>",
                   type=str, nargs=1)

    args = p.parse_args()

    merged_pr_branches(args.user, args.auth_token, args.repository[0])


if __name__ == "__main__":
    setup_parser()
