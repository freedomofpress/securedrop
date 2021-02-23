#!/usr/bin/env python3
# To execute on prod:
# python3 disable_v2.py /etc/tor/torrc /etc/tor/torrc
# To execute for testing locally:
# python3 disable_v2.py /etc/tor/torrc /tmp/dumytorrc
import sys


def filter_v2(filename):
    # Read the file
    with open(filename) as f:
        data = f.readlines()
    # We will store the filtered lines to result
    result = []

    i = 0
    while i < len(data):
        line = data[i]
        if line == "HiddenServiceDir /var/lib/tor/services/source\n":
            i += 1
            while data[i].strip() == "":
                i += 1
            line = data[i]
            if line == "HiddenServiceVersion 2\n":
                i += 1
                line = data[i]
                while data[i].strip() == "":
                    i += 1
                line = data[i]
                if line == "HiddenServicePort 80 127.0.0.1:80\n":
                    i += 1
                    continue
        # Now check for journalist
        if line == "HiddenServiceDir /var/lib/tor/services/journalist\n":
            i += 1
            while data[i].strip() == "":
                i += 1
            line = data[i]
            if line == "HiddenServiceVersion 2\n":
                i += 1
                line = data[i]
                while data[i].strip() == "":
                    i += 1
                line = data[i]
                if line == "HiddenServicePort 80 127.0.0.1:8080\n":
                    i += 1
                    line = data[i]
                    while data[i].strip() == "":
                        i += 1
                    line = data[i]
                    if line == "HiddenServiceAuthorizeClient stealth journalist\n":
                        i += 1
                        continue
        # Now the v2 ssh access
        if line == "HiddenServiceDir /var/lib/tor/services/ssh\n":
            i += 1
            while data[i].strip() == "":
                i += 1
            line = data[i]
            if line == "HiddenServiceVersion 2\n":
                i += 1
                line = data[i]
                while data[i].strip() == "":
                    i += 1
                line = data[i]
                if line == "HiddenServicePort 22 127.0.0.1:22\n":
                    i += 1
                    line = data[i]
                    while data[i].strip() == "":
                        i += 1
                    line = data[i]
                    if line == "HiddenServiceAuthorizeClient stealth admin\n":
                        i += 1
                        continue

        result.append(line)
        i += 1

    # Now return the result
    return result


if __name__ == "__main__":
    filename = sys.argv[1]
    outputfilename = sys.argv[2]
    result = filter_v2(filename)
    with open(outputfilename, "w") as fobj:
        for line in result:
            fobj.write(line)
