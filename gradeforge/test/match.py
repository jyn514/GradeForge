#!/usr/bin/env python
import re

def match(files, whitespace='    '):
    # \1: the 'root' indentation
    # \2: the type of indentation (usually tabs or 4 spaces), exactly the same as the variable whitespace
    # (#.*)? - and optional comment
    # ((\1\2.*$|\s*)\n)* - one or more lines of unrelated code within the indented block, including blank lines
    # (raise( [a-zA-Z]+\(.*\))) - the group we actually care about (parentheses are only so we have it in found.groups()
    # the string 'raise' then either a callable (such as ValueError) or nothing
    regex = r'((    )*)try:\s*(#.*)?\n((\1\2.*$|\s*)\n)*\1except[^:]*:\s*$\n((\1\2.*|\s*)$\n)*(\1\2*(raise ([a-zA-Z]+\(.*\)))\s*$)'
    regex = re.compile(regex.replace('    ', whitespace), re.MULTILINE)
    num_bad = 0
    for f in files:
        with open(f) as fh:
            text = fh.read()
        for bad_code in regex.finditer(text):
            line_number = text[:text.index(bad_code.group()) + len(bad_code.group())].count('\n')
            print('found bad handling "%s" at line %d in file %s' % (bad_code[9], line_number, f))
            print("(instead, use `raise %s from e`); see https://www.python.org/dev/peps/pep-3134/" % bad_code[10])
            num_bad += 1
    return num_bad

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--whitespace', '-w', default='    ', choices=(' ', '  ', '    ', '        ', '\t'))
    parser.add_argument('input', nargs='+')
    args = parser.parse_args()
    quit(match(args.input, args.whitespace))
