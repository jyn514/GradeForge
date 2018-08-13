'''The 'API' for gradeforge, as much as python has APIs'''
# https://stackoverflow.com/a/40846742
import warnings
warnings.filterwarnings("ignore", message="numpy.dtype size changed")
warnings.filterwarnings("ignore", message="numpy.ufunc size changed")

from .parse import (parse_exam, parse_sections, parse_bookstore,
                    parse_catalog, parse_grades, parse_semester)
from .download import get_exam, get_sections, get_bookstore, get_catalog, get_grades
from .sql import TABLES, create, query, dump
from .web import app
from .utils import allowed, get_season_today, DEFAULT_DATABASE
from .combine import combine_grades, combine_instructors, combine_departments, combine_terms
