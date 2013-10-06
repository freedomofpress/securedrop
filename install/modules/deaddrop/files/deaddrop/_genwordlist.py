"""
Generates `wordlist` from The English Open Word List http://dreamsteep.com/projects/the-english-open-word-list.html
Usage: Unzip the CSV files from the archive with the command `unzip EOWL-v1.1.2.zip EOWL-v1.1.2/CSV\ Format/*.csv`
"""
import string

def just7(x):
    return all(c in string.printable for c in x)

words = set()

for i in map(chr, range(65, 91)):
    words.update(x.strip() for x in file('EOWL-v1.1.2/CSV Format/%s Words.csv' % i) if just7(x))

fh = file('wordlist', 'w')
for word in words: fh.write('%s\n' % word)
