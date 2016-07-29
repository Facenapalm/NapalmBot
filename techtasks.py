"""
Script updates list of technical tasks in russian Wikipedia.
Written in python 3.5, compatibility with older versions doesn't tested.
Uses checkwiki.py module.

Usage:
    python techtasks.py
"""

import re
import pywikibot
import mwparserfromhell
from checkwiki import ignore, deignore

CATEGORY_NAME = "Категория:Википедия:Обсуждения с нерешёнными техническими задачами"
TEMPLATE_NAME = "техзадача"
DONE_PARAM = "выполнено"

SORT_PARAM = "дата"
DEFAULT_SORTKEY = "0000-00-00"
SORT_REVERSE = True

RESULT_PAGE = "Проект:Технические работы/Задачи из обсуждений"
RESULT_BEGINNING = "{{/шапка}}"
RESULT_FORMAT = "{{{{/задача|{params}|ссылка={link}}}}}"
RESULT_ENDING = "{{/подвал}}"

COMMENT = "Автоматическое обновление списка техзадач."

LOG_FORMAT = "Processed {done} out of {count} pages ({percentage} %)."

TEMPLATE_REGEXP = r"^\{\{\s*" + TEMPLATE_NAME + r"\s*\|"
IGNORE_FILTER = r"<nowiki>(.*?)</nowiki>|<nowiki\s*/>"

def find_heading(code, node):
    """Finds first second-level heading before the node."""
    index = code.index(node, recursive=True)
    for heading in list(code.nodes)[index::-1]:
        if not isinstance(heading, mwparserfromhell.nodes.heading.Heading):
            continue
        if heading.level != 2:
            continue
        return heading
    return None

def encode_string(text):
    """Replaces special symbols by its codes."""
    text = text.replace("<", "%3C")
    text = text.replace(">", "%3E")
    text = text.replace("[", "%5B")
    text = text.replace("]", "%5D")
    text = text.replace("{", "%7B")
    text = text.replace("}", "%7D")
    text = text.replace("|", "%7C")
    return text

def linkify_heading(text):
    """
    Converts heading text to link part, which goes after #.
    For example: "== [[Something|head]]''ing'' ==" -> "heading".
    """
    (text, ignored) = ignore(text, IGNORE_FILTER)
    text = re.sub(r"<!--.*?-->", "", text)
    text = re.sub(r"\[\[:?(?:[^|]*\|)?([^\]]*)\]\]", "\\1", text)
    text = re.sub(r"\[https?://[^ \]]+ ([^\]]+)\]", "\\1", text)
    text = re.sub(r"'''(.+?)'''", "\\1", text)
    text = re.sub(r"''(.+?)''", "\\1", text)
    text = re.sub(r"<[a-z]+(?:\s*[a-z]+\s*=[^<>]+)?\s*/?>|</[a-z]+>", "", text, flags=re.I)
    text = deignore(text, ignored)

    text = re.sub(IGNORE_FILTER, "\\1", text)
    text = encode_string(text)

    text = re.sub(r"[ ]{2,}", " ", text)
    text = text.strip()
    return text

def log(done, count):
    """Writes information about progress."""
    if count == 0:
        percentage = 100
    else:
        percentage = round(100 * done / count)
    print(LOG_FORMAT.format(done=done, count=count, percentage=percentage))

def main():
    """Updates list of technical tasks."""
    site = pywikibot.Site()
    pages = list(pywikibot.Category(site, CATEGORY_NAME).members())
    count = len(pages)

    templates = []
    for done, page in enumerate(pages):
        log(done, count)
        text = page.text
        # mwparserfromhell always parses ''''' as <i><b>. So, this case:
        #   '''''something'' something else'''
        # It will parse as:
        #   <i><b>something<i> something else<b>
        # And it can lead to the error. So, to prevent mwparserfromhell bug:
        text = re.sub(r"(?:'''''|'''|'')", "", text)
        code = mwparserfromhell.parse(text)
        for template in code.filter_templates(matches=TEMPLATE_REGEXP):
            if template.has(DONE_PARAM, ignore_empty=True):
                continue
            params = "|".join([str(param) for param in template.params])

            heading = find_heading(code, template)
            if heading is None:
                link = page.title()
            else:
                heading = str(heading.title)
                link = page.title() + "#" + linkify_heading(heading)

            if template.has(SORT_PARAM, ignore_empty=True):
                sortkey = template.get(SORT_PARAM).value.strip()
            else:
                sortkey = DEFAULT_SORTKEY

            line = RESULT_FORMAT.format(params=params, link=link)
            templates.append((line, sortkey))

    log(count, count)
    templates.sort(key=lambda template: template[1], reverse=SORT_REVERSE)

    lines = []
    lines.append(RESULT_BEGINNING)
    lines += [template[0] for template in templates]
    lines.append(RESULT_ENDING)

    page = pywikibot.Page(site, RESULT_PAGE)
    page.text = "\n".join(lines)
    page.save(COMMENT, minor=False)

if __name__ == "__main__":
    main()
