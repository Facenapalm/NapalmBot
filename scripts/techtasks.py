"""
Script updates list of technical tasks in russian Wikipedia.
Make sure that checkwiki.py module is available!

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

COMMENT = "Автоматическое обновление списка техзадач."

LOG = True
LOG_FORMAT = "Processed {done} out of {count} pages ({percentage} %)."

def find_heading(code, node):
    """Find first second-level heading before the mwparserfromhell node."""
    index = code.index(node, recursive=True)
    for heading in list(code.nodes)[index::-1]:
        if not isinstance(heading, mwparserfromhell.nodes.heading.Heading):
            continue
        if heading.level != 2:
            continue
        return heading
    return None

def encode_string_link(text):
    """Replace special symbols with its codes."""
    text = text.replace("<", "%3C")
    text = text.replace(">", "%3E")
    text = text.replace("[", "%5B")
    text = text.replace("]", "%5D")
    text = text.replace("{", "%7B")
    text = text.replace("}", "%7D")
    text = text.replace("|", "%7C")
    return text

def encode_string_text(text):
    """Replace special symbols with corresponding entities or magicwords."""
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace("[", "&#91;")
    text = text.replace("]", "&#93;")
    text = text.replace("{", "&#123;")
    text = text.replace("}", "&#125;")
    text = text.replace("|", "{{!}}")
    return text

def delete_markup(text, site=None, encoder=None):
    """
    Delete all wikimarkup (links, tags, etc) from text.
    First parameter is text to process.
    Second parameter is pywikibot.Site object used for text expansion.
    Third parameter is encoder function - callback which processed text and
    replaces special symbols (<, >, |, etc). It is neccessary for the text
    which was inside the <nowiki> tag.
    """
    ignore_filter = r"<nowiki>(.*?)</nowiki>|<nowiki\s*/>"

    if site is not None:
        text = site.expand_text(text)

    (text, ignored) = ignore(text, ignore_filter)
    text = re.sub(r"<!--.*?-->", "", text)
    text = re.sub(r"\[\[:?(?:[^|]*\|)?([^\]]*)\]\]", "\\1", text)
    text = re.sub(r"\[https?://[^ \]]+ ([^\]]+)\]", "\\1", text)
    text = re.sub(r"'''(.+?)'''", "\\1", text)
    text = re.sub(r"''(.+?)''", "\\1", text)
    text = re.sub(r"<[a-z]+(?:\s*[a-z]+\s*=[^<>]+)?\s*/?>|</[a-z]+>", "", text, flags=re.I)
    text = deignore(text, ignored)

    text = re.sub(ignore_filter, "\\1", text)
    if encoder is not None:
        text = encoder(text)

    text = re.sub(r"[ ]{2,}", " ", text)
    text = text.strip()
    return text

def log(done, count):
    """Write information about progress."""
    if not LOG:
        return
    if count == 0:
        percentage = 100
    else:
        percentage = round(100 * done / count)
    print(LOG_FORMAT.format(done=done, count=count, percentage=percentage))

def update_techtasks(pagename, beginning, line_format, ending, clear=False,
                     reverse_sort=True):
    """Update list of technical tasks."""
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
        for template in code.filter_templates(matches=r"^\{\{\s*" + TEMPLATE_NAME + r"\s*\|"):
            if template.has(DONE_PARAM, ignore_empty=True):
                continue
            param_list = []
            for param in template.params:
                param = str(param)
                if clear:
                    param = delete_markup(param, site, encode_string_text)
                param_list.append(param)
            params = "|".join(param_list)

            heading = find_heading(code, template)
            if heading is None:
                link = page.title()
            else:
                heading = str(heading.title)
                link = page.title() + "#" + delete_markup(heading, site, encode_string_link)

            if template.has(SORT_PARAM, ignore_empty=True):
                sortkey = template.get(SORT_PARAM).value.strip()
            else:
                sortkey = DEFAULT_SORTKEY

            line = line_format.format(params=params, link=link)
            templates.append((line, sortkey))

    log(count, count)
    templates.sort(key=lambda template: template[1], reverse=reverse_sort)

    lines = []
    if len(beginning) > 0:
        lines.append(beginning)
    for template in templates:
        lines.append(template[0])
    if len(ending) > 0:
        lines.append(ending)

    page = pywikibot.Page(site, pagename)
    page.text = "\n".join(lines)
    page.save(COMMENT, minor=False)

def main():
    """Main script function."""
    update_techtasks("Проект:Технические работы/Задачи из обсуждений",
                     "{{/шапка}}",
                     "{{{{/задача|{params}|ссылка={link}}}}}",
                     "{{/подвал}}",
                     clear=False)
    update_techtasks("Проект:Технические работы/Задачи из обсуждений/Актуальные задачи/Список задач",
                     "",
                     "{{{{Проект:Технические работы/Задачи из обсуждений/Актуальные задачи/Список задач/задача|{params}|ссылка={link}}}}}",
                     "",
                     clear=True)

if __name__ == "__main__":
    main()
