.PHONY: sql
sql: classes.sql data

.PHONY: data
data: .classes.data .sections.data

.classes.data: parse.py USC_all_courses.html
	./$< --catalog -s

.sections.data: parse.py sections.html .exams.data
	./$< --sections -s

.exams.data: parse.py
	./$< --exams -s

classes.sql: ./sql_queries.py data
	./$< | sqlite $@
