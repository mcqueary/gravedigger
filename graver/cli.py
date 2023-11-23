import importlib.metadata
import logging as log
import os
import re
import sys

import typer
from tqdm import tqdm

from graver.memorial import Memorial, MemorialMergedException

# Constants
DEFAULT_DB_FILE_NAME = "graves.db"
DEFAULT_OUTPUT_FILE = sys.stdout


parsed_args = None


def version_callback(value: bool):
    """Return version of graver application"""
    if value:
        metadata = importlib.metadata.metadata("graver")
        name_str = metadata["Name"]
        version_str = metadata["Version"]
        print("{} v{}".format(name_str, version_str))
        raise typer.Exit()


app = typer.Typer(add_completion=False)


@app.callback()
def common(
    ctx: typer.Context,
    version: bool = typer.Option(
        None,
        "-v",
        "--version",
        callback=version_callback,
        help="Return version of graver application.",
    ),
):
    pass


# TODO: Add support for log level DEBUG, INFO, WARNING, ERROR, CRITICAL
# Configure logging
# DEFAULT_LOG_LINE_FMT = "%(asctime)s %(levelname)s %(message)s"
# DEFAULT_LOG_DATE_FMT = "%m/%d/%Y %I:%M:%S %p"
# DEFAULT_LOG_LEVEL = "INFO"
# log_level = DEFAULT_LOG_LEVEL
# if log is not None:
#     log_level = parsed_args.log
# log.basicConfig(
#     format=DEFAULT_LOG_LINE_FMT, datefmt=DEFAULT_LOG_DATE_FMT, level=log_level
# )
# log.debug("Log level is " + str(log_level))

# TODO: Add support for output CSV
# TODO: Add init command
# TODO: Configure output database name


def get_id_from_url(url: str):
    result = None
    old_style = ".*?GRid=([0-9]+)/?$"
    new_style = Memorial.CANONICAL_URL_FORMAT.format("([0-9]+)/?")
    if re.match(old_style, url):  # oldstyle URL format
        result = int(re.match(old_style, url).group(1))
    elif re.match(new_style, url):
        result = int(re.match(new_style, url).group(1))
    return result

    # def get_urls_from_gedcom(gedfile: str):
    # TODO add gedcom input support
    # # read from gedcom
    # with open('tree.ged', encoding='utf8') as ged:
    #     for line in ged.readlines():
    #         num_memorials+=1
    #         if '_LINK ' in line and 'findagrave.com' in line:
    #             for unit in line.split('&'):
    #                 if 'GRid=' in unit:
    #                     if unit[5:-1] not in graveids:
    #                         graveids.append(unit[5:-1])
    #                         #print(graveids[numids])
    #                         numids+=1
    # return


def print_failed_urls(urls: list):
    if len(urls) > 0:
        print("Failed urls were:")
        print(*urls, sep="\n")


@app.command()
def scrape(input_filename: str, db: str = typer.Option(DEFAULT_DB_FILE_NAME, "--db")):
    """Scrape URLs from a file"""

    print(f"Input file: {input_filename}")
    print(f"Database file: {db}")

    urls = []

    # Main loop
    try:
        with open(input_filename) as file:
            os.environ["DATABASE_NAME"] = db
            Memorial.create_table(db)
            while line := file.readline():
                line = line.strip()
                if re.match("^[0-9]+$", line):  # id only
                    line = Memorial.CANONICAL_URL_FORMAT.format(line)
                if line not in urls:
                    urls.append(line)
    except OSError as e:
        print(str(e))
        raise typer.Exit(1)

    scraped = 0
    failed_urls = []
    for url in (pbar := tqdm(urls)):
        try:
            pbar.set_postfix_str(url)
            Memorial(url).save()
            # json_string = json.dumps(m.to_dict(), ensure_ascii=False)
            # print(json_string)
            scraped += 1
        except MemorialMergedException as ex:
            log.warning(ex)
        except Exception as e:
            out = "Unable to scrape Memorial [" + url + "]!"
            # log.error(out, ex.args)
            print(out)
            print(str(e))
            failed_urls.append(url)

    msg = "Successfully scraped {total} of {expected}"
    print(msg.format(total=scraped, expected=len(urls)))
    print_failed_urls(failed_urls)


if __name__ == "__main__":
    typer.run(app)
