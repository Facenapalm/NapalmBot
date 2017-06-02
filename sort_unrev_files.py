"""
This script is used for collection and analysis of list of unreviewed files in ruwiki.
This is the maintainer script for [[:ru:User:NapalmBot/файлы]] pages.

Usage:
    python sort_unrev_files.py
"""

import re
import pywikibot
from pywikibot.data.api import Request

DEFAULT_SITE = pywikibot.Site()

TALK_NS = [
    "Обсуждение",
    "Обсуждение участника",
    "Обсуждение Википедии",
    "Обсуждение файла",
    "Обсуждение шаблона",
    "Обсуждение категории",
    "Обсуждение портала",
    "Обсуждение Инкубатора",
    "Обсуждение проекта",
    "Обсуждение арбитража"
]

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

    for value in result:
        if "." in value["filename"]:
            value["extension"] = re.match(r".*\.(.+)$", value["filename"]).group(1).lower()
        else:
            value["extension"] = ""

        categories = []
        for page in value["pages"]:
            categories += catdict[page]
        value["categories"] = set(categories)
        value["filecats"] = set(catdict[value["filename"]])
        value["pages"] = set(value["pages"])

    return result

def sort_info(info, metapage, site=DEFAULT_SITE):
    """Sort files and create subpages of metapage with corresponding information."""

    metaline = "* [[{metapage}/{{page}}|{{page}}]] ({{num}} страниц)".format(metapage=metapage)
    emptylist = "<noinclude>Всё отпатрулировано. Отличная работа!</noinclude>"
    listcat = "\n<noinclude>[[Категория:Википедия:Списки неотпатрулированных файлов|{page}]]</noinclude>"
    comment = "Обновление списка."

    def _select_from_cats(pagename, catlist, mode="any"):
        """
        Select all unreviewed files used on pages from current categories.
        There are 3 modes: "all", "any" and "none".
        Return the line for metapage.
        """
        catset = set(catlist)
        files = []
        for value in info:
            count = len(catset & value["categories"])
            if (mode == "any" and count > 0 or
                mode == "none" and count == 0 or
                mode == "all" and count == len(catlist)):
                files.append(value["filename"])
        files = sorted(files)

        page = pywikibot.Page(site, metapage + "/" + pagename)
        if files == []:
            text = emptylist
        else:
            text = "\n".join(["# [[:{}]]".format(name) for name in files])
            text += listcat.format(page=pagename)
        page.text = text
        page.save(comment, minor=False)

        return metaline.format(page=pagename, num=len(files))

    def _select_from_ext(pagename, extensions, reverse=False):
        """
        Select all unreviewed files with given extensions.
        Return the line for metapage.
        """
        files = []
        for value in info:
            if (value["extension"] in extensions) != reverse:
                files.append(value["filename"])
        files = sorted(files)

        page = pywikibot.Page(site, metapage + "/" + pagename)
        if files == []:
            text = emptylist
        else:
            text = "\n".join(["# [[:{}]]".format(name) for name in files])
            text += listcat.format(page=pagename)
        page.text = text
        page.save(comment, minor=False)

        return metaline.format(page=pagename, num=len(files))

    def _select_from_use_count(pagename, min_usage=0, max_usage=float("inf")):
        """
        Select all high used unreviewed files.
        Return the line for metapage.
        """
        files = []
        for value in info:
            length = len(value["pages"])
            if length >= min_usage and length <= max_usage:
                files.append((value["filename"], length))
        files = sorted(files, key=lambda x: (-x[1], x[0]))

        page = pywikibot.Page(site, metapage + "/" + pagename)
        if files == []:
            text = emptylist
        else:
            text = "\n".join(["# [[:{}]] ({})".format(name, usage) for (name, usage) in files])
            text += listcat.format(page=pagename)
        page.text = text
        page.save(comment, minor=False)

        return metaline.format(page=pagename, num=len(files))

    def _select_from_namespaces(pagename, nslist):
        """
        Select all unreviewed files which are used on pages with given namespaces.
        Return the line for metapage.
        """
        files = []
        for value in info:
            if any([page.startswith(namespace + ":") for namespace in nslist for page in value["pages"]]):
                files.append(value["filename"])
        files = sorted(files)

        page = pywikibot.Page(site, metapage + "/" + pagename)
        if files == []:
            text = emptylist
        else:
            text = "\n".join(["# [[:{}]]".format(name) for name in files])
            text += listcat.format(page=nslist[0])
        page.text = text
        page.save(comment, minor=False)

        return metaline.format(page=pagename, num=len(files))

    lines = []

    lines.append("Списки неотпатрулированных файлов…")
    lines.append("")

    lines.append("…по тематике:")
    lines.append(_select_from_cats("персоналии", ["Категория:Персоналии по алфавиту"]))
    lines.append(_select_from_cats("фильмы", ["Категория:Фильмы по алфавиту"]))
    lines.append(_select_from_cats("населённые пункты", ["Категория:Населённые пункты по алфавиту"]))
    lines.append(_select_from_cats("альбомы", ["Категория:Альбомы по алфавиту"]))
    lines.append(_select_from_cats("компании", ["Категория:Компании по алфавиту"]))
    lines.append(_select_from_cats("футбольные клубы", ["Категория:Футбольные клубы по алфавиту"]))
    lines.append(_select_from_cats("компьютерные игры", ["Категория:Компьютерные игры по алфавиту"]))
    lines.append(_select_from_cats("песни", ["Категория:Песни по алфавиту"]))
    lines.append(_select_from_cats("мультфильмы", ["Категория:Мультфильмы по алфавиту"]))
    lines.append(_select_from_cats("музыкальные коллективы", ["Категория:Музыкальные коллективы по алфавиту"]))
    lines.append(_select_from_cats("программное обеспечение", ["Категория:Программное обеспечение по алфавиту"]))
    lines.append(_select_from_cats("водные объекты", ["Категория:Водные объекты по алфавиту"]))
    lines.append(_select_from_cats("улицы", ["Категория:Улицы по алфавиту"]))
    lines.append(_select_from_cats("телесериалы", ["Категория:Телесериалы по алфавиту"]))
    lines.append(_select_from_cats("предприятия", ["Категория:Предприятия по алфавиту"]))
    lines.append(_select_from_cats("университеты", ["Категория:Университеты по алфавиту"]))
    lines.append(_select_from_cats("литературные произведения", ["Категория:Литературные произведения по алфавиту"]))
    lines.append(_select_from_cats("книги", ["Категория:Книги по алфавиту"]))
    lines.append(_select_from_cats("станции метрополитена", ["Категория:Станции метрополитена по алфавиту"]))
    lines.append(_select_from_cats("культовые сооружения", ["Категория:Культовые сооружения по алфавиту"]))
    lines.append(_select_from_cats("хоккейные клубы", ["Категория:Хоккейные клубы по алфавиту"]))
    lines.append(_select_from_cats("награды", ["Категория:Награды по алфавиту"]))
    lines.append(_select_from_cats("музеи", ["Категория:Музеи по алфавиту"]))
    lines.append(_select_from_cats("организации", ["Категория:Организации по алфавиту"]))
    lines.append(_select_from_cats("суда", ["Категория:Суда по алфавиту"]))
    lines.append(_select_from_cats("оружие", ["Категория:Оружие по алфавиту"]))
    lines.append(_select_from_cats("сражения", ["Категория:Сражения по алфавиту"]))
    lines.append(_select_from_cats("сайты", ["Категория:Сайты по алфавиту"]))
    lines.append(_select_from_cats("телеканалы", ["Категория:Телеканалы по алфавиту"]))
    lines.append(_select_from_cats("политические партии", ["Категория:Политические партии по алфавиту"]))

    lines.append("…по пространствам имён:")
    lines.append(_select_from_namespaces("из шаблонов", ["Шаблон"]))
    lines.append(_select_from_namespaces("из порталов", ["Портал"]))
    lines.append(_select_from_namespaces("из проектов", ["Проект"]))
    lines.append(_select_from_namespaces("из ПИ Википедия", ["Википедия"]))
    lines.append(_select_from_namespaces("со страниц участников", ["Участник"]))
    lines.append(_select_from_namespaces("из обсуждений", TALK_NS))

    lines.append("…по расширению:")
    # lines.append(_select_from_ext("jpg-изображения", ["jpg", "jpeg"]))
    lines.append("* <s>[[Участник:NapalmBot/файлы/jpg-изображения|jpg-изображения]]</s> (не обновляется)")
    lines.append(_select_from_ext("png-изображения", ["png"]))
    lines.append(_select_from_ext("gif-изображения", ["gif"]))
    lines.append(_select_from_ext("svg-изображения", ["svg"]))
    lines.append(_select_from_ext("tiff-изображения", ["tif", "tiff"]))
    lines.append(_select_from_ext("не изображения", ["jpg", "jpeg", "png", "gif", "svg", "tif", "tiff"], reverse=True))

    lines.append("…по интенсивности использования:")
    lines.append(_select_from_use_count("самые используемые", min_usage=5))
    lines.append(_select_from_use_count("неиспользуемые", max_usage=0))

    lines.append("…используемых в статусных статьях:")
    lines.append(_select_from_cats("статьи года", ["Категория:Википедия:Статьи года по алфавиту"]))
    lines.append(_select_from_cats("избранные статьи", ["Категория:Википедия:Избранные статьи по алфавиту"]))
    lines.append(_select_from_cats("хорошие статьи", ["Категория:Википедия:Хорошие статьи по алфавиту"]))
    lines.append(_select_from_cats("добротные статьи", ["Категория:Википедия:Добротные статьи по алфавиту"]))
    lines.append(_select_from_cats("избранные списки", ["Категория:Википедия:Избранные списки по алфавиту"]))

    lines.append("Если вы не нашли в списке интересующую вас тематику — [[ОУ:Facenapalm|напишите ботоводу]].")
    lines.append("")
    lines.append("[[Категория:Википедия:Списки неотпатрулированных файлов| ]]")

    page = pywikibot.Page(site, metapage)
    page.text = "\n".join(lines)
    page.save(comment, minor=False)


def main():
    """Update NapalmBot's subpages."""
    info = collect_info()
    sort_info(info, "Участник:NapalmBot/файлы")

if __name__ == "__main__":
    main()
