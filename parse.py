#!/usr/bin/env python2
from __future__ import print_function, generators
# note: only works with python2 (sorry)
from lxml import etree
import cloudpickle

stdout = 'output.data'
document = 'USC_all_courses.html'

def fast_iter(context):
    forms = (elem.findall('input') for event, elem in context
             if event == 'end' and elem.tag == 'form' and elem.text != 'Search')
    return [[i.items() for i in inputs]
            for inputs in forms]


def load():
    return cloudpickle.load(open(stdout, 'rb'))


def save(obj):
    with open(stdout, 'wb') as out:
        cloudpickle.dump(obj, out)


def main():
    with open(document) as stdin:
        return fast_iter(etree.iterparse(stdin, html=True))


if __name__ == '__main__':
    save(main())
