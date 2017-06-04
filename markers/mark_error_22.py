"""Marks all fixed errors #22 on ruwiki's CheckWikipedia."""
import re
import pywikibot
from checkwiki import load_page_list, mark_error_done, log

NUMBER = "22"
REGEXP = r"""
    \[\[\s+(к|категория|category)\s*:|
    \[\[\s*(к|категория|category)\s+:|
    \[\[\s*(к|категория|category)\s*:\s+|
    \[\[\s*(к|категория|category)\s*:[^\]]+\s+[\|\]]
"""
FLAGS = re.I | re.VERBOSE

def main():
    """Main script function."""
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
