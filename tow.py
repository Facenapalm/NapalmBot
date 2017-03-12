"""
Script updates russian {{Перевод недели}} template according to Translate of
the Week project.

Usage:
    python tow.py
"""

import re
import pywikibot

def main():
    """Update template."""
    meta = pywikibot.Site("meta", "meta")
    template = pywikibot.Page(meta, "Template:TOWThisweek")
    match = re.search(r"\[\[:([a-z\-]+):(.*?)\]\]", template.text, flags=re.I)
    original = match.group(0)
    lang = match.group(1)
    link = match.group(2)

    ruwiki = pywikibot.Site()
    orwiki = pywikibot.Site(lang)
    try:
        russian = pywikibot.ItemPage.fromPage(pywikibot.Page(orwiki, link)).getSitelink(ruwiki)
    except Exception:
        russian = "'''[[Шаблон:Перевод недели|Укажите название статьи]]'''"

    template = pywikibot.Page(ruwiki, "Шаблон:Перевод недели")
    result = template.text
    result = re.sub(r"(<span id=\"russian\">).*?(</span>)", "\\1" + russian + "\\2", result)
    result = re.sub(r"(<span id=\"original\">).*?(</span>)", "\\1" + original + "\\2", result)
    template.text = result
    template.save("Обновление перевода недели.", minor=False)

if __name__ == "__main__":
    main()
