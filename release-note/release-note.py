import sys
import re

def getTicket(line):
    m = re.search('(CORE|PROD)-[0-9]{4}', line, re.IGNORECASE)
    if m:
        return m.group(0)

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

def hasForbiddenWords(line):
    words = [
        'revert',
        'bugfix',
        'hotfix'
    ]

    for word in words:
        if word in line.lower():
            return True

def createGhLinks(line):
    commitHash = getCommitHash(line)
    line = line.replace(commitHash, '')

    return '{subject} {hash}'.format(subject = line.strip(), hash = commitHash)

def generateTicket(line):
    subject = createGhLinks(line)
    ticket = getTicket(line)
    # Clean unecessary brackets
    subject = subject.replace('[{ticket}]'.format(ticket = ticket), ticket)
    subject = subject.replace(
        '{ticket}'.format(ticket = ticket),
        '[{ticket}](https://sisu-agile.atlassian.net/browse/{ticket})'.format(ticket = ticket)
    )

    return subject

tickets = [];
others = [];

print '# Tickets'

for line in sys.stdin:
    if hasForbiddenWords(line):
        continue

    if getTicket(line) is not None:
        tickets.append(generateTicket(line))
    elif getPrNumber(line) is not None:
        others.append(createGhLinks(line))

for ticket in tickets:
    print '- ' + ticket

print '\n# Others'

for other in others:
    print '- ' + other
