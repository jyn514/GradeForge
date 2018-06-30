'''Heavily adapted version of the original grade creator from jpc/grades.py'''
import os
import re
from sqlite3 import connect

# https://stackoverflow.com/questions/5503601
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot

from gradeforge.utils import get_semester_today

def png_for(department, code, section, semester=get_semester_today()):
    '''Given the appropriate info, create a bar graph of the grades for that section
    department: 4 character abbreviation (ex: CSCE)
    code: a 3-5 character major descriptor (ex: 145)
    section: a 3-4 character minor descriptor (ex: 001)
    semester: standard USC form, YYYYMM (ex: 201705)
    outputs to images/<department>-<code>-<section>-<semester>.png'''
    info = tuple(map(str, (semester, department, code, section)))
    root = os.path.dirname(os.path.dirname(__file__))
    output = os.path.join(root, 'images', "%s-%s-%s-%s.png" % info)
    if not os.path.exists(output):
        metadata_query = '''
                SELECT uid, instructor, title
                FROM section INNER JOIN class
                                ON class.department = section.department
                                AND class.code = section.code
                            INNER JOIN term
                                ON term.id = section.term
                WHERE semester = ?
                    AND class.department = ?
                    AND class.code = ?
                    AND section = ?'''
        grades = 'A, "B+", B, "C+", C, "D+", D, F, INCOMPLETE, W, WF'
        # NOTE: we can't use prepared statements for column names
        grades_query = ('SELECT ' + grades
                        + ''' FROM grade WHERE semester = ?
                                        AND department = ?
                                        AND code = ?
                                        AND section = ?''')
        with connect(os.path.join(root, 'classes.sql')) as connection:
            cursor = connection.cursor()
            try:
                uid, instructor, title = cursor.execute(metadata_query, info).fetchone()
                results = dict(zip(re.split('"?, "?', grades),
                                cursor.execute(grades_query, info).fetchone()))
            except TypeError as e:
                raise ValueError("No sections found for " + ' '.join(info)) from e

        if results == {}:
            quit("info for section did not match grades. query was",
                grades_query.replace('?', str(uid)))
        course_code = "%s %s (S: %s)" % (department, code, section)
        header = "%s - %s - %s" % (instructor, title, course_code)

        figure = pyplot.figure()
        figure.suptitle(header)
        pyplot.bar(range(len(results)), results.values(), align='center')
        pyplot.xticks(range(len(results)), results.keys())
        figure.autofmt_xdate()
        pyplot.savefig(output)
    return output
