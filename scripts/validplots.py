"""
This script creates validation plots based on statistics collected by
validstats.py module.
Statfile structure: first line - any comment (will be ignored), other lines -
values, separated with tabs (date, unrev_main, old_main, unrev_file, old_file,
unrev_template, old_template, unrev_cat, old_cat, unrev_redir, old_redir).

Usage:
    python validplots.py statfile [outdir]

outdir is used for temporary file storing.
"""

import sys
import os
import pywikibot
import matplotlib
matplotlib.use('AGG')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

FILEDESC = """
== Краткое описание ==
{{Изображение
| Описание       = Динамика числа неотпатрулированных страниц в виде графика.
| Источник       = собственная работа
| Время создания = 2017
| Автор          = [[У:Facenapalm]]
}}

== Лицензирование ==
{{self|CC-Zero}}
"""

LOCAL = False # set it to True to deny file uploading

def main():
    """Main script function."""
    argc = len(sys.argv)
    if argc == 1:
        return
    fname = sys.argv[1]
    if argc == 2:
        tempcat = "."
    else:
        tempcat = sys.argv[2]

    def _filter_date(date):
        """Return x-axis labels based on dates list."""
        months = ["январь", "февраль", "март", "апрель", "май", "июнь",
                  "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"]
        date_parts = date.split("-")
        if date_parts[2] != "01":
            return ""
        if date_parts[1] == "01":
            return date_parts[0]
        else:
            return months[int(date_parts[1]) - 1]

    data = [line.strip().split("\t") for line in list(open(fname))[1:]]
    data = [list(line) for line in zip(*data)] # transpose data
    data[0] = [_filter_date(date) for date in data[0]]
    axis = list(range(len(data[0])))

    def _plot_pair(title, ufilename, udata, ucolor, ofilename, odata, ocolor):
        """
        Make 2 plots with unreviewed and old pages respectively.
        If ufilename == ofilename, then make it on single canvas.
        """
        utitle = "Динамика числа неотпатрулированных {}".format(title)
        otitle = "Динамика числа устаревших {}".format(title)
        single = ufilename == ofilename

        def _init_plot(title):
            """Iternal function for plt initialization."""
            plt.figure(figsize=(16, 9), dpi=100)
            plt.xticks(axis, data[0])
            plt.xlabel(title)
            plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))

        def _line_plot(data, color, label):
            """Iternal function for making one plot line."""
            plt.plot(axis, data, linewidth=3, color=color, label=label)

        def _final_plot(filename):
            """Iternal function for plot saving and uploading."""
            filepath = os.path.join(tempcat, filename)
            if single:
                plt.legend()
            plt.margins(0, 0.02)
            plt.subplots_adjust(left=0.05, right=1, top=1, bottom=0.1)
            plt.savefig(filepath, bbox_inches="tight")

            if not LOCAL:
                site = pywikibot.Site()
                page = pywikibot.FilePage(site, filename)
                page.upload(filepath, comment="Обновление графика.", text=FILEDESC, ignore_warnings=True)

                os.remove(filepath)

        _init_plot(utitle)
        _line_plot(udata, ucolor, "Неотпатрулированные")
        if not single:
            _final_plot(ufilename)
            _init_plot(otitle)
        _line_plot(odata, ocolor, "Устаревшие")
        _final_plot(ofilename)

    _plot_pair("статей",
               "validation main unrev.png", data[1], "#027495",
               "validation main old.png", data[2], "#01A9C1")
    _plot_pair("файлов",
               "validation files unrev.png", data[3], "#D82488",
               "validation files old.png", data[4], "#EC7BCD")
    _plot_pair("шаблонов",
               "validation templates unrev.png", data[5], "#6A2B00",
               "validation templates old.png", data[6], "#AA5A01")
    _plot_pair("категорий",
               "validation categories.png", data[7], "#FB7E00",
               "validation categories.png", data[8], "#FECD42")
    _plot_pair("перенаправлений",
               "validation redirects unrev.png", data[9], "#427322",
               "validation redirects old.png", data[10], "#83A958")

if __name__ == "__main__":
    main()
