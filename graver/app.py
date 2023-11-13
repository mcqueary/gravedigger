import argparse
import logging as log
import os
import re
import sys

from dataclass_csv import DataclassWriter

# import sqlite3 as sql
from graver.memorial import Memorial
from graver.parsers import MemorialParser

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


def parse_args(args):
    """configure and parse arguments"""

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
        default=DEFAULT_DB_FILE_NAME,
        help="store the collected information in the specified SQLite db file",
    )
    parser.add_argument(
        "--log",
        type=str,
        required=False,
        help="log level, e.g. DEBUG, INFO, WARNING, ERROR, CRITICAL",
    )
    return parser.parse_args(args)


# main
def main(args=None):
    graveids = []
    numcites = 0
    numids = 0
    memorials = []

    parsed_args = parse_args(args)

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
    else:
        log.info("ofile: stdout")

    # Configure output database, if any
    if parsed_args is not None:
        if parsed_args.dbfile is not None:
            db_file_name = parsed_args.dbfile

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
            if db_file_name is not None:
                os.environ["DATABASE_NAME"] = db_file_name
            url = DEFAULT_URL_PREFIX + str(gid)
            memorial = MemorialParser().parse(url).save()
            memorials.append(memorial)

            parsed += 1
            print("Progress {:2.1%}".format(parsed / len(graveids)), end="\r")
        except Exception as e:
            out = "Unable to parse Memorial #" + str(gid) + "!"
            log.error(out, e)
            failedids.append(gid)

    if output_file is not None:
        try:
            csvwriter = DataclassWriter(output_file, memorials, Memorial)
            # writing headers (field names)
            # csvwriter.writeheader()
            csvwriter.write()
        except Exception as e:
            log.exception(e)

    out = "Successfully parsed " + str(parsed) + " of "
    out += str(len(graveids))
    log.info(out)
    if len(problemchilds) > 0:
        out = "Problem childz were:" + problemchilds
        log.info(out)

    with open("results.txt", "w") as f:
        f.write(out + "\n")
        f.write("\nProblem childz were:\n")
        f.write("\n".join(problemchilds))
        f.write("\nUnable to parse:\n")
        f.write("\n".join(failedids))


if __name__ == "__main__":
    main()
