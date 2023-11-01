import argparse
import logging as log
import os.path
import re
import sys
import urllib.error
import urllib.request
from urllib.request import Request, urlopen

# import sqlite3 as sql
from bs4 import BeautifulSoup
from db import addRowToDatabase, makeGraveDatabase, addRowToOutputFile

# Constants
DEFAULT_DB_FILE_NAME = "graves.db"
DEFAULT_INPUT_FILE = sys.stdin
DEFAULT_OUTPUT_FILE = sys.stdout
DEFAULT_LOG_LINE_FMT = "%(asctime)s %(levelname)s %(message)s"
DEFAULT_LOG_DATE_FMT = "%m/%d/%Y %I:%M:%S %p"
DEFAULT_LOG_LEVEL = "DEBUG"

log_level = DEFAULT_LOG_LEVEL
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
        log.exception(f"An HTTPError was thrown: {err.code} {err.reason}")
    except Exception as e:
        log.exception("The following error was thrown when reading this grave: ", e)

    # Get name
    try:
        name = soup.find("h1", id="bio-name").get_text()
        name = name.replace("Famous memorial", "")
        name = name.replace("VVeteran", "")
        name = name.strip()
        grave["name"] = name
    except Exception as e:
        log.exception(
            "The following error was thrown when getting the name from this grave: ", e
        )

    # Get Birth Date
    try:
        result = soup.find("time", itemprop="birthDate")
        if result is not None:
            grave["birth"] = result.get_text()
    except Exception as e:
        log.exception(
            "The following error was thrown when getting the birth date from this grave: ",
            e,
        )

    # Get Birth Place
    try:
        result = soup.find("div", itemprop="birthPlace")
        if result is not None:
            grave["birthplace"] = result.get_text()
        else:
            grave["birthplace"] = None
    except Exception as e:
        log.exception(
            "The following error was thrown when getting the birth place from this grave: ",
            e,
        )

    # Get Death Date
    try:
        result = soup.find("span", itemprop="deathDate")
        if result is not None:
            death_date = result.get_text().split("(")[0].strip()
            grave["death"] = death_date
        else:
            grave["death"] = None
    except Exception as e:
        log.exception(
            "The following error was thrown when getting the death date from this grave: ",
            e,
        )

    # Get Death Place
    try:
        result = soup.find("div", itemprop="deathPlace")
        if result is not None:
            grave["deathplace"] = result.get_text()
        else:
            grave["deathplace"] = None
    except Exception as e:
        log.exception(
            "The following error was thrown when getting the death place from this grave: ",
            e,
        )

    # Get Plot
    try:
        result = soup.find("span", id="plotValueLabel")
        if result is not None:
            grave["plot"] = result.get_text()
    except Exception as e:
        log.exception(
            "The following error was thrown when getting the burial plot from this grave: ",
            e,
        )

    addRowToOutputFile(output_file, grave)

    if args.dbfile is not None:
        addRowToDatabase(args.dbfile, grave)

    return grave


# main

graveids = []
numcites = 0
numids = 0

# Process arguments

parser = argparse.ArgumentParser(description="Scrape FindAGrave memorials.")
parser.add_argument(
    "-i",
    "--ifile",
    type=argparse.FileType("r", encoding="UTF-8"),
    required=True,
    default=DEFAULT_INPUT_FILE,
    help="the input file containing findagrave URLs/IDs (default: input.txt)",
)
parser.add_argument(
    "-o",
    "--ofile",
    type=argparse.FileType("w", encoding="UTF-8"),
    required=False,
    default=DEFAULT_OUTPUT_FILE,
    help="the desired output file for collected data",
)
parser.add_argument(
    "--dbfile",
    type=str,
    required=False,
    help="store the collected information in the specified SQLite db file",
)
parser.add_argument(
    "--log",
    type=str,
    required=False,
    help="log level, e.g. DEBUG, INFO, WARNING, ERROR, CRITICAL",
)
args = parser.parse_args()

# Configure logging
log_level = DEFAULT_LOG_LEVEL
if args.log is not None:
    log_level = args.log
log.basicConfig(
    format=DEFAULT_LOG_LINE_FMT, datefmt=DEFAULT_LOG_DATE_FMT, level=log_level
)
log.debug("Log level is " + str(log_level))

# Configure input file
input_file = args.ifile
log.debug("ifile: " + input_file.name)

# Configure output file, if any
if args.ofile is not None:
    output_file = args.ofile
    log.info("ofile: " + output_file.name)

# Configure output database, if any
if args.dbfile is not None:
    db_file_name = args.dbfile
    if not os.path.exists(db_file_name):
        makeGraveDatabase(db_file_name)

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
for line in args.ifile.readlines():
    numcites += 1
    currid = re.match('.*?([0-9]+)$', line).group(1)
    if currid not in graveids:
        graveids.append(currid)
        numids+=1
    elif line not in graveids:
        graveids.append(line)
        numids += 1

parsed = 0
failedids = []
for i, gid in enumerate(graveids):
    try:
        log.info(str(i + 1) + " of " + str(numids) + ":")
        findagravecitation(gid)
        parsed += 1
    except Exception as e:
        log.error("Unable to parse Memorial #" + str(gid) + "!", e)
        failedids.append(gid)

out = "Successfully parsed " + str(parsed) + " of "
out += str(len(graveids))
log.info(out)
if len(problemchilds) > 0:
    log.debug("\nProblem childz were:", problemchilds)

# with open('results.txt', 'w') as f:
#     f.write(out + '\n')
#     f.write('\nProblem childz were:\n')
#     f.write('\n'.join(problemchilds))
#     f.write('\nUnable to parse:\n')
#     f.write('\n'.join(failedids))
