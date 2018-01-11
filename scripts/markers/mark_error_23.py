"""Marks all fixed errors #23 on ruwiki's CheckWikipedia."""
import re
import pywikibot
from checkwiki import load_page_list, check_tag_balance, mark_error_done, log

NUMBER = "23"

def main():
    """Main script function."""
    site = pywikibot.Site()
    for line in load_page_list(NUMBER):
        page = pywikibot.Page(site, line)
        text = re.sub(r"<nowiki\s*/>", "", page.text, flags=re.I)
        if check_tag_balance(text, "nowiki"):
            mark_error_done(NUMBER, page.title())
            log(line, success=True)
        else:
            log(line, success=False)

if __name__ == "__main__":
    main()
