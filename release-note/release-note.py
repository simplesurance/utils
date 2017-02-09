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
        if o == "-v":
            verbose = True
        elif o in ("-h", "--help"):
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

        if len(getTicket(line)) != 0:
            tickets.append(generateTicket(line))
        elif getPrNumber(line) is not None:
            others.append(createGhLinks(line))

    for ticket in tickets:
        print '- ' + ticket

    print '\n# Others'

    for other in others:
        print '- ' + other


def getTicket(line):
    m = re.findall('([A-Z]+-[0-9]+)', line, re.IGNORECASE)

    return m

def getCommitHash(line):
    return line [:7]

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

def createGhLinks(line):
    commitHash = getCommitHash(line)
    line = line.replace(commitHash, '')

    return '{subject} {hash}'.format(subject = line.strip(), hash = commitHash)

def generateTicket(line):
    subject = createGhLinks(line)
    tickets = getTicket(line)

    # Clean unecessary brackets
    for ticket in tickets:
        subject = subject.replace('[{ticket}]'.format(ticket = ticket), ticket)
        subject = subject.replace(
            '{ticket}'.format(ticket = ticket),
            '[{ticket}](https://sisu-agile.atlassian.net/browse/{ticket})'.format(ticket = ticket)
        )

    return subject

def usage():
    print '\n'
    print 'Usage: git log --oneline | release-note.py \n'
    print 'Generates release notes from the git commit log. \n'
    print '  --help, -h  \t Display this help. \n'
    print 'Exclude lines lines by filtering keywords:'
    print formatKeyword('hotfix')
    print formatKeyword('bugfix')
    print formatKeyword('revert')
    print '\n'

def formatKeyword(word):
    return '  --no-{keyword}    {keyword}'.format(keyword = word)

if __name__ == "__main__":
    main()
