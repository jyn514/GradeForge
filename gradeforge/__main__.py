'''Command line parsing. Note that this module is decidedly harder to use than the
makefile; if you want to run SQL queries I recommend running `make` then
`gradeforge sql query <your_query>`.'''

from datetime import date
from sys import stdout
from os import path
import argparse
import logging

from . import *

def main():

    # override the default help formatter for ArgumentParser to avoid printing
    # duplicate copies of possible parameters
    # pylint: disable=undefined-variable
    argparse.HelpFormatter._format_action_invocation = utils.argparse_format_action_invocation

    from argparse import ArgumentParser

    PARSER = ArgumentParser(prog='gradeforge',
                            description="backend for the GradeForge app")
    PARSER.add_argument('--verbose', '--debug', '-v', action='count', default=0)
    # couldn't find a good way to do this in argparse; quiet will later be subtracted from verbose
    PARSER.add_argument('--quiet', '-q', action='count', default=0)

    SUBPARSERS = PARSER.add_subparsers(dest='subparser', help='commands to run')
    # this is a bug in argparse: https://stackoverflow.com/a/18283730
    SUBPARSERS.required = True

    # begin web parser
    WEB = SUBPARSERS.add_parser('web',
        description='run the web server')
    WEB.add_argument('--port', '-p', type=int, default=5000)

    # begin `parse` parser
    PARSE = SUBPARSERS.add_parser('parse', description='parse downloaded files')

    # parent parser
    IO = ArgumentParser(add_help=False)
    IO.add_argument('input', help='file to parse')
    IO.add_argument('output', help='main output of parse function', nargs='?', default=stdout)

    INFO = PARSE.add_subparsers(dest='info', help='type of info to parse')
    INFO.required = True
    INFO.add_parser('exam', parents=[IO])
    INFO.add_parser('bookstore', parents=[IO])
    INFO.add_parser('grades', parents=[IO])
    INFO.add_parser('catalog', parents=[IO]).add_argument('--departments', '--department-output',
                                                        default=stdout)

    SECTIONS = INFO.add_parser('sections', parents=[IO])
    for opt in ['instructor', 'term']:
        SECTIONS.add_argument('--%ss' % opt, '--%s-output' % opt,
                            default=stdout)

    # begin sql parser
    SQL = SUBPARSERS.add_parser('sql', description='create, query, and modify the sql database')
    SQL.add_argument('--database', '-d', default=DEFAULT_DATABASE)
    COMMAND = SQL.add_subparsers(dest='command', help='command to execute')
    COMMAND.required = True

    QUERY = COMMAND.add_parser('query', help='query information from an existing database')
    QUERY.add_argument('sql_query', default='SELECT sql FROM sqlite_master', nargs='?',
                    help='query to run. must be valid SQLite3 syntax, '
                    + 'but ending semicolon is optional.')

    COMMAND.add_parser('create', help='create a new database')
    COMMAND.add_parser('dump', help='show everything in a database')

    # begin combine parser
    COMBINE = SUBPARSERS.add_parser("combine", description="combine multiple CSV files")
    COMBINE.add_argument('info', choices=('grades', 'instructors', 'terms', 'departments'))
    COMBINE.add_argument('input', nargs='+')

    # begin download parser
    DOWNLOAD = SUBPARSERS.add_parser('download', description='download files from sc.edu')
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
    SECTIONS.add_argument('--campus', '-c', choices=allowed['campus'] + ('%',), default='%')
    # TODO: allowed['term'] is a dumpster fire that needs to be nuked from orbit
    SECTIONS.add_argument('--term', '-T', choices=allowed['term'], default='%')

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
    # https://docs.python.org/3/library/logging.html#logging-levels
    logging.basicConfig(level=max(40 - ARGS.verbose * 10, 10),
                        format="%(levelname)s: %(name)s: %(message)s")

    if ARGS.subparser == 'web':
        app.config['ENV'] = ('development' if ARGS.verbose else 'production')
        app.run(debug=ARGS.verbose > 0, port=ARGS.port, use_debugger=ARGS.verbose > 0)
    elif ARGS.subparser == 'sql':
        if ARGS.command == 'create':
            # TODO: add params for csv files
            create(database=ARGS.database)
        elif not path.exists(ARGS.database):
            raise ValueError("database '%s' does not exist or is invalid" % ARGS.database)
        if ARGS.command == 'query':
            print(query(ARGS.sql_query, database=ARGS.database))
        elif ARGS.command == 'dump':
            print(dump())
    elif ARGS.subparser == 'parse':
        if ARGS.info == 'exam':
            parse_exam(ARGS.input, ARGS.output)
        elif ARGS.info == 'bookstore':
            parse_bookstore(ARGS.input, ARGS.output)
        elif ARGS.info == 'grades':
            parse_grades(ARGS.input, ARGS.output)
        elif ARGS.info == 'catalog':
            parse_catalog(ARGS.input, catalog_output=ARGS.output,
                        department_output=ARGS.departments)
        else:
            parse_sections(ARGS.input, instructor_output=ARGS.instructors,
                        term_output=ARGS.terms,
                        section_output=ARGS.output)
    elif ARGS.subparser == 'combine':
        if ARGS.info == 'grades':
            combine_grades(ARGS.input)
        elif ARGS.info == 'instructors':
            combine_instructors(ARGS.input)
        elif ARGS.info == 'terms':
            combine_terms(ARGS.input)
        else:  # departments
            combine_departments(ARGS.input)
    else:  # download
        if ARGS.info == 'exam':
            print(get_exam(ARGS.year, ARGS.season))
        elif ARGS.info == 'sections':
            print(get_sections(semester=parse_semester(ARGS.season, year=ARGS.year),
                            campus=ARGS.campus, term=ARGS.term))
        elif ARGS.info == 'catalog':
            print(get_catalog(semester=parse_semester(ARGS.season, year=ARGS.year)))
        elif ARGS.info == 'bookstore':
            print(get_bookstore(parse_semester(ARGS.season, year=ARGS.year),
                                ARGS.department, ARGS.number, ARGS.section))
        else:
            stdout.buffer.write(get_grades(ARGS.year, ARGS.season, ARGS.campus))

if __name__ == '__main__':
    main()
else:
    logging.debug(__name__)
