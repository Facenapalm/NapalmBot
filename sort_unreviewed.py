"""
This script is used for collection and analysis of list of unreviewed files in ruwiki.
This is the maintainer script for [[:ru:User:NapalmBot/файлы]] pages.
"""

import re
import pywikibot
from pywikibot.data.api import Request

DEFAULT_SITE = pywikibot.Site()

def get_pages_categories(pagelist, site=DEFAULT_SITE, limit=500):
    """
    For every page from the list get list of categories and return
        {page: [categories]}
    dictionary.
    """
    result = dict.fromkeys(pagelist, [])
    kwargs = {
        "action": "query",
        "prop": "categories",
        "cllimit": "5000"
    }
    for idx in range(0, len(pagelist), limit):
        kwargs["titles"] = "|".join(pagelist[idx:idx+limit])
        request = Request(site=site, **kwargs)
        while True:
            answer = request.submit()
            for value in answer["query"]["pages"].values():
                if "categories" in value:
                    cats = [cat["title"] for cat in value["categories"]]
                    result[value["title"]] = result[value["title"]] + cats
            if "query-continue" in answer:
                request["clcontinue"] = answer["query-continue"]["categories"]["clcontinue"]
                continue
            break
    return result

def collect_info(site=DEFAULT_SITE):
    """
    Get the list of unreviewed files with additional information:
        "filename": title of file page
        "extension": in lowercase
        "filecats": file categories
        "pages": pages where category is used
        "categories": categories of those pages
    """
    result = []

    # get filename and pages from api request

    def _submit_and_parse(request):
        """Divide answer to list of values and continue info."""
        answer = request.submit()
        values = list(answer["query"]["pages"].values())
        if "query-continue" in answer:
            contin = answer["query-continue"]
        else:
            contin = {}
        return (values, contin)

    kwargs = {
        "action": "query",
        "prop": "fileusage",
        "fulimit": "5000",
        "generator": "unreviewedpages",
        "gurnamespace": "6",
        "gurfilterredir": "nonredirects",
        "gurlimit": "5000"
    }

    while True:
        # iterate for gurstart, get list of files
        request = Request(site=site, **kwargs)
        (values, contin) = _submit_and_parse(request)
        chunk = [{"filename": value["title"], "pages": []} for value in values]

        while True:
            # iterate for fucontinue, get list of file users
            for key, value in enumerate(values):
                if "fileusage" in value:
                    chunk[key]["pages"] += [usageinfo["title"] for usageinfo in value["fileusage"]]
            if "fileusage" in contin:
                request["fucontinue"] = contin["fileusage"]["fucontinue"]
                (values, contin) = _submit_and_parse(request)
                continue
            else:
                break
        result += chunk

        if "unreviewedpages" in contin:
            kwargs["gurstart"] = contin["unreviewedpages"]["gurstart"]
            continue
        else:
            break

    # collect additional info

    pagelist = [value["filename"] for value in result]
    for value in result:
        pagelist += value["pages"]
    pagelist = list(set(pagelist))
    catdict = get_pages_categories(pagelist, site=site)

    for key, value in enumerate(result):
        if "." in value["filename"]:
            value["extension"] = re.match(r".*\.(.+)$", value["filename"]).group(1).lower()
        else:
            value["extension"] = ""
        value["filecats"] = catdict[value["filename"]]

        categories = []
        for page in value["pages"]:
            categories += catdict[page]
        value["categories"] = list(set(categories))

    return result

def sort_info(info, metapage, site=DEFAULT_SITE):
    """Sort files and create subpages of metapage with corresponding information."""

    metaline = "* [[{metapage}/{{page}}|{{page}}]] ({{num}} страниц)".format(metapage=metapage)
    comment = "Обновление списка."

    def _select_from_cat(pagename, category):
        """
        Select all unreviewed files used on pages from current category.
        Return the line for metapage.
        """
        files = []
        for value in info:
            if category in value["categories"]:
                files.append(value["filename"])
        files = sorted(files)

        page = pywikibot.Page(site, metapage + "/" + pagename)
        if files == []:
            page.text = "Всё отпатрулировано. Отличная работа!"
        else:
            page.text = "\n".join(["# [[:{}]]".format(name) for name in files])
        page.save(comment)

        return metaline.format(page=pagename, num=len(files))

    def _select_from_ext(pagename, extensions, reverse=False):
        """
        Select all unreviewed files with given extensions.
        Return the number of found files.
        """
        files = []
        for value in info:
            if (value["extension"] in extensions) != reverse:
                files.append(value["filename"])
        files = sorted(files)

        page = pywikibot.Page(site, metapage + "/" + pagename)
        if files == []:
            page.text = "Всё отпатрулировано. Отличная работа!"
        else:
            page.text = "\n".join(["# [[:{}]]".format(name) for name in files])
        page.save(comment)

        return metaline.format(page=pagename, num=len(files))

    def _select_most_used(pagename, level):
        """
        Select all high used unreviewed files.
        Return the number of found files.
        """
        files = []
        for value in info:
            length = len(value["pages"])
            if length > level:
                files.append((value["filename"], length))
        files = sorted(files, key=lambda x: -x[1])

        page = pywikibot.Page(site, metapage + "/" + pagename)
        if files == []:
            page.text = "Всё отпатрулировано. Отличная работа!"
        else:
            page.text = "\n".join(["# [[:{}]] ({})".format(name, usage) for (name, usage) in files])
        page.save(comment)

        return metaline.format(page=pagename, num=len(files))

    lines = []

    lines.append("Неотпатрулированные файлы по тематике:")
    lines.append(_select_from_cat("персоналии", "Категория:Персоналии по алфавиту"))
    lines.append(_select_from_cat("фильмы", "Категория:Фильмы по алфавиту"))
    lines.append(_select_from_cat("населённые пункты", "Категория:Населённые пункты по алфавиту"))
    lines.append(_select_from_cat("альбомы", "Категория:Альбомы по алфавиту"))
    lines.append(_select_from_cat("компании", "Категория:Компании по алфавиту"))
    lines.append(_select_from_cat("футбольные клубы", "Категория:Футбольные клубы по алфавиту"))
    lines.append(_select_from_cat("компьютерные игры", "Категория:Компьютерные игры по алфавиту"))
    lines.append(_select_from_cat("песни", "Категория:Песни по алфавиту"))
    lines.append(_select_from_cat("мультфильмы", "Категория:Мультфильмы по алфавиту"))
    lines.append(_select_from_cat("музыкальные коллективы", "Категория:Музыкальные коллективы по алфавиту"))
    lines.append(_select_from_cat("программное обеспечение", "Категория:Программное обеспечение по алфавиту"))
    lines.append(_select_from_cat("водные объекты", "Категория:Водные объекты по алфавиту"))
    lines.append(_select_from_cat("улицы", "Категория:Улицы по алфавиту"))
    lines.append(_select_from_cat("телесериалы", "Категория:Телесериалы по алфавиту"))
    lines.append(_select_from_cat("предприятия", "Категория:Предприятия по алфавиту"))
    lines.append(_select_from_cat("университеты", "Категория:Университеты по алфавиту"))
    lines.append(_select_from_cat("литературные произведения", "Категория:Литературные произведения по алфавиту"))
    lines.append(_select_from_cat("книги", "Категория:Книги по алфавиту"))
    lines.append(_select_from_cat("станции метрополитена", "Категория:Станции метрополитена по алфавиту"))
    lines.append(_select_from_cat("культовые сооружения", "Категория:Культовые сооружения по алфавиту"))
    lines.append(_select_from_cat("хоккейные клубы", "Категория:Хоккейные клубы по алфавиту"))
    lines.append(_select_from_cat("награды", "Категория:Награды по алфавиту"))
    lines.append(_select_from_cat("музеи", "Категория:Музеи по алфавиту"))
    lines.append(_select_from_cat("организации", "Категория:Организации по алфавиту"))
    lines.append(_select_from_cat("суда", "Категория:Суда по алфавиту"))
    lines.append(_select_from_cat("оружие", "Категория:Оружие по алфавиту"))
    lines.append(_select_from_cat("сражения", "Категория:Сражения по алфавиту"))
    lines.append(_select_from_cat("сайты", "Категория:Сайты по алфавиту"))
    lines.append(_select_from_cat("телеканалы", "Категория:Телеканалы по алфавиту"))
    lines.append(_select_from_cat("политические партии", "Категория:Политические партии по алфавиту"))

    lines.append("Используемые в статусных статьях:")
    lines.append(_select_from_cat("статьи года", "Категория:Википедия:Статьи года по алфавиту"))
    lines.append(_select_from_cat("избранные статьи", "Категория:Википедия:Избранные статьи по алфавиту"))
    lines.append(_select_from_cat("хорошие статьи", "Категория:Википедия:Хорошие статьи по алфавиту"))
    lines.append(_select_from_cat("добротные статьи", "Категория:Википедия:Добротные статьи по алфавиту"))
    lines.append(_select_from_cat("избранные списки", "Категория:Википедия:Избранные списки по алфавиту"))

    lines.append("Прочее:")
    lines.append(_select_from_ext("не изображения", ["jpg", "jpeg", "png", "gif", "svg", "tif", "tiff"], reverse=True))
    lines.append(_select_most_used("самые используемые", 5))

    lines.append("")
    lines.append("[[Категория:Википедия:Патрулирование]]")

    page = pywikibot.Page(site, metapage)
    page.text = "\n".join(lines)
    page.save(comment)


def main():
    """Update NapalmBot's subpages."""
    info = collect_info()
    sort_info(info, "Участник:NapalmBot/файлы")

if __name__ == "__main__":
    main()
