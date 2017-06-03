"""
Script checks if checkwiki has a new dump scanned, and, if so, launches
markers/markall.py and checkwiki.py for obvious errors.

Usage:
    python cwtrigger.py path-to-markers datafile
"""

import re
import os
import sys
from urllib.request import urlopen

import pywikibot
import checkwiki
from markers import markall

CHECKWIKI = "http://tools.wmflabs.org/checkwiki/cgi-bin/checkwiki.cgi?project=ruwiki&view=project"
ERRORS = [
# MAJOR
    # references:
    "3",
    "104",
    # external links:
    "62",
    "80",
    "93",
    # HTML tags and syntax:
    "2",
    "98",
    "99",
    "42",
    # internal and interwiki links:
    "32",
    "51",
    "53",
    "68",
    # ISBN:
    "70",
# MINOR (keep once solved problems stay solved)
    # categories:
    "9",
    "17",
    # image descriptions with br:
    "65",
    # DEFAULTSORT:
    "88"
]

def main():
    """Main script function."""
    if len(sys.argv) < 3:
        return
    filename = sys.argv[2]
    if os.path.exists(filename):
        with open(filename) as datefile:
            prev_date = datefile.read()
    else:
        prev_date = "0000-00-00"

    datepage = urlopen(CHECKWIKI).read().decode()
    cur_date = re.search(r"Last scanned dump (\d{4}-\d{2}-\d{2})", datepage).group(1)

    if cur_date > prev_date:
        markall.main()

        site = pywikibot.Site()
        for num in ERRORS:
            checkwiki.process_server(site, num)

    with open(filename, "w") as datefile:
        datefile.write(cur_date)

if __name__ == "__main__":
    main()
