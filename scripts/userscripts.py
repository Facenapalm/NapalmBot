"""
This script collects statistics about userscripts usage in Russian Wikipedia and
publishes it at [[Участник:NapalmBot/Самые используемые скрипты]]. Script can
detect only importScript functions and do not count cross-wiki script imports.
"""
import re
from collections import Counter
import pywikibot

def ucfirst(string):
    """Return string with first letter in upper case."""
    if len(string) < 2:
        return string.upper()
    else:
        return string[:1].upper() + string[1:]

def unificate_link(link):
    """Remove "user:" prefix, deal with trailing spaces and underscores."""
    (pagename, prefix) = re.subn(r"^ *(?:[Уу]|[Уу]частник|[Уу]частница|[Uu]|[Uu]ser) *:", "", link)
    if not prefix:
        return None
    return ucfirst(re.sub(" ", "_", pagename).strip("_"))

def process_page(page):
    """Analyze all importScript functions and return a list of used scripts."""

    title = r"^[^/]+/(common|vector|cologneblue|minerva|modern|monobook|timeless)\.js$"
    comments = r"//.+|/\*(?:.|\n)*?\*/"
    scripts = r"importScript *\( *([\"'])([^\"'\n]*?)\1(?: *, *[\"']ru[\"'])? *\)"

    if not re.match(title, page.title()):
        return []

    text = page.text
    text = re.sub(comments, "", text)

    result = []
    for quote, link in re.findall(scripts, text):
        link = unificate_link(link)
        if link:
            result.append(link)

    return result

def get_stats(site):
    """Get an { script : count } dictionary."""
    result = []
    for page in site.search("insource:\"importScript\"", [2], content=True):
        result += process_page(page)
    return dict(Counter(result))

def main():
    """Main script function."""
    site = pywikibot.Site()
    stats = get_stats(site)

    result = "Последнее обновление: {{subst:#time:j xg Y, H:i}}\n\n"
    result += "{| class=\"wikitable sortable\"\n"
    result += "! Место !! Скрипт !! Использований\n"
    formatstr = "|-\n| {num} || [[Участник:{page}]] || [https://ru.wikipedia.org/w/index.php?search=insource%3A%22{page}%22&ns2=1 {count}]\n"
    for num, page in enumerate(sorted(sorted(stats), key=stats.get, reverse=True)):
        count = stats[page]
        result += formatstr.format(num=num + 1, page=page, count=count)
    result += "|}\n\n"

    page = pywikibot.Page(site, "Участник:NapalmBot/Самые используемые скрипты")
    page.text = result
    page.save("Обновление данных.", minor=False)

if __name__ == "__main__":
    main()
