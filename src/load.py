#!/usr/bin/env python
import sys, cloudpickle
def read_stdin():
    try:
        return cloudpickle.load(sys.stdin.buffer)
    except (EOFError, KeyboardInterrupt):
        return None


if __name__ == '__main__':
    quit(read_stdin())
