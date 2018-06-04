#!/usr/bin/env python3

'''Autogenerated SQL commands for creating an SQL database
TODO:
- have James redo schema
- add location table (all info is available in course['location'])
- make insertion NOT dependent on order dictionaries were created
- make bookstore_link a property of course instead of section
- compare section attribute to course attribute and remove if same
- ask brady if we care about registration start
'''

import sqlite3
import csv

TABLES = {'class': ["course_link tinytext",
                    "title tinytext",
                    "department char(4)",
                    "code varchar(4)",
                    "description text",
                    "credits tinyint(1)",
                    "attributes text",
                    "level tinytext",
                    "type tinytext",
                    "all_sections tinytext"],
          'department': ["code char(4)",
                         "description tinytext"],
          'instructor': ["name tinytext",
                         "email tinytext"],
          'semester': ["id char(6)",
                       "startDate date",
                       "endDate date",
                       'registrationStart data',
                       "registrationEnd date"],
          'location': ["uid smallint",
                       "building tinytext",
                       "room smallint"],
          'section': ["section_link",
                      "uid tinyint(5)",
                      "section tinytext",
                      "department char(4)",
                      "code varchar(4)",
                      "semester char(6)",
                      "attributes tinytext",
                      "campus tinytext",
                      'type tinytext',
                      'method tinytext',
                      'catalog_link',
                      'bookstore_link',
                      "syllabus tinytext",
                      "days varchar(7)",
                      "location smallint",
                      "startTime time",
                      "endTime time",
                      "instructor tinytext",  # this is by email, not name (since email is unique)
                      "finalExam dateTime"]
                     # always out of date; requires parsing different page
                     #"capacity tinyint", "remaining tinyint"
         }


def csv_insert(table, file_name, cursor):
    with open(file_name) as f:
        reader = csv.reader(f)
        headers = next(reader)  # TODO: check if this matches table
        cursor.executemany('INSERT INTO %s (%s) VALUES (%s)'
                           % (table, ', '.join(headers), ', '.join('?' * len(headers))),
                           reader)


def create_sql(catalog='catalog.csv', departments='departments.csv',
               instructors='instructors.csv', semesters='semesters.csv',
               sections='sections.csv', database='../classes.sql'):
    '''TODO: accept parameters for file IO'''
    with sqlite3.connect(database) as DATABASE:
        CURSOR = DATABASE.cursor()

        CURSOR.executescript(''.join('CREATE TABLE %s(%s);' % (key, ', '.join(value))
                                     for key, value in TABLES.items()))

        csv_insert('class', catalog, CURSOR)
        csv_insert('department', departments, CURSOR)
        csv_insert('instructor', instructors, CURSOR)
        csv_insert('semester', semesters, CURSOR)
        csv_insert('section', sections, CURSOR)


def limited_query(database='classes.sql', table='section', columns='*', **filters):
    '''NOTE: Does NOT validate input, that is the responsibility of calling code.
    Fails noisily if args are incorrect. Example: query_sql.py --department CSCE CSCI'''
    DATABASE = sqlite3.connect(database)
    # ex: subject IN ('CSCE', 'CSCI') AND CRN IN (12345, 12346)
    query_filter = ' AND '.join([key + ' IN (%s)' % str(value)[1:-1].replace("'", '"')
                                 for key, value in filters.items()])
    command = 'SELECT %s FROM %s%s;' % (', '.join(columns), table,
                                        ' WHERE ' + query_filter if query_filter != '' else '')
    stdout = DATABASE.execute(command).fetchall()
    DATABASE.close()
    return stdout


def query(sql_query, database='classes.sql'):
    '''Return the result of an sql query exactly as if it had been passed to the sqlite3 binary'''
    return '\n'.join('|'.join(str(s) for s in t)
                     for t in sqlite3.connect(database).execute(sql_query).fetchall())


def dump():
    print('\n'.join(query("SELECT * FROM " + table) for table in TABLES))
