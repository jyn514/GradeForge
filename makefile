.PHONY: data
data: output.data

.PHONY: sql
sql: classes.sql

output.data: parse.py USC_all_courses.html
	./$<

classes.sql: ./sql_queries.py output.data
	./$< | sqlite $@
