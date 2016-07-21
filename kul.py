"""
Script updates article list in ruwiki's {{Случайные статьи с КУЛ}} template.
Written in python 3.5, compatibility with older versions doesn't tested.

Usage:
    python kul.py
"""

import random
import pywikibot

CATEGORY_NAME = "Категория:Википедия:Статьи для срочного улучшения"
TEMPLATE_NAME = "Шаблон:Случайные статьи с КУЛ"

TEXT_BEFORE = "{{fmbox|text=<center>Статьи для доработки: "
TEXT_AFTER = ".</center>}}<noinclude>[[Категория:Навигационные шаблоны:Для обсуждений]]</noinclude>"

LIST_LEN = 5

def main():
    """Updates article list in {{Случайные статьи с КУЛ}} template."""
    site = pywikibot.Site()

    category = pywikibot.Category(site, CATEGORY_NAME)
    pages = list(category.articles())
    pages = ["[[" + page.title() + "]]" for page in pages]

    random.shuffle(pages)

    text = ", ".join(pages[:LIST_LEN])
    text = TEXT_BEFORE + text + TEXT_AFTER

    template = pywikibot.Page(site, TEMPLATE_NAME)
    template.text = text
    template.save("Обновление списка статей.")

if __name__ == "__main__":
    main()
