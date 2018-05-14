#!/usr/bin/env python

'''HTML parsing. Generally, works only on files, not on strings'''

from __future__ import print_function, generators
from os.path import exists
from sys import stderr, stdin, stdout
from tempfile import mkstemp  # used for downloading seats remaining
import re  # used for only very basic stuff

from lxml import etree

from utils import DAYS, save, army_time, parse_semester, ReturnSame, get_season
from post import  get_calendar, get_bookstore, get

BASE_URL = 'https://ssb.onecarolina.sc.edu'

def parse_catalog(file_handle):
    '''
    file -> (classes, departments)
        where classes = [c...]
            where c.keys() = ('course_link', 'title', 'department', 'code',
                              'description', 'credits', 'attributes', 'level',
                              'type', 'all_sections')
        where departments = {short: long for header in html}
    '''
    classes = []
    departments = {}
    doc = etree.parse(file_handle, parser=etree.HTMLParser())
    rows = doc.xpath('/html/body//table[@class="datadisplaytable" and @width="100%"]/tr')
    HEADER = True
    for row in rows:
        if HEADER:
            anchor = row.find('td').find('a')
            course = {'course_link': BASE_URL + anchor.attrib['href']}
            # some courses have '-' in title
            tmp = anchor.text.split(' - ')
            course_id, course['title'] = tmp[0], ' - '.join(tmp[1:])
            course['department'], course['code'] = course_id.split(' ')
        else:
            td = row.xpath('td')[0]
            course['description'] = td.text.strip()
            credits = td.xpath('br[1]/following-sibling::text()')[0]
            course['credits'] = credits.replace('Credit hours', '').replace('.000', '').replace(' TO     ', ' to ').strip()
            tmp = td.xpath('span/following-sibling::text()')
            tmp = tuple(map(lambda s: s.replace('\n', ''), filter(lambda s: s != '\n', tmp)))
            if len(td.xpath('span')) == 3:  # has attributes
                course['attributes'] = tmp[-1]
                tmp = tmp[:-1]
            else:
                course['attributes'] = 'None'
            # type can be multiple (since there might be anchor in middle)
            course['level'], course['type'], department = tmp[0],  ''.join(tmp[1:-1]), tmp[-1]
            departments[course['department']] = department

            a = td.find('a')
            if a is not None:
                course['all_sections'] = BASE_URL + a.attrib['href']
            else:
                course['all_sections'] = 'None'
            classes.append(course)
            del course

        HEADER = not HEADER

    return classes, departments


def parse_sections(file_handle):
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
    - department
    - code
    - UID (CRN code)
    - semester
    - instructor
    - email
    - start date
    - end date
    - location
    - start time
    - end time
    - days (of the week)
    - type (?? only seen this to be class)

    Not implemented:
    - description (have to follow catalog link to get)
    - final exam (not always present; should ideally get from academic calendar)
    - restrictions (under detailed catalog link)
        - prerequisites
        - min grades
        - campus
        - colleges
        - classification (Freshman, etc.)
        - other
    - direct bookstore link (should replace current redirect)
    - seat capacity: section_link
    - seats remaining: section_link (see also https://github.com/jyn514/GradeForge/issues/9)
    '''
    base_url = 'https://ssb.onecarolina.sc.edu'
    sections = []
    doc = etree.parse(file_handle, etree.HTMLParser())
    rows = doc.xpath('/html/body//table[@class="datadisplaytable" and @width="100%"][1]/tr[position() > 2]')
    assert len(rows) % 2 == 0  # even
    HEADER = True
    for row in rows:
        if HEADER:
            anchor = row.xpath('th/a[1]')[0]  # etree returns list even if only one element
            course = {'section_link': anchor.attrib.get('href')}
            text = anchor.text.split(' - ')
            # some courses have '-' in title
            course['UID'], tmp, course['section'] = text[-3:]
            course['title'] = ' - '.join(text[:-3])
            course['department'], course['code'] = tmp.split(' ')
        else:
            main = row.xpath('td[1]')[0]

            after = main.xpath('span/following-sibling::text()')
            after = tuple(map(lambda x: x.strip(), filter(lambda x: x != '\n', after)))
            course['semester'], registration, course['level'] = after[:3]
            if len(after) == 8:
                course['attributes'] = after[3]
            campus, schedule_type, method, credits = after[-4:]
            course['registration_start'], course['registration_end'] = registration.split(' to ')
            course['campus'] = campus.split('USC ')[1].split(' Campus')[0]
            course['type'] = schedule_type.split(' Schedule Type')[0]
            course['method'] = method.split(' Instructional Method')[0]
            course['credits'] = credits.split(' Credits')[0].replace('.000', '')

            tmp = main.xpath('a/@href')
            course['catalog_link'], course['bookstore_link'] = tmp[-2:]
            if len(tmp) == 3:
                syllabus = tmp[0]
                if syllabus.startswith('/'):
                    syllabus = base_url + syllabus
                course['syllabus'] = syllabus

            tmp = main.xpath('table/tr[2]/td//text()')
            if len(tmp) == 9:  # instructor exists
                tmp = tmp[:-2]  # don't get junk at end
            elif len(tmp) > 9:  # multiple instructors
                tmp = tmp[:6] + [''.join([tmp[7]] + tmp[9:])]  # make all instructors last element in list
            if len(tmp) == 0:  # independent study
                course['type'], course['start_time'], course['end_time'], course['days'], course['location'], course['start_date'], course['end_date'], course['instructor'], course['instructor_email'] = ['Independent Study'] + [None] * 8  # this is handled on the frontend
            else:
                course['type'], times, course['days'], course['location'], dates, _, instructor = tmp
                if times == 'TBA':
                    course['start_time'], course['end_time'] = dates, dates
                else:
                    course['start_time'], course['end_time'] = map(army_time, times.split(' - '))
                course['start_date'], course['end_date'] = dates.split(' - ')
                course['instructor'] = instructor.replace(' (', '').replace('   ', ' ')
                tmp = tuple(main.xpath('table/tr[2]/td/a/@href'))
                if len(tmp) == 1:
                    course['instructor_email'] = tmp[0]
                else:
                    course['instructor_email'] = tmp
            sections.append(course)
            del course  # so we get an error instead of silently add wrong info when rows are out of order
        HEADER = not HEADER
    return tuple(sections)


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


def follow_links(sections):
    exams = load('.exams.data')
    for s in sections:
        # Takes about half an hour. The data goes out of date quickly. Not worth it.
        #s['capacity'], s['actual'], s['remaining'] = get_seats(s['section_link'])
        # Still crashing.
        #s['final_exam'] = exams[s['semester']][s['days']][s['start_time']]
        pass
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
            result = parse_sections(stdin.buffer)
            # result = follow_links(result)
        elif args.catalog:
            result = parse_catalog(iterparse(stdin.buffer, html=True))
        else:
            result = parse_all_exams()
        pickle.dump(result, stdout.buffer)
    except (KeyboardInterrupt, AssertionError) as e:
        pass
