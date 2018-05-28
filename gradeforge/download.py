#!/usr/bin/env python3

'''Network-based querires; GETs and POSTs'''

from datetime import date

from requests import get, post

from gradeforge.utils import allowed, parse_semester, get_season

def get_sections(department='%', semester='201808', campus='COL', number='', title='',
                 min_credits=0, max_credits='', level='%', term='30', times='%',
                 location='%', start_hour=0, start_minute=0, end_hour=0,
                 end_minute=0, days='dummy'):
    '''str -> str (HTML)
    Return the unparsed webpage corresponding to the courses selected'''
    # TODO: term is a nightmare, replace it with [first_half, second_half, all]
    semester = utils.parse_semester(semester)
    if department == '%':  # all sections
        department = allowed['department']

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

'''This doesn't work because of the malicious javascript.
def get_bookstore(semester, department, number, section):
    '(str, str, int, str) -> str (HTML)
    Return content of bookstore page corresponding to class
    Note that this cannot be a link in utils because it requires a POST'
    base_url = 'https://secure.bncollege.com/webapp/wcs/stores/servlet/TBListView'
    data = {'storeId': '10052',
            'courseXml': "<textbookorder><courses><course dept='%s' num='%s' sect='%s' term='%s' /></courses></textbookorder>"
                         % (department, number, section, utils.b_and_n_semester(semester))}
    return post(base_url, data=data).text
'''

def get_bookstore(semester, department, number, section, driver=None):
    '''Example: https://ssb.onecarolina.sc.edu/BANP/bwckbook.site?p_term_in=201808&p_subj_in=ACCT&p_crse_numb_in=222&p_seq_in=001'''
    from time import sleep

    if driver is None:
        from selenium.webdriver import Chrome
        from selenium.webdriver.chrome.options import Options
        # https://stackoverflow.com/a/49582462
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        driver = Chrome(chrome_options=options)
        driver.implicitly_wait(10)  # timeout for page to be deobfuscated

    base_url = 'https://ssb.onecarolina.sc.edu/BANP/bwckbook.site'
    link = "%s?p_term_in=%s&p_subj_in=%s&p_crse_numb_in=%s&p_seq_in=%s" % (base_url, semester, department, number, section)

    driver.get(link)
    driver.execute_script('document.forms["BOOK"].submit()')
    driver.switch_to.window(driver.window_handles[1])
    driver.find_element_by_id('courseListForm')  # this is the implicit wait
    return driver.page_source


def get_catalog(department='%', semester=201808):
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
