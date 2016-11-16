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
        'bugfix'
    ]

    for word in words:
        if word in line.lower():
            return True

def createGhLinks(line):
    commitHash = getCommitHash(line)
    line = line.replace(commitHash, '')

    prNumber = getPrNumber(line)
    prNumber = prNumber.replace('#', '')

    line = line.replace(
        ('(#{})').format(prNumber),
        ('[`{commit}`](https://github.com/simplesurance/sisu/commit/{commit}) ([#{pr}](https://github.com/simplesurance/sisu/pull/{pr}))').format(commit=commitHash, pr=prNumber)
    )

    return line.strip()

def generateTicket(line):
    line = createGhLinks(line)
    ticket = getTicket(line)
    line = line.replace(('[{}]').format(ticket), ticket.upper());
    line = line.replace(ticket, ('[{ticket}](https://sisu-agile.atlassian.net/browse/{ticket})').format(ticket=ticket.upper()))

    return line.strip();

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
