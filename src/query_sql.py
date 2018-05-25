#!/usr/bin/env python3
from __future__ import print_function
from sqlite3 import connect

def limited_query(database='classes.sql', table='section', columns='*', **filters):
    '''NOTE: Does NOT validate input, that is the responsibility of calling code.
    Fails noisily if args are incorrect. Example: query_sql.py --department CSCE CSCI'''
    DATABASE = connect(database)
    # ex: subject IN ('CSCE', 'CSCI') AND CRN IN (12345, 12346)
    query_filter = ' AND '.join([key + ' IN (%s)' % str(value)[1:-1].replace("'", '"')
                                 for key, value in filters.items()])
    command = 'SELECT %s FROM %s%s;' % (', '.join(columns), table,
                                        ' WHERE ' + query_filter if query_filter != '' else '')
    if DEBUG:
        print(command, filters)
    stdout = DATABASE.execute(command).fetchall()
    DATABASE.close()
    return stdout


def query(query, database='classes.sql'):
    return '\n'.join('|'.join(str(s) for s in t)
                     for t in connect(database).execute(query).fetchall())


def schema(database='classes.sql'):
    return query('SELECT sql FROM sqlite_master;', database)


if __name__ == '__main__':
    from argparse import ArgumentParser
    from utils import SingleMetavarFormatter
    parser = ArgumentParser(__doc__, formatter_class=SingleMetavarFormatter)
    parser.add_argument('--database', '-d', '-f', default='classes.sql')
    parser.add_argument('--debug', '--verbose', '-v', action='store_true')
    parser.add_argument('query', default='SELECT sql FROM sqlite_master', nargs='?')
    args = parser.parse_args()
    DEBUG = args.__dict__.pop('debug')
    print(query(**args.__dict__), end='')
