#!/usr/bin/env python3

'Take the pickled contents of a file from stdin and output it to stdout'

import sys
import pickle

def read_stdin():
    'Return the contents of a pickled file'
    try:
        return pickle.load(sys.stdin.buffer)
    except (EOFError, KeyboardInterrupt):
        return None


if __name__ == '__main__':
    quit(read_stdin())
