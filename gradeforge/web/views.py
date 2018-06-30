from django.http import HttpResponse, Http404
from django.db import connection

from gradeforge.grades import png_for

def grade_png(request, semester, department, code, section):
    try:
        png_file = png_for(department, code, section, semester)  # side effects
    except ValueError as e:
        raise Http404("No such class exists") from e
    with open(png_file, 'rb') as png:
        return HttpResponse(png.read(), content_type='image/png')


def grade_csv(request, department, code, section, semester):
    sql_query = ('SELECT * FROM grade '
                 'WHERE department = %s AND code = %s AND section = %s AND semester = %s')
    with connection.cursor() as cursor:
        data = cursor.execute(sql_query, (department, code, section, semester)).fetchone()
        # https://www.python.org/dev/peps/pep-0249/#description
        headers = map(lambda d: d[0], cursor.description)
    csv = ','.join(headers) + '\n' + ','.join(map(str, data))
    return HttpResponse(csv, content_type='text/csv')
