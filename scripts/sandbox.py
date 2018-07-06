"""
Sandbox cleaner for Russian Wikipedia.

Usage:
    python sandbox.py
"""

import pywikibot

SANDBOXES = [
    ("Википедия:Песочница", "{{тестируйте ниже}}\n"),
    ("Обсуждение Википедии:Песочница", "{{тестируйте ниже}}\n"),
    ("Инкубатор:Песочница", "{{тестируйте ниже}}\n"),
    ("Шаблон:Песочница", "<noinclude>{{тестируйте ниже}}</noinclude>"),
    ("Шаблон:Песочница/doc", "<noinclude>{{тестируйте ниже}}</noinclude>\n"),
]

def delayed_edit(page, text, delay=15):
    """
    Replace text of the page (first parameter) with given one (second parameter)
    only if last edit was made more than 15 (can be changed via third parameter)
    minutes ago.
    """
    delta = pywikibot.Timestamp.utcnow() - page.editTime()
    if delta.total_seconds() >= 60 * delay:
        page.text = text
        page.save("Бот: очистка песочницы", force=True)

def main():
    """Main script function."""
    site = pywikibot.Site()
    for (title, text) in SANDBOXES:
        page = pywikibot.Page(site, title)
        delayed_edit(page, text)

if __name__ == "__main__":
    main()
 