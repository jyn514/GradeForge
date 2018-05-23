#!/usr/bin/env python

'Show the entire contents of a database created by create_sql'

import sqlite3
from create_sql import TABLES

DATABASE = sqlite3.connect('classes.sql')
CURSOR = DATABASE.cursor()

for table in TABLES:
    print('\n'.join('|'.join(str(s) for s in l)
                    for l in CURSOR.execute('SELECT * FROM ' + table)))

DATABASE.close()
