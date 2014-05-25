#!/usr/bin/env python

import sys

def start():
    pass

def test():
    pass

def refresh():
    pass

def main():
    valid_cmds = ["start", "test", "refresh"]
    help_str = "./manage.py {{{0}}}".format(','.join(valid_cmds))

    if len(sys.argv) != 2 or sys.argv[1] not in valid_cmds:
        print help_str
        sys.exit(1)

    cmd = sys.argv[1]
    getattr(sys.modules[__name__], cmd)()

if __name__ == "__main__":
    main()
