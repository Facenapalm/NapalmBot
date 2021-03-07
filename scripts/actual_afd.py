"""Update ruwiki's [[ВП:КУП]] shortcut to the actual 'Articles for deletion' page."""

import pywikibot

TEXT = """#REDIRECT [[Википедия:К удалению/{{subst:#time:j xg Y}}]]"""

def main():
    """Main script function."""
    site = pywikibot.Site()
    page = pywikibot.Page(site, "Википедия:КУП")
    page.text = TEXT
    page.save("Обновление даты.")

if __name__ == "__main__":
    main()
