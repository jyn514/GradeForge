#!/usr/bin/env python3

import lxml.etree
import argparse
import sys
import re
from graphviz import Digraph
import csv

def verbose(msg):
    #  return
    msg = "{}\n".format(msg)
    sys.stderr.write(msg)
    sys.stderr.flush()

def next_state(current_state, transition_table, text):

    # consider all possible transitions away from the current state
    for transition_tup in transition_table[current_state]:

        # unpack the tuple into it's component pats
        pattern, transition, field = transition_tup

        # check if it matches the pattern
        r = re.compile(pattern)
        if r.match(text):
            verbose("{} --- ('{}' matched '{}' => {}) ---> {}"
                    .format(current_state, text, pattern,
                            field, transition))

            # extra debugging output for ERROR fields
            if field == "ERROR":
                verbose("error transition while matching " +
                        "'{}' which is {} from state {}"
                        .format(
                            text, ':'.join([hex(ord(x))[2:] for x in text]),
                            current_state))
                verbose ("other transitions were: {}"
                         .format(transition_table[current_state]))

            return (transition, field)

    # if execution reaches this point, the transition table is invalid
    sys.stderr.write("FATAL: invalid transition table\n")
    exit(1)


def visualize_transitions(table):
    dot = Digraph(comment='Transition Table')
    for node_num in range(len(table)):
        nodelabel = "({})\n".format(node_num)
        transitions = table[node_num]
        t_num = 0
        for t in transitions:
            pattern, target, field = t

            # render nbsp literals
            pattern = pattern.replace("\xc2", "\\\\xc2")
            pattern = pattern.replace("\xa0", "\\\\xa0")

            # render epsilon transitions
            if pattern == "":
                pattern = "epsilon"

            pattern = "{}: {}\n".format(t_num, pattern)

            dot.edge("{}".format(node_num),
                     "{}".format(target),
                     label = pattern)
            nodelabel += "{}: ".format(t_num) + field + "\n"
            t_num += 1


        dot.node("{}".format(node_num), label=nodelabel)
    dot.render("table.gv", view=True)

def record2csv(rec):
    columns = ["CRN", "SELECT", "DEPARTMENT", "COURSECODE",
               "SECTION", "CAMPUS", "CREDITHOURS", " PARTOFTERM",
               "COURSETITLE", "DAY", "TIME", "CAPACITY", "ACTUAL", "REMAINING",
               "INSTRUCTOR", "DATERANGE", "LOCATION", "ATTRIBUTE"]

    depth = 1
    for k in rec:
        if len(rec[k]) > depth:
            depth = len(rec[k])

    for i in range(depth):
        cols = []
        for col in columns:
            s = ""
            if col in rec:
                if len(rec[col]) == 0:
                    s = "NULL"
                elif i >= len(rec[col]):
                    s = rec[col][0]
                else:
                    s = rec[col][i]

                s = s.replace('\xc2', ' ')
                s = s.replace('\xa0', ' ')
                s = ' '.join([x for x in s.split()])
            else:
                s = "NULL"

            cols.append(s)

        w = csv.writer(sys.stdout)
        w.writerow(cols)

def extractEntries(htmlPath, max_records):

    err_trans = ('', 0, "ERROR")
    daterange = '([0-9]{1,2}\/[0-9]{1,2}\-[0-9]{1,2}\/[0-9]{1,2}|None)'
    nbsp      = '(\xc2|\xa0)'
    dayofweek = '([MTWRFSU]|' + nbsp + '|None)'
    intornone = '([0-9-]|None)'
    location =  '([A-Z0-9]|' + nbsp + ')'

    # pattern, transition, field
    #
    # Note that anywhere where the field is NULL is matching an &nbsp literal
    transition_table = [
        [('None',                1, "CRN")],
        [('None',                2, "SELECT"),
         ('[A-Z]{4}',            3, "DEPARTMENT")],
        [('[A-Z]{4}',            3, "DEPARTMENT")],
        [('[A-Z]?[0-9]{3}[A-Z]?',4, "COURSECODE")],
        [('[0-9A-Z]+',           5, "SECTION")],
        [('[A-Z]+',              6, "CAMPUS")],
        [('[0-9\.[0-9]{1,3}',    7, "CREDITHOURS")],
        [('[a-zA-Z0-9]+',        8, "PARTOFTERM")],
        [('.*[a-zA-Z0-9].*',     9, "COURSETITLE")],
        [(dayofweek,            10, "DAY")],
        [('[a-zA-Z0-9]+',       11, "TIME")],
        [(intornone,            12, "CAPACITY")],
        [(intornone,            13, "ACTUAL")],
        [(intornone,            14, "REMAINING")],
        [('[a-zA-Z0-9()_ ]+',   15, "INSTRUCTOR")],
        [(daterange,            16, "DATERANGE")],
        [(location,             17, "LOCATION")],
        [('.*',                 18, "ATTRIBUTE")],
        [(nbsp,                 19, "NULL"),
         ('None',                1, "CRN")],
        [(nbsp,                 20, "NULL"),
         ('None',                1, "CRN")],
        [(nbsp,                 21, "NULL")],
        [(nbsp,                 22, "NULL")],
        [(nbsp,                 23, "NULL")],
        [(nbsp,                 24, "NULL")],
        [(nbsp,                 25, "NULL")],
        [(nbsp,                 26, "NULL")],
        [(nbsp,                 27, "NULL")],
        [(dayofweek,            28, "DAY")],
        [('[a-zA-Z0-9]+',       29, "TIME")],
        [(nbsp,                 30, "NULL")],
        [(nbsp,                 31, "NULL")],
        [(nbsp,                 32, "NULL")],
        [('[a-zA-Z0-9()_ ]+',   33, "INSTRUCTOR")],
        [(daterange,            34, "DATERANGE")],
        [(location,             35, "LOCATION")],
        [('.*',                 36, "ATTRIBUTE")],
        [(nbsp,                 19, "NULL"),
         ('None',                1,  "CRN")],

    ]



    # every transition must also support the error transition
    for t in transition_table:
        t.append(err_trans)

    # uncomment to visualize table
    visualize_transitions(transition_table)

    verbose("Extracting entries from file '{}'".format(htmlPath))

    tree = lxml.etree.HTML(open(htmlPath, "r").read())
    verbose("Finished parsing HTML")

    # results will now contain every candidate td cell
    results = tree.xpath("//table[contains(@class, 'datadisplaytable')]/tr/td[contains(@class, 'dddefault')]")
    verbose("Finished extracting candidate td cells")

    current_state = 0
    counter = 1
    field = None
    last_field = None
    records = []
    accumulator = {}

    # iterate over every td candidate
    for element in results:

        # get the next state from the transition table
        text = str(element.text)
        last_field = field
        current_state, field = \
            next_state(current_state, transition_table, text)

        # remove extraneous parens from instructor field
        if field == "INSTRUCTOR":
            text = text.replace('(', '')
            text = text.replace(')', '')
            text = text.strip()

        # make sure the transition was valid
        if field == "ERROR":
            sys.stderr.write("FATAL: invalid transition while reading " +
                             "record {}\n".format(counter) )
            exit(1)

        # insert the field into the accumulator
        if field != "NULL":
            if field not in accumulator:
                accumulator[field] = []
            accumulator[field].append(text)


        # transition to parsing a new record
        if last_field == "ATTRIBUTE" and field == "CRN":
            records.append(accumulator)
            verbose("Finished parsing a record: {}".format(accumulator))
            record2csv(accumulator)
            accumulator = {}

            counter += 1

            if (counter > max_records) and (max_records > 0):
                break




def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--html_path", "-i", required=True)
    parser.add_argument("--max_records", "-m", default=-1, type=int)

    args = parser.parse_args()

    extractEntries(args.html_path, args.max_records)


if __name__ == "__main__":
    main()
