"""Marks all fixed errors #13 on ruwiki's CheckWikipedia."""
import re
import pywikibot
from checkwiki import load_page_list, check_tag_balance, mark_error_done, log

NUMBER = "13"

def main():
    """Main script function."""
    site = pywikibot.Site()
    for line in load_page_list(NUMBER):
        page = pywikibot.Page(site, line)
        text = page.text
        if check_tag_balance(text, "math") and not re.search(r"<math\s*/>", text, flags=re.I):
            mark_error_done(NUMBER, page.title())
            log(line, success=True)
        else:
            log(line, success=False)

if __name__ == "__main__":
    main()
