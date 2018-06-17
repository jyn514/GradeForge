#!/usr/bin/env python3
import re
import sys

from matplotlib import pyplot
from sqlite3 import connect

from gradeforge.utils import get_semester_today

def png_for(department, code, section, semester=get_semester_today()):
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
    grades = "A", "B", "B+", "C", "C+", "D", "D+", "F", "I", "W", "WF"
    grades_query = "SELECT " + repr(grades)[1:-1].replace("'", '"') + " FROM grade WHERE section = ?"
    with connect('classes.sql') as database:
        cursor = database.cursor()
        try:
            uid, instructor, title = cursor.execute(metadata_query, (department, code, section, semester)).fetchone()
        except TypeError:
            raise ValueError("No sections found for " + ' '.join([department, code, section]))
        results = dict(zip(grades, cursor.execute(grades_query, [uid])))

    assert results != {}, "query was " + grades_query.replace('?', str(uid))
    course_code = "%s %s (S: %s)" % (department, code, section)
    header = "%s - %s - %s" % (instructor, title, course_code)

    pyplot.figure().suptitle(header)
    pyplot.xticks(range(len(results)), results.keys())
    pyplot.bar(range(len(results)), results.values(), align='center')
    pyplot.savefig("images/%s-%s-%s-%s.png" % (department, code, section, semester))
