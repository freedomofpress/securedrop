import sys
import json
import urllib2

def main():
    fpath = sys.argv[1]
    with open(fpath) as fobj:
        data = json.load(fobj)

    url = data['url']

    submission_req = urllib2.Request(url)
    submission_req.add_header(
        'Cookie',
        data['cookies'])
    raw_content = urllib2.urlopen(submission_req).read()
    print(raw_content)

if __name__ == '__main__':
    main()
