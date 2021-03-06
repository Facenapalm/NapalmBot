"""Marks all fixed errors #94 on ruwiki's CheckWikipedia."""
import re
import pywikibot
from checkwiki import load_page_list, check_tag_balance, mark_error_done, log

NUMBER = "94"

def main():
    """Main script function."""
    site = pywikibot.Site()
    for line in load_page_list(NUMBER):
        page = pywikibot.Page(site, line)
        if check_tag_balance(page.text, "ref"):
            mark_error_done(NUMBER, page.title())
            log(line, success=True)
        else:
            log(line, success=False)

if __name__ == "__main__":
    main()
