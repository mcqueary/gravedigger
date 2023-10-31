import argparse
# import logging as log
import os.path
import urllib.error
import urllib.request
from urllib.request import Request, urlopen

# import sqlite3 as sql
from bs4 import BeautifulSoup

from db import addRowToDatabase, makeGraveDatabase, addRowToOutputFile

problemchilds = []
CONNECT = False

if CONNECT:
    if not os.path.isfile("./graves.db"):
        makeGraveDatabase()


def findagravecitation(graveid):
    grave = {}
    grave["id"] = graveid

    url = "http://www.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid="
    url += str(graveid)
    grave["url"] = url

    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(urlopen(req).read(), "lxml")
    except urllib.error.HTTPError as err:
        print(f"An HTTPError was thrown: {err.code} {err.reason}")
    except Exception as e:
        print(
            "The following error was thrown when reading this grave: ", e
        )

    # Get name
    try:
        name = soup.find("h1", id="bio-name").get_text()
        name = name.replace("Famous memorial", "")
        name = name.replace("VVeteran", "")
        name = name.strip()
        grave["name"] = name
    except Exception as e:
                print(
            "The following error was thrown when getting the name from this grave: ", e
        )

    # Get Birth Date
    try:
        birthDate = soup.find("time", itemprop="birthDate").get_text()
        grave["birth"] = birthDate
    except Exception as e:
        print(
            "The following error was thrown when getting the birthDate from this grave: ",
            e,
        )

    # Get Birth Place
    try:
        birthPlace = soup.find("div", itemprop="birthPlace").get_text()
        grave["birthplace"] = birthPlace
    except Exception as e:
        print(
            "The following error was thrown when getting the birthPlace from this grave: ",
            e,
        )

    # Get Death Date
    try:
        deathDate = soup.find("span", itemprop="deathDate").get_text()
        deathDate = deathDate.split('(')[0].strip()
        grave["death"] = deathDate
    except Exception as e:
        print(
            "The following error was thrown when getting the deathDate from this grave: ",
            e,
        )

    # Get Death Place
    try:
        deathPlace = soup.find("div", itemprop="deathPlace").get_text()
        grave['deathplace'] = deathPlace
    except Exception as e:
        print(
            "The following error was thrown when getting the deathPlace from this grave: ",
            e,
        )

    if (len(output_filename) > 0):
        addRowToOutputFile(output_file_handle, grave)

    if CONNECT:
        addRowToDatabase(grave)

    return grave

# main

graveids = []
numcites = 0
numids = 0
output_filename=""
DEFAULT_INPUT_FILENAME = "input.txt"

# Process arguments

parser = argparse.ArgumentParser(description='Scrape FindAGrave memorials.')
parser.add_argument('--ifile', type=str, default=DEFAULT_INPUT_FILENAME,
                    help='the input file containing findagrave URLs/IDs (default: input.txt)')
parser.add_argument('--ofile', type=str, required=False,
                    help='the desired output file for collected data')
parser.add_argument('--db', type=str, required=False,
                    help='store the collected information in the specified SQLite db')
args = parser.parse_args()

input_filename = args.ifile
print ("ifile: " + args.ifile)
if args.ofile is not None:
    output_filename=args.ofile
    print ("ofile: " + output_filename)
    try:
        output_file_handle = open(output_filename, 'w')
    except Exception as e:
        print("Error opening output file" + e)

# # read from gedcom
# with open('tree.ged', encoding='utf8') as ged:
#     for line in ged.readlines():
#         numcites+=1
#         if '_LINK ' in line and 'findagrave.com' in line:
#             for unit in line.split('&'):
#                 if 'GRid=' in unit:
#                     if unit[5:-1] not in graveids:
#                         graveids.append(unit[5:-1])
#                         #print(graveids[numids])
#                         numids+=1

# read from text file
with open(input_filename, encoding="utf8") as txt:
    for line in txt.readlines():
        numcites += 1
        if "findagrave.com" in line:
            for unit in line.split("&"):
                if "GRid=" in unit:
                    if unit[5:-1] not in graveids:
                        graveids.append(unit[5:-1])
                        numids += 1
        elif line not in graveids:
            graveids.append(line)
            numids += 1

parsed = 0
failedids = []
for i, gid in enumerate(graveids):
    try:
        print(str(i + 1) + " of " + str(numids))
        print(findagravecitation(gid)['id'] + "\n\n")
        parsed += 1
    except Exception as e:
        print("Error: ", e)
        print("Unable to parse Memorial #" + str(gid) + "!\n\n")
        failedids.append(gid)

out = "Successfully parsed " + str(parsed) + " of "
out += str(len(graveids))
print(out)
if len(problemchilds) > 0:
    print("\nProblem childz were:", problemchilds)

# with open('results.txt', 'w') as f:
#     f.write(out + '\n')
#     f.write('\nProblem childz were:\n')
#     f.write('\n'.join(problemchilds))
#     f.write('\nUnable to parse:\n')
#     f.write('\n'.join(failedids))