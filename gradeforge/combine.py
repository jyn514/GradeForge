'''Stage three of data collection. Given many files of a given category,
combine them into a single enormous file as befits the category.'''

import csv
from sys import stdout

import pandas

def ensure_open(file_handle, read=True):
    '''given either a path or a file descriptor, return a file descriptor'''
    mode = 'read' if read else 'write'
    if hasattr(file_handle, mode):
        return file_handle
    return open(file_handle, mode[0])


def combine_grades(file_handles, output=stdout):
    '''The headers for CSV files change from file to file.
    This method normalizes headers and adds empty strings if needed.'''
    headers = ('SEMESTER,CAMPUS,DEPARTMENT,CODE,SECTION,TITLE,A,B+,B,C+,C,D+,D,F,'
               'A_GF,B+_GF,B_GF,C_GF,C+_GF,D+_GF,D_GF,F_GF,'
               'S,U,UN,INCOMPLETE,W,WF,NR,TOTAL,No Grade,T,IP,FN,AUDIT')
    output = ensure_open(output, read=False)
    writer = csv.DictWriter(output, headers.split(','))
    writer.writeheader()
    for handle in file_handles:
        handle = ensure_open(handle)
        writer.writerows(csv.DictReader(handle))
        handle.close()
    output.close()


def simple_combine(files, output=stdout, unique=False):
    '''Given some CSV files, slap them together.
    We don't use `cut` because it can't catch duplicates.
    unique: columns to drop if duplicated; if falsy, don't drop anything'''
    result = pandas.concat(map(pandas.read_csv, files), axis=0, ignore_index=True)
    if unique:
        result = result.drop_duplicates(unique)
    result.to_csv(output, index=False)


def combine_departments(files, output=stdout):
    '''just a little wrapper'''
    simple_combine(files, output, unique='code')


def combine_instructors(files, output=stdout):
    '''just a little wrapper'''
    simple_combine(files, output, unique='name')


def combine_terms(file_handles, output=stdout):
    '''This needs to be stateful so that terms with the same key still match
    the correct sections. As a result, it's pretty slow. Context: terms have no
    primary key, we used their index when parsing. If we didn't change it now,
    we'd have the same key point to multiple different terms.'''
    base = pandas.read_csv(file_handles[0])
    i = len(base)
    for handle in file_handles[1:]:
        current = pandas.read_csv(handle)
        base = pandas.concat((base, current), axis=0, ignore_index=True)
        name = handle.name if hasattr('read', handle) else handle
        section_handle = name.replace('.terms', '')
        sections = pandas.read_csv(section_handle)
        # broadcast operation, done to every value in the column 'term'
        # https://docs.scipy.org/doc/numpy/user/basics.broadcasting.html
        sections['term'] += i
        # write it straight back to disk
        sections.to_csv(section_handle, index=False)
        i += len(current)
    base.to_csv(output, index_label='id')
