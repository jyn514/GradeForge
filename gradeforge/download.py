#!/usr/bin/env python3

'''Network-based querires; GETs and POSTs'''

from datetime import date
from os.path import exists
from os import unlink
from logging import getLogger

from requests import get, post
from selenium.common.exceptions import NoSuchElementException

from gradeforge.utils import allowed, parse_semester, get_season, b_and_n_semester, DEFAULT_DATABASE

LOGGER = getLogger(__name__)

def get_sections(department='%', semester='201808', campus='%', number='', title='',
                 min_credits=0, max_credits='', level='%', term='%', times='%',
                 location='%', start_hour=0, start_minute=0, end_hour=0,
                 end_minute=0, days='dummy'):
    '''str -> str (HTML)
    Return the unparsed webpage corresponding to the courses selected'''
    # TODO: term is a nightmare, replace it with [first_half, second_half, all]
    if department == '%':  # all sections
        department = allowed['department']

    if campus == '%':
        campus = allowed['campus']

    params = locals()
    coursesite = 'https://ssb.onecarolina.sc.edu/BANP/bwckschd.p_get_crse_unsec'

    for p in params:
        # if p not in allowed, assume arbitrary input acceptable
        # TODO: allow partial subsets
        if (params[p] != 'dummy' and p in allowed and params[p] not in allowed[p]
                and params[p] != allowed[p]):
            raise ValueError("%s '%s' not in %s" % (p, params[p], allowed[p]))

    ampm = (divmod(start_hour, 12), divmod(end_hour, 12))
    data = {"BEGIN_AP": ('p' if ampm[0][0] else 'a'),
            "BEGIN_HH": ampm[0][1],
            "BEGIN_MI": start_minute,
            "END_AP": ('p' if ampm[1][0] else 'a'),
            "END_HH": ampm[1][1],
            "END_MI": end_minute,
            "SEL_ATTR": ('dummy', location),
            "SEL_CAMP": ('dummy', campus),
            "SEL_CRSE": number,
            "SEL_DAY": days,
            "SEL_FROM_CRED": min_credits,
            "SEL_TO_CRED": max_credits,
            "SEL_INSM": 'dummy', "SEL_INSTR": 'dummy', "SEL_SCHD": "dummy",
            "SEL_LEVL": ('dummy', level),
            "SEL_PTRM": ('dummy', term),
            "SEL_SESS": ('dummy', times),
            "SEL_SUBJ": ('dummy', department),
            "SEL_TITLE": title,
            "TERM_IN": ('dummy', semester)}

    return post(coursesite, data=data).text


def make_driver():
    '''Make a webdriver for selenium with appropriate options'''
    from selenium.webdriver import Chrome
    from selenium.webdriver.chrome.options import Options
    # https://stackoverflow.com/a/49582462
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = Chrome(chrome_options=options)
    driver.implicitly_wait(4)  # timeout for page to be deobfuscated; this was with trial and error
    return driver


def get_bookstore(semester, department, number, section, driver=None):
    '''The bookstore page is a hot mess of obfuscated javascript.
    We use selenium to deobfuscate the javascript, then parse the resulting HTML'''
    if driver is None:
        driver = make_driver()
    semester = str(semester)
    if len(semester) != 3:
        semester = b_and_n_semester(semester)

    xml = r'''<textbookorder><courses>\
                <course dept=\'%s\' num=\'%s\' sect=\'%s\' term=\'%s\' />\
              </courses></textbookorder>'''
    xml %= department, number, section, semester

    js = '''
    document.body.innerHTML += '\
        <form id="form" action="https://secure.bncollege.com/webapp/wcs/stores/servlet/TBListView" method="post">\
          <input name="storeId" value="10052">\
          <input name="courseXml" value="%s">\
        </form>';
    document.getElementById("form").submit();
    ''' % xml

    driver.execute_script(js)
    try:
        driver.find_element_by_id('courseListForm')  # this is the implicit wait
    except NoSuchElementException:
        if 'COURSE MATERIALS SELECTION PENDING' in driver.page_source:
            raise ValueError("No textbooks available for %s"
                             % ' '.join([semester, department, number, section]))
        raise
    return driver.page_source


def get_catalog(department='%', semester=201808):
    '''Return catalog courses from the given semester'''
    if department == '%':
        department = allowed['department']
    else:
        department = [department]

    base_url = 'https://ssb.onecarolina.sc.edu/BANP/bwckctlg.p_display_courses'
    data = {"term_in": semester,
            'call_proc_in': 'bwckctlg.p_disp_dyn_ctlg',
            'sel_subj': ('dummy', tuple(department)),
            'sel_levl': ('dummy', '%'),
            'sel_schd': ('dummy', '%'),
            'sel_coll': ('dummy', '%'),
            'sel_divs': 'dummy',
            'sel_dept': ('dummy', '%'),
            'sel_attr': ('dummy', '%'),
            'sel_crse_strt': '',
            'sel_crse_end': '',
            'sel_title': '',
            'sel_from_cred': '',
            'sel_to_cred': ''}
    return post(base_url, data=data).text


def get_exam(year, season):
    '''str -> str (HTML)
    Return content of calendar corresponding to given semester. Example:
    https://www.sc.edu/about/offices_and_divisions/registrar/final_exams/final-exams-spring-2018.php'''
    if season not in ('fall', 'summer', 'spring'):
        season = get_season(parse_semester(season)).lower()
    base_url = 'https://www.sc.edu/about/offices_and_divisions/registrar/final_exams'
    return get('%s/final-exams-%s-%s.php' % (base_url, season, year)).text


def get_grades(year, season, campus=None):
    campus = str(campus).lower()
    semester = parse_semester(season, year)
    base_url = 'https://www.sc.edu/about/offices_and_divisions/registrar/documents/grade_spreads'

    too_soon = "Ha. Ha ha. You think the university is that fast."
    if year == date.today().year:
        if int(semester[-1]) >= date.today().month:
            raise ValueError("Can't download grades from the future")
        elif int(semester[-1]) + 5 >= date.today().month:
            raise ValueError(too_soon)
    # TODO: check when this actually is
    elif year == date.today().year - 1 and semester[-1] == '8' and date.today().month < 2:
        raise ValueError(too_soon)

    if year >= 2014 or semester == '201341':  # fall 2013
        ext = 'xlsx'
    elif campus == 'none':
        raise ValueError("grade spreads prior to fall 2013 are seperated by campus")
    elif season not in ('fall', 'spring'):
        raise ValueError("No data for summer prior to 2014 (given '%s')" % season)
    elif year < 2008:
        raise ValueError("No data for year " + year)
    else:
        ext = 'pdf'
        semester += '_' + campus
    url = '%s/%s_grade_spread_report.%s' % (base_url, semester, ext)
    return get(url).content  # NOTE: content is binary; text is encoded

def get_all_books(semester='201805'):
    from sqlite3 import connect
    query = '''SELECT department, code, section
               FROM section INNER JOIN term ON term = term.id
               WHERE semester = ?'''
    with connect(DEFAULT_DATABASE) as database:
        result = database.execute(query, [semester]).fetchall()
    driver = make_driver()
    try:
        for section in result:
            output = "books/%s-%s-%s-%s.html" % (semester, *section)
            if not exists(output):
                with open(output, 'w') as f:
                    try:
                        f.write(get_bookstore(semester, *section, driver=driver))
                        LOGGER.info("downloaded %s", f.name)
                    except Exception as e:
                        LOGGER.warning("Info for %s not available, deleting: %s", semester + ' '.join(section), e)
                        unlink(output)
    finally:
        driver.quit()
