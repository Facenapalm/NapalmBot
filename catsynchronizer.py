"""
This module contains various functions which helps to create categories using
category tree from other wikipedia.
"""

import re
import pywikibot
import checkwiki

CREATE_COMMENT = "Автоматическая заливка категорий."
ADD_CATEGORY_COMMENT = "Простановка [[{}]]."

def get_sitelink_safe(page, site):
    """
    For current page (first parameter) return a name of the corresponding page in
    destination project (second parameter) if this page exists, otherwise return
    None.
    """
    try:
        sitelink = pywikibot.ItemPage.fromPage(page).getSitelink(site)
        return sitelink
    except Exception:
        return None

def calculate_category(source, site):
    """
    Calculate how much articles from source category (first parameter) have the
    corresponding article in destination project (second parameter). Return number.
    """
    return [get_sitelink_safe(page, site) is None for page in source.articles()].count(False)

def synchronize_category(source, category, log=True):
    """
    Process all articles from source category (first parameter), find corresponding
    articles in destination project and add them to destination category (second
    parameter), if category doesn't already contains them.

    All edits will be marked with ADD_CATEGORY_COMMENT comment (global variable).

    Function by default prints information about progress. To disable it, set the
    "log" parameter (the third one) to False.
    """
    site = category.site
    catname = category.title()
    for page in source.articles():
        title = page.title()
        new_title = get_sitelink_safe(page, site)
        if new_title is None:
            if log:
                pywikibot.output("- [[{}]]: no destination page".format(title))
            continue
        page = pywikibot.Page(site, new_title)

        if category in page.categories():
            if log:
                pywikibot.output("- [[{}]]: already in category".format(title))
            continue

        text = page.text
        text += "\n[[{}]]".format(catname)
        (text, fixed_errors) = checkwiki.process_text(text)
        page.text = text
        page.save(ADD_CATEGORY_COMMENT.format(catname))
        checkwiki.mark_error_list_done(fixed_errors, title)
        if log:
            pywikibot.output("+ [[{}]]: [[{}]] added".format(title, page.title()))

def create_categories(category, site, regexp, replace, text, update=True, limit=5, log=True):
    """
    For every subcategory from source category (first parameter) create a
    corresponding category in destination project (second parameter), if:
    1. The title of this subcategory matches regexp (third parameter). Regexp
    should contain ^ at start and $ at end. New title will be made by re.sub method
    using this regexp and fourth parameter as replace template.
    2. New category will have at least 5 members (this number can be changed via
    "limit" parameter).

    New category will created with given text (fifth parameter). Text can contain
    groups from regexp, for example, "[[Category:Albums by label|\1]]".

    Function will also update already created categories by default, regardless of
    its titles and members count. To prevent it, set "update" parameter to False.

    Function by default prints information about progress. To disable it, set the
    "log" parameter to False.
    """
    for source in category.members(namespaces=14): #yield only subcategories
        title = source.title()
        new_title = get_sitelink_safe(source, site)
        if new_title is None:
            (new_title, match) = re.subn(regexp, replace, title)
            if match == 0:
                if log:
                    pywikibot.output("[[{}]]: title doesn't matches regexp, skipped".format(title))
                continue
            size = calculate_category(source, site)
            if size < limit:
                if log:
                    pywikibot.output("[[{}]]: too small category ({} memebers), skipped".format(title, size))
                continue
            (new_text, match) = re.subn(regexp, text, title)
            dest = pywikibot.Category(site, new_title)
            dest.text = new_text
            dest.save(CREATE_COMMENT)
            if log:
                pywikibot.output("[[{}]]: created as [[{}]], synchronization".format(title, new_title))
        else:
            if update:
                dest = pywikibot.Category(site, new_title)
                if log:
                    pywikibot.output("[[{}]]: corresponding category found, synchronization".format(title))
            else:
                if log:
                    pywikibot.output("[[{}]]: corresponding category found, skipped".format(title))
                continue

        synchronize_category(source, dest, log=log)
