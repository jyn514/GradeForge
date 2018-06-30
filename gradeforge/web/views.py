import os

from django.http import HttpResponse
from django.conf import settings

from gradeforge.grades import png_for
from gradeforge.sql import query

database = os.path.join(os.path.dirname(os.path.dirname(settings.BASE_DIR)), 'classes.sql')
images = os.path.join(os.path.dirname(database), 'images')

def grade_png(request, semester, department, code, section):
    png_for(department, code, section, semester, database=database, directory=images)  # side effects
    with open(os.path.join(images, '%s-%s-%s-%s.png' % (semester, department, code, section)), 'rb') as png:
        return HttpResponse(png.read(), content_type='image/png')


def grade_csv(request, department, code, section, semester):
    sql_query = ('SELECT * FROM grade '
                 'WHERE department = ? AND code = ? AND section = ? AND semester = ?')
    csv = query(sql_query, (department, code, section,semester), seperator=',', database=database)
    return HttpResponse(csv, content_type='text/csv')
