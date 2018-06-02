EXAMS := $(addsuffix .py,$(addprefix exams/,Fall-2016 Fall-2017 Fall-2018 Summer-2016 Summer-2017 Summer-2018 Spring-2017 Spring-2018))
OLD_GRADES := $(addsuffix .pdf,$(addprefix grades/,Fall-2008-Columbia Fall-2008-Aiken Fall-2008-Upstate Fall-2009-Columbia Fall-2009-Aiken Fall-2009-Upstate Fall-2010-Columbia Fall-2010-Aiken Fall-2010-Upstate Fall-2011-Columbia Fall-2011-Aiken Fall-2011-Upstate Fall-2012-Columbia Fall-2012-Aiken Fall-2012-Upstate Spring-2008-Columbia Spring-2008-Aiken Spring-2008-Upstate Spring-2009-Columbia Spring-2009-Aiken Spring-2009-Upstate Spring-2010-Columbia Spring-2010-Aiken Spring-2010-Upstate Spring-2011-Columbia Spring-2011-Aiken Spring-2011-Upstate Spring-2012-Columbia Spring-2012-Aiken Spring-2012-Upstate Spring-2013-Columbia Spring-2013-Aiken Spring-2013-Upstate))
NEW_GRADES := $(addsuffix .xlsx,$(addprefix grades/,Summer-2014 Summer-2015 Summer-2016 Summer-2017 Fall-2013 Fall-2014 Fall-2015 Fall-2016 Fall-2017 Spring-2014 Spring-2015 Spring-2016 Spring-2017))
DATA = .courses.data .sections.data .exams.data
MAKEFLAGS += -j4
GRADEFORGE = python -m gradeforge

.PHONY: sql
sql: classes.sql

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

exams/%.html: | exams
	$(GRADEFORGE) download \
	  --season `echo $* | cut -d- -f1` \
	  --year   `echo $* | cut -d- -f2`\
	  exam > $@
	$(call clean,$@)

exams/%.py: exams/%.html
	$(GRADEFORGE) parse exam $^ > $@

$(NEW_GRADES): | grades
	$(GRADEFORGE) download \
	  --season `echo $@ | cut -d. -f1 | cut -d/ -f2 | cut -d- -f1` \
	  --year `echo $@ | cut -d. -f1 | cut -d- -f2` \
	  grades > $@

$(OLD_GRADES): | grades
	$(GRADEFORGE) download \
	  --season `echo $@ | cut -d. -f1 | cut -d/ -f2 | cut -d- -f1` \
	  --year `echo $@ | cut -d. -f1 | cut -d- -f2` \
	  grades `echo $@ | cut -d. -f1 | cut -d- -f3` > $@

$(subst .xlsx,.csv,$(NEW_GRADES)): $$(subst .csv,.xlsx,$$@)
	xlsx2csv $^ > $@

$(subst .pdf,.txt,$(OLD_GRADES)): $$(subst .txt,.pdf,$$@)
	pdftotext -layout $^

$(subst .pdf,.csv,$(OLD_GRADES)): $$(subst .csv,.txt,$$@)
	$(GRADEFORGE) parse grades $^ > $@

# WARNING: since make allows only a single pattern to match, this unconditionally
# matches all html files in the directory. HOWEVER, the rule will fail for any
# filename not in the format books/<department>-<code>-<section>.html
books/%.html: | books
	$(GRADEFORGE) download bookstore \
		`echo $* | cut -d- -f1- --output-delimiter=' '` > $@

books/%.py: books/%.html
	$(GRADEFORGE) parse bookstore $^ > $@

.courses.data: gradeforge/parse.py webpages/catalog.html
	$(GRADEFORGE) parse catalog $(lastword $^) > $@

.sections.data: gradeforge/parse.py webpages/sections.html .exams.data
	$(GRADEFORGE) parse sections $(word 2,$^) > $@

# multiline variable: https://stackoverflow.com/a/649462
define command
import gradeforge
result = {}
for exam in '$(EXAMS)'.split(' '):
	key = gradeforge.utils.parse_semester(*exam.replace('exams/', '').replace('.py', '').split('-'))
	with open(exam) as f:
		result[key] = eval(f.read())
print(result)
endef
export command
.exams.data: $(EXAMS)
	echo "$$command"  # so you can see what's going on :)
	python -c "$$command" > $@

webpages exams grades books:
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
	$(RM) -r __pycache__
	$(RM) $(DATA) $(EXAMS) classes.sql *.pyc

.PHONY: clobber
clobber: clean
	$(RM) -r webpages exams

.PHONY: dist-clean
dist-clean: clobber
	git clean -dfx
