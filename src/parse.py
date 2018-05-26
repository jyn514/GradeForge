#!/usr/bin/env python3

'''HTML parsing. Generally, works only on files, not on strings'''

from __future__ import print_function, generators
from os.path import exists
from sys import stderr, stdin, stdout
from tempfile import mkstemp  # used for downloading seats remaining
import re  # used for only very basic stuff
from datetime import date

from lxml import etree

from utils import save, army_time, parse_semester, ReturnSame, get_season, load, parse_days
from post import get_bookstore, get

BASE_URL = 'https://ssb.onecarolina.sc.edu'

def parse_catalog(file_handle):
    '''
    file -> (classes, departments)
        where classes = [c...]
            where c.keys() = ('course_link', 'title', 'department', 'code',
                              'description', 'credits', 'attributes', 'level',
                              'type', 'all_sections')
        where departments = {short: long for header in html}
    TODO: lots
    - seperate prereqs from description
    - 'type' is not picked up if inside an anchor; the current mess doesn't do what I thought
    - general screwy stuff
        - description
        - departments
    - restrictions need to be subparsed, I think they're currently in attributes -JN
        - prerequisites
        - min grades
        - campus
        - colleges
        - classification (Freshman, etc.)
        - other
    '''
    classes = []
    doc = etree.parse(file_handle, parser=etree.HTMLParser())
    rows = doc.xpath('/html/body//table[@class="datadisplaytable" and @width="100%"]/tr')
    HEADER = True
    for row in rows:
        if HEADER:
            anchor = row.find('td').find('a')
            course = {'course_link': anchor.attrib['href']}
            # some courses have '-' in title
            tmp = anchor.text.split(' - ')
            course_id, course['title'] = tmp[0], ' - '.join(tmp[1:])
            course['department'], course['code'] = course_id.split(' ')
        else:
            td = row.xpath('td')[0]
            course['description'] = td.text.strip()
            course['credits'] = td.xpath('br[1]/following-sibling::text()')[0]
            tmp = td.xpath('span/following-sibling::text()')
            tmp = tuple(map(lambda s: s.replace('\n', ''), filter(lambda s: s != '\n', tmp)))
            if len(td.xpath('span')) == 3:  # has attributes
                course['attributes'] = tmp[-1]
                tmp = tmp[:-1]
            # type can be multiple (since there might be anchor in middle)
            course['level'], course['type'], course['department_long'] = tmp[0], ''.join(tmp[1:-1]), tmp[-1]

            a = td.find('a')
            if a is not None:
                course['all_sections'] = a.attrib['href']
            classes.append(clean_catalog(course))
            del course

        HEADER = not HEADER
    return infer_tables(classes)


def infer_tables(iterable, classes=True):
    '''If classes, assume classes. Else, assume sections.'''
    iterable = tuple(iterable)  # so generators aren't exhausted
    if classes:
        departments = dict(set((c['department'], c.pop('department_long'))
                               for c in iterable))
        return departments, iterable

    instructors = dict(set((s['instructor_email'], s.pop('instructor'))
                           for s in iterable))
    semesters = tuple(set((s['semester'], s.pop('start_date'), s.pop('end_date'),
                           s.pop('registration_start'),
                           s.pop('registration_end'))
                          for s in iterable))
    return instructors, semesters, iterable


def clean_catalog(course):
    '''Make elements of dict predictable'''
    if course['course_link'].startswith('/'):
        course['course_link'] = BASE_URL + course['course_link']
    # ex: '7.000    OR  8.000 Credit hours' -> '7 TO 8'
    course['credits'] = re.sub(' +(TO|OR) +', ' TO ',
                               course['credits'].replace('Credit hours', '')
                               .replace('.000', '')
                               .strip())
    try:
        course['attributes']
    except KeyError:
        course['attributes'] = None
    try:
        if course['all_sections'].startswith('/'):
            course['all_sections'] = BASE_URL + course['all_sections']
    except KeyError:
        course['all_sections'] = None
    return course


def parse_sections(file_handle):
    '''file_handle -> tuple(c, ...)
            where c is dictionary with keys (section_link, UID, section, department,
            code, registration_start, registration_end, semester, attributes,
            campus, type, method, catalog_link, bookstore_link, syllabus,
            days, location, start_time, end_time, start_date, end_date,
            instructor, instructor_email
    Parses sections of a course
    Essentially a giant finite state autonoma

    Working:
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
    - attributes

    Not implemented:
    - final exam (not always present; should ideally get from academic calendar)
    - books (this is implemented, just not called in follow_links)
    - seat capacity: section_link
    - seats remaining: section_link (see also https://github.com/jyn514/GradeForge/issues/9)

    TODO:
    - figure out why start_date and end_date are sometimes the same
    - department is overwritten by last seen, so there's a lot of stuff specific to upstate
    - remove 'Department' from departments
    - fix misc screwiness
    '''
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
            # everything before last three is title
            course['UID'], tmp, course['section'] = text[-3:]
            course['department'], course['code'] = tmp.split(' ')
        else:
            main = row.xpath('td[1]')[0]

            after = main.xpath('span/following-sibling::text()')
            after = tuple(map(lambda x: x.strip(), filter(lambda x: x != '\n', after)))

            semester, registration = after[:2]  # third is level, which we know
            course['registration_start'], course['registration_end'] = registration.split(' to ')

            course['semester'] = parse_semester(*semester.split(' '))
            if len(after) == 8:
                course['attributes'] = after[3]
            campus, schedule_type, method = after[-4:-1]  # last is credits
            course['campus'] = campus.replace('USC ', '').replace(' Campus', '')
            course['type'] = schedule_type.replace(' Schedule Type', '')
            course['method'] = method.replace(' Instructional Method', '')

            tmp = main.xpath('a/@href')
            course['catalog_link'], course['bookstore_link'] = tmp[-2:]
            if len(tmp) == 3:
                course['syllabus'] = tmp[0]

            tmp = main.xpath('table/tr[2]/td//text()')
            if len(tmp) == 9:  # instructor exists
                tmp = tmp[:-2]  # don't get junk at end
            elif len(tmp) > 9:  # multiple instructors
                # combine instructors into one element
                tmp = tmp[:6] + [''.join([tmp[7]] + tmp[9:])]
            if not tmp:  # independent study
                for key in ['days', 'location', 'start_time', 'end_time',
                            'start_date', 'end_date', 'instructor', 'instructor_email']:
                    course[key] = None  # this is handled on the frontend
            else:
                _, times, course['days'], course['location'], dates, _, course['instructor'] = tmp
                if times == 'TBA':
                    course['start_time'], course['end_time'] = 'TBA', 'TBA'
                else:
                    course['start_time'], course['end_time'] = map(army_time, times.split(' - '))
                course['start_date'], course['end_date'] = dates.split(' - ')
                tmp = main.xpath('table/tr[2]/td/a/@href')
                if len(tmp) == 1:
                    # str is necessary, otherwise returns _ElementUnicodeResult
                    course['instructor_email'] = str(tmp[0])
            sections.append(clean_section(course))
            # error instead of silently addding wrong info when rows are out of order
            del course
        HEADER = not HEADER
    return infer_tables(follow_links(sections), classes=False)


def clean_section(course):
    '''Make course elements more predictable'''
    try:
        if course['instructor_email'] == '':
            course['instructor_email'] = None
    except KeyError:
        course['instructor_email'] = None
    if course['instructor'] is not None:
        course['instructor'] = re.sub(' +', ' ', course['instructor'].replace(' (', ''))
    try:
        if course['syllabus'].startswith('/'):
            course['syllabus'] = BASE_URL + course['syllabus']
    except KeyError:
        course['syllabus'] = None
    try:
        course['attributes']
    except KeyError:
        course['attributes'] = None
    for key in ('catalog_link', 'bookstore_link', 'section_link'):
        if course[key].startswith('/'):
            course[key] = BASE_URL + course[key]
    return course


def parse_exam(file_handle):
    '''Return {days_met: [(time_met, exam_datetime), ...], ...}
    File can be either absolute/relative path or an actual file handle
    Quite fast compared to parse_sections, but it's handling less data.'''
    all_exams = {}
    try:
        doc = etree.parse(file_handle, etree.HTMLParser())
        # Yeah. I know.
        div = doc.xpath('/html/body/section/div/div/section[2]/div/section/div/div/section')
    except AssertionError:  # This was annoying
        raise ValueError("'%s' is empty or not an HTML file" % file_handle)

    assert len(div) == 1, str(len(div)) + " should be 1"
    div = div[0]
    headers = div.xpath('div[@class="accordion-summary"]/h5')
    bodies = div.xpath('div[@class="accordion-details"]/table/tbody')
    for i, header in enumerate(headers):
        try:
            days_met = parse_days(header.text)
        # given session, not days. Ex: 'Spring I (3A) and Spring II (3B)'
        except KeyError:
            days_met = None  # TODO
        times = {}
        for row in bodies[i].findall('tr'):
            # Example: ('TR - 8:30 a.m.', 'Thursday, May 3 - 9:00 a.m.')
            # school likes to put some as spans, some not
            time_met, exam_datetime = map(lambda td: ''.join(td.itertext())
                                                     .strip()
                                                     .replace('\xa0', ' '),
                                          row.findall('td'))
            if exam_datetime == 'TBA':  # this is frustrating
                all_exams[days_met] = 'TBA'
                continue
            split = exam_datetime.split(', ')
            regex = r'\s*[–-]\s*'
            if any(map(str.isnumeric, split[0])):  # sometimes it's 'May 4th, Fri.'
                exam_date, exam_time = split[0], split[-1]  # commma after Friday
                try:
                    exam_time = re.split(regex, exam_time)[1]
                except IndexError:
                    assert 'class meeting time' in exam_time.lower(), exam_time
            else:  # Friday, May 4 - 8:30 p.m.
                exam_date, exam_time = re.split(r'\s*[–-]\s*', split[1])
            exam_date = re.sub('(th|nd|st|rd)', '', exam_date)
            try:
                exam_time = army_time(exam_time)
            except ValueError:  # TODO: DRY
                assert 'class meeting time' in exam_time.lower(), exam_time
            if 'all sections' in time_met.lower():
                times = ReturnSame(exam_date, exam_time)
            else:
                split = re.split(r'\s*[MTWRFSU]+\s+(-\s+)?', time_met)
                time_met = split[-1]
                # example: '8:30 a.m.,11:40 a.m., 2:50 p.m., 6:00 p.m.'
                for time in re.split(', ?', time_met):
                    times[army_time(time)] = exam_date, exam_time
        all_exams[days_met] = times
    return all_exams


def parse_all_exams():
    '''Repeat parse_exam for each semester between Summer 2016 and the present'''
    result = {}
    for year in range(16, date.today().year + 1 - 2000):
        for semester in ('Spring', 'Summer', 'Fall'):
            name = semester + '-' + '20' + str(year)
            if name == 'Spring-2016':
                continue  # Removed from site, gives 404
            with open('exams/' + name + '.html') as stdin:
                try:
                    result[parse_semester(*name.split('-'))] = parse_exam(stdin)
                except:
                    print(name, file=stderr)
                    raise
    return result


def get_seats(section_link):
    'str -> (capacity, taken, remaining)'
    from lxml.etree import iterparse
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


def parse_b_and_n(file_handle):
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
    doc = etree.parse(file_handle, etree.HTMLParser())
    form = doc.xpath('/html/body/header/section/div[@class="courseMaterialsList"]/div/form[@id="courseListForm"]')[0]
    books = form.xpath('div[@class="book_sec"]/div/div[@class="book-list"]/div')

    all_books = []
    for book in books:
        info = {}
        info['image'] = book.xpath('div[2]/a/img/@src')[0]
        anchor = book.xpath('div[3]/h1/a')[0]
        info['link'] = anchor.attrib['href']
        info['title'] = anchor.attrib['title']
        info['required'] = book.xpath('div[3]/h2/span[@class="recommendBookType"]/text()')[0].strip().lower()
        info['author'] = book.xpath('div[3]/h2/span/i/text()')[0].replace('By ', '')
        # ok but actually wtf
        info['edition'], info['publisher'], info['isbn'] = map(lambda s: s.tail.replace('\xa0', '').replace('Â', '').strip(),
                                                               book.xpath('div[3]/ul/li/strong'))
        prices = book.xpath('div[4]/div[@class="selectBookCont"]/div/ul/li[2]/ul/li')
        for p in prices:
            info[p.attrib['title'].lower().strip().replace(' ', '-')] = p.find('span').text.strip()
        all_books.append(info)
    return all_books


def get_books(semester, department, number, section):
    html = 'books/%s-%s-%s-%s-%s.html' % (get_season(semester), semester[:4],
                                          department, number, section)
    if not exists(html):  # TODO: move this to makefile
        save(get_bookstore_selenium(semester, department, number, section), html, binary=False)

    return parse_b_and_n(html)


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
        elif args.catalog:
            result = parse_catalog(stdin.buffer)
        else:
            result = parse_all_exams()
        pickle.dump(result, stdout.buffer)
    except KeyboardInterrupt:
        pass
