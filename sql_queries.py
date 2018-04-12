#!/usr/bin/env python
from parse import load

classes, departments = load('.courses.data')
sections = load('.sections.data')

TABLES = ('''
CREATE TABLE class(
    abbr char(4),
    code varchar(4),
    title tinytext,
    description text,
    level tinytext default 'undergrad',
    credits tinyint(1) default 3,
    type tinytext default 'lecture'
)''', '''
CREATE TABLE department(
    abbr char(4),
    title tinytext,
)''', '''
CREATE TABLE instructor(
    name tinytext,
    email tinytext,
)''', '''
CREATE TABLE semester(
    id char(6),
    startDate date,
    endDate date,
    registrationEnd date
)''', '''
CREATE TABLE location(
    uid smallint,
    building tinytext,
    room smallint,
)''', '''
CREATE TABLE section(
    CRN tinyint(5),
    abbr char(4),
    code varchar(4),
    semester char(6),
    campus tinytext default 'Columbia',
    bookstoreLink text,
    startTime time,
    endTime time,
    days varchar(7),
    registrationStart date,
    instructor smallint,
    location smallint,
    finalExam dateTime,
    capacity tinyint,
    remaining tinyint
)''')

base = 'INSERT INTO class (abbr, code, title) VALUES ("%s", "%s", "%s");'
class_commands = ''.join(base % (c['abbr'], c['code'], c['title']) for c in classes)

base = 'INSERT INTO department (abbr, title) VALUES ("%s", "%s");'
department_commands = ''.join(base % d for d in departments.items())


base = 'INSERT INTO instructor (name, email) VALUES ("%s", "%s);'
instructor_commands = ''.join(base % (i[0], i[1])
                              for i in set((s['instructor'], s.pop('instructor_email', None))
                               for s in sections))

base = '''INSERT INTO sections VALUES
        ("%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s");'''
section_commands = ''.join(base % (course['UID'], course['abbr'], course['code'],
                                  course['semester'], course['campus'],
                                  course['bookstore_link'], course['start_time'],
                                  course['end_time'], course['days'],
                                  course['registration_start'], course['instructor'],
                                  course['final_exam'], course['capacity'], course['remaining']) for course in sections)

print("%s%s%s%s%s%s" % ("BEGIN TRANSACTION;", ";".join(TABLES),
                        class_commands, department_commands, instructor_commands,
                        section_commands, "COMMIT;"))

