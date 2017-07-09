"""Extract list of oldreviewed redirects."""

import pywikibot
import validstats

TO_FILE = False

def main():
    """Main script function."""
    site = pywikibot.Site()
    titles = sorted(validstats.get_orlist(site, "*", "redirects"))
    text = "\n".join(["* [{{{{fullurl:{title}|action=history}}}} {title}]".format(title=title) for title in titles])
    if TO_FILE:
        output = open("output.txt", "w", encoding="utf-8")
        output.write(text)
        output.close()
    else:
        page = pywikibot.Page(site, "Участник:ØM/Перенаправления")
        page.text = text
        page.save("Обновление списка.")

if __name__ == "__main__":
    main()
