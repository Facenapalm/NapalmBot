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
        (?:[^<]|<(?!/?onlyinclude))*?\s*
        </onlyinclude>
    )
""", re.I | re.VERBOSE)

TIME_FORMAT = "%Y%m%d%H%M%S"
UTCNOW = datetime.utcnow()
UTCNOWSTR = UTCNOW.strftime(TIME_FORMAT)

CORRECTED_COUNT = 0
DELETED_DONE_COUNT = 0
DELETED_UNDONE_COUNT = 0

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
    template = match.group("section")

    # missing timestamp fix
    (template, flag) = re.subn(
        r"(\|\s*администратор\s*=[^/\n]*[^/\s][^/\n]*)\n",
        "\\1/" + UTCNOWSTR + "\n",
        template)
    if flag > 0:
        corrected = True

    # wrong header fix
    question = re.search(r"\|\s*вопрос\s*=(.*)", template)
    timestamp = re.search(r"\|\s*автор\s*=[^/]+/\s*(\d{14})", template)
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
        return "{}== {} ==\n{}".format(indent, header, template)
    else:
        return match.group(0)

def delete_old_request(match):
    """Process one table row and delete it if it's neccessary."""
    template = match.group("section")
    status_match = re.search(r"\|\s*статус\s*=\s*([+-])", template)
    admin_match = re.search(r"\|\s*администратор\s*=([^/\n]+)/\s*(\d{14})", template)
    if admin_match is None:
        # request is still open
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
    page = pywikibot.Page(site, "Википедия:Запросы к администраторам/Быстрые")
    text = page.text

    text = minor_fixes(text)
    text = REGEXP.sub(correct_request, text)
    text = REGEXP.sub(delete_old_request, text)

    comment = form_comment()
    if comment:
        page.text = text
        page.save(comment)

if __name__ == "__main__":
    main()
