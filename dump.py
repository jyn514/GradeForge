#!/usr/bin/env python
import sqlite3
from create_sql import TABLES

database = sqlite3.connect('classes.sql')
cursor = database.cursor()

for table in TABLES.keys():
    print('\n'.join('|'.join(str(s) for s in l) for l in cursor.execute('SELECT * FROM ' + table)))

database.close()
