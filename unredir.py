"""
Fixes redirects in navigation templates.
Written in python 3.5, compatibility with older versions doesn't tested.
Uses checkwiki.py module.

Usage:
    python unredir.py template1 template2 ... templateN

Or you can just use this file as a module and call unredir_template function.
"""
import re
import sys
import pywikibot
import checkwiki

NS_MAIN = 0 # namespace const

MESSAGE = "Исправление редиректов в навшаблоне."

SHORT_FINDER = re.compile(r"\[\[([^\]\|\n]+)[\|\]]")
LINK_FINDER = re.compile(r"\[\[([^\]\|\n]+)(?:\|([^\]\|\n]+))?\]\]")

def unredir_template(site, name, text):
    """
    Fixes all redirects in text if:
        destination page is in main namespace;
        destination page contains this navigation template;
        link doesn't contains '#' symbol;
        only one link leads from template to the new destination.

    Function parameters:
        site - instance of pywikibot.Site();
        name - string, the name of navigation template;
        text - string, the content of the navigation template.

    Returns string - new text.
    """
    (text, ignored) = checkwiki.ignore(text, checkwiki.IGNORE_FILTER)

    count = {}
    redir_dest = {}

    # data collection
    for link in SHORT_FINDER.findall(text):
        page = pywikibot.Page(site, link)
        if not page.exists():
            continue

        if page.isRedirectPage():
            page = page.getRedirectTarget()
            new_link = page.title()

            if "#" in new_link:
                continue
            if page.namespace() != NS_MAIN:
                continue
            if not any(template.title() == name for template in page.templates()):
                continue

            redir_dest[link] = new_link
        else:
            new_link = page.title()

        if new_link in count:
            count[new_link] += 1
        else:
            count[new_link] = 1

    # redirects fix
    start_pos = 0
    for match in iter(lambda: LINK_FINDER.search(text, start_pos), None):
        start_pos = match.end(0)

        dest_name = match.group(1)
        view_name = match.group(2)
        if view_name is None:
            view_name = dest_name

        if not dest_name in redir_dest:
            continue

        dest_name = redir_dest[dest_name]

        if count[dest_name] > 1:
            continue

        if dest_name == view_name:
            new_link = dest_name
        else:
            new_link = dest_name + "|" + view_name
        new_link = "[[" + new_link + "]]"

        text = text[:match.start(0)] + new_link + text[match.end(0):]
        start_pos = match.start(0) + len(new_link)

    text = checkwiki.deignore(text, ignored)
    return text

def main():
    """Reads console arguments and fixes corresponding pages."""
    site = pywikibot.Site()

    for arg in sys.argv:
        page = pywikibot.Page(site, arg)
        if not page.exists():
            continue
        if not page.botMayEdit():
            continue

        page.text = unredir_template(site, page.title(), page.text)
        page.save(MESSAGE)

if __name__ == "__main__":
    main()
