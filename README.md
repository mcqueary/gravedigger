# graver

>  Scrape and Retrieve [FindAGrave](http://findagrave.com) memorial page data and save them to an SQL database.


## Scraping
[FindAGrave](http://findagrave.com) is an index of gravemarkers from cemeteries around the world. Often when doing genealogy research, you don't want to rely on a webpage's future and so you want to download the information to your local file. This python script takes a list of Grave Marker numbers, or FindAGrave urls, scrapes the site for data and prints out a citation of the information. It is currently setup to also save the data in an SQL database.


## Requirements

You are expected to have [Python3](https://www.python.org/downloads/). The main requirement is the BeautifulSoup, but in case more are added in future, please install from the requirements.txt to be sure you have everything:
```sh
$ pip install -r requirements.txt
```

## Usage
Download these files and change the contents of input text to be a list of FindAGrave ids, or FindAGrave urls. Then run
```sh
$ python3 graver.py
```

The citations will be printed to the console and saved in an SQL database named `graves.db`.

It is also possible to **read links from a GEDCOM** by un-highlighting the ["read from gedcom" section](https://github.com/PirtleShell/scrape-a-grave/blob/master/getgraveids.py#L88). This assumes your GEDCOM source citations have a LINK field with the FindAGrave site.


## License

This is intended as a convenient tool for personal genealogy research. Please be aware of FindAGrave's [Terms of Service](https://secure.findagrave.com/terms.html).

MIT © [Larry McQueary](https://github.com/mcqueary), [Robert Pirtle](https://pirtle.xyz)
