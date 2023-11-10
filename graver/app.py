import argparse
import csv
import logging as log
import os
import re
import sys

# import sqlite3 as sql
from .models import Memorial
from .soup import (
    get_birth_date,
    get_birth_place,
    get_burial_plot,
    get_death_date,
    get_death_place,
    get_name,
    get_soup,
)

# Constants
DEFAULT_URL_PREFIX = "https://www.findagrave.com/memorial/"
DEFAULT_DB_FILE_NAME = "graves.db"
DEFAULT_OUTPUT_FILE = sys.stdout
DEFAULT_LOG_LINE_FMT = "%(asctime)s %(levelname)s %(message)s"
DEFAULT_LOG_DATE_FMT = "%m/%d/%Y %I:%M:%S %p"
DEFAULT_LOG_LEVEL = "INFO"
COLUMNS = [
    "id",
    "url",
    "name",
    "birth",
    "birthplace",
    "death",
    "deathplace",
    "burial",
    "plot",
    "more_info",
]

log_level = DEFAULT_LOG_LEVEL
csvwriter = None
problemchilds = []
parsed_args = None
db_file_name = None

# configure arguments

parser = argparse.ArgumentParser(description="Scrape FindAGrave memorials.")
parser.add_argument(
    "-i",
    "--ifile",
    type=argparse.FileType("r", encoding="UTF-8"),
    required=True,
    help="the input file containing findagrave URLs/IDs",
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


def scrape_grave(graveid):
    grave = {}
    grave["id"] = graveid

    url = DEFAULT_URL_PREFIX + str(graveid)
    grave["url"] = url

    tree = get_soup(url)

    # Get name
    grave["name"] = get_name(tree)

    # Get Birth Date
    grave["birth"] = get_birth_date(tree)

    # Get Birth Place
    grave["birthplace"] = get_birth_place(tree)

    # Get Death Date
    grave["death"] = get_death_date(tree)

    # Get Death Place
    grave["deathplace"] = get_death_place(tree)

    # Get Plot
    grave["plot"] = get_burial_plot(tree)

    return grave


# main
def main(args=None):
    graveids = []
    numcites = 0
    numids = 0

    parsed_args = parser.parse_args(args)

    # Configure logging
    log_level = DEFAULT_LOG_LEVEL
    if parsed_args.log is not None:
        log_level = parsed_args.log
    log.basicConfig(
        format=DEFAULT_LOG_LINE_FMT, datefmt=DEFAULT_LOG_DATE_FMT, level=log_level
    )
    log.debug("Log level is " + str(log_level))

    # Configure input file
    input_file = parsed_args.ifile
    log.debug("ifile: " + input_file.name)

    # Configure output file, if any
    if parsed_args.ofile is not None:
        output_file = parsed_args.ofile
        log.info("ofile: " + output_file.name)
        try:
            csvwriter = csv.DictWriter(output_file, fieldnames=COLUMNS)
            # writing headers (field names)
            csvwriter.writeheader()
        except Exception as e:
            log.exception(e)
    else:
        log.info("ofile: stdin")

    # Configure output database, if any
    if parsed_args is not None:
        if parsed_args.dbfile is not None:
            db_file_name = parsed_args.dbfile
        else:
            db_file_name = DEFAULT_DB_FILE_NAME

    Memorial.create_table(db_file_name)

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
    for line in parsed_args.ifile.readlines():
        numcites += 1
        currid = re.match(".*?([0-9]+)$", line).group(1)
        if currid not in graveids:
            graveids.append(currid)
            numids += 1
        elif line not in graveids:
            graveids.append(line)
            numids += 1

    parsed = 0
    failedids = []
    for gid in graveids:
        try:
            grave = scrape_grave(gid)
            # Optionally write grave to the specified database
            if db_file_name is not None:
                os.environ["DATABASE_NAME"] = db_file_name
                # add_row_to_database(db_file_name, grave)
                Memorial(
                    id=grave["id"],
                    name=grave["name"],
                    birth=grave["birth"],
                    birthplace=grave["birthplace"],
                    death=grave["death"],
                    deathplace=grave["deathplace"],
                    burial=grave["burial"],
                    plot=grave["plot"],
                    more_info=grave["more_info"],
                ).save()

            # Optionally write grave to CSV file
            if csvwriter is not None:
                try:
                    csvwriter.writerow(grave)
                except Exception as e:
                    log.exception("Exception encountered when writing row to CSV:", e)

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
