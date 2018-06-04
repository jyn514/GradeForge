# common tasks: sql/all, data, web, test, dump, clean

# NOTE: make does not allow spaces anywhere in filenames
# this is implicit to the tool itself and there are no workarounds that I am aware of

# input config
BOOK_DIR = books
EXAM_DIR = exams
GRADE_DIR = grades

# output config
BOOKSTORE_OUTPUT = books.csv

CATALOG_OUTPUT = catalog.csv
DEPARTMENT_OUTPUT = departments.csv

GRADES_OUTPUT = grades.csv

EXAM_OUTPUT = exams.csv

INSTRUCTOR_OUTPUT = instructors.csv
SECTION_OUTPUT = sections.csv
SEMESTER_OUTPUT = semesters.csv

# NOTE: because instructors, semesters, and departments are marked SECONDARY later,
# they don't need to be prereqs (because there's no rule for how to make them)
# BOOKSTORE_OUTPUT is not here because a) getting books for every section would
# get us IP-banned and b) cut doesn't work with newlines
DATA := $(CATALOG_OUTPUT) $(GRADES_OUTPUT) $(EXAM_OUTPUT) $(SECTION_OUTPUT)

GRADEFORGE = python -m gradeforge

# make config; don't change until you read man (1) make
# WARNING: changing -j4 to -j will spawn arbitrary processes and probably set your computer thrashing
MAKEFLAGS += -j4 --warn-undefined-variables
SHELL = sh

EXAMS := $(addsuffix .csv,$(addprefix exams/,Fall-2016 Fall-2017 Fall-2018 Summer-2016 Summer-2017 Summer-2018 Spring-2017 Spring-2018))

OLD_GRADES != for season in Fall Spring; do \
		for campus in Columbia Aiken Upstate; do \
			for year in `seq 2008 2013`; do \
				if ! ([ $$year = 2013 ] && [ $$season = Fall ]); then \
					printf "$(GRADE_DIR)/$$season-$$year-$$campus.pdf "; \
				fi \
			done; done; done;

NEW_GRADES := $(addsuffix .xlsx,$(addprefix $(GRADE_DIR)/,Summer-2014 Summer-2015 Summer-2016 Summer-2017 Fall-2013 Fall-2014 Fall-2015 Fall-2016 Fall-2017 Spring-2014 Spring-2015 Spring-2016 Spring-2017))

.PHONY: all
all: sql

.PHONY: sql
sql: classes.sql

.PHONY: data
data: $(DATA)

.PHONY: web server website
web server website: sql
	$(GRADEFORGE) web

.PHONY: dump
dump: sql
	$(GRADEFORGE) sql dump

.PHONY: test
test: sql
	pytest --pyargs gradeforge
	pylint --extension-pkg-whitelist=lxml gradeforge | tee pylint.txt
	if grep '^E:' pylint.txt; then exit 1; fi

classes.sql: gradeforge/sql.py $(DATA)
	$(RM) $@
	PYTHONIOENCODING=utf-8 $(GRADEFORGE) sql create

.SECONDEXPANSION:
.PHONY: catalog sections
catalog sections: webpages/$$@.html

.DELETE_ON_ERROR:
webpages/%.html: | webpages
	$(GRADEFORGE) download $* > $@
	$(call clean,$@)

$(EXAM_DIR)/%.html: | $(EXAM_DIR)
	$(GRADEFORGE) download \
	  --season `echo $* | cut -d- -f1` \
	  --year   `echo $* | cut -d- -f2`\
	  exam > $@
	$(call clean,$@)

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

sed = s/\([A-DF]+?\)_GF/\1/g; s/COURSE_SECTION/SECTION/; s/_NUMBER//g; \
      s/No ?Grade/No Grade/; s/Num Grades Posted/TOTAL/; \
      s/Incomplete/INCOMPLETE/i; s/SUBJECT/DEPARTMENT/
$(subst .xlsx,.csv,$(NEW_GRADES)): $$(subst .csv,.xlsx,$$@)
	xlsx2csv $^ $@
	sed -i '$(sed)' $@

$(subst .pdf,.txt,$(OLD_GRADES)): $$(subst .txt,.pdf,$$@)
	pdftotext -layout $^

$(subst .pdf,.csv,$(OLD_GRADES)): $$(subst .csv,.txt,$$@)
	$(GRADEFORGE) parse grades $^ $@

$(GRADES_OUTPUT): $(subst .pdf,.csv,$(OLD_GRADES)) $(subst .xlsx,.csv,$(NEW_GRADES))
	files=$$(echo $(GRADE_DIR)/*.csv); \
	python -c "from gradeforge.parse import combine_grades; \
	combine_grades('$@', *'$$(echo $$files)'.split())"


# WARNING: since make allows only a single pattern to match, this unconditionally
# matches all html files in the directory. HOWEVER, the rule will fail for any
# filename not in the format books/<department>-<code>-<section>.html
books/%.html: | books
	$(GRADEFORGE) download bookstore \
		`echo $* | cut -d- -f1- --output-delimiter=' '` > $@

.SECONDARY: $(DEPARTMENT_OUTPUT)
$(CATALOG_OUTPUT): webpages/catalog.html
	$(GRADEFORGE) parse catalog --department-output $(DEPARTMENT_OUTPUT) \
				    $^ $@

.SECONDARY: $(INSTRUCTOR_OUTPUT) $(SEMESTER_OUTPUT)
$(SECTION_OUTPUT): webpages/sections.html
	$(GRADEFORGE) parse sections --instructor-output $(INSTRUCTOR_OUTPUT) \
				     --semester-output $(SEMESTER_OUTPUT) \
				     $^ $@
# TODO: make this concurrent
$(EXAM_OUTPUT): $(EXAMS)
	head -1 $< > $@  # headers
	for exam in $^; do tail -n+2 $$exam >> $@; done

webpages $(EXAM_DIR) $(GRADE_DIR) books:
	mkdir $@

# lxml has trouble with too much whitespace
define clean =
	if grep '404 page not found' $1; then \
		echo file "'$1'" gave a 404 not found; \
		rm $1; \
		exit 999; \
	fi
	sed -i 's/\s\+$$//' $1
endef

.PHONY: clean
clean:
	$(RM) $(DATA) $(EXAMS) classes.sql *.pyc

.PHONY: clobber
clobber: clean
	$(RM) -r webpages $(EXAM_DIR) __pycache__ gradeforge/__pycache__

.PHONY: dist-clean
# careful with this, it's a good way to lose anything you haven't committed
dist-clean: clobber
	git clean -dfx
