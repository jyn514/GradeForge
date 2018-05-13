#!/usr/bin/env python

'''Autogenerated SQL commands for creating an SQL database'''

from __future__ import print_function
from utils import load

CLASSES, DEPARTMENTS = load('.courses.data')
SECTIONS = load('.sections.data')

TABLES = {'class': ["department char(4)",
                    "code varchar(4)",
                    "title tinytext",
                    "description text",
                    "level tinytext default 'undergrad'",
                    "credits tinyint(1) default 3",
                    "type tinytext default 'lecture'"],
          'department': ["abbr char(4)",
                         "title tinytext"],
          'instructor': ["name tinytext",
                         "email tinytext"],
          'semester': ["id char(6)",
                       "startDate date",
                       "endDate date",
                       "registrationEnd date"],
          'location': ["uid smallint",
                       "building tinytext",
                       "room smallint"],
          'section': ["uid tinyint(5)",
                       "department char(4)",
                       "section tinytext",
                       "code varchar(4)",
                       "semester char(6)",
                       "campus tinytext default 'Columbia'",
                       "startTime time",
                       "endTime time",
                       "days varchar(7)",
                       "registrationStart date",
                       "instructor smallint",
                       "location smallint",
                       "finalExam dateTime",
                       "capacity tinyint",
                       "syllabus tinytext",
                       "remaining tinyint"]
       }

base = '''CREATE TABLE %s(
          %s);'''
tables_commands = '\n'.join(base % (key, ', '.join(TABLES[key])) for key in TABLES.keys())

base = 'INSERT INTO class (department, code, title) VALUES ("%s", "%s", "%s");'
class_commands = '\n'.join(base % (c['department'], c['code'], c['title']) for c in CLASSES)

base = 'INSERT INTO department (abbr, title) VALUES ("%s", "%s");'
department_commands = '\n'.join(base % d for d in DEPARTMENTS.items())


base = 'INSERT INTO instructor (name, email) VALUES ("%s", "%s");'
instructor_commands = '\n'.join(base % (i[0], i[1])
                              for i in set((s['instructor'], s['instructor_email'])
                                            for s in SECTIONS))

base = '''INSERT INTO section (uid, department, section, code, semester, campus, startTime, endTime, days, registrationStart, instructor, location, finalExam, capacity, syllabus, remaining) VALUES
        ("%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s",
         "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s");'''

section_commands = '\n'.join(base % (course['UID'],
                                     course['department'],
                                     course['section'],
                                     course['code'],
                                     course['semester'],
                                     course['campus'],
                                     course['start_time'],
                                     course['end_time'],
                                     course['days'],
                                     course['registration_start'],
                                     course['instructor'],
                                     course['location'],
                                     course.get('final_exam', None),
                                     course.get('capacity', None),
                                     course.get('syllabus', None),
                                     course.get('remaining', None))
                            for course in SECTIONS)

if __name__ == "__main__":
    print("BEGIN TRANSACTION;%s%s%s%s%sCOMMIT;" % (tables_commands, class_commands,
                                                   department_commands, instructor_commands,
                                                   section_commands), end='')
