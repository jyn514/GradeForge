#!/usr/bin/env python

'''Misc utils. Strictly functional, not state-based.'''

from datetime import date
from argparse import HelpFormatter
import cloudpickle

allowed = {'semester':  ("201341", "201401", "201405", "201408", "201501", "201505",
                         "201508", "201601", "201605", "201608", "201701", "201705",
                         "201708", "201801", "201805", "201808"),
           'campus': ('AIK', 'BFT', 'COL', 'LAN', 'SAL', 'SMT', "UNI", "UPS"),
           'subject': ("ACCT", "AERO", "AFAM", "ANES", "ANTH", "ARAB", "ARMY",
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
           'term': ("1A", "1B", "10", "2A", "2B", "20", "3A", "3B", "30", "4A", "4B",
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
              into:    -s, --long ARGS'''
    def _format_action_invocation(self, action):
        if not action.option_strings:
            return self._metavar_formatter(action, action.dest)(1)[0]

        parts = list(action.option_strings)

        # if the Optional takes a value, format is:
        #    -s, --long ARGS
        if action.nargs != 0:
            parts[-1] += ' %s' % self._format_args(action, action.dest.upper())
        return ', '.join(parts)


def print_request(req, **kwargs):
    print(req.method, req.url, req.headers, req.body, sep='\n', **kwargs)


def b_and_n_semester(semester):
    '''Example: 201808 -> F18'''
    return parse_semester(semester)[0].upper() + semester[-2:]


def get_season(semester='201808'):
    if semester[-1] == '8':
        return 'fall'
    elif semester[-1] == '1':
        return 'spring'
    return 'summer'

def get_season_today():
    pass
    # TODO
    #m = date.today().month
    #return 'spring' if m <


def parse_semester(s):
    if s in allowed['semester']:
        return s
    s = s.lower()
    # TODO: check if this year or next year is spring
    if s == 'fall':
        return str(date.today().year) + '08'
    elif s == 'spring':
        return str(date.today().year) + '01'
    elif s == 'summer':
        return str(date.today().year) + '05'
    raise ValueError(s)


def load(stdin):
    with open(stdin, 'rb') as i:
        return cloudpickle.load(i)


def save(obj, stdout):
    with open(stdout, 'wb') as i:
        cloudpickle.dump(obj, i)


def army_time(ampm):
    if ampm == 'TBA': return ampm
    hours, minutes = ampm.split(':')
    minutes, ampm = minutes.split(' ')
    if ampm == 'pm':
        hours = str((int(hours) + 12) % 24)  # midnight is 00:00
    return ':'.join((hours, minutes))

DAYS = {'Monday': 'M',
        'Tuesday': 'T',
        'Wednesday': 'W',
        'Thursday': 'R',
        'Friday': 'F',
        'Saturday': 'S'}
