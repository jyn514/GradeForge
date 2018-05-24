#!/usr/bin/env python
from __future__ import print_function
from argparse import ArgumentParser
from sqlite3 import connect

from utils import arg_filter, SingleMetavarFormatter
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


def query(query, database='../classes.sql'):
    return '\n'.join('|'.join(str(s) for s in t)
                     for t in connect(database).execute(query).fetchall())


def schema(database='../classes.sql'):
    return query('SELECT sql FROM sqlite_master;', database)


if __name__ == '__main__':
    parser = ArgumentParser(__doc__, formatter_class=SingleMetavarFormatter)
    parser.add_argument('query', default='SELECT sql FROM sqlite_master', nargs='?')
    args = arg_filter(parser.parse_args())
    print(query(**args), end='')
