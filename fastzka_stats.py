"""
Publishes a list of the most active administrators based on logfile,
created by fastzka.py script, and deletes old records from log.

Usage:
    python fastzka_stats.py logfile
"""

import re
import sys
from datetime import date, timedelta
import pywikibot

def get_dates():
    """Get minimal and maximal date to count and localized name of current month."""
    months = ["январь", "февраль", "март", "апрель", "май", "июнь",
              "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"]
    cur = date.today()
    prev = cur.replace(day=1) - timedelta(days=1)
    localized = "{} {}".format(months[prev.month - 1], prev.year)
    return (prev.strftime('%Y%m'), cur.strftime('%Y%m'), localized)

def unificate_name(name):
    """Process whitespaces, make first letter upper."""
    name = re.sub(r"[_ ]+", " ", name).strip()
    if len(name) < 2:
        return name.upper()
    else:
        return name[0].upper() + name[1:]

def main():
    """Main script function."""
    if len(sys.argv) == 1:
        return
    (mindate, maxdate, month) = get_dates()

    statistics = {}
    filelines = []
    for line in open(sys.argv[1], encoding="utf-8"):
        parts = line.split("/")
        name = unificate_name(parts[0])
        timestamp = parts[1].strip()
        if timestamp > mindate and timestamp < maxdate:
            if name in statistics:
                statistics[name] = statistics[name] + 1
            else:
                statistics[name] = 1
        if timestamp > maxdate:
            filelines += line

    statarray = []
    for admin, count in statistics.items():
        statarray.append((count, admin))
    statarray.sort(reverse=True)

    if len(statarray) == 0:
        return

    pagelines = []
    pagelines.append("\n\n== Статистика за {} ==".format(month))
    for count, admin in statarray:
        pagelines.append("# [[У:{admin}|]] ({count} {{{{subst:plural:{count}|итог|итога|итогов}}}})".format(admin=admin, count=count))
    pagelines.append("Отправлено ~~~~")

    site = pywikibot.Site()
    page = pywikibot.Page(site, "Обсуждение Википедии:Запросы к администраторам/Быстрые")
    page.text = page.text + "\n".join(pagelines)
    page.save("/* Статистика за {} */ Новая тема.".format(month), minor=False)

    open(sys.argv[1], "w", encoding="utf-8").write("".join(filelines))

if __name__ == "__main__":
    main()
