"""
Maintainer script for ruwiki's administrator attention requests table
([[:ru:ВП:ЗКАБ]]).

Log file is used for saving "администратор" field in deleted requests.

Usage:
    python fastrfaa.py [logfile]
"""

import re
import sys
from datetime import datetime
import pywikibot

REGEXP = re.compile(r"""
    (?P<indent>\n*)
    ==[ ]*(?P<header>.*?)[ ]*==\s+
    (?P<section>
        <onlyinclude>\s*
        (?P<template>
            (?:[^<]|<(?!/?onlyinclude))*?
        )
        \s*</onlyinclude>
    )
""", re.I | re.VERBOSE)

TIME_FORMAT = "%Y%m%d%H%M%S"
UTCNOW = datetime.utcnow()
UTCNOWSTR = UTCNOW.strftime(TIME_FORMAT)

MOVED_TEXT = ""

CORRECTED_COUNT = 0
DELETED_DONE_COUNT = 0
DELETED_UNDONE_COUNT = 0
MOVED_COUNT = 0

if len(sys.argv) > 1:
    LOGFILE = open(sys.argv[1], "a", encoding="utf-8")
else:
    LOGFILE = None

def minor_fixes(text):
    """Fix some minor errors before processing the page."""
    text = re.sub(r"^==.*?==\n+(==.*?==)$", "\\1", text, flags=re.M) # empty sections
    return text

def correct_request(match):
    """Fix some errors, for example, update header if it doesn't match the content."""
    # initialization
    corrected = False
    indent = match.group("indent")
    header = match.group("header")
    section = match.group("section")

    # missing timestamp fix
    (section, flag) = re.subn(
        r"(\|\s*администратор\s*=[^/\n]*[^/\s][^/\n]*)\n",
        "\\1/" + UTCNOWSTR + "\n",
        section)
    if flag > 0:
        corrected = True

    # wrong header fix
    question = re.search(r"\|\s*вопрос\s*=(.*)", section)
    timestamp = re.search(r"\|\s*автор\s*=[^/]+/\s*(\d{14})", section)
    if question is None or timestamp is None:
        # request is completely broken
        return match.group(0)

    correct_header = question.group(1).strip() + "/" + timestamp.group(1)
    if header != correct_header:
        corrected = True
        header = correct_header

    # finalization
    if corrected:
        global CORRECTED_COUNT
        CORRECTED_COUNT += 1
        return "{}== {} ==\n{}".format(indent, header, section)
    else:
        return match.group(0)

def move_old_request(template):
    """Forms text for (non-fast) rfaa in MOVED_TEXT."""
    global MOVED_TEXT
    global MOVED_COUNT
    parts = re.search(r"\|\s*вопрос\s*=(.*)", template).group(1).strip().split("/")
    if len(parts) == 2:
        header = parts[1]
    else:
        header = parts[0]
    MOVED_TEXT += "== {} ==\n".format(header)
    MOVED_TEXT += re.sub(r"(ЗКА:Быстрый запрос)", "subst:\\1", template)
    MOVED_TEXT += "\n* {{block-small|Перенесено со страницы быстрых запросов ботом, поскольку запрос не был выполнен в течение 7 дней. ~~~~}}"
    MOVED_TEXT += "\n\n"
    MOVED_COUNT += 1

def delete_old_request(match):
    """Process one table row and delete it if it's neccessary."""
    template = match.group("template")
    status_match = re.search(r"\|\s*статус\s*=\s*([+-])", template)
    date_match = re.search(r"\|\s*автор\s*=[^/]+/\s*(\d{14})", template)
    admin_match = re.search(r"\|\s*администратор\s*=([^/\n]+)/\s*(\d{14})", template)
    if admin_match is None:
        # request is still open
        if date_match is not None:
            date = datetime.strptime(date_match.group(1), TIME_FORMAT)
            if (UTCNOW - date).total_seconds() > 7 * 24 * 60 * 60:
                # very old request that should be moved to rfaa
                move_old_request(template)
                return ""
        return match.group(0)
    if status_match is None:
        done = True
    else:
        done = status_match.group(1) == "+"
    admin = admin_match.group(1).strip()
    date_str = admin_match.group(2)

    delay = (1 if done else 3) * 24 * 60 * 60
    date = datetime.strptime(date_str, TIME_FORMAT)
    if (UTCNOW - date).total_seconds() < delay:
        return match.group(0)
    else:
        if done:
            global DELETED_DONE_COUNT
            DELETED_DONE_COUNT += 1
        else:
            global DELETED_UNDONE_COUNT
            DELETED_UNDONE_COUNT += 1
        if LOGFILE:
            LOGFILE.write("{}/{}\n".format(admin, date_str))
        return ""

def form_comment():
    """Analyze global variables and form a comment for an edit."""
    plural = lambda num, word: word + ("ый" if num % 10 == 1 and num % 100 != 11 else "ых")
    plural_phrase = lambda num, word: str(num) + " " + plural(num, word)

    deleted_parts = []
    if DELETED_DONE_COUNT > 0:
        deleted_parts.append(plural_phrase(DELETED_DONE_COUNT, "выполненн"))
    if DELETED_UNDONE_COUNT > 0:
        deleted_parts.append(plural_phrase(DELETED_UNDONE_COUNT, "невыполненн"))
    if MOVED_COUNT > 0:
        deleted_parts.append(plural_phrase(MOVED_COUNT, "перенесённ"))
    deleted = ", ".join(deleted_parts)

    if CORRECTED_COUNT:
        corrected = str(CORRECTED_COUNT)
    else:
        corrected = ""

    if corrected and deleted:
        return "Исправление ошибочных ({}), удаление старых запросов ({}).".format(corrected, deleted)
    elif corrected:
        return "Исправление ошибочных запросов ({}).".format(corrected)
    elif deleted:
        return "Удаление старых запросов ({}).".format(deleted)
    else:
        return ""

def main():
    """Main script function."""
    site = pywikibot.Site()
    fast = pywikibot.Page(site, "Википедия:Запросы к администраторам/Быстрые")
    ftext = fast.text

    ftext = minor_fixes(ftext)
    ftext = REGEXP.sub(correct_request, ftext)
    ftext = REGEXP.sub(delete_old_request, ftext)

    if MOVED_TEXT != "":
        rfaa = pywikibot.Page(site, "Википедия:Запросы к администраторам")
        rtext = rfaa.text
        insert = rtext.find("==")
        if insert == -1:
            insert = len(rtext)
        rtext = rtext[:insert] + MOVED_TEXT + rtext[insert:]
        rfaa.text = rtext
        open("rfaa.txt", "w", encoding="utf-8").write(rtext)
        # rfaa.save("Перенос залежавшихся быстрых запросов.", minor=False)

    comment = form_comment()
    if comment:
        fast.text = ftext
        open("fast.txt", "w", encoding="utf-8").write(ftext)
        # fast.save(comment)

if __name__ == "__main__":
    main()
