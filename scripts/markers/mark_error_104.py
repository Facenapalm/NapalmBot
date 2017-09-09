"""Marks all fixed errors #104 on ruwiki's CheckWikipedia."""
import re
import pywikibot
from checkwiki import load_page_list, mark_error_done, log

NUMBER = "104"
REGEXP = r"<ref\s+name=\s*(.*?)\s*(?:group=.*?)?\s*/?>"
FLAGS = re.I

def main():
    """Main script function."""
    site = pywikibot.Site()
    for line in load_page_list(NUMBER):
        page = pywikibot.Page(site, line)
        mark = True
        for name in re.findall(REGEXP, page.text, flags=FLAGS):
            if re.match(r"^'.*'$|^\".*\"$", name):
                continue
            if re.search(r"[\"'/\\=?#>\s]", name):
                mark = False
                break
        if mark:
            mark_error_done(NUMBER, page.title())
            log(line, success=True)
        else:
            log(line, success=False)

if __name__ == "__main__":
    main()
