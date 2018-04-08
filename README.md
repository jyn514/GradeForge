# USC-scraping
[my.sc.edu](https://ssb.onecarolina.sc.edu/BANP/bwskfcls.P_GetCrse) has an absolutely terrible web interface.
This is a repository to download courses for viewing offline.
~~I plan to eventually add an SQL database.~~ Added.

# Requirements
- `python2`
- `lxml`
- (optional) `cloudpickle`
- (optional) `sqlite`

# Usage
- Parsing: `./parse.py [filename]` or simply `make`
- Viewing: `./parse.py -l`
- Parse and view: `./parse.py -v`
- Help: `./parse.py -h`
- SQL database: `make sql`
