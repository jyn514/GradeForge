SQL != which sqlite 2>/dev/null || which sqlite3
EXAMS := $(addprefix exams/,$(addsuffix .html,Fall-2016 Fall-2017 Fall-2018 Summer-2016 Summer-2017 Summer-2018 Spring-2016 Spring-2017 Spring-2018))
DATA = .courses.data .sections.data

.PHONY: sql
sql: classes.sql

webpages:
	mkdir webpages

# lxml has trouble with too much whitespace
define clean =
	sed -i 's/\s\+$$//' $1
endef

.SECONDEXPANSION:
.PHONY: courses sections
courses sections: webpages/USC_all_$$@.html

webpages/USC_all_%.html: | post.py webpages
	./$(firstword $|) $(subst .html,,$(subst webpages/USC_all_,,$@)) > $@
	$(call clean,$@)

webpages/%: | webpages

exams:
	mkdir exams

exams/%.html: | post.py exams
	./$| `echo $@ | cut -d. -f1 | cut -d/ -f2 | cut -d- -f1` \
	     `echo $@ | cut -d. -f1 | cut -d- -f2` > $@
	$(call clean $@)

.courses.data: webpages/USC_all_courses.html | parse.py
	./$| --catalog < $< > $@ || { rm -f $@; exit 999; }

.sections.data: webpages/USC_all_sections.html | parse.py # .exams.data
	./$| --sections < $< > $@ || { rm -f $@; exit 999; }

.exams.data: $(EXAMS) | parse.py
	./$| --exams

classes.sql: create_sql.py $(DATA)
	$(RM) $@
	PYTHONIOENCODING=utf-8 ./$< | $(SQL) $@

.PHONY: clean
clean:
	$(RM) -r *.pyc __pycache__

.PHONY: clobber
clobber: clean
	$(RM) -r webpages
	$(RM) $(DATA) classes.sql

.PHONY: dist-clean
dist-clean: clobber
	git clean -dfx
