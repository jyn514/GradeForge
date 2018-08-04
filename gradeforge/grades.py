'''Heavily adapted version of the original grade creator from jpc/grades.py'''
import re
from sqlite3 import connect

# https://stackoverflow.com/questions/5503601
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot

from gradeforge.utils import get_semester_today, DEFAULT_DATABASE

def png_for(department, code, section, semester=get_semester_today()):
    '''Given the appropriate info, create a bar graph of the grades for that section
    department: 4 character abbreviation (ex: CSCE)
    code: a 3-5 character major descriptor (ex: 145)
    section: a 3-4 character minor descriptor (ex: 001)
    semester: standard USC form, YYYYMM
    outputs to images/<department>-<code>-<section>-<semester>.png
    TODO: allow customization of output file'''
    department, code, section, semester = map(str, (department, code, section, semester))

    metadata_query = '''
            SELECT uid, primary_instructor, title
            FROM section INNER JOIN class
                            ON class.department = section.department
                            AND class.code = section.code
                         INNER JOIN term
                            ON term.id = section.term
            WHERE class.department = ?
                  AND class.code = ?
                  AND section = ?
                  AND semester = ?'''
    grades = 'A, "B+", B, "C+", C, "D+", D, F, INCOMPLETE, W, WF'
    # NOTE: we can't use prepared statements for column names
    grades_query = ('SELECT ' + grades
                    + ''' FROM grade WHERE department = ?
                                     AND code = ?
                                     AND section = ?
                                     AND semester = ?''')
    info = department, code, section, semester
    with connect(DEFAULT_DATABASE) as database:
        cursor = database.cursor()
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
    pyplot.savefig("images/%s-%s-%s-%s.png" % (department, code, section, semester))
