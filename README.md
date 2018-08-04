# USC-scraping
[![Build Status](https://travis-ci.org/jyn514/GradeForge.svg?branch=dev)](https://travis-ci.org/jyn514/GradeForge)

[my.sc.edu](https://ssb.onecarolina.sc.edu/BANP/bwskfcls.P_GetCrse) has an
absolutely terrible web interface. This is a repository to download courses for
viewing offline. Support is available for an SQL database. Work on a web
interface is [ongoing](https://github.com/jyn514/GradeForge/tree/frontend).

## Requirements
- GNU `make` (`gmake` for BSD users)
- `python3`
- `pip` and modules from `requirements.txt`. if not using a packaged version of `lxml`, you will need
	- a working C compiler
	- the `python-dev` library
	- `libxml2-dev`
	- `libxslt-dev`
- [`pdftotext`](https://poppler.freedesktop.org/) (part of `poppler-utils`)
- [`chromedriver`](http://chromedriver.chromium.org/)
- [`tidy`](http://www.html-tidy.org/)

## Goals
### Long-Term
- have all the information needed or useful to register on one page. this includes
	- RateMyProfessor
	- past grade distributions
	- schedule planner or an equivalent
	- degreeworks
	- required textbooks

### Short-Term
- parse_bookstore has yet to be implemented either in the makefile or in `parse sections`
- all the `parse` functions should take a boolean `create`
	- if true, assert the output file does not exist
	- if false, don't write headers
- the submit button for `index.html` is broken
- add rules in the makefile for courses in past years.

### Non-Goals
- registering automatically. this would require storing the *university*
usernames and passwords of anyone who used the service. this is acceptable
for personal use (and feel free to do this, `login.py` is file you're looking
for), but absolutely unacceptable for other users.


## Usage
- SQL database: `make`
- Web server: `make web` or `make server`
- Dump of everything: `make dump`
- Unit tests (the few we have): `make test`

## Development
### Setting up
1. `git clone https://github.com/jyn514/gradeforge` && cd gradeforge
2. ln -s ../../scripts/pre-commit .git/hooks
3. (optional) run `make data` to pre-populate the HTML

### Bugs
- `parse_section` does not parse days met properly if the times are different
on different days. run `make` on branch `broken` for an example.
- course['attributes'] is a tuple on `broken`; this crashes `create_sql.py`

### Notes
- please do not try to use gradeforge directly for parsing,
the dependencies will drive you mad. use the beautiful makefile instead.
- data for grades is available back until 2008, but data for sections is only available until 2013.
- columns in grades ending in `_GF` stand for 'Grade Forgiveness'
- png_for won't work for this semester (because the grades haven't been published).
  this sounds stupid but I was wracking my brains trying to figure out why it was broken.

### Types
- semester: a date in YYYYMM format, where MM is one of 01, 05, 08 and YYYY >= 2008; for example, 201608
- department: a department name which matches the regex [A-Z]{4}; for example, CSCE
- code: a class name which matches the regex [A-Z]?[0-9]{3}; for example, 145
- section: a section identifier which identifies an instance of a class; for example 001
- uid: a section identifier which is unique within a semester; matches the regex [0-9]{5}. for example, 84495

## Relevant Links
### Search Pages
- [Bookstore](http://sc.bncollege.com/webapp/wcs/stores/servlet/TBWizardView?catalogId=10001&langId=-1&storeId=10052)
- [Sections](https://ssb.onecarolina.sc.edu/BANP/bwckschd.p_disp_dyn_sched)
- [Sign up for sections](https://ssb.onecarolina.sc.edu/BANP/bwskfreg.P_AltPin)

### Result Examples
- [Catalog](https://ssb.onecarolina.sc.edu/BANP/bwckctlg.p_disp_course_detail?cat_term_in=201808&subj_code_in=BADM&crse_numb_in=B210)
- [Bulletin](http://bulletin.sc.edu/preview_course.php?catoid=70&coid=85439)
- [Section](https://ssb.onecarolina.sc.edu/BANP/bwckschd.p_disp_detail_sched?term_in=201808&crn_in=12566)
- [Exams](https://www.sc.edu/about/offices_and_divisions/registrar/final_exams/final-exams-spring-2018.php)

### External Links
- [Login](https://cas.auth.sc.edu/cas/login)
- [Semester starts and ends](https://my.sc.edu/codes/partofterms/list)
- [RateMyProfessor](https://www.ratemyprofessors.com/search.jsp?queryBy=schoolId&schoolID=1309)
- [Schedule Planner](https://sc.collegescheduler.com/entry)
- [Grade Spreads](https://www.sc.edu/about/offices_and_divisions/registrar/toolbox/grade_processing/grade_spreads/index.php)
- [Grade Abbreviations](https://www.sc.edu/about/offices_and_divisions/registrar/transcripts_and_records/grade_point_scale/index.php)
