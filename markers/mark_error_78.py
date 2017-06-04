"""Marks all fixed errors #78 on ruwiki's CheckWikipedia."""
import re
import pywikibot
from checkwiki import load_page_list, mark_error_done, log

NUMBER = "78"
REGEXP = r"\{\{\s*(?:примечания2?|список примечаний|reflist\+?)(?![^}]*group)|<\s*references"
FLAGS = re.I

def main():
    """Main script function."""
    site = pywikibot.Site()
    for line in load_page_list(NUMBER):
        page = pywikibot.Page(site, line)
        if len(re.findall(REGEXP, page.text, flags=FLAGS)) < 2:
            mark_error_done(NUMBER, page.title())
            log(line, success=True)
        else:
            log(line, success=False)

if __name__ == "__main__":
    main()
