"""Marks all fixed errors #29 on ruwiki's CheckWikipedia."""
import re
import pywikibot
from checkwiki import load_page_list, check_tag_balance, mark_error_done, log

NUMBER = "29"

def main():
    """Main script function."""
    site = pywikibot.Site()
    for line in load_page_list(NUMBER):
        page = pywikibot.Page(site, line)
        text = page.text
        if check_tag_balance(text, "gallery") and not re.search(r"<gallery\s*/>", text, flags=re.I):
            mark_error_done(NUMBER, page.title())
            log(line, success=True)
        else:
            log(line, success=False)

if __name__ == "__main__":
    main()
