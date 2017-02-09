import sys, re, getopt, pprint

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'h', ['help', 'no-bugfix', 'no-revert', 'no-hotfix'])
    except getopt.GetoptError as err:
        print str(err)
        usage()
        sys.exit(2)

    blacklistedWords = [];

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("--no-bugfix"):
            blacklistedWords.append('bugfix')
        elif o in ("--no-revert"):
            blacklistedWords.append('revert')
        elif o in ("--no-hotfix"):
            blacklistedWords.append('hotfix')
        else:
            assert False, "unhandled option"

    tickets = [];
    others = [];

    print '# Tickets'

    for line in sys.stdin:
        if hasBlacklistedWords(line, blacklistedWords):
            continue

        issueIds = getIssueIds(line)

        if len(issueIds) == 0:
            others.append(line.rstrip())
            continue

        tickets.append(generateIssueUrl(line, issueIds))

    for ticket in tickets:
        print '- ' + ticket

    print '\n# Others'

    for other in others:
        print '- ' + other

def getIssueIds(line):
    m = re.findall('([A-Z]+-[0-9]+)', line, re.IGNORECASE)

    return m

def getPrNumber(line):
    m = re.search('#[0-9]{4}', line)
    if m:
        return m.group(0)

def isJunk(line):
    if getTicket(line) is not None:
        return False
    if getPrNumber(line) is not None:
        return False

    return True

def hasBlacklistedWords(line, words = []):
    for word in words:
        if word in line.lower():
            return True

def generateIssueUrl(line, issueIds):
    for issueId in issueIds:
        line = line.replace('[{issueId}]'.format(issueId = issueId), issueId)
        line = line.replace(
            '{issueId}'.format(issueId = issueId),
            '[{issueId}](https://sisu-agile.atlassian.net/browse/{issueId})'.format(issueId = issueId.upper())
        )

    return line.rstrip()

def usage():
    print '\n'
    print 'Usage: git log master..develop --format=\'%s %h\' --no-merges | release-note.py \n'
    print 'Generates release notes from the git commit log. \n'
    print '  --help, -h     Display this help. \n'
    print 'Exclude lines lines by filtering keywords:'
    print formatKeyword('hotfix')
    print formatKeyword('bugfix')
    print formatKeyword('revert')
    print '\n'

def formatKeyword(word):
    return '  --no-{keyword}    {keyword}'.format(keyword = word)

if __name__ == "__main__":
    main()
