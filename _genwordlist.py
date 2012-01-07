"""
Generates `wordlist` from scowl-7.1 (http://wordlist.sourceforge.net/).
"""
import web
import string

def just7(x):
    return all(c in string.printable for c in x)

words = set()
for i in [35, 20, 10]:
    words.update(web.rstrips(x.strip(), "'s") for x in file('english-words.%s' % i) if just7(x))

fh = file('wordlist', 'w')
for word in words: fh.write('%s\n' % word)
