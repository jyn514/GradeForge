EXAMS := $(addprefix exams/,$(addsuffix .html,Fall-2016 Fall-2017 Fall-2018 Summer-2016 Summer-2017 Summer-2018 Spring-2016 Spring-2017 Spring-2018))

.PHONY: sql
sql: classes.sql

.PHONY: data
data: .classes.data .sections.data

webpages:
	mkdir webpages

define clean =
	sed -i 's/\s\+$$//' $1  # lxml has trouble with too much whitespace
endef

webpages/USC_all_courses.html: post.py webpages
	./$< courses > $@
	$(call clean,$@)

webpages/USC_all_sections.html: post.py webpages
	./$< sections % > $@
	$(call clean,$@)

webpages/%: webpages

exams:
	mkdir exams

exams/%.html: post.py | exams
	./$< exams `echo $@ | cut -d. -f1 | cut -d/ -f2 | cut -d- -f1` \
	     `echo $@ | cut -d. -f1 | cut -d- -f2` > $@
	$(call clean $@)

.classes.data: parse.py webpages/USC_all_courses.html
	./$< --catalog < webpages/USC_all_courses.html > $@

.sections.data: parse.py webpages/USC_all_sections.html # .exams.data
	./$< --sections < webpages/USC_all_sections.html > $@

.exams.data: parse.py $(EXAMS)
	./$< --exams

classes.sql: sql_queries.py data
	./$< | sqlite $@

.PHONY: clean
clean:
	$(RM) -r *.pyc __pycache__
