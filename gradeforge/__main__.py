from argparse import ArgumentParser
from datetime import date
from os import path
# I tried making this relative and it failed miserably, not worth the pain
from gradeforge.utils import SingleMetavarFormatter, arg_filter, allowed, get_season_today, parse_semester, load

verbosity_parser = ArgumentParser(add_help=False)
verbosity_parser.add_argument('--verbose', '--debug', '-v', action='count', default=0)
# couldn't find a good way to do this in argparse; quiet will later be subtracted from verbose
verbosity_parser.add_argument('--quiet', '-q', action='count', default=0)

parser = ArgumentParser(formatter_class=SingleMetavarFormatter, prog='gradeforge',
                        description="backend for the GradeForge app")

subparsers = parser.add_subparsers(dest='subparser', help='commands to run')
# this is a bug in argparse: https://stackoverflow.com/a/18283730
subparsers.required = True

# begin web parser
web = subparsers.add_parser('web', description='run the web server', parents=[verbosity_parser])
web.add_argument('--port', '-p', type=int, default=5000)

# begin `parse` parser
parse = subparsers.add_parser('parse', description='parse downloaded files',
                              parents=[verbosity_parser])
parse.add_argument('info', help='type of info to parse',
             choices=('sections', 'catalog', 'exam', 'bookstore'))
parse.add_argument('file', help='file to parse')

# begin sql parser
sql = subparsers.add_parser('sql', description='create, query, and modify the sql database')
sql.add_argument('--database', '-d', default=path.abspath('classes.sql'))
command = sql.add_subparsers(dest='command', help='command to execute')
command.required = True

query = command.add_parser('query', help='query information from an existing database')
query.add_argument('sql_query', default='SELECT sql FROM sqlite_master', nargs='?',
                   help='query to run. must be valid SQLite3 syntax, but ending semicolon is optional.')

create = command.add_parser('create', help='create a new database')
create.add_argument('--source', default=None, nargs='+',
                    help='one or more files containing data. must be valid python using built-in datastructures. '
                         + 'must contain the variables DEPARTMENTS, CLASSES, INSTRUCTORS, SEMESTERS, and SECTIONS.')

dump = command.add_parser('dump', help='show everything in a database')

# begin download parser
download = subparsers.add_parser('download', description='download files from sc.edu',
                             parents=[verbosity_parser])
download.required = True

download.add_argument('--season', '-s', type=str.lower,
                      default=get_season_today(),
                      choices=('fall', 'summer', 'spring'))
download.add_argument('--year', '-y', type=int, default=date.today().year,
                      choices=range(2013, date.today().year + 1))

info = download.add_subparsers(dest='info')
info.required = True

sections = info.add_parser('sections', description='course sections offered')
# TODO: make campus nicer
sections.add_argument('--campus', '-c', choices=allowed['campus'])
# TODO: allowed['term'] is a dumpster fire that needs to be nuked from orbit
sections.add_argument('--term', '-T', choices=allowed['term'])

bookstore = info.add_parser('bookstore', description='textbooks for a given section')
bookstore.add_argument('department', choices=allowed['department'])
bookstore.add_argument('number', choices=range(1000))
bookstore.add_argument('section')

catalog = info.add_parser('catalog', description='courses offered')
exam = info.add_parser('exam', description='final exam times')


args = parser.parse_args()
if 'verbose' in args.__dict__:
    args.verbose -= args.quiet - 1  # verbosity defaults to 1

if args.subparser == 'web':
    from gradeforge.web import app
    app.config['ENV'] = ('development' if args.verbose else 'production')
    app.run(debug=args.verbose > 0, port=args.port, use_debugger=args.verbose > 0)
elif args.subparser == 'sql':
    if args.command == 'create':
        from gradeforge.sql import create_sql
        # TODO: do this in a sane way
        DEPARTMENTS, CLASSES = load('.courses.data')
        INSTRUCTORS, SEMESTERS, SECTIONS = load('.sections.data')
        quit(create_sql(DEPARTMENTS, CLASSES, INSTRUCTORS, SEMESTERS, SECTIONS, database=args.database))
    if not path.exists(args.database):
        raise ValueError("database '%s' does not exist or is invalid" % args.database)
    if args.command == 'query':
        from gradeforge.sql import query
        print(query(args.sql_query, database=args.database))
    elif args.command == 'dump':
        from gradeforge.sql import dump
        print(dump(database=args.database))
elif args.subparser == 'parse':
    # I love the smell of meta-programming in the morning.
    exec('from gradeforge.parse import parse_' + args.info + ' as parse')
    with open(args.file) as f:
        print(parse(f))
else:  # download
    exec('from gradeforge.download import get_' + args.info + ' as get')
    semester = parse_semester(args.season, year=args.year)
    if args.info == 'exam':
        print(get(args.year, args.season))
    elif args.info == 'sections':
        print(get(semester=semester, campus=args.campus, term=args.term))
    elif args.info == 'catalog':
        print(get(semester))
    else:
        print(get(semester, args.department, args.number, args.section))
