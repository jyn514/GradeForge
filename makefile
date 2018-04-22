EXAMS := $(addprefix exams/,$(addsuffix .html,Fall-2016 Fall-2017 Fall-2018 Summer-2016 Summer-2017 Summer-2018 Spring-2016 Spring-2017 Spring-2018))

.PHONY: sql
sql: classes.sql data

.PHONY: data
data: .classes.data .sections.data

.classes.data: parse.py USC_all_courses.html
	./$< --catalog -s

.sections.data: parse.py sections.html .exams.data
	./$< --sections -s

.exams.data: parse.py $(EXAMS)
	./$< --exams -s

exams:
	mkdir exams

exams/%.html: post.py | exams
	./$< exams `echo $@ | cut -d. -f1 | cut -d/ -f2 | cut -d- -f1` \
	     `echo $@ | cut -d. -f1 | cut -d- -f2` > $@
	sed -i 's/\s\+$$//' $@  # lxml has trouble with too much whitespace

classes.sql: ./sql_queries.py data
	./$< | sqlite $@

.PHONY: clean
clean:
	$(RM) -r *.pyc __pycache__
