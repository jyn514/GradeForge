#!/usr/bin/env python3

import csv
import argparse
import re
import sys
import matplotlib.pyplot as plt

def parseWebData(s):
    print("query string is: {}".format(s))
    r = re.compile('\=.*?\&')
    return [s[1:-1] for s in r.findall(s)]


def compare(queryList, ssc, xls):
    ssc_results = []
    xls_results = []
    for row in xls:
        if(row[0] == queryList[0] and
           row[1] == queryList[1] and
           row[2] == queryList[2]):
           xls_results = row
           break

    for row in ssc:
        if(row[2] == queryList[0] and
           row[3] == queryList[1] and
           row[4] == queryList[2]):
           ssc_results = row
           break

    return(xls_results, ssc_results)

#  def sendFail():


#handle multiple files?
#input as argv too?
#  parser = argparse.ArgumentParser(
                            #  description="Merges grade spreads and SSC data.")

#  parser.add_argument("files", nargs="*",
#                      help="List of files to dump tags for",
#                      default=[])

#  args = parser.parse_args()

xls_data = "201701_grade_spread_report.csv"
ssc_data = "../cad/out.csv"

xls_data = [r for r in csv.reader(open(xls_data, 'r', encoding="utf-8"))]
ssc_data = [r for r in csv.reader(open(ssc_data, 'r'))]

#  file_list = args.files
#  if args.input is not None:
#      with open(args.input, 'r') as f:
#          for line in f:
#              file_list.append(line.strip())
#
#  queryList = parseWebData("'prefix=CSCE&course-number=145&section=001&'")
queryList = parseWebData(sys.argv[1])

xls, ssc = compare(queryList, ssc_data, xls_data)

print(xls)
print(ssc)

profName = ssc[14]
courseName = ssc[8]
courseCode = "{}{} (S: {})".format(ssc[2], ssc[3], ssc[4])
distr = {
    "A" : xls[6],
    "B" : xls[8],
    "B+" : xls[10],
    "C" : xls[12],
    "C+" : xls[14],
    "D" : xls[16],
    "D+" : xls[18],
    "F" : xls[20],
    "I" : xls[23],
    "W" : xls[31],
    "WF" : xls[32],
}

for k in distr:
    distr[k] = int(distr[k])

print(profName, courseName, courseCode, distr)

D = distr

ks = list(D.keys())
ks.sort()

vals = [D[k] for k in ks]

fig = plt.figure()
fig.suptitle("{} - {} - {}".format(profName, courseName, courseCode))

plt.bar(range(len(D)), vals, align='center')
plt.xticks(range(len(D)), ks)

#  plt.show()
plt.savefig("test.png")

