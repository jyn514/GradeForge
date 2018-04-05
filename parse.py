#!/usr/bin/env python2
from __future__ import print_function, generators
from argparse import ArgumentParser
from sys import argv

# note: only works with python2 (sorry)
from lxml.etree import iterparse
import cloudpickle

stdout = 'output.data'
document = 'USC_all_courses.html'

def fast_iter(context):
    forms = (elem.findall('input') for event, elem in context
             if event == 'end' and elem.tag == 'form' and elem.text != 'Search')
    return [[{item[0]: item[1] for item in field.items()
              if item[1] != 'hidden' and item[0] != 'style'}
             for field in form if field.items()[1][1] != 'dummy']
            for form in forms]


def load(stdin=stdout):
    with open(stdin, 'rb') as i:
        return cloudpickle.load(i)


def main(args):
    if args.load:
        print(load(args.output))
    else:
        with open(document) as stdin:
            result = fast_iter(iterparse(stdin, html=True))
        with open(args.output, 'wb') as out:
            cloudpickle.dump(result, out)
        if args.verbose:
            print(result)


if __name__ == '__main__':
    parser = ArgumentParser()
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--save', '-s', '--save-binary', action='store_true',
                        help='Save result of main() in binary form',
                        default=True)
    action.add_argument('--load', '--print', '-l', action='store_true',
                        help='Show result on stdout')
    parser.add_argument('--verbose', '-v', help='Show result',
                        action='store_true')
    parser.add_argument('--output', '-o', help='File to store binary',
                        default=stdout)
    main(parser.parse_args())
