'''Command line parsing. Note that this module is decidedly harder to use than the
makefile; if you want to run SQL queries I recommend running `make` then
`gradeforge sql query <your_query>`.'''

from argparse import ArgumentParser
from datetime import date
from sys import stdout
from os import path
# I tried making this relative and it failed miserably, not worth the pain
from gradeforge.utils import SingleMetavarFormatter, allowed, get_season_today, parse_semester, load
from gradeforge.parse import parse_exam, parse_sections, parse_bookstore, parse_catalog, parse_grades
from gradeforge.download import get_exam, get_sections, get_bookstore, get_catalog, get_grades
from gradeforge.sql import create_sql, dump, query
from gradeforge.web import app

VERBOSITY = ArgumentParser(add_help=False)
VERBOSITY.add_argument('--verbose', '--debug', '-v', action='count', default=0)
# couldn't find a good way to do this in argparse; quiet will later be subtracted from verbose
VERBOSITY.add_argument('--quiet', '-q', action='count', default=0)

PARSER = ArgumentParser(formatter_class=SingleMetavarFormatter, prog='gradeforge',
                        description="backend for the GradeForge app")

SUBPARSERS = PARSER.add_subparsers(dest='subparser', help='commands to run')
# this is a bug in argparse: https://stackoverflow.com/a/18283730
SUBPARSERS.required = True

# begin web parser
WEB = SUBPARSERS.add_parser('web', description='run the web server', parents=[VERBOSITY])
WEB.add_argument('--port', '-p', type=int, default=5000)

# begin `parse` parser
PARSE = SUBPARSERS.add_parser('parse', description='parse downloaded files',
                              parents=[VERBOSITY])
PARSE.add_argument('info', help='type of info to parse',
                   choices=('sections', 'catalog', 'exam', 'bookstore', 'grades'))
PARSE.add_argument('file', help='file to parse')

# begin sql parser
SQL = SUBPARSERS.add_parser('sql', description='create, query, and modify the sql database')
SQL.add_argument('--database', '-d', default=path.abspath('classes.sql'))
COMMAND = SQL.add_subparsers(dest='command', help='command to execute')
COMMAND.required = True

QUERY = COMMAND.add_parser('query', help='query information from an existing database')
QUERY.add_argument('sql_query', default='SELECT sql FROM sqlite_master', nargs='?',
                   help='query to run. must be valid SQLite3 syntax, '
                   + 'but ending semicolon is optional.')

CREATE = COMMAND.add_parser('create', help='create a new database')
# TODO: implement this
CREATE.add_argument('--source', nargs='+',
                    help='one or more files containing data. '
                    + 'must be valid python using built-in datastructures. '
                    + 'must contain the variables '
                    + 'DEPARTMENTS, CLASSES, INSTRUCTORS, SEMESTERS, and SECTIONS.')

COMMAND.add_parser('dump', help='show everything in a database')

# begin download parser
DOWNLOAD = SUBPARSERS.add_parser('download', description='download files from sc.edu',
                                 parents=[VERBOSITY])
DOWNLOAD.required = True

DOWNLOAD.add_argument('--season', '-s', type=str.lower,
                      default=get_season_today(),
                      choices=('fall', 'summer', 'spring'))
DOWNLOAD.add_argument('--year', '-y', type=int, default=date.today().year,
                      choices=range(2008, date.today().year + 1))

INFO = DOWNLOAD.add_subparsers(dest='info')
INFO.required = True

SECTIONS = INFO.add_parser('sections', description='course sections offered')
# TODO: make campus nicer
SECTIONS.add_argument('--campus', '-c', choices=allowed['campus'], default='COL')
# TODO: allowed['term'] is a dumpster fire that needs to be nuked from orbit
SECTIONS.add_argument('--term', '-T', choices=allowed['term'], default='30')

BOOKSTORE = INFO.add_parser('bookstore', description='textbooks for a given section')
BOOKSTORE.add_argument('department', choices=allowed['department'],
                       metavar='DEPARTMENT', type=str.upper)
BOOKSTORE.add_argument('number', choices=range(1000), type=int, metavar='CODE')

BOOKSTORE.add_argument('section')

INFO.add_parser('catalog', description='courses offered')
INFO.add_parser('exam', description='final exam times')
GRADES = INFO.add_parser('grades', description='grade spreads for past semester')
GRADES.add_argument('campus', nargs='?', type=str.lower,
                    choices=('columbia', 'aiken', 'upstate'))

ARGS = PARSER.parse_args()
if 'verbose' in ARGS.__dict__:
    ARGS.verbose -= ARGS.quiet - 1  # verbosity defaults to 1

if ARGS.subparser == 'web':
    app.config['ENV'] = ('development' if ARGS.verbose else 'production')
    app.run(debug=ARGS.verbose > 0, port=ARGS.port, use_debugger=ARGS.verbose > 0)
elif ARGS.subparser == 'sql':
    if ARGS.command == 'create':
        # TODO: do this in a sane way
        DEPARTMENTS, CLASSES = load('.courses.data')
        INSTRUCTORS, SEMESTERS, SECTIONS = load('.sections.data')
        quit(create_sql(DEPARTMENTS, CLASSES, INSTRUCTORS,
                        SEMESTERS, SECTIONS, database=ARGS.database))
    if not path.exists(ARGS.database):
        raise ValueError("database '%s' does not exist or is invalid" % ARGS.database)
    if ARGS.command == 'query':
        print(query(ARGS.sql_query, database=ARGS.database))
    elif ARGS.command == 'dump':
        print(dump())
elif ARGS.subparser == 'parse':
    parse = (parse_exam if ARGS.info == 'exam' else
             parse_sections if ARGS.info == 'sections' else
             parse_catalog  if ARGS.info == 'catalog' else
             parse_bookstore if ARGS.info == 'bookstore' else
             parse_grades)
    print(parse(ARGS.file))
else:  # download
    if ARGS.info == 'exam':
        print(get_exam(ARGS.year, ARGS.season))
    elif ARGS.info == 'sections':
        print(get_sections(semester=parse_semester(ARGS.season, year=ARGS.year),
                           campus=ARGS.campus, term=ARGS.term))
    elif ARGS.info == 'catalog':
        print(get_catalog(parse_semester(ARGS.season, year=ARGS.year)))
    elif ARGS.info == 'bookstore':
        print(get_bookstore(parse_semester(ARGS.season, year=ARGS.year),
                            ARGS.department, ARGS.number, ARGS.section))
    else:
        stdout.buffer.write(get_grades(ARGS.year, ARGS.season, ARGS.campus))
