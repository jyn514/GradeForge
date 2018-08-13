#!/usr/bin/env python3
# encoding: utf-8
'''HTML parsing. Generally, works only on files, not on strings'''

from collections import defaultdict
from tempfile import mkstemp  # used for downloading seats remaining
from sys import stdout
from logging import getLogger
from datetime import datetime
import csv
import re  # used for only very basic stuff

from lxml import etree
from requests import get

from gradeforge.utils import army_time, parse_semester

BASE_URL = 'https://ssb.onecarolina.sc.edu'
LOGGER = getLogger(__name__)

def parse_catalog(file_handle, catalog_output='courses.csv', department_output='departments.csv'):
    '''
    file -> None

    TODO:
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
    if not hasattr(catalog_output, 'write'):
        with open(catalog_output, 'w') as writable:
            parse_catalog(file_handle, writable, department_output)
            return

    if not hasattr(department_output, 'write'):
        with open(department_output, 'w') as writable:
            parse_catalog(file_handle, catalog_output, writable)
            return


    catalog_headers = ('title', 'department', 'code', 'description', 'credits',
                       'attributes', 'level', 'type', 'all_sections', 'division')
    catalog = csv.DictWriter(catalog_output, catalog_headers)
    catalog.writeheader()

    departments = {}

    doc = etree.parse(file_handle, parser=etree.HTMLParser())
    rows = doc.xpath('/html/body//table[@class="datadisplaytable" and @width="100%"]/tr')
    HEADER = True

    for row in rows:
        if HEADER:
            course = {}
            header_text = row.find('td').find('a').text.split(' - ')
            # some courses have '-' in title
            course_id, course['title'] = header_text[0], ' - '.join(header_text[1:]).strip()
            course['department'], course['code'] = course_id.split(' ')
        else:
            td = row.xpath('td')[0]
            course['description'] = td.text.strip()
            credits = td.xpath('br[1]/following-sibling::text()')[0]
                # ex: '7.000    OR  8.000 Credit hours' -> '7 TO 8'
            course['credits'] = re.sub(' +(TO|OR) +', ' TO ',
                                       credits.replace('Credit hours', '')
                                       .replace('.000', '')
                                       .strip())

            spans = td.xpath('span/following-sibling::text()')
            spans = tuple(map(lambda s: s.replace('\n', ''), filter(lambda s: s != '\n', spans)))
            course['level'], spans = spans[0], spans[1:]

            # this is a dumpster fire
            course_id = course['department'] + ' ' + course['code']
            department_description = None
            if spans and ' Department' in spans[-1]:
                department_description, spans = spans[-1], spans[:-1]
            elif len(spans) > 1:
                course['attributes'], spans = spans[-1], spans[:-1]
                if ' Department' in spans[-1]:
                    department_description, spans = spans[-1], spans[:-1]
            if spans and ' Division' in spans[-1]:
                course['division'], spans = spans[-1].replace(' Division', ''), spans[:-1]
            # remove duplicates; sometimes type are over multiple, sometimes not
            course['type'] = ', '.join(set(', '.join(spans).split(', '))) or None

            # store departments in their own data structure
            if department_description is not None:
                regex = ' Department|(USC-[AB]|Upstate|Sch of) '
                department_description = re.sub(regex, '', department_description).strip()
                if course['department'] not in departments:
                    departments[course['department']] = defaultdict(int)
                departments[course['department']][department_description] += 1

            a = td.find('a')
            if a is not None:
                course['all_sections'] = a.attrib['href']
            catalog.writerow(course)
            del course
        HEADER = not HEADER

    department = csv.writer(department_output)
    department_output.write('code,description\n')
    for abbreviation, descriptions in departments.items():
        # https://stackoverflow.com/a/613218
        final = sorted(descriptions.items(), key=lambda tup: tup[1], reverse=True)
        most_common = final[0][0]
        if len(final) > 1:
            LOGGER.info("%d descriptions available for '%s'; choosing the most common (%s)", len(final), abbreviation, most_common)
            LOGGER.debug("all descriptions: %s", final)
        department.writerow((abbreviation, most_common))


def _add_instructors(instructors, emails, instructor_dict):
    '''INTERNAL DO NOT USE'''
    assert len(instructors) == len(emails), (instructors, emails)
    for instructor, email in zip(instructors, emails):
            try:
                if email is not None and email != instructor_dict[instructor]:
                    LOGGER.warning("email '%s' for instructor '%s' already exists; refusing to overwrite with '%s'",
                                instructor_dict[instructor], instructor, email)
            except KeyError:
                instructor_dict[instructor] = email

def _parse_instructors(row, instructors, instructor_dict):
    'Element, str, dict -> str, str'
    if instructors == 'TBA':
        return instructors, None

    email_struct = row.xpath("td/a/@*[name()='href' or name()='target']")

    if not email_struct:
        LOGGER.debug(instructors)
        instructors = re.sub(r'\s+', ' ', instructors).replace(' (P)', '').split(',')
        LOGGER.info("No emails present for instructors %s", instructors)
    else:
        instructors, emails = email_struct[1::2], email_struct[::2]
        LOGGER.debug("instructors: %s; emails: %s", instructors, emails)
        _add_instructors(instructors, emails, instructor_dict)

    return instructors[0], ','.join(instructors[1:])


def _parse_inner_row(row, course, term, instructor_dict):
    table_info = row.xpath('td//text()')
    if not table_info:  # independent study; this is handled on the frontend
        for key in ['days', 'location', 'startTime', 'endTime',
                    'instructor']:
            course[key] = None
        term['startDate'], term['endDate'] = None, None
    else:
        _, times, course['days'], course['location'], dates, _ = table_info[:6]
        instructors = ''.join(table_info[6:])

        course['primary_instructor'], course['secondary_instructors'] = _parse_instructors(row, instructors, instructor_dict)

        if times == 'TBA':
            course['startTime'], course['endTime'] = 'TBA', 'TBA'
        else:
            course['startTime'], course['endTime'] = map(army_time, times.split(' - '))
        term['startDate'], term['endDate'] = dates.split(' - ')


def parse_sections(file_handle, instructor_output='instructors.csv',
                   term_output='semesters.csv', section_output='sections.csv'):
    '''file_handle -> None

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
    - fix misc screwiness
    '''

    if not hasattr(instructor_output, 'write'):
        with open(instructor_output, 'w') as writable:
            parse_sections(file_handle, writable, term_output, section_output)
            return

    if not hasattr(term_output, 'write'):
        with open(term_output, 'w') as writable:
            parse_sections(file_handle, instructor_output, writable, section_output)
            return

    if not hasattr(section_output, 'write'):
        with open(section_output, 'w') as writable:
            parse_sections(file_handle, instructor_output, term_output, writable)
            return

    headers = ('department', 'code', 'section', 'UID', 'term', 'campus',
               'type', 'method', 'days', 'location', 'startTime', 'endTime',
               'primary_instructor', 'secondary_instructors', 'syllabus', 'attributes')
    sections = csv.DictWriter(section_output, headers)
    sections.writeheader()

    # these allow constant-time lookups to see if a key is already present,
    # as opposed to sets, which require linear search
    # the reason for lookups is because the parsing is still imperfect;
    # this allows warning when a key already exists in the dict
    instructor_dict = {}
    # this should be a set but we need a primary key; index serves this purpose
    # TODO: switch to ordered set: https://pypi.org/project/ordered-set/
    # see https://github.com/jyn514/GradeForge/issues/20 for details
    terms = []

    doc = etree.parse(file_handle, etree.HTMLParser())
    rows = doc.xpath('/html/body//table[@class="datadisplaytable" '
                                       'and @width="100%"][1]/tr[position() > 2]')
    assert not len(rows) & 1  # even
    HEADER = True
    for row in rows:
        if HEADER:
            course = {}
            text = re.split(r'\W-\W', row.xpath('th/a[1]/text()')[0])
            # everything before last three is title
            course['UID'], course_id, course['section'] = text[-3:]
            course['department'], course['code'] = re.split(r'\W+', course_id)
        else:
            main = row.xpath('td[1]')[0]

            after = main.xpath('(.|a|b|p)/span/following-sibling::text()')
            after = tuple(map(str.strip, filter(lambda x: x != '\n', after)))

            term = {}
            try:  # this is always first point of failure for parser
                semester_raw, registration = after[:2]  # third is level, which we know
            except Exception:
                LOGGER.debug("%s %s %s %s", after, course, list(main), text)
                raise

            term['semester'] = parse_semester(*re.split(r'\W+', semester_raw))
            term['registrationStart'], term['registrationEnd'] = map(lambda s: re.sub(r'\W+', ' ', s),
                                                                     registration.split(' to '))

            if len(after) == 8:
                course['attributes'] = after[3]
            campus, schedule_type, method = after[-4:-1]  # last is credits
            course['campus'] = campus.replace('USC ', '').replace(' Campus', '')
            course['type'] = schedule_type.replace(' Schedule Type', '')
            course['method'] = method.replace(' Instructional Method', '')

            syllabus = main.xpath('(.|b|p)/a[position() = 3]/@href')
            if syllabus:
                if syllabus[0].startswith('/'):
                    course['syllabus'] = BASE_URL + syllabus[0]
                else:
                    LOGGER.debug("syllabus '%s' doesn't start with '/'", syllabus)
                    course['syllabus'] = syllabus[0]

            inner_row = main.xpath('table/tr[2]')
            if inner_row:
                assert len(inner_row) == 1, (row, course)
                _parse_inner_row(inner_row[0], course, term, instructor_dict)

            for key, value in term.items():
                if key != 'semester' and value is not None:
                    'Aug 24, 2018 -> 2018-08-24'
                    term[key] = datetime.strptime(value.replace(',', ''),
                                                  "%b %d %Y").date().isoformat()
            try:
                course['term'] = terms.index(term)
            except ValueError:
                terms.append(term)
                course['term'] = len(terms) - 1
            sections.writerow(course)
            # error instead of silently addding wrong info when rows/headers out of order
            del course
        HEADER = not HEADER

    instructors = csv.writer(instructor_output)
    instructor_output.write('name, email\n')
    instructors.writerows(instructor_dict.items())

    headers = 'semester', 'startDate', 'endDate', 'registrationStart', 'registrationEnd'
    term_writer = csv.DictWriter(term_output, headers)
    term_writer.writeheader()
    term_writer.writerows(terms)


def parse_exam(file_handle, output=stdout):
    '''Writes a csv to `output`, with headers.
    Quite fast compared to parse_sections, but it's handling less data.

    Params:
        - file_handle: str or implements `read`
        - semester: the semester to use for every exam in the csv.
                    default is to infer from file_handle name.
                    custom is to use USC semester (use utils.parse_semester).
        - output: same type as file_handle, where to write the csv
    '''
    if not hasattr(output, 'write'):
        with open(output, 'w') as writable:
            parse_exam(file_handle, writable)
            return

    def parse_days(text):
        '''
        'Monday/Wednesday/Friday Meeting Times' -> 'MWF'
        'Monday Only Meetings Times' -> 'M'
        '''
        days = {'Monday': 'M',
                'Tuesday': 'T',
                'Wednesday': 'W',
                'Thursday': 'R',
                'Friday': 'F',
                'Saturday': 'S',
                'Sunday': 'U'}

        text = text.split(' Meeting Times')[0].replace('\xa0', ' ')
        if 'Session' in text:
            return text  # don't mess with this
        elif 'Only' in text:
            return days[text.split(' Only')[0]]
        return ''.join(days[d] for d in text.split('/'))

    def parse_exam_datetime(datetime):
        '''str -> (date:str, time:str)

        There are five cases to handle.
        0. 'TBA'
        1. <month>\.? <day>, <day of week>, regular class meeting time
        2. <day of week>, <month>\.?, <day> - normal class meeting time
        3. <month>\. <day>, <day of week> - <time>
        4. <day of week> <month> <day> - <time>
        '''
        # case 0
        if datetime == 'TBA':
            return 'TBA', 'TBA'
        # case 1, no dash
        if 'regular class meeting time' in datetime.lower():
            exam_time = None
            exam_date = datetime.split(',')[0]
        else:
            date, time = re.split(r'\s*[–-]\s*', datetime)
            # case 2
            if 'normal class meeting time' in time.lower():
                exam_time = None
                exam_date = date[date.index(', ') + 2:]
            # case 3
            elif ',' in date:
                exam_time = army_time(time)
                exam_date = date.split(', ')[0]
            # case 4
            else:
                exam_time = army_time(time)
                exam_date = date[date.index(' ') + 1:]
        exam_date = re.sub(r'(th|nd|st|rd)\s*$', '', exam_date).replace('.', '')
        return exam_date, exam_time

    doc = etree.parse(file_handle, etree.HTMLParser())

    title = doc.xpath('/html/head/title/text()')[0]
    semester = title.split(' - ')[0].replace('Final Exam Schedule ', '')
    semester = parse_semester(*semester.split(' '))

    div = doc.xpath('/html/body/section/div/div/section[2]/div/section/div/div/section')[0]
    csv_headers = 'semester', 'days', 'time_met', 'exam_date', 'exam_time'
    writer = csv.DictWriter(output, csv_headers)
    writer.writeheader()

    headers = div.xpath('div[@class="accordion-summary"]/h5')
    bodies = div.xpath('div[@class="accordion-details"]/table/tbody')
    for i, header in enumerate(headers):
        try:
            days_met = parse_days(header.text)
        # given session, not days. Ex: 'Spring I (3A) and Spring II (3B)'
        except KeyError:
            terms = re.findall(r'\(([0-9][A-Z])\)', header.text)
            days_met = ','.join(terms)

        for row in bodies[i].findall('tr'):
            current = {'semester': semester, 'days': days_met}
            # Example: ('TR - 8:30 a.m.', 'Thursday, May 3 - 9:00 a.m.')
            # school likes to put some as spans, some not
            time_met, exam_datetime = map(lambda td: ''.join(td.itertext())
                                          .strip()
                                          .replace('\xa0', ' '),
                                          row.findall('td'))

            exam_date, exam_time = parse_exam_datetime(exam_datetime)

            if 'all sections' in time_met.lower():
                # TODO: add post-processing
                if exam_time is None:
                    exam_time = 'any'
                current.update({'time_met': 'any', 'exam_time': exam_time,
                                'exam_date': exam_date})
                writer.writerow(current)
            else:
                split = re.split(r'\s*[MTWRFSU]+\s+(-\s+)?', time_met)
                # example: '8:30 a.m.,11:40 a.m., 2:50 p.m., 6:00 p.m.'
                for time in re.split(', ?', split[-1]):
                    time = army_time(time)
                    copy = current.copy()
                    if exam_time is None:
                        copy['exam_time'] = time
                    else:
                        copy['exam_time'] = exam_time
                    copy.update({'time_met': time, 'exam_date': exam_date})
                    writer.writerow(copy)

def get_seats(section_link):
    'str -> (capacity, taken, remaining)'
    document = etree.fromstring(get(section_link).text, parser=etree.HTMLParser())
    return document.xpath('/html/body//table[@class="datadisplaytable"]/tr[2]/td'
                          '//table/tr[2]/td/text()')


def parse_bookstore(file_handle, output=stdout):
    '''
    Implemented:
    - name
    - ISBN
    - prices
        Note that if price is not available on bookstore,
        it is not entered as a key
        - used rent
        - new rent
        - used buy
        - new buy
    - link
    - author
    - edition
    - required/recommended/optional

    Not implemented:
    - price on amazon, abebooks, etc
    '''

    if not hasattr(output, 'write'):
        with open(output, 'w') as writable:
            parse_bookstore(file_handle, writable)
            return
    doc = etree.parse(file_handle, etree.HTMLParser())
    xpath = ('/html/body/header/section/div[@class="courseMaterialsList"]'
             '/div/form[@id="courseListForm"]')
    form = doc.xpath(xpath)[0]
    books = form.xpath('div[@class="book_sec"]/div/div[@class="book-list"]/div')

    # TODO: sometimes prices are missing. need to handle this gracefully
    headers = ('title', 'required', 'author', 'edition', 'publisher', 'isbn',
               'image', 'link', 'buy-new', 'buy-used', 'rent-new', 'rent-used')
    writer = csv.DictWriter(output, headers)
    writer.writeheader()
    for book in books:
        info = {}

        info['image'] = book.xpath('div[2]/a/img/@src')[0]

        main = book.find('div[3]')

        anchor = main.xpath('h1/a')[0]
        info['link'] = anchor.attrib['href']
        info['title'] = anchor.attrib['title']

        xpath = 'h2/span[@class="recommendBookType"]/text()'
        info['required'] = main.xpath(xpath)[0].strip().lower()
        info['author'] = main.xpath('h2/span/i/text()')[0].replace('By ', '')

        clean = lambda s: s.tail.replace('\xa0', '').replace('Â', '').strip()
        info['edition'], info['publisher'], info['isbn'] = map(clean, main.xpath('ul/li/strong'))
        prices = book.xpath('div[4]/div[@class="selectBookCont"]/div/ul/li[2]/ul/li')
        for p in prices:
            info[p.attrib['title'].lower().strip().replace(' ', '-')] = p.find('span').text.strip()
        writer.writerow(info)


def parse_grades(file_handle, output=stdout):
    '''File_handle is assumed to contain the output of `pdftotext -layout <pdf>`'''
    if not hasattr(file_handle, 'read'):
        with open(file_handle) as readable:
            parse_grades(readable, output)
            return

    if not hasattr(output, 'write'):
        with open(output, 'w') as writable:
            parse_grades(file_handle, writable)
            return

    while True:  # sometimes header is not on first line
        metadata = next(file_handle).strip()
        metadata = re.sub(r'\s?GRADE\s?(SPREAD FOR|DISTRIBUTION)', '', metadata)
        match = re.search(r'(FALL|SUMMER|SPRING)?\s?([0-9]{4})', metadata, re.IGNORECASE)
        if match is not None:
            season, year = match.groups()
            break
    if season is None:
        LOGGER.warning("'%s' does not have enough info to parse semester, assuming season is Spring", metadata)
        season = 'spring'
    semester = parse_semester(season, year)
    try:
        expr = r'((THE\s)?UNIVERSITY\sOF\sSOUTH\sCAROLINA\s?([‐-]|at)\s?|USC[‐\s-])([^:]*)'
        campus = re.search(expr, metadata, flags=re.IGNORECASE)
        campus = re.sub(r'\sCAMPUS', '', campus.groups()[0]).upper()
    except Exception:
        LOGGER.debug(metadata)
        raise
    while True:
        try:
            headers = next(file_handle)
        except StopIteration:
            LOGGER.debug(file_handle)
            raise
        if re.match(r'\s*DEP(ar)?T', headers, flags=re.IGNORECASE) is not None:
            headers = headers.upper()
            headers = re.sub(r'DEP(AR)?T(\.|MENT)?', 'DEPARTMENT', headers)
            headers = re.sub(r'SEC(T(ION)?)?\.?', 'SECTION', headers)
            headers = re.sub(r'C(OU)?RSE(\s?#)?', 'CODE', headers)
            headers = headers.replace('DEPARTMENT/CODE', 'DEPARTMENT CODE')
            headers = headers.replace('AUD', 'AUDIT')
            headers = re.sub(r'\sI\s', ' INCOMPLETE ', headers).split()
            break
    if len(headers) < 18:
        raise ValueError("Bad value '%s' for headers" % headers)
    output.write(','.join(['SEMESTER', 'CAMPUS'] + headers) + '\n')
    # all of these functions are generators, which require very low memory usage
    csv.writer(output).writerows(map(lambda s: [semester, campus] + s,
                                     filter(lambda l: len(l) == len(headers),
                                            map(str.split, file_handle))))
