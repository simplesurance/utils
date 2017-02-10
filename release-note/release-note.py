import sys, re, getopt

def main():
    try:
        opts, _ = getopt.getopt(sys.argv[1:], 'h', ['help', 'no-bugfix', 'no-revert', 'no-hotfix', 'jira-url='])
    except getopt.GetoptError as err:
        print str(err)
        usage()
        sys.exit(2)

    blacklistedWords = [];
    jiraUrl = '';

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif "--no-bugfix" == o:
            blacklistedWords.append('bugfix')
        elif "--no-revert" == o:
            blacklistedWords.append('revert')
        elif "--no-hotfix" == o:
            blacklistedWords.append('hotfix')
        elif "--jira-url" == o:
            jiraUrl = a;
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

        tickets.append(generateIssueUrl(line, issueIds, jiraUrl))

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

def generateIssueUrl(line, issueIds, jiraUrl):
    line = line.rstrip()

    if '' == jiraUrl:
        return line

    for issueId in issueIds:
        line = line.replace('[{issueId}]'.format(issueId = issueId), issueId)
        line = line.replace(
            '{issueId}'.format(issueId = issueId),
            '[{issueId}]({jiraUrl}/browse/{issueId})'.format(issueId = issueId.upper(), jiraUrl = jiraUrl)
        )

    return line

def usage():
    print '\n'
    print 'Usage: git log master..develop --format=\'%s %h\' --no-merges | release-note.py \n'
    print 'Generates release notes from the git commit log. \n'
    print '  --help, -h     Display this help.'
    print '  --jira-url     Prefix, used to create links from JIRA issue IDs. \n'
    print 'Exclude lines lines by filtering keywords:'
    print formatKeyword('hotfix')
    print formatKeyword('bugfix')
    print formatKeyword('revert')
    print '\n'

def formatKeyword(word):
    return '  --no-{keyword}    {keyword}'.format(keyword = word)

if __name__ == "__main__":
    main()
