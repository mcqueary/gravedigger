import argparse
import csv
import logging as log
import os.path
import re
import sys

# import sqlite3 as sql
from gravedigger.db import add_row_to_database, make_grave_database
from gravedigger.soup import get_soup, get_name, get_birth_date, get_birth_place, get_death_date, get_death_place, get_burial_plot

# Constants
DEFAULT_DB_FILE_NAME = "graves.db"
DEFAULT_INPUT_FILE = sys.stdin
DEFAULT_OUTPUT_FILE = sys.stdout
DEFAULT_LOG_LINE_FMT = "%(asctime)s %(levelname)s %(message)s"
DEFAULT_LOG_DATE_FMT = "%m/%d/%Y %I:%M:%S %p"
DEFAULT_LOG_LEVEL = "DEBUG"
COLUMNS = [ 'id', 'url', 'name', 'birth', 'birthplace', 'death', 'deathplace', 'burial', 'plot', 'more_info']

log_level = DEFAULT_LOG_LEVEL
csvwriter = None
problemchilds = []
args = None

def findagravecitation(graveid):
    grave = {}
    grave['id'] = graveid

    url = "http://www.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid="
    url += str(graveid)
    grave['url'] = url

    tree = get_soup(url)

    # Get name
    grave['name'] = get_name(tree)

    # Get Birth Date
    grave['birth'] = get_birth_date(tree)

    # Get Birth Place
    grave['birthplace'] = get_birth_place(tree)

    # Get Death Date
    grave['death'] = get_death_date(tree)

    # Get Death Place
    grave['deathplace'] = get_death_place(tree)

    # Get Plot
    grave['plot'] = get_burial_plot(tree)

    if csvwriter is not None:
        try:
            csvwriter.writerow(grave)
        except Exception as e:
            log.exception('Exception encountered when writing row to CSV:', e)

    if args.dbfile is not None:
        add_row_to_database(args.dbfile, grave)

    return grave


# main
def main():
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
        try:
            csvwriter = csv.DictWriter(output_file, fieldnames = COLUMNS)
            # writing headers (field names)
            csvwriter.writeheader()
        except Exception as e:
            log.exception(e)
    else:
        log.info("ofile: stdin")


    # Configure output database, if any
    if args.dbfile is not None:
        db_file_name = args.dbfile
        if not os.path.exists(db_file_name):
            make_grave_database(db_file_name)

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
    for gid in graveids:
        try:
            findagravecitation(gid)
            parsed += 1
            print("Progress {:2.1%}".format(parsed / len(graveids)), end="\r")
        except Exception as e:
            out = "Unable to parse Memorial #" + str(gid) + "!"
            log.error(out, e)
            failedids.append(gid)

    out = "Successfully parsed " + str(parsed) + " of "
    out += str(len(graveids))
    log.info(out)
    if len(problemchilds) > 0:
        out = "Problem childz were:" + problemchilds
        log.info(out)

    # with open('results.txt', 'w') as f:
    #     f.write(out + '\n')
    #     f.write('\nProblem childz were:\n')
    #     f.write('\n'.join(problemchilds))
    #     f.write('\nUnable to parse:\n')
    #     f.write('\n'.join(failedids))

if __name__ == "__main__":
    main()
