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

def process_purge(site, catname, limit=500):
    """Purge all pages from category and return status for logging."""
    members = list(pywikibot.Category(site, catname).members())
    length = len(members);
    for i in range(0, length, limit):
        if not site.purgepages(members[i:i+limit]):
            return "неожиданный ответ сервера"
    return str(length)

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
            # if page was deleted while script is working, touch() can create empty page (WHY?!)
            # temporary pywikibot.Page() object initialization should fix this problem
            temp = pywikibot.Page(site, page.title())
            temp.touch()
        except pywikibot.exceptions.LockedPage:
            errors += 1
    return "нулевых правок: " + str(len(members) - errors)

def log(site, respond):
    """Edit template status page."""
    page = pywikibot.Page(site, "Шаблон:Очищать кэш/статус")
    page.text = "~~~~. Обработано " + "; ".join(respond) + "<noinclude>\n[[Категория:Википедия:Подстраницы шаблонов]]\n</noinclude>"
    page.save("Отчёт.")

KEYS = {
    "--hourly": process_hourly,
    "--daily": process_daily,
    "--null": process_null
}

DISABLE_LOG = "--nolog"

def main():
    """Get console arguments and call corresponding fucntions."""
    if len(sys.argv) == 1:
        return
    args = sys.argv[1:]
    site = pywikibot.Site()
    respond = []
    for arg in args:
        if arg in KEYS:
            respond.append(KEYS[arg](site))
    if DISABLE_LOG not in args:
        log(site, respond)

if __name__ == "__main__":
    main()
