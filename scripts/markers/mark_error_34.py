"""Marks all fixed errors #34 on ruwiki's CheckWikipedia."""
import re
import pywikibot
from checkwiki import load_page_list, mark_error_done, log

NUMBER = "34"
REGEXP = r"{{{[^!]|#if:|#ifeq:|#switch:|#ifexist:|{{fullpagename}}|{{sitename}}|{{namespace}}|{{basepagename}}|{{pagename}}|{{subpagename}}|{{talkpagename}}|{{подст:|{{subst:"
FLAGS = re.I

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
