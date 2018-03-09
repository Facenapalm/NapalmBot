"""
Script updates russian {{Перевод недели}} template according to Translate of
the Week project.

Usage:
    python tow.py
"""

import re
import pywikibot

META_TEMPLATE = "Template:TOWThisweek"
LOCAL_TEMPLATE = "Шаблон:Перевод недели"

ORIGINAL_ID = "original"
LOCAL_ID = "russian"

ARCHIVE_PAGE = "Проект:Переводы/Невыполненные переводы недели"
ARCHIVE_ALL = False
ARCHIVE_LABEL = "<!-- NapalmBot: insert here -->"
ARCHIVE_DEFAULT = "???"
ARCHIVE_FORMAT = "|-\n| {local} || {original}\n"

DEFAULT_TEXT = "'''[[Шаблон:Перевод недели|Укажите название статьи]]'''"
UPDATE_COMMENT = "Обновление перевода недели."
ARCHIVE_COMMENT = "Архивация перевода недели."

def parse_meta_template():
    """Return (link, langcode, pagename) tuple."""
    site = pywikibot.Site("meta", "meta")
    template = pywikibot.Page(site, META_TEMPLATE)
    match = re.search(r"\[\[:([A-Za-z\-]+):(.*?)\]\]", template.text)
    return (match.group(0), match.group(1), match.group(2))

def get_sitelink(site, lang, name):
    """Return interwiki of [[:lang:name]] in current site."""
    try:
        page = pywikibot.Page(pywikibot.Site(lang), name)
        result = pywikibot.ItemPage.fromPage(page).getSitelink(site)
    except:
        result = None
    return result

def get_regexps():
    """
    Return (original, local) re object tuple for matching links:
    $1 — prefix,
    $2 — link,
    $3 — postfix.
    """
    regexp = r"(<span id\s*=\s*\"{}\">)(.*?)(</span>)"
    wrap = lambda x: re.compile(regexp.format(x))
    return (wrap(ORIGINAL_ID), wrap(LOCAL_ID))

def archive(site, local, original):
    """Archive link if neccessary."""
    if ARCHIVE_PAGE == "":
        return
    if local != DEFAULT_TEXT:
        if not ARCHIVE_ALL:
            match = re.match(r"\[\[(.*?)[\]|]", local)
            if match is None:
                return
            try:
                if pywikibot.Page(site, match.group(1)).exists():
                    return
            except:
                return
    else:
        local = ARCHIVE_DEFAULT
    page = pywikibot.Page(site, ARCHIVE_PAGE)
    text = page.text
    pos = text.find(ARCHIVE_LABEL)
    if pos == -1:
        return
    text = text[:pos] + ARCHIVE_FORMAT.format(local=local, original=original) + text[pos:]
    page.text = text
    page.save(ARCHIVE_COMMENT, minor=False)

def main():
    """Main script function."""
    site = pywikibot.Site()
    (interwiki, lang, name) = parse_meta_template()
    local = get_sitelink(site, lang, name)
    if local:
        local = "[[{}]]".format(local)
    else:
        local = DEFAULT_TEXT

    (interwiki_re, local_re) = get_regexps()
    template = pywikibot.Page(site, LOCAL_TEMPLATE)
    result = template.text
    old_interwiki = interwiki_re.search(result).group(2)
    old_local = local_re.search(result).group(2)

    if interwiki == old_interwiki:
        return
    else:
        archive(site, old_local, old_interwiki)

    result = local_re.sub("\\1" + local + "\\3", result)
    result = interwiki_re.sub("\\1" + interwiki + "\\3", result)
    template.text = result
    template.save(UPDATE_COMMENT, minor=False)

if __name__ == "__main__":
    main()
