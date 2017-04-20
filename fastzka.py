"""
Maintainer script for ruwiki's admin request table ([[:ru:ВП:ЗКАБ]]).

Usage:
    python fastzka.py
"""

import re
from datetime import datetime
import pywikibot

REGEXP = re.compile(r"""
    (?P<indent>\n*)
    ==\s*(?P<header>.*?)\s*==\s+
    (?P<section>
        <onlyinclude>\s*
        (?:[^<]|<(?!/?onlyinclude))*?\s*
        </onlyinclude>
    )
""", re.I | re.VERBOSE)
UTCNOW = datetime.utcnow()

CORRECTED_COUNT = 0
DELETED_DONE_COUNT = 0
DELETED_UNDONE_COUNT = 0

def correct_request(match):
    """
    Fix some errors, for example, update header if it doesn't match the content.
    """
    indent = match.group("indent")
    header = match.group("header")
    template = match.group("section")

    question = re.search(r"\|\s*вопрос\s*=(.*)", template)
    timestamp = re.search(r"\|\s*автор\s*=[^/]+/\s*(\d{14})", template)
    if question is None or timestamp is None:
        # request is completely broken
        return match.group(0)

    correct_header = question.group(1).strip() + "/" + timestamp.group(1)
    if header == correct_header:
        # all is ok
        return match.group(0)

    global CORRECTED_COUNT
    CORRECTED_COUNT += 1
    return "{}== {} ==\n{}".format(indent, correct_header, template)

def delete_old_request(match):
    """Process one table row and delete it if it's neccessary."""
    template = match.group("section")
    status_match = re.search(r"\|\s*статус\s*=\s*([+-])", template)
    date_match = re.search(r"\|\s*администратор\s*=[^/]+/\s*(\d{14})", template)
    if date_match is None:
        # request is still open
        return match.group(0)
    if status_match is None:
        done = True
    else:
        done = status_match.group(1) == "+"

    delay = (1 if done else 3) * 24 * 60 * 60
    date = datetime.strptime(date_match.group(1), "%Y%m%d%H%M%S")
    if (UTCNOW - date).total_seconds() < delay:
        return match.group(0)
    else:
        if done:
            global DELETED_DONE_COUNT
            DELETED_DONE_COUNT += 1
        else:
            global DELETED_UNDONE_COUNT
            DELETED_UNDONE_COUNT += 1
        return ""

def form_comment():
    """Analyze global variables and form a comment for an edit."""
    plural = lambda num, word: word + ("ый" if num % 10 == 1 and num % 100 != 11 else "ых")
    plural_phrase = lambda num, word: str(num) + " " + plural(word, num)

    deleted_parts = []
    if DELETED_DONE_COUNT > 0:
        deleted_parts.append(plural_phrase("выполненн", DELETED_DONE_COUNT))
    if DELETED_UNDONE_COUNT > 0:
        deleted_parts.append(plural_phrase("невыполненн", DELETED_UNDONE_COUNT))
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
    """Update list."""
    site = pywikibot.Site()
    page = pywikibot.Page(site, "Википедия:Запросы к администраторам/Быстрые")
    text = page.text

    text = REGEXP.sub(correct_request, text)
    text = REGEXP.sub(delete_old_request, text)

    comment = form_comment()
    if comment:
        page.text = text
        page.save(comment)

if __name__ == "__main__":
    main()
