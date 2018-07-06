"""
Sandbox cleaner for Russian Wikipedia.

Usage:
    python sandbox.py [--noclear]

If --noclear is specified, script will restore deleted headers, but will not
clear sandboxes.
"""

import sys
import pywikibot

SANDBOXES = [
    ("Википедия:Песочница", "{{тестируйте ниже}}\n", 15),
    ("Обсуждение Википедии:Песочница", "{{тестируйте ниже}}\n", 15),
    ("Инкубатор:Песочница", "{{тестируйте ниже}}\n", 15),
    ("Шаблон:Песочница", "<noinclude>{{тестируйте ниже}}</noinclude>", 30),
    ("Шаблон:Песочница/doc", "<noinclude>{{тестируйте ниже}}</noinclude>\n", 30),
]

def main():
    """Main script function."""
    site = pywikibot.Site()
    time = pywikibot.Timestamp.utcnow()
    for (title, text, delay) in SANDBOXES:
        page = pywikibot.Page(site, title)
        delta = time - page.editTime()
        if "--noclear" not in sys.argv and delta.total_seconds() >= 60 * delay:
            # clear sandbox
            page.text = text
            page.save("Бот: очистка песочницы", force=True)
        elif not page.text.startswith(text.strip()):
            # restore header
            page.text = text + page.text
            page.save("Бот: не удаляйте шаблон, тестируйте ниже!", force=True)

if __name__ == "__main__":
    main()
 
