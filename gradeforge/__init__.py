'''The 'API' for gradeforge, as much as python has APIs'''
from .parse import parse_exam, parse_sections, parse_bookstore, parse_catalog
from .download import get_exam, get_sections, get_bookstore, get_catalog
from .sql import TABLES, create_sql, query, dump
from .utils import ReturnSame
from .web import app
