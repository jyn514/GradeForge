# Architecture
There are 5 major categories:

- sections
- catalog/class (the naming is iffy)
- exams
- books
- grades

Grades are further subdivided as such due to how the downloads worked out; they have substantially different formatting but I try to smooth this over in the parsing phase:

- old grades (before Fall 2013)
- new grades

I plan to eventually add a 6th category for books,
where the primary key is the ISBN number,
but this would require downloading a separate bookstore page for each section
and I just haven't gotten that far yet.

## Phases
There are 4 major phases:

1. Download
2. Parse
3. Combine
4. Create

### Download
The download phase is simplest: take this url, attach the necessary POST/GET data, put the output somewhere on disk.
Files are organized by directory and semester:
`<category>/{Spring|Summer|Fall}-{2008-2018}.{html|xlsx|pdf}`,
for example `grades/Spring-2017.xlsx`.

### Parse
Parse results are similarly organized by semester and category.
Output for all files defaults to stdout.
Note that a single parse function/command (`gradeforge parse sections`) may have multiple outputs;
if so, the output files are optional arguments in the CLI.

For example, `gradeforge parse sections sections/Fall-2017.html` would output three separate csv files to stdout: sections, instructors, and semesters.

Convention in the makefile is for the primary output to go to the same file with the extension changed to `csv`; in the example above, `sections/Fall-2017.csv`. There currently is no standard convention for secondary files, I've been throwing them to `/dev/null` :(

### Combine
After each file is parsed, they are combined into a single enormous csv file
(sections.csv is currently sitting at 85 MB).
There is one csv file per category; it sits in the root directory, not any subdirectory.
This is simple, fast, and crude - take the headers from a single CSV, take the contents of every CSV in a category, throw all of it in a file using shell redirection.
This *will* misinterpret files where the headers are in a different order;
I need to go through the code at some point and ensure the order is the same for every file within a category.

### Create
Finally, the function `create` from `sql.py` is run.
For every category, it creates a table and runs `csv_insert`,
which reads the headers from the combined file and inserts all rows correspondingly.
The result is output to `classes.sql`.
As currently implemented, the headers in the CSV and the names of the SQL columns
*must* be identical or the function will fail.
This is very fast but prone to error.

At one point I tried to remove duplicate info but [this failed](https://github.com/jyn514/GradeForge/issues/19).

Note also that the equivalent of [`COMMIT TRANSACTION`](https://docs.microsoft.com/en-us/sql/t-sql/language-elements/begin-transaction-transact-sql)
is run after every table, so if you remove [`.DELETE_ON_ERROR`](https://www.gnu.org/software/make/manual/html_node/Special-Targets.html) from the makefile,
you could conceivably have a decent database even if it fails halfway.
If you're wondering how this is done,
`with database.cursor() as cursor` runs an implicit `BEGIN TRANSACTION`
and [`__exit__`](https://stackoverflow.com/a/1984346) runs an implicit `COMMIT`.

## Getting familiar
I am aware downloads take forever. This is unfortunately beyond my control;
the Oracle server used by the school is just really slow,
it's not a network limitation. I am considering adding HTML files to source control.
In the meantime, run `make -n` to see what will happen when downloads finish.

There's a fairly close correspondence between CLI args and the python code. Examples:

- `gradeforge parse sections` calls the function `parse_sections` from module `parse.py`
- `gradeforge download bookstore` calls `get_bookstore` from `download.py`

The makefile is ludicrously hard to read.
I keep meaning to rewrite it but never get around to it.
Most of the makefile issues are also living in comments because I'm worried
how silly/confusing they'd look on Github.

## Makefile
In theory the makefile can be customized; in practice there are a lot of strings
hard-coded into the .py files. Change things at your own risk.
<small>(sorry)</small>

## Overview
Most of this is at the 'works on my machine' stage;
the CI builds are cached because downloads take so long,
so all we know is that parsing worked at *some* point.
I do plan to add make clean to the test,
which throws out the CSV files but keeps the downloads.

# Webpage
	/: redirects to search.html
	|
	| - index.html: redirects to search.html
	|
	| - search.html: what is currently index.html.
	|    client-side form to search for classes.
	|    submits to sections.html.
	|    MAY load auto-completion with AJAX
	|
	| - sections.html: takes query from search.html and returns all matching sections from database
	|    dynamically generated search page. MAY use AJAX instead of dynamic HTML to speed load times.
	|
	| - api/: unused directory used to organize the site
	  |    - all subdirectories MUST accept BOTH GET AND POST requests
	  |    - GET requests must be URL-encoded
	  |    - parameters are case-insensitive unless specified otherwise
	  |    - unrecognized parameters MUST be silently ignored
	  |    - parameters are used to filter results; without parameters, all results will be returned
	  |    - all subdirectories accept a special parameter 'column' used to determine the information returned;
	  |       the values accepted for 'column' are dependent on the SQL database implementation
	  |       as a special case, if 'column' is not given, all columns are returned
	  |    - multiple of any parameters are allowed; if given multiple, a logical OR is assumed
	  |       for examples of parameter values, see the SQL database.
	  |    - example: the request "GET /api/courses?subject=ACCT&subject=CSCE&credits=0"
	  |       is intepreted as "SELECT * FROM course WHERE subject IN ('ACCT', 'CSCE') AND credits = 0"
	  |
	  | - courses: takes the following parameters:
	  |     - department: 4-character abbreviation
	  |     - code
	  |     - title
	  |     - credits (>= 0); negative credits SHALL be assumed to be zero
	  |     - attribute
	  |     - level: one of (Undergraduate, Graduate, Medical, Law)
	  |
	  | - sections: takes the following parameters:
	  |   - uid: 5-digit number determined by the university, also known as CRN
	  |   - section: name of the section, for example H01 or Y01
	  |   - department: 4-character abbreviation
	  |   - code
	  |   - campus: one of (columbia, aiken, upstate)
	  |   - days: one of (M, T, W, R, F, S, U)
	  |   - semester: a 6-digit number in the form YYYYMM.
	  |      as a special case ONLY for years before 2014,
	  |      the month values '11' and '41' are treated as '01' and '08', respectively
	  |      the month values '01', '05', and '08' correspond to Spring, Summer, and Fall respectively; all other values, except where mentioned above, will be silently ignored.
	  |      as a special case, when ONLY invalid values for semester are passed, no results shall be returned
	  |
	  | - sql: takes raw SQL queries. the only parameter shall be 'query'.
	  |    MUST only accept queries which do not modify the database.
	  |    SHALL NOT accept the special parameter 'column'
	  |
	  | - department: takes NO parameters, excluding the special parameter 'column'
	  |
	  | - instructor: takes NO parameters, excluding the special parameter 'column'
