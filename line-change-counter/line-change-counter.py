import sys
import re

def findPattern(pattern, string):
    m = re.search(pattern, string, re.IGNORECASE)

    if m:
        return m.group(0)

def findInLine(line, pattern):
    if line is None:
        return 0;

    filesChanged = findPattern(pattern, line)

    if filesChanged is None:
        return 0;

    n = findPattern('\d+', filesChanged)

    return n

filesChanged = 0
insertions = 0
deletions = 0

for line in sys.stdin:
    filesChanged += int(findInLine(line, '\d+ file'))
    insertions += int(findInLine(line, '\d+ insertion'))
    deletions += int(findInLine(line, '\d+ deletion'))

print '{files} files changed, {insertions} insertions(+), {deletions} deletions(-)'.format(files=filesChanged, insertions=insertions, deletions=deletions)
