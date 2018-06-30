import os

from django.http import HttpResponse, Http404
from django.conf import settings

from gradeforge.grades import png_for
from gradeforge.sql import query

database = settings.DATABASES['default']['NAME']
images = os.path.join(os.path.dirname(database), 'images')

def grade_png(request, semester, department, code, section):
    try:
        # side effects
        png_file = png_for(department, code, section, semester,
                           database=database, directory=images)
    except ValueError as e:
        raise Http404("No such class exists") from e
    with open(png_file, 'rb') as png:
        return HttpResponse(png.read(), content_type='image/png')


def grade_csv(request, department, code, section, semester):
    sql_query = ('SELECT * FROM grade '
                 'WHERE department = ? AND code = ? AND section = ? AND semester = ?')
    csv = query(sql_query, (department, code, section,semester), seperator=',', database=database)
    return HttpResponse(csv, content_type='text/csv')
