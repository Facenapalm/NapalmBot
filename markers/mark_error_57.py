"""Marks all fixed errors #57 on ruwiki's CheckWikipedia."""
import re
import pywikibot
from checkwiki import load_page_list, mark_error_done, log

NUMBER = "57"
REGEXP = r":[ ]*=+[ ]*$"
FLAGS = re.I

def main():
    """Downloads list from server and marks relevant errors as done."""
    site = pywikibot.Site()
    for line in load_page_list(NUMBER):
        page = pywikibot.Page(site, line)
        if re.search(REGEXP, page.text, flags=FLAGS) is None:
            mark_error_done(NUMBER, page.title())
            log(line, success=True)
        else:
            log(line, success=False)

if __name__ == "__main__":
    main()
