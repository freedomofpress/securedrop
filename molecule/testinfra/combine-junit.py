#!/usr/bin/env python
#
#  Corey Goldberg, Dec 2012
#  Original source from gist.github.com/cgoldberg/4320815

import os
import sys
import xml.etree.ElementTree as ET


"""Merge multiple JUnit XML files into a single results file.

Output dumps to sdtdout.

example usage:
    $ python merge_junit_results.py results1.xml results2.xml > results.xml
"""


def main():
    args = sys.argv[1:]
    if not args:
        usage()
        sys.exit(2)
    if '-h' in args or '--help' in args:
        usage()
        sys.exit(2)
    merge_results(args[:])


def merge_results(xml_files):
    failures = 0
    tests = 0
    errors = 0
    time = 0.0
    cases = []

    for file_name in xml_files:
        tree = ET.parse(file_name)
        test_suite = tree.getroot()
        failures += int(test_suite.attrib['failures'])
        tests += int(test_suite.attrib['tests'])
        errors += int(test_suite.attrib['errors'])
        time += float(test_suite.attrib['time'])
        cases.append(test_suite.getchildren())

    new_root = ET.Element('testsuite')
    new_root.attrib['failures'] = '%s' % failures
    new_root.attrib['tests'] = '%s' % tests
    new_root.attrib['errors'] = '%s' % errors
    new_root.attrib['time'] = '%s' % time
    for case in cases:
        new_root.extend(case)
    new_tree = ET.ElementTree(new_root)
    ET.dump(new_tree)


def usage():
    this_file = os.path.basename(__file__)
    print 'Usage:  %s results1.xml results2.xml' % this_file


if __name__ == '__main__':
    main()
