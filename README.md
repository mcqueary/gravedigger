[![CI](https://github.com/mcqueary/graver/actions/workflows/python-package.yml/badge.svg)](https://github.com/mcqueary/graver/actions/workflows/python-package.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Coverage Status](https://coveralls.io/repos/github/mcqueary/graver/badge.svg)](https://coveralls.io/github/mcqueary/graver)
# graver

>  Scrape and Retrieve [FindAGrave](http://findagrave.com) memorial data and save them to an SQL database.


## Scraping
[FindAGrave](http://findagrave.com) Find A Grave is a free website providing access to and an opportunity to input cemetery information to an online database of cemetery records (over 226 million and counting). Often when doing genealogy research, you don't want to rely on a webpage's future and so you want to download the information to your local file. ```graver```takes a list of Find A Grave memorial IDs or FindAGrave URLs, scrapes relevant genealogical data, and outputs the contents to a SQLite3 database.


## Requirements

You are expected to have [Python3](https://www.python.org/downloads/). The main requirement is BeautifulSoup, but in case more are added in future, please install from the requirements.txt to be sure you have everything:
```sh
$ pip install -r requirements.txt
```

## Usage
### Install
```shell
$ pip install -e graver
````
### Scrape
```sh
$ graver scrape <input-file>
```
The memorial data will be saved in a SQL database (default: `graves.db`), where it can be viewed with any SQLite viewer, or exported to CSV. 

### Exporting
Future versions of `graver` will support direct export to CSV from the CLI, but for now, you can use SQLite3 to execute these commands, which will output the contents of `graves.db` to `graves.csv`:
```shell
$ sqlite3 graves.db
sqlite> .headers on
sqlite> .mode csv
sqlite> .output graves.csv
sqlite> select * from graves;
sqlite> .quit
```
Alternatively, you can do exactly the same thing by running a shell script like the following (this script is provided in `bin/export.sh`):
```shell
#!/bin/sh
sqlite3 graves.db <<EOF
.headers on
.mode csv
.output graves.csv
select * from graves;
.quit
EOF
```


## License

This is intended as a convenient tool for personal genealogy research. Please be aware of FindAGrave's [Terms of Service](https://secure.findagrave.com/terms.html).

MIT © [Larry McQueary](https://github.com/mcqueary), [Robert Pirtle](https://pirtle.xyz)
