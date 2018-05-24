#!/usr/bin/env python
from __future__ import print_function
from argparse import ArgumentParser
from sqlite3 import connect

from utils import arg_filter, allowed, SingleMetavarFormatter
from create_sql import TABLES

DEBUG = True

def query(table='section', columns='*', **filters):
    '''NOTE: Does NOT validate input, that is the responsibility of calling code.
    Fails noisily if args are incorrect.'''
    DATABASE = connect('classes.sql')
    # ex: subject IN ('CSCE', 'CSCI') AND CRN IN (12345, 12346)
    query_filter = ' AND '.join([key + ' IN ' + str(value)[1:-1].replace("'", '"')
                                 for key, value in filters.items()])
    command = 'SELECT %s FROM %s%s;' % (', '.join(columns), table,
                                        ' WHERE ' + query_filter if query_filter != '' else '')
    if DEBUG:
        print(command, filters)
    stdout = DATABASE.execute(command).fetchall()
    DATABASE.close()
    return stdout






if __name__ == '__main__':
    parser = ArgumentParser(__doc__, formatter_class=SingleMetavarFormatter)
    parser.add_argument('--semester', '-s', type=str.lower, nargs='*',
                        choices=allowed['semester'] + ('fall', 'summer', 'spring'))
    parser.add_argument('--campus', '-c', choices=allowed['campus'], nargs='*')
    parser.add_argument('--number', '-n', help='course code', type=int, nargs='*')
    parser.add_argument('--title', '-t', help='name of course', nargs='*')
    parser.add_argument('--min_credits', '--min', '-m', type=int, nargs='?')
    parser.add_argument('--max_credits', '--max', '-M', type=int, nargs='?')
    parser.add_argument('--level', '-l', choices=filter_out(allowed['level']), nargs='*')
    parser.add_argument('--term', '-T', choices=allowed['term'], nargs='*')
    parser.add_argument('--times', choices=filter_out(allowed['times']), nargs='*')
    parser.add_argument('--location', '-L', choices=filter_out(allowed['location']), nargs='*')
    parser.add_argument('--department', choices=allowed['department'] + ([],),
                        type=str.upper, nargs='*', metavar='DEPARTMENT')
    parser.add_argument('columns', choices=tuple(TABLES.keys()) + ('*',), type=str.lower, nargs='*',
                        metavar='COLUMNS', default='*')
    args = arg_filter(parser.parse_args())
    print(query(**args), end='')
