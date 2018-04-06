#!/usr/bin/env python
from parse import load

classes, departments = load()

class_table = '''
CREATE TABLE class(
    abbr char(4),
    code varchar(4),
    title tinytext,
    credits tinyint(1) default 3,
    type tinyint
);
'''

department_table = '''
CREATE TABLE department(
    abbr char(4),
    title tinytext
);
'''

base = 'INSERT INTO class (abbr, code, title) VALUES ("%s", "%s", "%s");'
class_commands = ''.join(base % (c['abbr'], c['code'], c['title']) for c in classes)

base = 'INSERT INTO department (abbr, title) VALUES ("%s", "%s");'
department_commands = ''.join(base % d for d in departments.items())

print("%s%s%s%s%s%s" % ("BEGIN TRANSACTION;", class_table, department_table,
                        class_commands, department_commands, "COMMIT;"))
