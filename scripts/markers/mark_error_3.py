"""Marks all fixed errors #3 on ruwiki's CheckWikipedia."""
import re
import pywikibot
from checkwiki import load_page_list, mark_error_done, log

NUMBER = "3"

def main():
    """Main script function."""
    site = pywikibot.Site()
    for line in load_page_list(NUMBER):
        page = pywikibot.Page(site, line)
        if (re.search(r"{{(?:[Пп]римечания|[Сс]писок[_ ]примечаний|[Rr]eflist\+?)", page.text) or
            re.search(r"<\s*references.*?>", page.text, flags=re.I) or
            re.search(r"<\s*ref", page.text, flags=re.I) is None):
            mark_error_done(NUMBER, page.title())
            log(line, success=True)
        else:
            log(line, success=False)

if __name__ == "__main__":
    main()
