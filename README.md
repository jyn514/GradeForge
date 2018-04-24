# USC-scraping
[my.sc.edu](https://ssb.onecarolina.sc.edu/BANP/bwskfcls.P_GetCrse) has an absolutely terrible web interface.
This is a repository to download courses for viewing offline.
Support is available for an SQL database.

# Requirements
- `python`
- `lxml` (`pip install lxml`)
- (optional) `cloudpickle` (`pip install pickle`)
- (optional) `sqlite` (`apt install sqlite3`)

# Usage
- Parsing catalogs: `./parse.py -C < file` or simply `make`
- Viewing: `./load.py < file`
- Parse and view: `./parse.py | tee filename`
- Help: `./parse.py -h`
- SQL database: `make sql`
