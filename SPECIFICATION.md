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
