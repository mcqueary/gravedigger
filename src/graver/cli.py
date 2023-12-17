import importlib.metadata
import logging
import os
import re
import sys
from logging.handlers import RotatingFileHandler
from typing import List, Tuple
from urllib.parse import urlparse

import typer
from tqdm import tqdm

from graver import (
    Cemetery,
    Driver,
    Memorial,
    MemorialMergedException,
    MemorialParseException,
)
from graver.constants import (
    APP_NAME,
    FINDAGRAVE_BASE_URL,
    MEMORIAL_CANONICAL_URL_FORMAT,
)

# Constants
DEFAULT_OUTPUT_FILE = sys.stdout
DEFAULT_DB_FILE_NAME = "graves.db"

# Logging setup
DEFAULT_LOG_FILENAME = "graver.log"
DEFAULT_LOG_LEVEL = "INFO"
# DEFAULT_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
# DEFAULT_LOG_FORMAT = "%(name)-12s: %(levelname)-8s %(message)s"
DEFAULT_LOG_FORMAT = (
    "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s"
)
DEFAULT_LOG_DATE_FORMAT = "%H:%M:%S"


# set up logging to console and file
logging.root.handlers = []
console = logging.StreamHandler(sys.stdout)
console_formatter = logging.Formatter("%(message)s")
console.setFormatter(console_formatter)
logging.basicConfig(
    level=DEFAULT_LOG_LEVEL,
    format=DEFAULT_LOG_FORMAT,
    datefmt=DEFAULT_LOG_DATE_FORMAT,
    handlers=[
        RotatingFileHandler(
            DEFAULT_LOG_FILENAME,
            mode="a",
            maxBytes=5 * 1024 * 1024,
            backupCount=2,
            encoding=None,
        ),
        console,
    ],
)

log = logging.getLogger()


def version_callback(value: bool):
    """Return version of graver application"""
    if value:
        metadata = importlib.metadata.metadata("graver")
        name_str = metadata["Name"]
        version_str = metadata["Version"]
        log.info("{} v{}".format(name_str, version_str))
        raise typer.Exit()


# FIXME clean up logging initialization
def logging_callback(log_level: str):
    """Set log level for graver application"""
    if log_level:
        logging.getLogger().setLevel(log_level.upper())
        log.debug("Log level is " + str(log_level.upper()))


app = typer.Typer(
    add_completion=False, context_settings={"help_option_names": ["-h", "--help"]}
)


@app.callback()
def common(
    version: bool = typer.Option(
        None,
        "-V",
        "--version",
        case_sensitive=True,
        callback=version_callback,
        help=f"Return version of {APP_NAME} application.",
    ),
    loglevel: str = typer.Option(
        DEFAULT_LOG_LEVEL,
        "-l",
        "--log",
        "--logging",
        callback=logging_callback,
        help="Set logging level, e.g. --log-level=debug",
    ),
):
    pass


# TODO: Add support for output CSV
# TODO: Add init command

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
        text = "\n".join(urls)
        log.info(f"Failed urls were:\n{text}")


def format_url(line: str):
    """
    Creates a properly formed FindAGrave URL from a memorial id (e.g. 1784) or an
    old-style FindAGrave URL (e.g.
    "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=1784")

    @param line: the input string
    @return: a URL in the form "https://www.findagrave.com/memorial/<id>"
    """
    if re.search("^[0-9]+$", line) is not None:  # id only
        line = MEMORIAL_CANONICAL_URL_FORMAT.format(line)
    elif (match := re.search("GRid=([0-9]+)$", line)) is not None:  # id only
        line = MEMORIAL_CANONICAL_URL_FORMAT.format(match.group(1))
    return line


def uri_validator(uri):
    result = urlparse(uri)
    is_memorial = ("/memorial/" in uri) or ("GRid=" in uri)
    return is_memorial and all(
        [result.scheme in ["file", "http", "https"], result.path]
    )


def collect_and_validate_urls(input_filename) -> Tuple[List[str], List[str]]:
    good = []
    bad = []
    with open(input_filename) as file:
        while line := file.readline().strip():
            line = format_url(line)
            if not uri_validator(line):
                log.warning(f"{line} is not a valid URL")
                bad.append(line)
                continue
            else:
                if line not in good:
                    good.append(line)
    return good, bad


def parse_and_save_memorial(url, driver=None) -> Memorial:
    driver = driver if driver is not None else Driver()
    try:
        m = Memorial.parse(url, driver=driver).save()
    except MemorialMergedException as ex:
        log.warning(ex)
        m = Memorial.parse(ex.new_url, driver=driver).save()
    return m


@app.command()
def scrape_file(
    input_filename: str, db: str = typer.Option(DEFAULT_DB_FILE_NAME, "--db")
):
    """Scrape URLs from a file"""

    log.info(f"Input file: {input_filename}")
    log.info(f"Database file: {db}")

    urls: List[str]
    failed_urls: List[str]

    # Collect and validate URLs
    try:
        urls, failed_urls = collect_and_validate_urls(input_filename)
    except OSError as e:
        log.error(e)
        raise typer.Exit(1)

    # Process URLs
    scraped = 0
    disable = os.getenv("TQDM_DISABLE")
    os.environ["DATABASE_NAME"] = db
    Memorial.create_table(db)
    # Pass in driver to ensure we reuse the same session
    driver: Driver = Driver()
    for url in (pbar := tqdm(urls, disable=bool(disable))):
        pbar.set_postfix_str(url)
        try:
            parse_and_save_memorial(url, driver)
            scraped += 1
            pbar.set_postfix_str("")
        except MemorialParseException as ex:
            log.error(ex)
            failed_urls.append(url)

    log.info(f"Successfully scraped {scraped} of {len(urls)}")
    print_failed_urls(failed_urls)


@app.command()
def scrape_url(url: str, db: str = typer.Option(DEFAULT_DB_FILE_NAME, "--db")):
    """Scrape a specific memorial URL"""
    if not uri_validator(url):
        log.error(f"Invalid or non-memorial URL: [{url}]")
        raise typer.Exit(1)
    Memorial.create_table(db)
    try:
        m: Memorial = parse_and_save_memorial(url)
    except MemorialParseException as ex:
        log.error(ex)
        raise SystemExit()
    log.info(m.to_json())


def gpsfilter_callback(value: str):
    if value is not None:
        if value not in ["gps", "nogps"]:
            raise typer.BadParameter("Only 'gps' or 'nogps' is allowed")
    return value


def year_filter_callback(value: str):
    if value is not None and value != "":
        if value not in ["before", "after", "exact"]:
            if re.search(r"^\d{1,3}$", value) is None:
                raise typer.BadParameter(
                    "Only 'before', 'after', 'exact', or 0 < value < 999 is allowed"
                )
    return value


@app.command()
def search(
    cemetery_id: int = typer.Option(
        None,
        "--cid",
        "--cemetery-id",
        help="The numeric ID of a FindAGrave cemetery/monument to search within",
    ),
    firstname: str = typer.Option("", "--firstname"),
    middlename: str = typer.Option("", "--middlename"),
    lastname: str = typer.Option("", "--lastname"),
    birthyear: int = typer.Option(None, "--birthyear"),
    birthyearfilter: str = typer.Option(
        "",
        "--birthyearfilter",
        callback=year_filter_callback,
        help="'before', 'after', or 'n' where 'n' is interpreted as +/- n years",
    ),
    deathyear: int = typer.Option(None, "--deathyear"),
    deathyearfilter: str = typer.Option(
        "",
        "--deathyearfilter",
        callback=year_filter_callback,
        help="'before', 'after', or 'n' where 'n' is interpreted as +/- n years",
    ),
    location: str = typer.Option(
        "",
        "--location",
        help="A location name, e.g. 'Albemarle County, Virginia, USA'. "
        "FindAGrave requires you to also supply locationId.",
    ),
    location_id: str = typer.Option(
        "",
        "--locationId",
        help="A lookup code used by FindAGrave to uniquely identify place-names in its "
        "database.",
    ),
    memorial_id: int = typer.Option(
        None,
        "--id",
        "--memorialid",
        help="The memorial ID. "
        "If supplied, this will supersede all other search terms",
    ),
    mcid: int = typer.Option(
        None, "--mcid", help="The memorial contributor's FindAGrave ID"
    ),
    linkedtoname: str = typer.Option(
        "",
        "--linkedToName",
        help="The name(s), full or partial, of relatives linked to the memorial, "
        "e.g. 'Mary Jefferson' or 'Steve Mike Barry'.",
    ),
    datefilter: int = typer.Option(
        None, "--datefilter", help="Memorials added in last n days"
    ),
    orderby: str = typer.Option(
        "r",
        "--orderby",
        help="Order results by: date created(n/n-), birth year(b/b-), "
        "death year(d/d-), plot(pl)",
    ),
    plot: str = typer.Option("", "--plot"),
    no_cemetery: bool = typer.Option(
        None,
        "--noCemetery",
        help="Limit search to memorials not associated with a cemetery (e.g. cremation,"
        " lost at sea, unknown, etc)",
    ),
    famous: bool = typer.Option(
        None,
        "--famous",
        is_flag=False,
        help="Limit search to people designated as Famous by FindAGrave (note: this is "
        "mutually exclusive with --sponsored)",
    ),
    sponsored: bool = typer.Option(
        None,
        "--sponsored",
        is_flag=False,
        help="Limit search to memorials that have been sponsored on FindAGrave (note: "
        "this is mutually exclusive with --famous)",
    ),
    cenotaph: bool = typer.Option(None, "--cenotaph", is_flag=False),
    monument: bool = typer.Option(None, "--monument", is_flag=False),
    veteran: bool = typer.Option(None, "--isVeteran", is_flag=False),
    include_nickname: bool = typer.Option(None, "--includeNickName"),
    include_maiden_name: bool = typer.Option(None, "--includeMaidenName"),
    include_titles: bool = typer.Option(None, "--includeTitles"),
    exact_name: bool = typer.Option(None, "--exactName"),
    fuzzy_names: bool = typer.Option(None, "--fuzzyNames"),
    photo_filter: str = typer.Option(None, "--photofilter"),
    gps_filter: str = typer.Option(None, "--gpsfilter", callback=gpsfilter_callback),
    flowers: bool = typer.Option(None, "--flowers", is_flag=False),
    has_plot: bool = typer.Option(None, "--hasPlot", is_flag=False),
    page: int = typer.Option(None, "--page"),
    max_results: int = typer.Option(
        0,
        "--max",
        "--max-results",
        help="The maximum number of results to process (0 == no limit)",
    ),
):
    """Scrape memorial search results with specified search parameters"""
    search_terms: dict = {
        "max_results": max_results,
        "firstname": firstname,
        "middlename": middlename,
        "lastname": lastname,
        "birthyear": str(birthyear) if birthyear is not None else "",
        "birthyearfilter": birthyearfilter,
        "deathyear": str(deathyear) if deathyear is not None else "",
        "deathyearfilter": deathyearfilter,
        "location": location,
        "locationId": location_id,
        "memorialid": str(memorial_id) if memorial_id is not None else "",
        "mcid": str(mcid) if mcid is not None else "",
        "linkedToName": linkedtoname,
        "datefilter": datefilter if datefilter is not None else "",
        "orderby": orderby,
        "plot": plot,
    }
    optional_terms: dict = {
        "noCemetery": no_cemetery,
        "famous": famous,
        "sponsored": sponsored,
        "cenotaph": cenotaph,
        "monument": monument,
        "isVeteran": veteran,
        "includeNickName": include_nickname,
        "includeMaidenName": include_maiden_name,
        "includeTitles": include_titles,
        "exactName": exact_name,
        "fuzzyNames": fuzzy_names,
        "photofilter": photo_filter,
        "gpsfilter": gps_filter,
        "flowers": flowers,
        "hasPlot": has_plot,
        "page": page,
    }

    for key in optional_terms.keys():
        if optional_terms[key] is not None:
            search_terms[key] = optional_terms[key]

    log.debug(f"Search terms = {search_terms}")

    if memorial_id is not None:
        m = Memorial.parse(f"{FINDAGRAVE_BASE_URL}/memorial/{memorial_id}")
        log.info(m.to_json())
    else:
        cem = None
        if cemetery_id is not None:
            cem = Cemetery(f"{FINDAGRAVE_BASE_URL}/cemetery/{cemetery_id}")

        results = Memorial.search(cem, **search_terms)
        log.debug(f"Num results = {len(results)}")
        if len(results) > 0:
            for idx, m in enumerate(results):
                if idx == 0:
                    log.info("[" + m.to_json() + ",")
                elif idx == len(results) - 1:
                    log.info(m.to_json() + "]")
                else:
                    log.info(m.to_json() + ",")


if __name__ == "__main__":  # pragma: no cover
    typer.run(app)
