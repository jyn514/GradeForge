EXAMS := $(addprefix exams/,$(addsuffix .html,Fall-2016 Fall-2017 Fall-2018 Summer-2016 Summer-2017 Summer-2018 Spring-2017 Spring-2018))
DATA = .courses.data .sections.data

.PHONY: sql
sql: classes.sql

.PHONY: web server website
web server website: sql
	flask/app.py

.PHONY: dump
dump: sql
	src/query_sql.py

.PHONY: test
test: sql
	pytest


# lxml has trouble with too much whitespace
define clean =
	if grep '404 page not found' $1; then \
		echo file "'$1'" gave a 404 not found; \
		rm $1; \
		exit 999; \
	fi
	sed -i 's/\s\+$$//' $1
endef

.SECONDEXPANSION:
.PHONY: courses sections
courses sections: webpages/USC_all_$$@.html

webpages:
	mkdir webpages

webpages/USC_all_%.html: | src/post.py webpages
	./$(firstword $|) $(subst .html,,$(subst webpages/USC_all_,,$@)) > $@
	$(call clean,$@)

exams:
	mkdir exams

exams/%.html: | src/post.py exams
	./$| `echo $@ | cut -d. -f1 | cut -d/ -f2 | cut -d- -f1` \
	     `echo $@ | cut -d. -f1 | cut -d- -f2` > $@
	$(call clean,$@)

.courses.data: src/parse.py webpages/USC_all_courses.html
	./$< --catalog < $(lastword $^) > $@ || { $(RM) $@; exit 999; }

.sections.data: src/parse.py webpages/USC_all_sections.html .exams.data
	./$< --sections < $(word 2,$^) > $@ || { $(RM) $@; exit 999; }

.exams.data: src/parse.py $(EXAMS)
	./$< --exams > $@ || { $(RM) $@; exit 999; }

classes.sql: src/create_sql.py $(DATA)
	$(RM) $@
	# python2 compat
	PYTHONIOENCODING=utf-8 ./$<

.PHONY: clean
clean:
	$(RM) -r __pycache__
	$(RM) $(DATA) classes.sql *.pyc

.PHONY: clobber
clobber: clean
	$(RM) -r webpages exams

.PHONY: dist-clean
dist-clean: clobber
	git clean -dfx
