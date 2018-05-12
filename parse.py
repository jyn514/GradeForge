#!/usr/bin/env python

'''HTML parsing. Generally, works only on files, not on strings'''

from __future__ import print_function, generators
from os.path import exists
from sys import stderr, stdin, stdout
from tempfile import mkstemp  # used ONLY for seats remaining
import re  # used to treat non-breaking spaces as spaces

from lxml.etree import iterparse, XMLSyntaxError

from utils import DAYS, save, army_time, parse_semester, ReturnSame, get_season
from post import  get_calendar, get_bookstore, get

DEBUG = False  # WARNING: VERY verbose

def parse_catalog(html):
    '''
    lxml.etree.iterparse -> (classes, departments)
        where classes = [c...]
            where c.keys() = ('code', 'department', 'title')
        where departments = {short: long for header in html}
    '''
    classes = []
    departments = {}
    for event, elem in html:
        if elem.tag == 'td':
            cls = elem.attrib.get('class', None)
            if cls == 'nttitle':
                header, title = elem.find('a').text.split(' - ', 1)
                department, code = header.split(' ')
                current = {'code': code, 'department': department, 'title': title}
                departments[header[0]] = header[1]
            elif cls == 'ntdefault' and elem.text is not None:
                current['description'] = elem.text.strip()
                classes.append(current)
    return filter(None, classes), departments


def parse_sections(html):
    '''Parses sections of a course
    Essentially a giant finite state autonoma

    Working:
    - title
    - bookstore link
    - catalog link
    - section link
    - level (UG, grad, etc.)
    - registration start
    - registration end
    - abbr
    - code
    - UID (CCR code)
    - semester
    - instructor
    - email
    - start date
    - end date
    - location
    - start time
    - end time
    - days (of the week)
    - credit hours
    - campus
    - schedule type (Dissertation, seminar, etc.)

    Not implemented:
    - type (? only seen this to be class, discarding for now)
    - description (have to follow catalog link to get)
    - final exam (not always present; should ideally get from academic calendar)
    - restrictions (under detailed catalog link)
        - prerequisites
        - min grades
        - campus
        - other
    - direct bookstore link (should replace current redirect)
    - seat capacity: section_link
    - seats remaining: section_link
    '''
    base_url = 'https://ssb.onecarolina.sc.edu'
    sections = []
    for _, elem in html:
        try:
            if elem.tag == 'th' and elem.attrib.get('class', None) == 'ddtitle':
                if ('course' in locals() and course != {}):  # this is old course
                    sections.append(course)
                elem = elem.find('a')
                link = elem.attrib.get('href', None)
                if link.startswith('/'):
                    link = base_url + link
                course = {'section_link': link}
                # some courses have '-' in title
                if elem.text.count(' - ') > 3:
                    a = elem.text.split(' - ')
                    course['UID'], tmp, course['section'] = a[-3:]
                    course['title'] = ' - '.join(a[:-3])
                else:
                    course['title'], course['UID'], tmp, course['section'] = elem.text.split(' - ')
                course['department'], course['code'] = tmp.split(' ')
            elif elem.tag == 'span' and elem.attrib.get('class', None) == 'fieldlabeltext':
                try:
                    following = elem.tail.strip()
                except AttributeError:
                    continue
                if elem.text == 'Associated Term: ':
                    course['semester'] = following
                elif elem.text == 'Registration Dates: ':
                    course['registration_start'], course['registration_end'] = following.split(' to ')
                elif elem.text == 'Levels: ':
                    course['level'] = following
                    elem = elem.getnext()
                    if elem is None: continue
                    elem = elem.getnext()
                    if elem is None: continue
                    if elem.tag == 'span':
                        try:
                            course['attributes'] = elem.tail.strip()
                            elem = elem.getnext().getnext()
                        except AttributeError:
                            continue
                    try:
                        course['campus'] = elem.tail.strip().split(' Campus')[0]
                    except AttributeError:
                        continue
                    elem = elem.getnext()
                    try:
                        course['type'] = elem.tail.strip().split(' Schedule Type')[0]
                    except AttributeError:
                        continue
                    elem = elem.getnext()
                    try:
                        course['method'] = elem.tail.strip().split(' Instructional Method')[0]
                    except AttributeError:
                        continue
                    elem = elem.getnext()
                    try:
                        course['credits'] = int(elem.tail.strip().split('.000')[0])
                    except AttributeError:
                        continue
            elif elem.tag == 'a':
                if elem.text == 'View Catalog Entry':
                    # TODO: get restrictions
                    # TODO: get description
                    # URL looks like this: base_url +
                    #     /BANP/bwckctlg.p_disp_course_detail?cat_term_in=201808&subj_code_in=ACCT&crse_numb_in=225
                    # can also follow and parse link below
                    link = elem.attrib.get('href', None)
                    if link.startswith('/'):
                        link = base_url + link
                    course['catalog_link'] = link
                elif elem.text == 'Bookstore':
                    # TODO: link directly to bookstore
                    # currently, looks like
                    # /BANP/bwckbook.site?p_term_in=201808&p_subj_in=ACCT&p_crse_numb_in=222&p_seq_in=001
                    # should be https://secure.bncollege.com/webapp/wcs/stores/servlet/TBListView
                    # requires POST
                    link = elem.attrib.get('href', None)
                    if link.startswith('/'):
                        link = link + base_url
                    course['bookstore_link'] = link
            elif elem.tag == 'table' and elem.attrib.get('class', None) == 'datadisplaytable' and elem.attrib.get('summary', None).endswith('this class..'):
                elem = elem.getiterator('tr').__next__().getnext()
                for i, column in enumerate(elem):
                    if i == 0:
                        if column.text != 'Class':
                            print(column.text, file=stderr)
                    elif i == 1:
                        if column.text is None or column.text.strip() == '':
                            course['start_time'] = 'TBA'
                            course['end_time'] = 'TBA'
                        else:
                            course['start_time'], course['end_time'] = column.text.split(' - ')
                    elif i == 2:
                        if column.text.strip() != '':
                            course['days'] = column.text
                        else:
                            course['days'] = 'TBD'
                    elif i == 3:
                        course['location'] = column.text  # can be 'TBD'
                    elif i == 4:
                        course['start_date'], course['end_date'] = column.text.split(' - ')
                    elif i == 5:
                        pass  # already covered earlier (schedule type)
                    elif i == 6:
                        if column.text is None:
                            course['instructor'] = 'TBA'
                        else:
                            course['instructor'] = column.text.split(' (')[0].replace('   ', ' ')
                            mail = column.find('a')
                            if mail is not None:
                                course['instructor_email'] = mail.attrib.get('href')
        except:
            print(elem, elem.text, elem.tail, elem.attrib, course, elem.getchildren(),
                  elem.getnext(), elem.getprevious().tail,
                  elem.getparent().itertext().__next__(), file=stderr)
            if 'following' in locals():
                print(following, file=stderr)
            if 'i' in locals() or 'column' in locals():
                print(i, column, column.text, file=stderr)
            raise
    sections.append(course)
    return sections


def parse_days(text):
    text = text.split(' Meeting Times')[0]
    if 'Session' in text:
        return text  # don't mess with this
    elif 'Only' in text:
        return DAYS[text.split(' Only')[0]]
    return ''.join(DAYS[d] for d in text.split('/'))


def parse_exam(html):
    d = {}
    for _, elem in html:
        if elem.tag == 'h5':
            tmp = {}
            try:
                for row in elem.getparent().getnext().find('table').find('tbody').findall('tr'):
                    meetings, time = row.findall('td')
                    # TODO: THIS IS BAD
                    if 'normal class meeting time' in time:  # Spring half-semester
                        print('quitting', file=stderr)
                        break
                    if re.search(r'\s-\s', ''.join(meetings.itertext())) is not None:
                        for meeting in re.split(r'\s-\s', ''.join(meetings.itertext()))[1].split(', '):
                            tmp[meeting] = time
                    else:
                        assert any('all sections' in text.lower() for text in meetings.itertext())
                        tmp = ReturnSame(time)
                d[parse_days(elem.text)] = tmp
            except:
                print('tag:', elem.tag, 'text:', elem.text, 'row:', row, file=stderr)
                if 'meetings' in locals():
                    print('meetings:', list(meetings.itertext()), 'time:', time.text, file=stderr)
                    if 'meeting' in locals():
                        print('meeting:', meeting, file=stderr)
                table = elem.getparent().getnext().find('table')
                print(elem.getparent().getnext().attrib['class'],
                      table.attrib['class'],
                      list(table), 'row:', list(row), row[0].text, file=stderr)
                raise
    return d
    '''return {parse_days(elem.text): {row.find('td').text.split(' - ')[1]:
                                    row.find('span').text
                                    for row in elem.getparent().getnext().find('table').find('tbody').findall('tr')}
            for _, elem in html if elem.tag == 'h5'}'''

def parse_all_exams():
    result = {}
    for year in range(16, 19):
        for semester in ('Spring', 'Summer', 'Fall'):
            name = semester + '-' + '20' + str(year)
            with open('exams/' + name + '.html', 'rb') as stdin:
                try:
                    result[name.replace('-', ' ')] = parse_exam(iterparse(stdin, html=True))
                except:
                    print(name, file=stderr)
                    raise
    return result


def get_seats(section_link):
    tmp = mkstemp()[1]
    save(get(section_link).text, tmp, binary=False)
    body = iterparse(open(tmp, 'rb'), html=True).__next__()[1].getparent().getnext()
    table = list(body.iterdescendants('table'))[2].iterdescendants('table').__next__()
    elements = list(list(table.iterdescendants('tr'))[1])[-3:]
    return tuple(map(lambda x: x.text, elements))


def clean_sections(sections):
    #if 'exams' not in globals():
    #    exams = load('.exams.data')
    for s in sections:
        try:
            if 'start_time' in s:
                s['start_time'] = army_time(s['start_time'])
                s['end_time'] = army_time(s['end_time'])
            #s['final_exam'] = exams[s['semester']][s['days']][s['start_time']]
        except:
            print(s, file=stderr)
            raise
    return sections

def parse_b_and_n(html):
    '''
    Not implemented:
    - name
    - ISBN
    - prices
        - used rent
        - new rent
        - used buy
        - new buy
        - amazon
    - link
    - author
    - edition
    - required/recommended/optional
    '''
    books = []
    for _, elem in html:
        if elem.tag == 'div':
            print(elem.attrib['class'], file=stderr)

'''TODO: irrelevant
Example: https://ssb.onecarolina.sc.edu/BANP/bwckbook.site?p_term_in=201808&p_subj_in=ACCT&p_crse_numb_in=222&p_seq_in=001
        base_url = 'https://ssb.onecarolina.sc.edu/BANP/bwckbook.site'
        redirect = "%s?p_term_in=%s&p_subj_in=%s&p_crse_numb_in=%s&p_seq_in=%s" % (base_url, semester, department, number, section)'''

def get_books(semester, department, number, section):
    html = 'books/%s-%s-%s-%s-%s.html' % (get_season(semester), semester[:4],
                                          department, number, section)
    if not exists(html):
        save(get_bookstore(semester, department, number, section), html, binary=False)

    course = parse_b_and_n(iterparse(open(html, 'rb'), html=True))
    course['semester'] = semester
    course['department'] = department
    course['number'] = number
    course['section'] = section
    return course


if __name__ == '__main__':
    import argparse
    import pickle

    parser = argparse.ArgumentParser()
    data = parser.add_mutually_exclusive_group(required=True)
    data.add_argument('--sections', '-S', action='store_true')
    data.add_argument('--catalog', '--classes', '-C', action='store_true')
    data.add_argument('--exams', '-e', action='store_true')
    args = parser.parse_args()

    try:
        if args.sections:
            result = clean_sections(parse_sections(iterparse(stdin.buffer, html=True)))
        elif args.catalog:
            result = parse_catalog(iterparse(stdin.buffer, html=True))
        else:
            result = parse_all_exams()
        pickle.dump(result, stdout.buffer)
    except (KeyboardInterrupt, XMLSyntaxError) as e:
        pass
