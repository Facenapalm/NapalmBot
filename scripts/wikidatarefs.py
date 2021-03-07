"""Add missing references section to pages with refs, comes from wikidata."""

import pywikibot

CATEGORY = "Категория:Википедия:Статьи с источниками из Викиданных"
TEMPLATE = "Шаблон:Примечания"
COMMENT = "Исправление отсутствующей секции примечаний."


LABEL_PREFIX = "\x01"
LABEL_SUFFIX = "\x02"

def ignore(text, ignore_filter=IGNORE_FILTER):
    """
    Replace all text matches regexp with special label.

    Parameters:
        text - text to be processed;
        ignore_filter - compiled regular expression or string with regexp.

    Return (new_text, deleted_text_list) tuple.
    """
    if isinstance(ignore_filter, str):
        ignore_filter = re.compile(ignore_filter, flags=re.I | re.DOTALL)

    ignored = []
    count = 0

    def _ignore_line(match_obj):
        """Replace founded text with special label."""
        #pylint: disable=undefined-variable
        nonlocal ignored
        ignored.append(match_obj.group(0))

        nonlocal count
        old_count = count
        count += 1
        return LABEL_PREFIX + str(old_count) + LABEL_SUFFIX

    text = re.sub(LABEL_PREFIX + r"(\d+)" + LABEL_SUFFIX, _ignore_line, text)
    text = ignore_filter.sub(_ignore_line, text)
    return (text, ignored)

def deignore(text, ignored):
    """
    Restore the text returned by the ignore() function.

    Parameters:
        text - text to be processed;
        ignored - deleted_text_list, returned by the ignore() function.

    Return string.
    """
    def _deignore_line(match_obj):
        """Replace founded label with corresponding text."""
        index = int(match_obj.group(1))
        return ignored[index]

    return re.sub(LABEL_PREFIX + r"(\d+)" + LABEL_SUFFIX, _deignore_line, text)

def insert_references(text, last_ref=0):
    """
    Insert references section to the page according to local manual of style.
    last_ref parameter is used for transfering last reference position: it will be
    used for additional checks. If last_ref equals -1, references section will not
    be added.
    You can change FIX_UNSAFE_MISSING_REFERENCES global variable to allow unsafe
    insertions.
    Return (new_text, is_inserted) tuple, where is_inserted is 0 or 1.
    """
    if last_ref == -1:
        # no references in page
        return (text, 0)
    if (re.search(r"{{\s*(?:примечания|список[_ ]примечаний|reflist\+?)", text, flags=re.I) or
        re.search(r"<\s*references", text, flags=re.I)):
        # references are already here
        return (text, 0)
    if ("noinclude" in text or "includeonly" in text or "onlyinclude" in text):
        # page is included somewhere - dangerous to fix, we don't know how it will affect to this page
        return (text, 0)

    # try to place references into corresponding section
    section = re.search(r"^==[ ]*Примечани[ея][ ]*==$", text, flags=re.M)
    if section:
        pos = section.end(0)
        if pos < last_ref:
            # that's not a solution
            return (text, 0)
        if re.match(r"\s*($|\n==|\[\[Категория:)", text[pos:]) is None:
            if not (FIX_UNSAFE_MISSING_REFERENCES and
                re.match(r"({{[^:{}][^{}]*}}|\[\[Категория:[^\[\]]+\]\]|\s)*$", text[pos:])):
                # section isn't empty
                return (text, 0)
        text = text[:pos] + "\n{{примечания}}" + text[pos:]
        return (text, 1)

    # try to place references before special sections
    section = re.search(r"^==[ ]*(Литература|Ссылки|Источники)[ ]*==$", text, flags=re.M | re.I)
    if section:
        start = section.start(0)
        end = section.end(0)
        if start < last_ref:
            return (text, 0)
        if re.match(r"\s*($|\[\[Категория:)", text[end:]):
            # section is empty
            text = text[:start] + "== Примечания ==\n{{примечания}}" + text[end:]
        else:
            text = text[:start] + "== Примечания ==\n{{примечания}}\n\n" + text[start:]
        return (text, 1)

    # place references at the end of the article, just before categories and templates
    if FIX_UNSAFE_MISSING_REFERENCES:
        section = re.search(r"\n({{[^:{}][^{}]*}}|\[\[Категория:[^\[\]]+\]\]|\s)*$", text)
        pos = section.start(0)
        if pos < last_ref:
            return (text, 0)
        text = text[:pos] + "\n\n== Примечания ==\n{{примечания}}" + text[pos:]
        return (text, 1)

    return (text, 0)

def main():
    """Main script function."""
    site = pywikibot.Site()
    category = pywikibot.Category(site, CATEGORY)
    refs = [page.title() for page in category.articles(namespaces=[0])]
    template = pywikibot.Page(site, TEMPLATE)
    references = set([page.title() for page in template.embeddedin(namespaces=[0])])
    pages = [pywikibot.Page(site, page) for page in refs if not page in references]
    # converting to titles and back is needed for saving memory
    for page in pages:
        (text, ignored) = ignore(page.text)
        (text, flag) = checkwiki.insert_references(text)
        text = deignore(text, ignored)
        if flag:
            page.text = text
            page.save(COMMENT)

if __name__ == "__main__":
    main()
