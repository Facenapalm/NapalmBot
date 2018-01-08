"""Marks all fixed errors #105 on ruwiki's CheckWikipedia."""
import re
import pywikibot
from checkwiki import load_page_list, mark_error_done, log

NUMBER = "105"

def main():
    """Main script function."""
    site = pywikibot.Site()
    for pagename in load_page_list(NUMBER):
        page = pywikibot.Page(site, pagename)
        error = False
        for line in page.text.split("\n"):
            match = re.search(r"==+$", line)
            if not match:
                continue
            if line.startswith(match.group(0)):
                continue
            error = True
            break
        if error:
            log(pagename, success=False)
        else:
            mark_error_done(NUMBER, page.title())
            log(pagename, success=True)

if __name__ == "__main__":
    main()
