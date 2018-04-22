#!/usr/bin/env python

'''HTML parsing. Generally, works only on files, not on strings'''

from __future__ import print_function, generators
from os.path import exists
from sys import stderr, stdin, stdout

from lxml.etree import iterparse, XMLSyntaxError

from utils import DAYS, save, load, army_time, parse_semester
from post import  get_calendar, get_bookstore

def parse_catalog(html):
    '''
    lxml.etree.iterparse -> (classes, departments)
        where classes = [c...]
            where c.keys() = ('code', 'abbr', 'title')
        where departments = {short: long for header in html}
    '''
    classes = []
    departments = {}
    code = True
    for event, elem in html:
        if event == 'end' and elem.text is not None and elem.text != '\n':
            if elem.tag == 'th':
                header = elem.text.split(' - ')
                departments[header[0]] = header[1]
            elif elem.tag == 'td':
                if code:
                    current = {'code': elem.text, 'abbr': header[0]}
                else:
                    current.update({'title': elem.text})
                    classes.append(current)
                code = not code
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
                course = {'section_link': base_url + elem.attrib.get('href', None)}
                course['title'], course['UID'], tmp, course['section'] = elem.text.split(' - ')
                course['abbr'], course['code'] = tmp.split(' ')
            elif elem.tag == 'span' and elem.attrib.get('class', None) == 'fieldlabeltext':
                following = elem.tail.strip()
                if elem.text == 'Associated Term: ':
                    course['semester'] = following
                elif elem.text == 'Registration Dates: ':
                    course['registration_start'], course['registration_end'] = following.split(' to ')
                elif elem.text == 'Levels: ':
                    course['level'] = following
                    elem = elem.getnext().getnext()
                    if elem.tag == 'span':
                        course['attributes'] = elem.tail.strip()
                        elem = elem.getnext().getnext()
                    course['campus'] = elem.tail.strip().split(' Campus')[0]
                    elem = elem.getnext()
                    course['type'] = elem.tail.strip().split(' Schedule Type')[0]
                    elem = elem.getnext()
                    course['method'] = elem.tail.strip().split(' Instructional Method')[0]
                    elem = elem.getnext()
                    course['credits'] = int(elem.tail.strip().split('.000')[0])
            elif elem.tag == 'a':
                if elem.text == 'View Catalog Entry':
                    # TODO: get restrictions
                    # TODO: get description
                    # URL looks like this: base_url +
                    #     /BANP/bwckctlg.p_disp_course_detail?cat_term_in=201808&subj_code_in=ACCT&crse_numb_in=225
                    # can also follow and parse link below
                    course['catalog_link'] = base_url + elem.attrib.get('href', None)
                elif elem.text == 'Bookstore':
                    # TODO: link directly to bookstore
                    # currently, looks like
                    # /BANP/bwckbook.site?p_term_in=201808&p_subj_in=ACCT&p_crse_numb_in=222&p_seq_in=001
                    # should be https://secure.bncollege.com/webapp/wcs/stores/servlet/TBListView
                    # requires POST
                    course['bookstore_link'] = base_url + elem.attrib.get('href', None)
            elif elem.tag == 'table' and elem.attrib.get('class', None) == 'datadisplaytable' and elem.attrib.get('summary', None).endswith('this class..'):
                for i, column in enumerate(elem.find('./tr[2]')):
                    if i == 0:
                        assert column.text == 'Class'
                    elif i == 1:
                        if column.text is None:
                            course['start_time'] = column.text
                            course['end_time'] = column.text
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
            print(elem, elem.text, elem.attrib, course)
            if 'following' in locals():
                print(following)
            if 'i' in locals() or 'column' in locals():
                print(i, column, column.text)
            raise
    return sections


def parse_days(text):
    text = text.split(' Meeting Times')[0]
    if 'Only' in text:
        return DAYS[text.split(' Only')[0]]
    return ''.join(DAYS[d] for d in text.split('/'))


def parse_exam(html):
    return {parse_days(elem.text): {row.find('td').text.split(' - ')[1]:
                                    row.find('span').text
                                    for row in elem.getparent().getnext().find('table').find('tbody').findall('tr')}
            for _, elem in html if elem.tag == 'h5'}


def parse_all_exams():
    result = {}
    for year in range(13, 19):
        for semester in ('spring', 'summer', 'fall'):
            name = '20' + str(year) + parse_semester(semester)[-2:]
            if not exists(name + '.html'):
                save(get_calendar('20' + str(year), semester), name + '.html')
            with open(name + '.html', 'rb') as stdin:
                result[name] = parse_exam(iterparse(stdin, html=True))
    return result


def clean_sections(sections):
    if 'exams' not in globals():
        exams = load('.exams.data')
    for s in sections:
        s['start_time'] = army_time(s['start_time'])
        s['end_time'] = army_time(s['end_time'])
        s['final_exam'] = exams[s['semester']][s['days']][s['start_time']]


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


def get_books(semester, department, number, section):
    '''Example: https://ssb.onecarolina.sc.edu/BANP/bwckbook.site?p_term_in=201808&p_subj_in=ACCT&p_crse_numb_in=222&p_seq_in=001'''
    base_url = 'https://ssb.onecarolina.sc.edu/BANP/bwckbook.site'
    redirect = "%s?p_term_in=%s&p_subj_in=%s&p_crse_numb_in=%s&p_seq_in=%s" % base_url, semester, department, number, section
    return parse_b_and_n(get_bookstore(semester, department, number, section))


def main(args):
    if args.load:
        print(load(args.output))
    elif args.save or args.verbose:
        if args.sections:
            with open(args.input, 'rb') as stdin:
                result = clean_sections(parse_sections(iterparse(stdin, html=True)))
        elif args.catalog:
            with open(args.input, 'rb') as stdin:
                result = parse_catalog(iterparse(stdin, html=True))
        else:
            result = parse_all_exams()
        if args.save:
            save(result, args.output)
        if args.verbose:
            print(result)


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
