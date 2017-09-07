"""Dump scanner for ToolForge. In work."""
import os
import os.path
import re
import pywikibot
import mwparserfromhell
from pywikibot import xmlreader
from checkwiki import ignore, deignore

DIRECTORY = "/public/dumps/public/ruwiki/"
FILENAME = "/public/dumps/public/ruwiki/{date}/ruwiki-{date}-pages-meta-current.xml.bz2"
CATEGORY = "Категория:Википедия:Запросы на автоматическое сканирование дампа"

def add_match_to_dict(dictionary, match, prefix=""):
    """Add all group-value pairs from match to dict with given key prefix."""
    dictionary[prefix + "0"] = match.group(0)
    for idx, val in enumerate(match.groups()):
        dictionary[prefix + str(idx + 1)] = val
    for key, val in match.groupdict().items():
        dictionary[prefix + str(key)] = val
    return dictionary

class Processor(object):
    """Class for processing one request."""
    limit = 1000000

    def __init__(self, page, date):
        """Initialize class from a page with request template."""
        if not (page.namespace().id in [2, 104] and "/" in page.title()):
            self.correct = False
            return

        code = mwparserfromhell.parse(page.text)
        templates = code.filter_templates(matches=r"^\{\{\s*scan dump")
        if len(templates) != 1:
            self.correct = False
            return
        template = templates[0]

        self.page = page
        self.date = date
        self.data = []
        self.stopped_at = 0
        self.processed = 0

        self.title = None
        self.namespaces = None
        self.ignore = None
        self.contains = None
        self.not_contains = None
        self.flags = 0

        self.prefix = ""
        self.result = "* [[{title}]]\n"
        self.postfix = ""
        self.sortkey = None
        self.sortreverse = False

        process_param = lambda x: re.sub(r"^<nowiki>(.*)</nowiki>$", "\\1", x.strip(), flags=re.I | re.DOTALL)
        for param in template.params:
            name = param.name.strip()
            value = process_param(param.value)
            if value == "":
                continue
            if name == "title":
                self.title = value
            elif name == "namespaces":
                self.namespaces = [x.strip() for x in value.split(",")]
            elif name == "ignore":
                self.ignore = value
            elif name == "contains":
                self.contains = value
            elif name in ["not_contains", "not contains"]:
                self.not_contains = value
            elif name == "ignorecase":
                self.flags = self.flags | re.IGNORECASE
            elif name == "multiline":
                self.flags = self.flags | re.MULTILINE
            elif name == "dotall":
                self.flags = self.flags | re.DOTALL
            elif name == "verbose":
                self.flags = self.flags | re.VERBOSE
            elif name == "prefix":
                self.prefix = value + "\n"
            elif name == "result":
                self.result = value
            elif name == "postfix":
                self.postfix = "\n" + value
            elif name == "sortkey":
                self.sortkey = value
            elif name == "sortreverse":
                self.sortreverse = True
            elif name == "done":
                self.correct = False
                return

        if self.contains is None:
            self.correct = False
            return

        self.length = len(self.prefix) + len(self.postfix)
        if self.length > self.limit:
            self.correct = False
            return

        self.correct = True

    def process(self, entry):
        """Process single entry."""
        self.processed += 1
        if not self.correct or self.stopped_at != 0:
            return False

        groups = {
            "title": entry.title,
            "namespace": entry.ns,
            "id": entry.id,
            "text": entry.text
        }

        if self.namespaces is not None:
            if entry.ns not in self.namespaces:
                return False

        if self.title is not None:
            match = re.match(self.title, entry.title)
            if match:
                add_match_to_dict(groups, match, "t_") 
            else:
                return False

        if self.ignore is not None:
            (entry.text, ignored) = ignore(entry.text, self.ignore)

        match = re.search(self.contains, entry.text, flags=self.flags)
        if match:
            add_match_to_dict(groups, match, "c_")
        else:
            return False

        if self.not_contains is not None:
            if re.search(self.not_contains, entry.text, flags=self.flags):
                return False

        result = self.result.format(**groups)
        if self.sortkey is None:
            sortkey = int(entry.id)
        else:
            sortkey = self.sortkey.format(**groups)

        if self.ignore is not None:
            result = deignore(result, ignored)
            if self.sortkey is not None:
                sortkey = deignore(sortkey, ignored)
        self.length += len(result) + 1

        if self.length > self.limit:
            self.stopped_at = self.processed
            return False

        self.data.append((sortkey, result))
        return True

    def save_result(self):
        """Save the result to the page."""
        self.data = sorted(self.data, reverse=self.sortreverse)
        result = self.prefix + "\n".join([pair[1] for pair in self.data]) + self.postfix
        params = "\\1|done=True|date={}|pages={}".format(self.date, self.processed)
        if self.stopped_at != 0:
            params += "|processed={}".format(self.stopped_at)

        text = self.page.text
        text = re.sub(r"(\{\{\s*[Ss]can dump)", params, text)
        text = text + "\n\n" + result

        self.page.text = text
        self.page.save("Результат сканирования дампа.")

def get_dump_date():
    """Iterate through labs dumps and find the newest one."""
    dates = sorted(next(os.walk(DIRECTORY))[1], reverse=True)
    for date in dates:
        if os.path.isfile(FILENAME.format(date=date)):
            return date
    return None

def main():
    """Main script function."""
    processors = []
    date = get_dump_date()
    dump = xmlreader.XmlDump(FILENAME.format(date=date))
    site = pywikibot.Site()
    category = pywikibot.Category(site, CATEGORY)
    for page in category.members():
        processor = Processor(page, date)
        if processor.correct:
            processors.append(processor)
            if len(processors) > 100:
                break
    if len(processors) == 0:
        return
    for entry in dump.parse():
        for processor in processors:
            processor.process(entry)
    for processor in processors:
        processor.save_result()

if __name__ == "__main__":
    main()

