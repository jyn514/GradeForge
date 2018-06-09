#!/usr/bin/env python3
import re
import sys

import pandas
from matplotlib import pyplot
from sqlite3 import connect

def png_for(department, code, section, semester='201808'):
    department, code, section, semester = map(str, (department, code, section, semester))
    assert code.isnumeric()

    metadata_query = '''
            SELECT uid, instructor, title
            FROM section INNER JOIN class
                         ON class.department = section.department
                         AND class.code = section.code
            WHERE class.department = ?
                  AND class.code = ?
                  AND section = ?
                  AND semester = ?'''
    grades = "A","B","B+","C","C+","D","D+","F","I","W","WF"
    grades_query = "SELECT " + repr(grades)[1:-1] + " FROM grade WHERE section = ?"
    with connect('classes.sql') as database:
        cursor = database.cursor()
        uid, instructor, title = cursor.execute(metadata_query, (department, code, section, semester)).fetchone()
        results = dict(zip(grades, cursor.execute(grades_query, [uid])))

    course_code = "%s %s (S: %s)" % (department, code, section)
    header = "%s - %s - %s" % (instructor, title, course_code)

    pyplot.figure().suptitle(header)
    plt.bar(range(len(results)), results.keys(), align='center')
    plt.xticks(range(len(results)), results.values())
    plt.savefig("images/%s-%s-%s-%s.png" % (department, code, section, semester))
