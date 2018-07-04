#!/usr/bin/env python3

'''Autogenerated SQL commands for creating an SQL database
TODO:
- have James redo schema
- add location table (all info is available in course['location'])
- compare section attribute to course attribute and remove if same
- ask brady if we care about registration start
'''

import sqlite3
import csv

TABLES = {'class': ["title tinytext",
                    "department char(4)",
                    "code varchar(4)",
                    "description text",
                    "credits tinyint(1)",
                    "attributes text",
                    "level tinytext",
                    "type tinytext",
                    # I don't even know, this is a campus I think?
                    'division tinytext',
                    # NOTE: not unique because course could be crosslisted
                    "all_sections tinytext"],
          'department': ["code char(4) PRIMARY KEY",
                         "description tinytext"],
          'instructor': ["name tinytext PRIMARY KEY",
                         "email tinytext"],
          'term': ["id INTEGERY PRIMARY KEY",
                   "semester char(6)",
                   "startDate date",
                   "endDate date",
                   'registrationStart data',
                   "registrationEnd date"],
          # currently unused
          'location': ["id smallint PRIMARY KEY",
                       "building tinytext",
                       "room smallint"],
                      # NOTE: unique within a semester, duplicated across semesters
          'section': ["uid tinyint(5)",
                      "section tinytext",
                      "department char(4)",
                      "code varchar(5)",
                      "term INTEGER",
                      "attributes tinytext",
                      "campus tinytext",
                      'type tinytext',
                      'method tinytext',
                      "syllabus tinytext",
                      "days varchar(7)",
                      "location smallint",
                      "startTime time",
                      "endTime time",
                      "primary_instructor tinytext",
                      'secondary_instructors tinytext',
                      "finalExam dateTime"],
                      # always out of date; requires parsing different page
                      #"capacity tinyint", "remaining tinyint"
          'grade': ['semester char(6)',
                    'department char(4)',
                    'code varchar(5)',
                    'title tinytext',
                    'section tinytext',
                    'campus tinytext',
                    'A tinyint',
                    '"B+" tinyint',
                    'B tinyint',
                    '"C+" tinyint',
                    'C tinyint',
                    '"D+" tinyint',
                    'D tinyint',
                    'F tinyint',
                    'AUDIT tinyint',
                    'W tinyint',
                    'WF tinyint',
                    # columns after this are questionable
                    'A_GF tinyint',
                    '"B+_GF" tinyint',
                    'B_GF tinyint',
                    '"C+_GF" tinyint',
                    'C_GF tinyint',
                    '"D+_GF" tinyint',
                    'D_GF tinyint',
                    'F_GF tinyint',
                    'S tinyint',
                    'U tinyint',
                    'UN tinyint',
                    'INCOMPLETE tinyint',
                    '"No Grade" tinyint',
                    'NR tinyint',
                    'T tinyint',
                    'FN tinyint',
                    'IP tinyint',
                    'TOTAL tinyint'
                   ]
         }


def csv_insert(table, csv_file, cursor):
    '''Given a table and the corresponding CSV file, plop the whole thing into a database
    TODO: accept file descriptor for csv_file'''
    with open(csv_file) as f:
        # TODO: use a dict reader?
        reader = csv.reader(f)
        # TODO: check if this matches table
        try:
            headers = tuple(map(lambda s: repr(s.strip()), next(reader)))
        except StopIteration as e:
            raise ValueError("FATAL: csv file '%s' exists but is empty. Is there a makefile problem?" % csv_file) from e
        command = 'INSERT INTO %s (%s) VALUES (%s)'
        command %= table, ', '.join(headers), ', '.join('?' * len(headers))
        cursor.executemany(command, reader)


def create(catalog='catalog.csv', departments='departments.csv',
           instructors='instructors.csv', terms='terms.csv',
           sections='sections.csv', grades='grades.csv',
           database='../classes.sql'):
    '''main create function for the gradeforge project. for every table in
    TABLES, create it in the database and add the corresponding CSV file.'''
    with sqlite3.connect(database) as connection:
        command = ''.join('CREATE TABLE %s(%s);' % (key, ', '.join(value))
                          for key, value in TABLES.items())
        connection.executescript(command)

        csv_insert('class', catalog, connection)
        csv_insert('department', departments, connection)
        csv_insert('instructor', instructors, connection)
        csv_insert('term', terms, connection)
        csv_insert('section', sections, connection)
        csv_insert('grade', grades, connection)


def limited_query(database='classes.sql', table='section', columns='*', **filters):
    '''NOTE: Does NOT validate input, that is the responsibility of calling code.
    Fails noisily if args are incorrect. Example: query_sql.py --department CSCE CSCI'''
    # ex: subject IN ('CSCE', 'CSCI') AND CRN IN (12345, 12346)
    query_filter = ' AND '.join([key + ' IN (%s)' % str(value)[1:-1].replace("'", '"')
                                 for key, value in filters.items()])
    command = 'SELECT %s FROM %s%s;' % (', '.join(columns), table,
                                        ' WHERE ' + query_filter if query_filter != '' else '')
    with sqlite3.connect(database) as connection:
        return connection.execute(command).fetchall()


def query(sql_query, database='classes.sql'):
    '''Return the result of an sql query exactly as if it had been passed to the sqlite3 binary'''
    with sqlite3.connect(database) as connection:
        return '\n'.join('|'.join(map(str, t))
                         for t in connection.execute(sql_query).fetchall())


def dump(database='classes.sql'):
    '''Dump the whole database. Assumes the database was created by GradeForge.'''
    print('\n'.join(query("SELECT * FROM " + table) for table in TABLES))
