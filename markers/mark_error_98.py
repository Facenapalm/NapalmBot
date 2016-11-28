"""Marks all fixed errors #98 on ruwiki's CheckWikipedia."""
import re
import pywikibot
from checkwiki import load_page_list, check_tag_balance, mark_error_done, log

NUMBER = "98"
FLAGS = re.I

def main():
    """Downloads list from server and marks relevant errors as done."""
    site = pywikibot.Site()
    for line in load_page_list(NUMBER):
        page = pywikibot.Page(site, line)
        if check_tag_balance(page.text, "sub"):
            mark_error_done(NUMBER, page.title())
            log(line, success=True)
        else:
            log(line, success=False)

if __name__ == "__main__":
    main()
