"""Marks all fixed errors #2 on ruwiki's CheckWikipedia."""
import re
import pywikibot
from checkwiki import load_page_list, mark_error_done, log

NUMBER = "2"
REGEXP = r"""
    <\s*/?\s*abbr\s*/\s*>|
    <\s*/?\s*b\s*/\s*>|
    <\s*/?\s*big\s*/\s*>|
    <\s*/?\s*blockquote\s*/\s*>|
    <\s*/?\s*center\s*/\s*>|
    <\s*/?\s*cite\s*/\s*>|
    <\s*/?\s*del\s*/\s*>|
    <\s*/?\s*div\s*/\s*>|
    <\s*/?\s*em\s*/\s*>|
    <\s*/?\s*font\s*/\s*>|
    <\s*/?\s*i\s*/\s*>|
    <\s*/?\s*p\s*/\s*>|
    <\s*/?\s*s\s*/\s*>|
    <\s*/?\s*small\s*/\s*>|
    <\s*/?\s*span\s*/\s*>|
    <\s*/?\s*strike\s*/\s*>|
    <\s*/?\s*sub\s*/\s*>|
    <\s*/?\s*sup\s*/\s*>|
    <\s*/?\s*td\s*/\s*>|
    <\s*/?\s*th\s*/\s*>|
    <\s*/?\s*tr\s*/\s*>|
    <\s*/?\s*tt\s*/\s*>|
    <\s*/?\s*u\s*/\s*>|

    <br\s*/\s*[^ ]>|
    <br[^ ]/>|
    <br[^ /]>|
    <br\s*/\s*[^ >]|
    <br\s*[^ >/]|
    <[^ w]br[^/]*\s*>|
    </hr>|

    <ref><cite>
"""
FLAGS = re.I | re.VERBOSE

def main():
    """Downloads list from server and marks relevant errors as done."""
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
