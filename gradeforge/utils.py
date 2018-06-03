#!/usr/bin/env python3

'''Misc utils. Strictly functional, not state-based.'''
from __future__ import print_function

from datetime import date
from argparse import HelpFormatter
import re

# first semester is not a typo, this is how it is really accepted on the USC side
allowed = {'semester': ("201341", "201401", "201405", "201408", "201501", "201505",
                        "201508", "201601", "201605", "201608", "201701", "201705",
                        "201708", "201801", "201805", "201808"),
           'campus': ('AIK', 'BFT', 'COL', 'LAN', 'SAL', 'SMT', "UNI", "UPS"),
           'department': ("ACCT", "AERO", "AFAM", "ANES", "ANTH", "ARAB", "ARMY",
                          "ARTE", "ARTH", "ARTS", "ASLG", "ASTR", "ATEP", "BADM",
                          "BIOL", "BIOS", "BMEN", "BMSC", "CHEM", "CHIN", "CLAS",
                          "COLA", "COMD", "CPLT", "CRJU", "CSCE", "DANC", "DMED",
                          "DMSB", "ECHE", "ECIV", "ECON", "EDCE", "EDCS", "EDEC",
                          "EDEL", "EDET", "EDEX", "EDFI", "EDHE", "EDLP", "EDML",
                          "EDPY", "EDRD", "EDRM", "EDSE", "EDTE", "ELCT", "EMCH",
                          "EMED", "ENCP", "ENFS", "ENGL", "ENHS", "ENVR", "EPID",
                          "EXSC", "FAMS", "FINA", "FORL", "FPMD", "FREN", "GENE",
                          "GEOG", "GEOL", "GERM", "GLST", "GMED", "GRAD", "GREK",
                          "HGEN", "HIST", "HPEB", "HRSM", "HRTM", "HSPM", "IBUS",
                          "IDST", "INTL", "ITAL", "ITEC", "JAPA", "JOUR", "LASP",
                          "LATN", "LAWS", "LIBR", "LING", "MART", "MATH", "MBAD",
                          "MBIM", "MCBA", "MEDI", "MGMT", "MGSC", "MKTG", "MSCI",
                          "MUED", "MUSC", "MUSM", "NAVY", "NEUR", "NPSY", "NURS",
                          "OBGY", "OPTH", "ORSU", "PALM", "PAMB", "PATH", "PEDI",
                          "PEDU", "PHAR", "PHIL", "PHMY", "PHPH", "PHYS", "PHYT",
                          "PMDR", "POLI", "PORT", "PSYC", "PUBH", "RADI", "RCON",
                          "RELG", "RETL", "RHAB", "RUSS", "SAEL", "SCCP", "SCHC",
                          "SLIS", "SMED", "SOCY", "SOST", "SOWK", "SPAN", "SPCH",
                          "SPTE", "STAT", "SURG", "THEA", "UNIV", "WGST"),
           'number': ('',) + tuple(range(1, 1000)),
           'level': ('%', 'GR', 'LW', 'MD', 'UG'),
           'term': ('%', "1A", "1B", "10", "2A", "2B", "20", "3A", "3B", "30", "4A", "4B",
                    "40", "50", "6A", "6B", "60", "7A", "7B", "70", "8A", "8B", "80"),
           'times': ('%', 'E', 'O', 'W'),
           'location': ('%', "1A@S", "3FJ", "3GDC", "3GDG", "3GDI", "3GDL", "3GDR",
                        "8GRV", "8GRS", "7LAU", "3PLM", "3HNR", "1HNR", "1ONL",
                        "8HNR", "8PLM", "8SLC"),
           'start_hour': range(24),
           'start_minute': range(60),
           'end_hour': range(24),
           'end_minute': range(60),
           'days': ('m', 't', 'w', 'r', 'f', 's', 'u'),
           'credits': range(4)}

# https://stackoverflow.com/a/16969505
class SingleMetavarFormatter(HelpFormatter):
    '''For the picky among us.
    Turns the default: -s ARGS, --long ARGS
              into:    -s, --long ARGS
    example: parser = ArgumentParser(formatter_class=SingleMetavarFormatter)'''
    def _format_action_invocation(self, action):
        if not action.option_strings:
            return self._metavar_formatter(action, action.dest)(1)[0]

        parts = list(action.option_strings)

        # if the Optional takes a value, format is:
        #    -s, --long ARGS
        if action.nargs != 0:
            parts[-1] += ' %s' % self._format_args(action, action.dest.upper())
        return ', '.join(parts)


class ReturnSame(object):
    '''Returns the same value no matter what object is used to access.
    Meant to mimic a dictionary.
    Example use:
    >>> d = ReturnSame(4)
    >>> d['some_value']
    4
    '''
    def __init__(self, *values):
        self.value = values[0] if len(values) == 1 else values

    def __getitem__(self, item):
        return self.value

    def __str__(self):
        # str is necessary in case value is a tuple
        return "gradeforge.ReturnSame(%s)" % str(self.value)

    def __repr__(self):
        return self.__str__()


def b_and_n_semester(semester):
    '''Example: 201808 -> F18'''
    semester = str(semester)
    season = get_season(semester)
    if season == 'Fall':
        return 'F' + semester[2:4]
    elif season == 'Summer':
        return 'A' + semester[2:4]
    return 'W' + semester[2:4]


def get_season(semester='201808'):
    'Given a semester in USC format, return corresponding season'
    semester = str(semester)
    if not (len(semester) == 6 and semester.isnumeric()):
        raise ValueError("Expected 6 digit semester; got " + semester)
    if semester[-2:] == '08':
        return 'Fall'
    elif semester[-2:] == '01':
        return 'Spring'
    elif semester[-2:] == '05':
        return 'Summer'
    raise ValueError("Bad month %s in %s" % (semester[-2:], semester))


def get_season_today():
    month = date.today().month
    if month < 5:
        return 'Spring'
    if month < 8:
        return 'Summer'
    return 'Fall'


def parse_semester(season, year=date.today().year):
    '''The opposite of get_season.
    Given a season and an optional year, return a semester in USC format.'''
    if season in allowed['semester']:
        return season
    season = season.lower()
    year = str(year)
    if len(year) != 4 or not year.isnumeric():
        raise ValueError("expected four digit year; was given " + year)
    if int(year) >= 2014:
        if season == 'fall':
            return year + '08'
        elif season == 'spring':
            return year + '01'
        elif season == 'summer':
            return year + '05'
    else:
        if season == 'fall':
            return year + '41'
        elif season == 'spring':
            return year + '11'
    raise ValueError("'%s' not a valid USC season for year %s" % (season, year))


def save(obj, output):
    with open(output, 'wb') as i:
        i.write(obj)


def army_time(time):
    if ':' not in time:
        raise ValueError("Invalid time " + time)
    hours, minutes = time.split(':')
    hours = int(hours)
    if hours > 24 or hours < 0:
        raise ValueError("Invalid time " + time)

    try:
        minutes, ampm = re.split(r' *([ap])\.? *m', minutes)[:2]
    except ValueError:
        ampm = None
    if (hours > 12 or hours == 0) and ampm is not None:
        raise ValueError("Conflicting time system used in " + time)

    if not (ampm == 'p') ^ (hours != 12):
        hours += 12
    return ':'.join((str(hours % 24), minutes))


def parse_days(text):
    text = text.split(' Meeting Times')[0].replace('\xa0', ' ')
    if 'Session' in text:
        return text  # don't mess with this
    elif 'Only' in text:
        return DAYS[text.split(' Only')[0]]
    return ''.join(DAYS[d] for d in text.split('/'))


DAYS = {'Monday': 'M',
        'Tuesday': 'T',
        'Wednesday': 'W',
        'Thursday': 'R',
        'Friday': 'F',
        'Saturday': 'S',
        'Sunday': 'U'}


def arg_filter(args):
    return {k: v for k, v in args.__dict__.items()
            if v is not None}

def catalog_link(semester, department, code):
    '''Example:
    https://ssb.onecarolina.sc.edu/BANP/bwckctlg.p_disp_course_detail?cat_term_in=201808&subj_code_in=BADM&crse_numb_in=B210'''
    base_url = 'https://ssb.onecarolina.sc.edu/BANP/bwckctlg.p_disp_course_detail'
    return "%s?cat_term_in=%s&subj_code_in=%s&crse_numb_in=%s" % (base_url, semester, department, code)


def bulletin_link():
    '''Example: http://bulletin.sc.edu/preview_course.php?catoid=70&coid=85439'''
    raise BaseException("NOPE NOPE NOPE")


def section_link(semester, CRN):
    '''Example:
    https://ssb.onecarolina.sc.edu/BANP/bwckschd.p_disp_detail_sched?term_in=201808&crn_in=12566'''
    base_url = 'https://ssb.onecarolina.sc.edu/BANP/bwckschd.p_disp_detail_sched'
    return "%s?term_in=%s&crn_in=%s" % (base_url, semester, CRN)
