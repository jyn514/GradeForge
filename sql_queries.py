#!/usr/bin/env python
from parse import load

classes, departments = load()

base = 'INSERT INTO class (abbr, code, title) VALUES ("%s", "%s", "%s");'
class_commands = ''.join(base % (c['abbr'], c['code'], c['title']) for c in classes)

base = 'INSERT INTO department (abbr, title) VALUES ("%s", "%s");'
department_commands = ''.join(base % d for d in departments.items())

print("%s%s%s%s" % ("BEGIN TRANSACTION;", class_commands, department_commands, "COMMIT;"))
