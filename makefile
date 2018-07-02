# common tasks: sql/all, data, web, test, dump, clean

# NOTE: make does not allow spaces anywhere in filenames
# this is implicit to the tool itself and there are no workarounds that I am aware of

# input config
BOOK_DIR = books
EXAM_DIR = exams
GRADE_DIR = grades
SECTION_DIR = sections
CATALOG_DIR = catalogs

# output config
BOOKSTORE_OUTPUT = books.csv

CATALOG_OUTPUT = catalog.csv
DEPARTMENT_OUTPUT = departments.csv

GRADES_OUTPUT = grades.csv

EXAM_OUTPUT = exams.csv

INSTRUCTOR_OUTPUT = instructors.csv
SECTION_OUTPUT = sections.csv
TERM_OUTPUT = terms.csv


# make config; don't change until you read man (1) make
# WARNING: changing -j4 to -j will spawn arbitrary processes and probably set your computer thrashing
MAKEFLAGS += -j4 --warn-undefined-variables
SHELL = sh

# data variables
GRADEFORGE = python -m gradeforge

# NOTE: BOOKSTORE_OUTPUT is not here because a) getting books for every section would
# get us IP-banned and b) cut doesn't work with newlines
DATA := $(CATALOG_OUTPUT) $(GRADES_OUTPUT) $(EXAM_OUTPUT) $(SECTION_OUTPUT) $(INSTRUCTOR_OUTPUT) $(TERM_OUTPUT) $(DEPARTMENT_OUTPUT)

EXAMS := $(addsuffix .csv,$(addprefix exams/,Fall-2016 Fall-2017 Fall-2018 Summer-2016 Summer-2017 Summer-2018 Spring-2017 Spring-2018))

OLD_GRADES != for season in Fall Spring; do \
		for campus in Columbia Aiken Upstate; do \
			for year in `seq 2008 2013`; do \
				if ! ([ $$year = 2013 ] && [ $$season = Fall ]); then \
					printf "$(GRADE_DIR)/$$season-$$year-$$campus.pdf "; \
				fi \
			done; done; done

NEW_GRADES := $(addsuffix .xlsx,$(addprefix $(GRADE_DIR)/,Summer-2014 Summer-2015 Summer-2016 Summer-2017 Fall-2013 Fall-2014 Fall-2015 Fall-2016 Fall-2017 Spring-2014 Spring-2015 Spring-2016 Spring-2017))

SECTIONS := $(addsuffix .csv,$(addprefix $(SECTION_DIR)/,Fall-2013 Fall-2014 Fall-2015 Fall-2016 Fall-2017 Summer-2014 Summer-2015 Summer-2016 Summer-2017 Summer-2018 Spring-2014 Spring-2015 Spring-2016 Spring-2017 Spring-2018))

.PHONY: help
help tasks:
	@# grep doesn't respect capturing groups; we use sed instead
	@# additionally, we abuse echo to treat newlines as spaces
	@echo .PHONY: $$(sed -n -e 's/^\.PHONY: \(.*\)/\1/p' makefile)
	@echo
	@echo PATTERNS: $$(sed -n -e 's/^\([^%]*%[^ ]*\):.*/\1/p' makefile)
	@echo
	@echo DERIVED: $$(sed -n -e 's/^\($$(subst .*)\):.*/\1/p' makefile)

.PHONY: help-tasks
help-tasks:
	@# modified from https://stackoverflow.com/a/26339924
	$(MAKE) -npRr | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$$$1 !~ "^[#.]") {print $$$$1}}' | grep --color=auto -v "^[#`printf '\t'`]" | sed 's/:$$//'

.PHONY: help-recipies
help-recipies:
	$(MAKE) -npRr | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$$$1 !~ "^[#.]") {print $$$$1}}' | grep --color=auto -v "^#"

.DEFAULT_GOAL = all
.PHONY: all
all: sql

.PHONY: sql
sql: classes.sql

.PHONY: data
data: $(DATA)

.PHONY: all-grades all-sections
all-grades: $(GRADES_OUTPUT)
all-sections: $(SECTIONS)

.PHONY: web server website
web server website: sql
	PYTHONPATH=. $(GRADEFORGE) web

.PHONY: dump
dump: sql
	$(GRADEFORGE) sql dump

.PHONY: test
test: sql | images
	# these are ordered from least to most picky
	python -c 'from gradeforge.grades import png_for; png_for("NURS", "U497", "PC8", 201705)'
	pytest --pyargs gradeforge
	pylint --extension-pkg-whitelist=lxml gradeforge | tee pylint.txt
	if grep '^E:' pylint.txt; then exit 1; fi
	gradeforge/test/match.py gradeforge/**.py

classes.sql: $(DATA)
	$(RM) $@
	$(GRADEFORGE) sql create

.PHONY: catalog
catalog: webpages/catalog.html

# lxml has trouble with too much whitespace
define clean =
	if grep '404 page not found' $1; then \
		echo file "'$1'" gave a 404 not found; \
		$(RM) $1; \
		exit 999; \
	fi
	sed -i 's/\s\+$$//' $1
endef

.DELETE_ON_ERROR:
webpages/catalog.html: | webpages
	$(GRADEFORGE) download catalog > $@
	$(call clean,$@)

$(EXAM_DIR)/%.html: | $(EXAM_DIR)
	$(GRADEFORGE) download \
	  --season `echo $* | cut -d- -f1` \
	  --year   `echo $* | cut -d- -f2`\
	  exam > $@
	$(call clean,$@)

$(INSTRUCTOR_OUTPUT): $(SECTIONS)
	$(GRADEFORGE) combine instructors $(subst .csv,.instructors.csv,$^) > $@

$(TERM_OUTPUT): $(SECTIONS)
	$(GRADEFORGE) combine terms $(subst .csv,.terms.csv,$^) > $@

$(DEPARTMENT_OUTPUT): $(CATALOG_OUTPUT)
	$(GRADEFORGE) combine departments $(subst .csv,.departments.csv,$^) > $@

$(GRADES_OUTPUT): $(subst .pdf,.csv,$(OLD_GRADES)) $(subst .xlsx,.csv,$(NEW_GRADES))
	$(GRADEFORGE) combine grades $^ > $@

.SECONDEXPANSION:
$(EXAMS): $$(subst .csv,.html, $$@)
	$(GRADEFORGE) parse exam $^ $@

$(NEW_GRADES): | $(GRADE_DIR)
	$(GRADEFORGE) download \
	  --season `echo $@ | cut -d. -f1 | cut -d/ -f2 | cut -d- -f1` \
	  --year `echo $@ | cut -d. -f1 | cut -d- -f2` \
	  grades > $@

$(OLD_GRADES): | $(GRADE_DIR)
	$(GRADEFORGE) download \
	  --season `echo $@ | cut -d. -f1 | cut -d/ -f2 | cut -d- -f1` \
	  --year `echo $@ | cut -d. -f1 | cut -d- -f2` \
	  grades `echo $@ | cut -d. -f1 | cut -d- -f3` > $@

cleanup = 1 s/\([A-DF]+?\)_GF/\1/g; 1 s/COURSE_SECTION/SECTION/; 1 s/_NUMBER//g; \
      1 s/No ?Grade/No Grade/; 1 s/Num Grades Posted/TOTAL/; \
      1 s/Incomplete/INCOMPLETE/i; 1 s/SUBJECT/DEPARTMENT/; 1 s/COURSE/CODE/
$(subst .xlsx,.csv,$(NEW_GRADES)): $$(subst .csv,.xlsx,$$@)
	xlsx2csv $^ $@
	sed -i '$(cleanup)' $@
	$(eval SEMESTER := $(shell python -c 'from gradeforge.utils import parse_semester; \
					      tmp = "$@".split("/")[1].split(".")[0].split("-"); \
					      print(parse_semester(*tmp))'))
	sed -i '1 s/^/SEMESTER,CAMPUS,/' $@
	sed -i "2,$$ s/^/$(SEMESTER),,/" $@

$(subst .pdf,.txt,$(OLD_GRADES)): $$(subst .txt,.pdf,$$@)
	pdftotext -layout $^

$(subst .pdf,.csv,$(OLD_GRADES)): $$(subst .csv,.txt,$$@)
	$(GRADEFORGE) parse grades $^ $@



# WARNING: since make allows only a single pattern to match, this unconditionally
# matches all html files in the directory. HOWEVER, the rule will fail for any
# filename not in the format <department>-<code>-<section>.html
.PRECIOUS: $(BOOK_DIR)/%.html
$(BOOK_DIR)/%.html: | $(BOOK_DIR)
	$(GRADEFORGE) download bookstore \
		`echo $* | cut -d- -f1- --output-delimiter=' '` > $@
	if grep 'Textbook Not Registered' $@; then exit 1; fi

$(BOOK_DIR)/%.csv: $$(subst .csv,.html,$$@)
	$(GRADEFORGE) parse bookstore $^ $@

$(CATALOG_OUTPUT): webpages/catalog.html
	$(GRADEFORGE) parse catalog --department-output $(subst .csv,.departments.csv,$@) $^ $@

$(SECTIONS): $$(subst .csv,.html,$$@)
	$(GRADEFORGE) parse sections --instructor-output $(subst .csv,.instructors.csv,$@) \
				     --term-output $(subst .csv,.terms.csv,$@) \
				     $^ $@

$(subst .csv,.html.bak,$(SECTIONS)): | $(SECTION_DIR)
	$(eval tmp := $(shell echo $@ | cut -d/ -f2 | cut -d. -f1 | cut -d- -f1-2 --output-delimiter=' '))
	# keep original because we'll be changing it in a second
	$(GRADEFORGE) download --season $(firstword $(tmp)) --year $(lastword $(tmp)) sections > $@


$(subst .csv,.html,$(SECTIONS)): $$(addsuffix .bak,$$@)
	# 1. change two opening tags to single closed tag
	# 2. the school seems to think <p> is the same as <br>
	sed 's#<b>\(.*\)<b>#<b>\1</b>#; s/ <p>$$//' $^ > $@
	# required for Summer 2016, others *might* work but less effort this way
	# note that tidy returns 1 on warnings, and the html always gives warnings
	tidy -modify -f /dev/null $@ || if [ $$? -ne 1 ]; then exit $$?; fi

# TODO: this is wrong, it's just convenient
$(SECTION_OUTPUT): $(SECTIONS) | $(TERM_OUTPUT)
$(EXAM_OUTPUT): $(EXAMS)

$(SECTION_OUTPUT) $(EXAM_OUTPUT):
	head -1 $< > $@  # headers
	for exam in $^; do tail -n+2 $$exam >> $@; done

# TODO: the HTML needs to be rate limited
.PHONY: all-books
all-books: classes.sql | $(BOOK_DIR)
	for semester in `sqlite3 $^ "select distinct semester from section;"`; do \
		python -c "from gradeforge.download import get_all_books; \
			   get_all_books($$semester)"; done

# the reason this calls make recursively is because it's really a collection of
# dependencies, same as $(EXAMS), but we don't know the sections until after
# we've made the database.
# TODO: can be parallel
.PHONY: bookstore
bookstore: classes.sql all-books
	# sqlite uses '||' for string concatenation for some reason
	for f in `sqlite3 $^ "select '$(BOOK_DIR)/' || semester || '-' || department || '-' || code || '-' || section || '.csv' from section"`; do $(MAKE) $$f; done;

$(EXAM_DIR) $(GRADE_DIR) $(BOOK_DIR) $(SECTION_DIR) $(CATALOG_DIR) images webpages:
	mkdir $@



.PHONY: clean
clean:
	$(RM) $(DATA) $(EXAMS) $(subst .pdf,.csv,$(OLD_GRADES)) $(subst .xlsx,.csv,$(NEW_GRADES)) $(SECTION_DIR)/*.csv classes.sql catalog.departments.csv

.PHONY: clobber
clobber: clean
	$(RM) -r webpages $(EXAM_DIR) $(GRADE_DIR) $(BOOK_DIR) __pycache__ gradeforge/__pycache__ *.pyc

.PHONY: dist-clean
# careful with this, it's a good way to lose anything you haven't committed
dist-clean: clobber
	git clean -dfx
