"""
Script updates list of technical tasks in russian Wikipedia.
Written in python 3.5, compatibility with older versions doesn't tested.

Usage:
    python techtasks.py
"""

import re
import pywikibot
import mwparserfromhell

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

TEMPLATE_REGEXP = r"^\{\{\s*" + TEMPLATE_NAME + r"\s*\|"

def linkify_heading(text):
    """
    Converts heading text to link part, which goes after #.
    For example: "== [[Something|head]]''ing'' ==" -> "heading".
    """
    text = re.sub(r"\[\[:?(?:[^|]*\|)?([^\]]*)\]\]", "\\1", text)
    text = re.sub(r"'''(.+?)'''", "\\1", text)
    text = re.sub(r"''(.+?)''", "\\1", text)
    text = re.sub(r"[ ]{2,}", " ", text)
    text = text.strip()
    return text

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

def main():
    """Updates list of technical tasks."""
    site = pywikibot.Site()

    templates = []
    category = pywikibot.Category(site, CATEGORY_NAME)
    for page in category.members():
        text = page.text
        code = mwparserfromhell.parse(text)
        link_prefix = page.title()
        for template in code.filter_templates(matches=TEMPLATE_REGEXP):
            if template.has(DONE_PARAM, ignore_empty=True):
                continue
            params = "|".join([str(param) for param in template.params])

            heading = find_heading(code, template)
            if heading is None:
                link = link_prefix
            else:
                heading = str(heading.title)
                link = link_prefix + "#" + linkify_heading(heading)

            sortkey = DEFAULT_SORTKEY
            if template.has(SORT_PARAM, ignore_empty=True):
                sortkey = template.get(SORT_PARAM).value.strip()

            line = RESULT_FORMAT.format(params=params, link=link)
            templates.append((line, sortkey))
    templates.sort(key=lambda template: template[1], reverse=SORT_REVERSE)

    lines = []
    lines.append(RESULT_BEGINNING)
    lines += [template[0] for template in templates]
    lines.append(RESULT_ENDING)
    text = "\n".join(lines)

    page = pywikibot.Page(site, RESULT_PAGE)
    page.text = text
    page.save(COMMENT, minor=False)

if __name__ == "__main__":
    main()
