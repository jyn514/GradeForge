#!/usr/bin/env python
from __future__ import print_function, generators
from argparse import ArgumentParser

from lxml.etree import iterparse
import cloudpickle

stdout = 'output.data'
document = 'USC_all_courses.html'

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
    Essentially a giant finite state autonoma because the HTML has very few recognizable patterns

    Working:
    - title
    - bookstore link
    - catalog link
    - section link
    - level (UG, grad, etc.)
    - registration start
    - registration end
    - section
    - abbr
    - number
    - UID (CCR code)
    - term
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
    - restrictions (have to follow catalog link to get)
    - direct bookstore link (should replace current redirect)
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
                for i, data in enumerate(elem.text.split(' - ')):
                    if i == 0:
                        course['title'] = data
                    elif i == 1:
                        course['UID'] = data
                    elif i == 2:
                        course['abbr'], course['number'] = data.split(' ')
                    else:
                        course['section'] = data
            elif elem.tag == 'span' and elem.attrib.get('class', None) == 'fieldlabeltext':
                following = elem.tail.strip()
                if elem.text == 'Associated Term: ':
                    course['term'] = following
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
                        if (column.text is None):
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


def load(stdin=stdout):
    with open(stdin, 'rb') as i:
        return cloudpickle.load(i)


def main(args):
    if args.load:
        print(load(args.output))
    elif args.sections:
        with open(args.input, 'rb') as stdin:
            print(parse_sections(iterparse(stdin, html=True)))
    elif args.save or args.verbose:
        with open(args.input, 'rb') as stdin:
            result = parse_catalog(iterparse(stdin, html=True))
        if args.save:
            with open(args.output, 'wb') as out:
                cloudpickle.dump(result, out)
        if args.verbose:
            print(result)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('input', help='HTML file', nargs='?', default=document)
    parser.add_argument('output', help='File to store binary', default=stdout,
                        nargs='?')
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--save', '-s', '--save-binary', action='store_true',
                        default=True,
                        help='Save result of main() in binary form')
    action.add_argument('--sections', action='store_true')
    action.add_argument('--load', '--print', '-l', action='store_true',
                        help='Show result on stdout')
    parser.add_argument('--verbose', '-v', help='Show result',
                        action='store_true')
    main(parser.parse_args())
