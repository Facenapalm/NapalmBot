"""Sandbox cleaner for Russian Wikipedia."""

import pywikibot

SANDBOXES = [
    ("Википедия:Песочница", "{{/Пишите ниже}}\n<!-- Не удаляйте, пожалуйста, эту строку, тестируйте ниже -->\n"),
    ("Обсуждение Википедии:Песочница", "{{/Пишите ниже}}\n<!-- Не удаляйте, пожалуйста, эту строку, тестируйте ниже -->\n"),
    ("Инкубатор:Песочница", "{{/Пишите ниже}}\n<!-- Не удаляйте, пожалуйста, эту строку, тестируйте ниже -->\n"),
    ("Шаблон:Песочница для шаблонов", "<noinclude>{{/Пишите ниже}}</noinclude><!-- Не удаляйте, пожалуйста, эту строку, тестируйте ниже -->")
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
    """Clean all sandboxes."""
    site = pywikibot.Site()
    for (title, text) in SANDBOXES:
        page = pywikibot.Page(site, title)
        delayed_edit(page, text)

if __name__ == "__main__":
    main()
 