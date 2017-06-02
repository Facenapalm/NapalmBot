"""
Maintainer script for ruwiki's {{очищать кэш}} aka {{autopurge}} template.

Usage:
    python autopurge.py [--hourly] [--daily] [--null]

Each key process one category, see template documentation; period should be
correctly set via crontab.
"""

import sys
import pywikibot
import pywikibot.exceptions

def process_purge(site, catname):
    """Purge all pages from category and return status for logging."""
    members = list(pywikibot.Category(site, catname).members())
    if site.purgepages(members):
        return str(len(members))
    else:
        return "неожиданный ответ сервера"

def process_hourly(site):
    """Purge all hourly-purged pages and return log part."""
    return "срочных: " + process_purge(site, "К:Википедия:Страницы с ежечасно очищаемым кэшем")

def process_daily(site):
    """Purge all daily-purged pages and return log part."""
    return "ежедневных: " + process_purge(site, "К:Википедия:Страницы с ежедневно очищаемым кэшем")

def process_null(site):
    """Purge all daily-nulledited pages and return log part."""
    catname = "К:Википедия:Страницы с ежедневно совершаемой нулевой правкой"
    members = list(pywikibot.Category(site, catname).members())
    errors = 0
    for page in members:
        try:
            page.touch()
        except pywikibot.exceptions.LockedPage:
            errors += 1
    return "нулевых правок: " + str(len(members) - errors)

def log(site, respond):
    """Edit template status page."""
    page = pywikibot.Page(site, "Шаблон:Очищать кэш/статус")
    page.text = "~~~~. Обработано " + "; ".join(respond)
    page.save("Отчёт.")

KEYS = {
    "--hourly": process_hourly,
    "--daily": process_daily,
    "--null": process_null
}

def main():
    """Get console arguments and call corresponding fucntions."""
    if len(sys.argv) == 1:
        return
    site = pywikibot.Site()
    respond = []
    for arg in sys.argv[1:]:
        if arg in KEYS:
            respond.append(KEYS[arg](site))
    log(site, respond)

if __name__ == "__main__":
    main()
