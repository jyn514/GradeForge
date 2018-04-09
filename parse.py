#!/usr/bin/env python
from __future__ import print_function, generators
from argparse import ArgumentParser
from sys import argv

from lxml.etree import iterparse
import cloudpickle

stdout = 'output.data'
document = 'USC_all_courses.html'

def parse(context):
    classes = []
    departments = {}
    code = True
    for event, elem in context:
        if event == 'end' and elem.text is not None and elem.text != '\n':
            if elem.tag == 'th':
                header = elem.text.split(' - ')
                departments[header[0]] = header[1]
            elif elem.tag == 'td':
                if code:
                    current = {'code': elem.text, 'abbr': header[0]}
                else:
                    current.update({'title': elem.text})
                    classes.append(current)
                code = not code
    return filter(None, classes), departments


def load(stdin=stdout):
    with open(stdin, 'rb') as i:
        return cloudpickle.load(i)


def main(args):
    if args.load:
        print(load(args.output))
    elif args.save or args.verbose:
        with open(args.input, 'rb') as stdin:
            classes, departments = parse(iterparse(stdin, html=True))
        if args.save:
            with open(args.output, 'wb') as out:
                cloudpickle.dump((classes, departments), out)
        if args.verbose:
            print(classes, departments)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('input', help='HTML file', nargs='?', default=document)
    parser.add_argument('output', help='File to store binary', default=stdout,
                        nargs='?')
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--save', '-s', '--save-binary', action='store_true', 
                        default=True,
                        help='Save result of main() in binary form')
    action.add_argument('--load', '--print', '-l', action='store_true',
                        help='Show result on stdout')
    parser.add_argument('--verbose', '-v', help='Show result',
                        action='store_true')
    main(parser.parse_args())
