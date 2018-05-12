# USC-scraping
[my.sc.edu](https://ssb.onecarolina.sc.edu/BANP/bwskfcls.P_GetCrse) has an absolutely terrible web interface.
This is a repository to download courses for viewing offline.
Support is available for an SQL database.

## Requirements
- `python`
- `sqlite`
- `pip` and modules from `requirements.txt`

## Usage
- SQL database: `make`
- Web server: `make web` or `make server` (requires `flask`)
- Dump of everything: `make dump`

## Relevant Links
### Search Pages
- Bookstore:	http://sc.bncollege.com/webapp/wcs/stores/servlet/TBWizardView?catalogId=10001&langId=-1&storeId=10052
- Sections:	https://ssb.onecarolina.sc.edu/BANP/bwckschd.p_disp_dyn_sched
- Sign up for sections: https://ssb.onecarolina.sc.edu/BANP/bwskfreg.P_AltPin

### Result Examples
- Catalog:	https://ssb.onecarolina.sc.edu/BANP/bwckctlg.p_disp_course_detail?cat_term_in=201808&subj_code_in=BADM&crse_numb_in=B210
- Bulletin:	http://bulletin.sc.edu/preview_course.php?catoid=70&coid=85439
- Section:	https://ssb.onecarolina.sc.edu/BANP/bwckschd.p_disp_detail_sched?term_in=201808&crn_in=12566
- Exams:	https://www.sc.edu/about/offices_and_divisions/registrar/final_exams/final-exams-spring-2018.php

### External Links
- Login:	https://cas.auth.sc.edu/cas/login
- RateMyProfessor:	https://www.ratemyprofessors.com/search.jsp?queryBy=schoolId&schoolID=1309
- Schedule Planner:	https://sc.collegescheduler.com/entry
- Grade Spreads:	https://www.sc.edu/about/offices_and_divisions/registrar/toolbox/grade_processing/grade_spreads/index.php
