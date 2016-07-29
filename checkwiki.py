"""
Pywikipedia bot, which automatically fixes various errors from WikiProject
CheckWiki. Full list of errors see in ENABLED_ERRORS constant.
Written in python 3.5, compatibility with older versions doesn't tested.
Adapted for ruwiki. Do not use this bot on other wikis!

Using as script:
    python checkwiki.py [keys_or_params ...]
Keys changes bot condition, so next parameters will be processed with another
rules.
There are 6 available keys:
    --maj: send fixed page only if it have at least one major fix [default]
    --min: send fixed page if it have at least one fix (maybe minor)
    --p: next parameters are titles of the Wikipedia pages [default]
    --f: next parameters are names of the files, which contains page titles
    --s: next parameters are numbers of the errors which is neccessary to fix
    --t: also process test page (see TEST_PAGE constant)
For example:
    python checkwiki.py Example1 Example2 --f pages.txt
Process "Example1" and "Example2" pages and all pages from "pages.txt" file.

Using as module...
... on high level:
    import checkwiki
    # here you can modify ENABLED_ERRORS and MAJOR_ERRORS lists
    checkwiki.process_page("Example")
See process_page() function help for more information.

... on low level:
    import pywikibot
    import checkwiki

    site = pywikibot.Site()
    page = pywikibot.Page(site, "Example")

    text = page.text

    (text, fixed_errors) = checkwiki.process_text(text, page.title())

    # here you can do additional fixes in text

    if checkwiki.has_major(fixed_errors):
        page.text = text
        page.save(checkwiki.get_comment(fixed_errors))
        checkwiki.mark_error_list_done(fixed_errors, page.title())
See the corresponding functions help for more information.
"""

import re
import sys
from urllib.parse import unquote, urlencode
from urllib.request import urlopen

import pywikibot

HELP_STRING = __doc__[:__doc__.index("\n\nUsing as module")]

# customization

CHECKWIKI_URL = "http://tools.wmflabs.org/checkwiki/cgi-bin/checkwiki.cgi?"

PROJECT = "ruwiki"
LANG_CODE = "ru"
TEST_PAGE = "Википедия:Песочница"

IMAGE = r"(?:файл|file|изображение|image)\s*:"
CATEGORY = r"(?:категория|к|category)\s*:"
# "c:" also means "category:", but [[c:smth]] is a link to commons
TEMPLATE = r"(?:шаблон|ш|template|t)\s*:"
MODULE = r"(?:module|модуль)\s*:"

INTERWIKI = r"(?:[a-z]{2,3}|nds_nl|simple|be-tarask)"

IGNORE_FILTER = re.compile(r"""(
    <!--.*?-->|

    <nowiki>.*?</nowiki>|
    <nowiki\s*/>|

    <math>.*?</math>|
    <hiero>.*?</hiero>|

    <source>.*?</source>|
    <tt>.*?</tt>|
    <code>.*?</code>|
    <pre>.*?</pre>|
    <syntaxhighlight[^>]*>.*?</syntaxhighlight>|

    <templatedata>.*?</templatedata>|
    <imagemap>.*?</imagemap>
)""", re.I | re.DOTALL | re.VERBOSE)

# also see ENABLED_ERRORS and MAJOR_ERRORS lists in #main section

FIX_UNSAFE_EXTLINKS = False

# stdlib addiction

def allsubn(pattern, repl, string, count=0, flags=0):
    """Works just as re.subn, but works until there is no matches left."""
    total_count = 0
    cur_count = 1
    while cur_count:
        if count > 0:
            if total_count >= count:
                return (string, total_count)
            count_left = count - total_count
        else:
            count_left = 0
        (string, cur_count) = re.subn(pattern, repl, string, count=count_left, flags=flags)
        total_count += cur_count
    return (string, total_count)

def allsub(pattern, repl, string, count=0, flags=0):
    """Works just as re.sub, but works until there is no matches left."""
    return allsubn(pattern, repl, string, count=count, flags=flags)[0]

def unique(lst):
    """Returns the list without element dublication; element's order might be broken."""
    return list(set(lst))

def count_ignore_case(string, substring):
    """count_ignore_case(s1, s2) works just as s1.count(s2), but ignores case."""
    return string.lower().count(substring.lower())

# common

def process_link_whitespace(link):
    """Replaces "_" symbols with spaces, deletes leading spaces."""
    return re.sub(r"_", " ", link).strip()

def unificate_link(link):
    """Processes whitespaces, makes first letter upper."""
    link = process_link_whitespace(link)
    if len(link) < 2:
        return link.upper()
    else:
        return link[0].upper() + link[1:]

def compare_links(link1, link2):
    """Returns True, if two strings refers to the same Wikipedia article."""
    if link1 is None or link2 is None:
        return link1 == link2
    else:
        return unificate_link(link1) == unificate_link(link2)

DATE_REGEXP = r"(?:0?[1-9]|[12]\d|3[01])\.(?:0?[1-9]|1[0-2])\.\d{4}"

def decode_link(link):
    """Decodes encoded links, such as "%D0%A1#.D0.B2"."""
    new_link = process_link_whitespace(link)

    (new_link, ignored) = ignore(new_link, DATE_REGEXP)
    new_link = allsub(r"(#.*?)\.([0-9A-F]{2})", "\\1%\\2", new_link)
    new_link = deignore(new_link, ignored)

    new_link = unquote(new_link)

    if "\ufffd" in new_link:
        # failed to decode link
        return (link, False)
    else:
        return (new_link, True)

def process_external_link(match_obj):
    """
    Converts external link to a wiki-link.

    match_obj is an instance of MatchObject with at least 3 groups:
        group(1) - lang code, for example, "ru" or "en"
        group(2) - encoded link, for example, "%D0%A1%D0%B2%D0%B5%D1%82"
        group(3) - link text, for example, "Light"

    Returns string.
    """
    code = match_obj.group(1)
    (link, success) = decode_link(match_obj.group(2))
    if not success:
        return match_obj.group(0)
    if match_obj.lastindex < 3:
        name = None
    else:
        name = match_obj.group(3)

    if code is None or code == LANG_CODE:
        code = ""
    else:
        code = ":" + code + ":"

    is_category = not re.match(r"^" + CATEGORY, link, flags=re.I) is None
    is_image = not re.match(r"^" + IMAGE, link, flags=re.I) is None
    if (is_category or is_image) and code == "":
        code = ":"

    if compare_links(link, name):
        name = None

    if not name is None:
        return "[[" + code + link + "|" + name + "]]"
    elif code == "":
        return "[[" + link + "]]"
    else:
        return "[[" + code + link + "|" + link + "]]"

def process_link_as_external(text, lang_code=LANG_CODE):
    """
    Replaces all links to wikipedia on language, matching lang_code regexp, with a wikilinks.
    Used in 90th and 91st errors.
    """
    lang_code = "(" + lang_code + ")"
    prefix = r"\[https?://" + lang_code + r"\.(?:m\.)?wikipedia\.org/(?:w|wiki)/"
    suffix = r"\]"

    count_before = len(re.findall(prefix, text))

    exp1 = prefix + r"([^\[\]\|?=]+)\|([^\[\]\|]+)" + suffix # [wp/Example Article|text]
    text = re.sub(exp1, process_external_link, text, flags=re.I)
    exp2 = prefix + r"([^\[\]\| ?=]+) ([^\[\]\|]+)" + suffix # [wp/Example_Article text]
    text = re.sub(exp2, process_external_link, text, flags=re.I)

    if FIX_UNSAFE_EXTLINKS:
        exp3 = prefix + r"([^\[\]\|?=]+)" + suffix # [wp/Example_Article]
        text = re.sub(exp3, process_external_link, text, flags=re.I)

    count_after = len(re.findall(prefix, text))

    return (text, count_before - count_after)

def check_tag_balance(text, tag, recursive=False):
    """
    Checks if all tags have a pair. Returns True if yes, otherwise False.
    tag parameter must contains only name of the tag, for example, "b" for <b>.
    recursive flag must be True if nested tags are correct. The default value is False.
    """
    tags = re.findall(r"<(/?)\s*" + tag + r"\b", text, flags=re.I)
    tags = [cur_tag == "" for cur_tag in tags] # True for opening, False for closing

    balance = 0
    for cur_tag in tags:
        if cur_tag:
            balance += 1
        else:
            balance -= 1
        if balance < 0:
            return False
        if not recursive and balance > 1:
            return False
    if balance != 0:
        return False

    return True

def fix_unpair_tag(text, tag):
    """
    Fixes self-closing unpair tags and returns (new_text, replacements_count) tuple.
    tag parameter must contains only name of the tag, for example, "br" for <br>.
    Used in 2nd error.
    """
    correct_tag = "<" + tag + ">"
    all_tags = r"<[/\\]?[ ]*" + tag + r"[ ]*[/\\]?>"

    correct = count_ignore_case(text, correct_tag)
    (text, fixed) = re.subn(all_tags, correct_tag, text, flags=re.I)
    return (text, fixed - correct)

def fix_pair_tag(text, tag, recursive=False):
    """
    Fixes self-closing pair tags and returns (new_text, replacements_count) tuple.
    tag parameter must contains only name of the tag, for example, "b" for <b>.
    recursive flag must be True if nested tags are correct. The default value is False.
    Checks tag balance: if something going wrong, function willn't change anything.
    Used in 2nd error.
    """
    old_text = text
    correct_tag = "</" + tag + ">"

    (text, fixed1) = re.subn(r"<[ ]*" + tag + r"[ ]*[/\\]>", correct_tag, text, flags=re.I)
    (text, fixed2) = re.subn(r"<\\[ ]*" + tag + r"[ ]*>", correct_tag, text, flags=re.I)

    if check_tag_balance(text, tag, recursive):
        return (text, fixed1 + fixed2)
    else:
        return (old_text, 0)

LABEL_PREFIX = "\x01"
LABEL_SUFFIX = "\x02"

def ignore(text, ignore_filter):
    """
    Replaces all text matches regexp with special label.

    Parameters:
        text - text to be processed;
        ignore_filter - compiled regular expression or string with regexp.

    Returns (new_text, deleted_text_list) tuple.
    """
    if isinstance(ignore_filter, str):
        ignore_filter = re.compile(ignore_filter, flags=re.I | re.DOTALL)

    ignored = []
    count = 0

    def _ignore_line(match_obj):
        """Replaces founded text with special label."""
        #pylint: disable=undefined-variable
        nonlocal ignored
        ignored.append(match_obj.group(0))

        nonlocal count
        old_count = count
        count += 1
        return LABEL_PREFIX + str(old_count) + LABEL_SUFFIX

    text = re.sub(LABEL_PREFIX + r"(\d+)" + LABEL_SUFFIX, _ignore_line, text)
    text = ignore_filter.sub(_ignore_line, text)
    return (text, ignored)

def deignore(text, ignored):
    """
    Restores the text returned by the ignore() function.

    Parameters:
        text - text to be processed;
        ignored - deleted_text_list, returned by the ignore() function.

    Returns string.
    """
    def _deignore_line(match_obj):
        """Replaces founded label with corresponding text."""
        index = int(match_obj.group(1))
        return ignored[index]

    return re.sub(LABEL_PREFIX + r"(\d+)" + LABEL_SUFFIX, _deignore_line, text)

# errors

def error_001_template_with_keyword(text):
    """Fixes the error and returns (new_text, replacements_count) tuple."""
    return re.subn(r"\{\{" + TEMPLATE + r"\s*", "{{", text, flags=re.I)

def error_002_invalid_tags(text):
    """Fixes the error and returns (new_text, replacements_count) tuple."""
    (text, fixed_br) = fix_unpair_tag(text, "br")
    (text, fixed_hr) = fix_unpair_tag(text, "hr")
    fixed_total = fixed_br + fixed_hr

    (text, fixed_small) = fix_pair_tag(text, "small")
    (text, fixed_center) = fix_pair_tag(text, "center")
    (text, fixed_div) = fix_pair_tag(text, "div", recursive=True)
    (text, fixed_span) = fix_pair_tag(text, "span", recursive=True)
    fixed_total += fixed_small + fixed_center + fixed_div + fixed_span

    return (text, fixed_total)

def error_009_category_without_br(text):
    """Fixes the error and returns (new_text, replacements_count) tuple."""
    (text, no_after) = re.subn(r"(\[\[категория:.*?\]\][ ]*)([^ \n])", "\\1\n\\2", text, flags=re.I)
    (text, no_before) = re.subn(r"([^\n])(\[\[категория:.*?\]\])", "\\1\n\\2", text, flags=re.I)
    return (text, no_after + no_before)

def error_016_control_characters(text):
    """
    Fixes some cases and returns (new_text, replacements_count) tuple.
    One of the regexps is copied from wikificator.
    """
    (text, count1) = allsubn(r"(\[\[[^|\[\]]*)[\u00AD\u200E\u200F]+([^\[\]]*\]\])", "\\1\\2", text)
    (text, count2) = re.subn(r"[\u200E\uFEFF\u200B\u2028\u202A\u202C\u202D\u202E]", "", text)
    (text, count3) = re.subn(r"[\u2004\u2005\u2006\u2007\u2008]", " ", text)
    return (text, count1 + count2 + count3)

def error_017_category_dublicate(text):
    """
    Fixes the error and returns (new_text, replacements_count) tuple.
    Always chooses the category with the longest sort key.
    """
    regexp = r"\[\[категория:([^\|\[\]\n]+)(?:\|([^\|\[\]\n]*))?\]\]\n?"
    category_finder = re.compile(regexp, flags=re.I)
    category_list = category_finder.findall(text)

    def need_to_delete(match_obj, category_list, cur_cat):
        """Returns true if it's neccessary to delete founded category."""
        name = match_obj.group(1)
        key = match_obj.group(2)
        if key is None:
            key = ""

        cur_len = len(key)
        for i, category in enumerate(category_list):
            if compare_links(name, category[0]):
                candidate_len = len(category[1])
                if candidate_len > cur_len or candidate_len == cur_len and i < cur_cat:
                    return True
        return False

    count = 0
    cur_cat = 0
    cur_pos = 0
    while True:
        cur_match = category_finder.search(text[cur_pos:])
        if cur_match is None:
            break

        start = cur_match.start(0)
        end = cur_match.end(0)
        if need_to_delete(cur_match, category_list, cur_cat):
            text = text[:cur_pos + start] + text[cur_pos + end:]
            count += 1
            cur_pos += start
        else:
            cur_pos += end
        cur_cat += 1
    return (text, count)

def error_021_category_in_english(text):
    """Fixes the error and returns (new_text, replacements_count) tuple."""
    return re.subn(r"\[\[category\s*:", "[[Категория:", text, flags=re.I)

def error_022_category_with_spaces(text):
    """Fixes the error and returns (new_text, replacements_count) tuple."""
    correct = count_ignore_case(text, "[[Категория:")
    (text, fixed) = re.subn(r"\[\[\s*Категория\s*:\s*", "[[Категория:", text, flags=re.I)
    count1 = fixed - correct

    (text, count2) = re.subn(r"(\[\[Категория:[^\[\]|]+?)\s+([\]|])", "\\1\\2", text, flags=re.I)
    return (text, count1 + count2)

def error_026_bold_tag(text):
    """Fixes the error and returns (new_text, replacements_count) tuple."""
    if check_tag_balance(text, "b") and check_tag_balance(text, "strong"):
        return re.subn(r"</?(?:b|strong)>", "'''", text, flags=re.I)
    else:
        return (text, 0)

def error_032_link_two_pipes(text):
    """Fixes some cases and returns (new_text, replacements_count) tuple."""
    (text, count1) = re.subn(r"\[\[([^\|\[\]\n]+)\|\|([^\|\[\]\n]+)\]\]", "[[\\1|\\2]]", text)
    (text, count2) = re.subn(r"\[\[([^\|\[\]\n]+)\|([^\|\[\]\n]+)\|\]\]", "[[\\1|\\2]]", text)
    return (text, count1 + count2)

def error_034_template_elements(text):
    """Fixes pagename magicwords and returns (new_text, replacements_count) tuple."""
    return re.subn(r"{{(NAMESPACE|SITENAME|PAGENAME|FULLPAGENAME)}}", "{{subst:\\1}}", text)

def error_038_italic_tag(text):
    """Fixes the error and returns (new_text, replacements_count) tuple."""
    if check_tag_balance(text, "i") and check_tag_balance(text, "em"):
        return re.subn(r"</?(?:i|em)>", "''", text, flags=re.I)
    else:
        return (text, 0)

def error_042_strike_tag(text):
    """Fixes the error and returns (new_text, replacements_count) tuple."""
    return re.subn(r"(</?)strike>", "\\1s>", text, flags=re.I)

def error_044_headline_with_bold(text):
    """Fixes the error and returns (new_text, replacements_count) tuple."""
    return allsubn(r"^(=+) (.*?)'''(.*?)'''(.*?) \1$", "\\1 \\2\\3\\4 \\1", text, flags=re.M)

def error_048_title_link_in_text(text):
    """
    Fixes the error and returns (new_text, replacements_count) tuple.
    Uses static variable title. Make sure you have set it before function call:
        error_048_title_link_in_text.title = "Example"
    Replaces title links with its text without bold tag.
    """
    if error_048_title_link_in_text.title is None:
        return (text, 0)

    count = 0

    def _process_link(match_obj):
        """Deals with founded wiki-link."""
        link = match_obj.group(1)
        name = match_obj.group(2)
        if name is None:
            name = link

        if compare_links(link, error_048_title_link_in_text.title):
            #pylint: disable=undefined-variable
            nonlocal count
            count += 1
            return name
        else:
            return match_obj.group(0)

    text = re.sub(r"\[\[([^\]\|\n]+)(?:\|([^\]\|\n]+))?\]\]", _process_link, text)
    return (text, count)

error_048_title_link_in_text.title = None

def error_050_mnemonic_dash(text):
    """
    Fixes the error and returns (new_text, replacements_count) tuple.
    """
    (text, count1) = re.subn("&ndash;", "–", text, flags=re.I)
    (text, count2) = re.subn("&mdash;", "—", text, flags=re.I)
    return (text, count1 + count2)

def error_052_category_in_article(text):
    """Fixes all wrong categories and returns (new_text, fixed_errors_count) tuple."""
    ignore_filter = re.compile(r"""(
        <noinclude>.*?</noinclude>|
        <onlyinclude>.*?</onlyinclude>|
        <includeonly>.*?</includeonly>
    )""", re.I | re.DOTALL | re.VERBOSE)
    (text, ignored) = ignore(text, ignore_filter)

    category_finder = r"\[\[Категория:[^\[\]\n]+\]\][ ]*\n"
    wrong_category_finder = category_finder + "(?=.*\n==)"

    # count wrong categories
    text = text + "\n"
    count = len(re.findall(wrong_category_finder, text, flags=re.DOTALL))

    # fix (all)
    category_finder = re.compile(category_finder)
    categories = category_finder.findall(text)
    text = category_finder.sub("", text)

    text = deignore(text, ignored)
    if len(categories) == 0:
        return (text, 0)

    insert_pos = re.search(r"(?:\[\[[A-Za-z\-]+:[^\[\]\n]+\]\]\s*)*$", text).start(0)
    # we must to insert categories before interwikis
    prefix = text[:insert_pos].rstrip()
    interwikis = text[insert_pos:]

    if prefix.strip() == "": # page consists of categories only. Possible for Category: namespace
        text = "".join(categories) + "\n" + interwikis
    else:
        text = prefix + "\n\n" + "".join(categories) + "\n" + interwikis
    text = text.rstrip() + "\n"

    return (text, count)

def error_054_list_with_br(text):
    """Fixes some cases and returns (new_text, replacements_count) tuple."""
    return allsubn(r"^(\*.*)<br>[ ]*$", "\\1", text, flags=re.M)

def error_057_headline_with_colon(text):
    """Fixes the error and returns (new_text, replacements_count) tuple."""
    return re.subn(r"^(=+) (.*?): \1$", "\\1 \\2 \\1", text, flags=re.M)

def error_059_template_with_br(text):
    """Fixes the error and returns (new_text, replacements_count) tuple."""
    br_finder = re.compile(r"[ ]*<br>[ ]*(?=\n?\s*(?:\||\}\}))")

    # pipes can be also used in tables and wikilinks
    # we shouldn't detect these uses (expecially tables)
    ignore_filter = re.compile(r"(\[\[.*?\]\]|\{\|.*?\|\})", re.DOTALL)
    (text, ignored) = ignore(text, ignore_filter)
    (text, count) = br_finder.subn(r"", text)
    text = deignore(text, ignored)

    return (text, count)

def error_062_url_without_http(text):
    """Fixes the error in refs and returns (new_text, replacements_count) tuple."""
    return re.subn(r"(<ref[^<>]*>)\s*(\[?)\s*www\.", "\\1\\2http://www.", text)

def error_063_small_tag_in_refs(text):
    """Fixes some cases and returns (new_text, replacements_count) tuple."""
    regexp = r"(<(ref|su[bp])[^>]*>)<small>([^<>]+)</small>(</\2>)"
    return re.subn(regexp, "\\1\\3\\4", text, flags=re.I)

def error_064_link_equal_linktext(text):
    """
    Fixes the error and returns (new_text, replacements_count) tuple.
    Also corrects links with spaces.
    """
    count = 0

    def _process_link(match_obj):
        """Deals with founded wiki-link."""
        link = match_obj.group(1)
        name = match_obj.group(2)
        if re.match(r"^Категория:", link):
            return match_obj.group(0)
        if name is None:
            return "[[" + link.strip() + "]]"

        name = name.strip()
        link = link.strip()

        quotes = ""
        parsed_name = re.match(r"^('''''|'''|'')(.*)\1$", name)
        if not parsed_name is None:
            quotes = parsed_name.group(1)
            name = parsed_name.group(2)
            name = name.strip()

        if compare_links(link, name):
            #pylint: disable=undefined-variable
            nonlocal count
            count += 1
            return quotes + "[[" + name + "]]" + quotes
        else:
            return "[[" + link + "|" + quotes + name + quotes + "]]"

    text = re.sub(r"\[\[([^\]\|\n]+)(?:\|([^\]\|\n]+))?\]\]", _process_link, text)
    return (text, count)

def error_065_image_desc_with_br(text):
    """Fixes the error and returns (new_text, replacements_count) tuple."""
    return re.subn(r"(\[\[Файл:[^\]]+)\s*<br>\s*(\]\])", "\\1\\2", text)

def error_067_ref_after_dot(text):
    """
    [WARNING: dangerous to use without manual control]
    Fixes references after dots, commas, colons and semicolons.
    Returns (new_text, replacements_count) tuple.
    """
    return allsubn(r"([.,:;])(<ref[^/>]*/>|<ref[^/>]*>.*?</ref>)", "\\2\\1", text, flags=re.DOTALL)

def error_069_isbn_wrong_syntax(text):
    """Fixes some cases and returns (new_text, replacements_count) tuple."""
    ignore_filter = re.compile(r"""(https?://[^ ]+)""", re.I)
    (text, ignored) = ignore(text, ignore_filter)

    # colon after ISBN
    (text, count1) = re.subn(r"ISBN(?:[- ]?1[03])?\s*:\s*(\d)", "ISBN \\1", text, flags=re.I)
    # "-" insted of space or lack of space
    (text, count2) = re.subn(r"ISBN-?((?:[0-9X]-?){10})", "ISBN \\1", text, flags=re.I)
    # two or more spaces
    (text, count3) = re.subn(r"ISBN[ ]{2,}(\d)", "ISBN \\1", text, flags=re.I)
    # "10-" or "13-" prefixes
    (text, count4) = re.subn(r"(?:1[03]-)ISBN (\d)", "ISBN \\1", text, flags=re.I)
    # ISBN in lower case (minor)
    text = re.sub(r"ISBN (\d)", "ISBN \\1", text, flags=re.I)

    text = deignore(text, ignored)
    return (text, count1 + count2 + count3 + count4)

def error_070_isbn_wrong_length(text):
    """Fixes using russian Х/х instead of english X."""
    return re.subn(r"((?:ISBN |\|isbn\s*=\s*)(?:[0-9]-?){9})Х", "\\1X", text, flags=re.I)

def error_080_ext_link_with_br(text):
    """Fixes the error and returns (new_text, replacements_count) tuple."""
    unclosen_regexp = r"(<ref[^<>/]*>\[https?://[^\[\]]*?)(</ref>)"
    broken_regexp = r"(\[https?://[^\[\]]*?)\n([^\[\]]*?\])"
    (text, unclosen) = re.subn(unclosen_regexp, "\\1]\\2", text, flags=re.I)
    (text, broken) = allsubn(broken_regexp, "\\1 \\2", text, flags=re.I)
    return (text, unclosen + broken)

def error_085_empty_tag(text):
    """Fixes some cases and returns (new_text, replacements_count) tuple."""
    full_count = 0
    cur_count = 1
    while cur_count:
        (text, count1) = re.subn(r"<(ref|center)>\s*</\1>", "", text)
        (text, count2) = re.subn(r"<gallery.*?>\s*</gallery>", "", text)
        (text, count3) = re.subn(r"<(noinclude|onlyinclude)></\1>", "", text)
        (text, count4) = re.subn(r"<(div|span)>(\s*)</\1>", "\\2", text)
        cur_count = count1 + count2 + count3 + count4
        full_count += cur_count

    return (text, full_count)

def error_086_ext_link_two_brackets(text):
    """Fixes some cases and returns (new_text, replacements_count) tuple."""
    # case: [[http://youtube.com/|YouTube]]
    def _process_link(match_obj):
        """Deals with founded wiki-link."""
        link = match_obj.group(1)
        name = match_obj.group(2)
        if "wikipedia.org" in link.lower():
            link = re.sub(" ", "_", link)
        else:
            link = re.sub(" ", "%20", link)
        return "[" + link + " " + name + "]"
    exp1 = r"\[\[(https?://[^\[\]\|\n]+)\|([^\[\]\|\n]+)\]\]"
    (text, count1) = re.subn(exp1, _process_link, text, flags=re.I)
    # case: [[http://youtube.com YouTube]]
    exp2 = r"\[(\[https?://[^\[\]\n]+\])\]"
    (text, count2) = re.subn(exp2, "\\1", text, flags=re.I)
    return (text, count1 + count2)

def error_088_dsort_with_spaces(text):
    """Fixes the error and returns (new_text, replacements_count) tuple."""
    correct = count_ignore_case(text, "{{DEFAULTSORT")
    (text, fixed) = re.subn(r"\{\{\s*DEFAULTSORT\s*:\s*", "{{DEFAULTSORT:", text, flags=re.I)
    return (text, fixed - correct)

def error_090_internal_link_as_ext(text):
    """Fixes the error and returns (new_text, replacements_count) tuple."""
    return process_link_as_external(text)

def error_091_interwiki_link_as_ext(text):
    """Fixes the error and returns (new_text, replacements_count) tuple."""
    return process_link_as_external(text, INTERWIKI)

def error_093_double_http(text):
    """Fixes the error and returns (new_text, replacements_count) tuple."""
    return allsubn(r"https?:/?/?(?=https?://)", "", text, flags=re.I)

def error_098_unclosen_sub(text):
    """Fixes self-closing tags and returns (new_text, replacements_count) tuple."""
    return fix_pair_tag(text, "sub")

def error_099_unclosen_sup(text):
    """Fixes self-closing tags and returns (new_text, replacements_count) tuple."""
    return fix_pair_tag(text, "sup")

def error_101_sup_in_numbers(text):
    """Fixes the error and returns (new_text, replacements_count) tuple."""
    return re.subn(r"(\d)<sup>(st|nd|rd|th)</sup>", "\\1\\2", text, flags=re.I)

def error_103_pipe_in_wikilink(text):
    """Fixes the error and returns (new_text, replacements_count) tuple."""
    return re.subn(r"(\[\[[^\]\|\n]+){{!}}([^\]\|\n]+\]\])", "\\1|\\2", text)

def error_104_quote_marks_in_refs(text):
    """Fixes the error and returns (new_text, replacements_count) tuple."""
    (text, count1) = re.subn(r"(<ref name=\"[^\">]+?)(\s*/?>)", "\\1\"\\2", text)
    (text, count2) = re.subn(r"(<ref name=)([^\">]+?\"\s*/?>)", "\\1\"\\2", text)
    return (text, count1 + count2)

def minor_fixes_before(text):
    """
    Fixes some minor defects. Automatically called before standart filters.
    Always returns (new_text, 0) tuple.
    """
    text = allsub(r"\n[ ]+\n", "\n\n", text) # spaces in the empty line

    # headers:
    text = re.sub(r"^(==.*==)[ ]+\n", "\\1\n", text, flags=re.M) # spaces after
    text = re.sub(r"^(=+)\s*(.*?)\s*(=+)$", "\\1 \\2 \\3", text, flags=re.M) # spaces inside
    text = allsub(r"([^\n])(\n==.*==)", "\\1\n\\2", text) # empty line before
    text = re.sub(r"^(==.*==\n)\n+(?!=)", "\\1", text, flags=re.M) # empty line after

    text = re.sub(r"^(\*+)([^ *#:])", "\\1 \\2", text) # spaces in lists

    extlink_regexp = re.compile(r"\[https?://[^\n\]]+\]", flags=re.I)
    (text, ignored) = ignore(text, extlink_regexp)
    link_decoder = lambda x: decode_link(x.group(0))[0]
    text = re.sub(r"\[\[[^\[\]\|]+\|", link_decoder, text) # encoded links
    text = deignore(text, ignored)

    return (text, 0)

def minor_fixes_after(text):
    """
    Fixes some minor defects. Automatically called after standart filters.
    Always returns (new_text, 0) tuple.
    """
    text = re.sub(r"(\[\[:?)" + CATEGORY + r"(\s*)", "\\1Категория:", text, flags=re.I)
    text = re.sub(r"(\[\[:?)" + MODULE + r"(\s*)", "\\1Модуль:", text, flags=re.I)
    text = re.sub(r"(\[\[:?)" + TEMPLATE + r"(\s*)", "\\1Шаблон:", text, flags=re.I)
    text = re.sub(r"(\[\[:?)" + IMAGE + r"(\s*)", "\\1Файл:", text, flags=re.I)

    text = allsub(r"(\[\[[^\[\]\|\n]+)_", "\\1 ", text) # "_" symbols inside links

    text = re.sub(r"\{\{reflist(?!\+)", "{{примечания", text, flags=re.I)
    text = re.sub(r"\{\{список примечаний", "{{примечания", text, flags=re.I)

    text = re.sub(r" +(\{\{ref-[a-z]+\}\})", "\\1", text)

    text = re.sub(r"\{\{(?:удар|ударение|stress|')\}\}", "{{подст:удар}}", text, flags=re.I)

    return (text, 0)

# main

ENABLED_ERRORS = [
    minor_fixes_before,
    error_016_control_characters,

    # html tags
    error_002_invalid_tags,
    error_026_bold_tag,
    error_038_italic_tag,
    error_042_strike_tag,
    error_085_empty_tag,
    error_098_unclosen_sub,
    error_099_unclosen_sup,

    # templates, must be after 002
    error_001_template_with_keyword,
    error_034_template_elements,
    error_059_template_with_br,

    # headlines, must me after 026
    error_044_headline_with_bold,
    error_057_headline_with_colon,

    # external links
    error_062_url_without_http,
    error_093_double_http,
    error_080_ext_link_with_br,
    error_086_ext_link_two_brackets,
    error_090_internal_link_as_ext,
    error_091_interwiki_link_as_ext,

    # categories, must be after 086
    error_021_category_in_english,
    error_022_category_with_spaces,
    error_009_category_without_br,
    error_017_category_dublicate,
    error_052_category_in_article,

    # links, must be after external links and 034
    error_103_pipe_in_wikilink,
    error_032_link_two_pipes,
    error_048_title_link_in_text,
    error_064_link_equal_linktext,

    # isbn
    error_069_isbn_wrong_syntax,
    error_070_isbn_wrong_length,

    # other, must be after 002
    error_054_list_with_br,
    error_065_image_desc_with_br,

    error_050_mnemonic_dash,
    error_063_small_tag_in_refs,
    error_088_dsort_with_spaces,
    error_101_sup_in_numbers,
    error_104_quote_marks_in_refs,

    minor_fixes_after
]

MAJOR_ERRORS = {
    "32": "ссылок",
    "42": "устаревших тегов",
    # "44": "заголовков",
    # "48": "ссылок",
    # "57": "заголовков",
    "62": "ссылок",
    "69": "ISBN",
    "70": "ISBN",
    "80": "ссылок",
    "86": "ссылок",
    "90": "ссылок",
    # "91": "ссылок",
    "93": "ссылок",
    "98": "самозакрывающихся тегов",
    "99": "самозакрывающихся тегов",
    "104": "сносок"
}

def get_error_num(function):
    """
    Extracts first number from function name and returns string with it.
    Lead zeroes will be truncated.
    """
    match_obj = re.search(r"\d+", function.__name__)
    if match_obj is None:
        return "0"

    result = match_obj.group(0).lstrip("0")
    if result == "":
        result = "0"
    return result

def mark_error_done(error_num, page_name):
    """Marks error as done in CheckWiki web interface."""
    error_num = str(error_num)
    if error_num == "0":
        return

    params = {"project": PROJECT, "view": "detail", "id": error_num, "title": page_name}
    urlopen(CHECKWIKI_URL + urlencode(params)).read()

def mark_error_list_done(error_list, page_name):
    """Marks all errors from list as done in CheckWiki web interface."""
    for error_num in error_list:
        mark_error_done(error_num, page_name)

def load_page_list(error_num, offset=0):
    """Downloads list of pages with error_num error from CheckWiki server."""
    params = {"project": PROJECT, "view": "bots", "id": str(error_num), "offset": str(offset)}
    data = urlopen(CHECKWIKI_URL + urlencode(params)).read().decode()
    if not "Check Wikipedia" in data:
        return []
    data = re.search(r"<pre>(.*)</pre>", data, flags=re.DOTALL)
    if data is None:
        return []
    return data.group(1).strip().split("\n")

def process_text(text, title=None):
    """
    Fixes all errors from ENABLED_ERRORS and returns (new_text, fixed_errors_list) tuple.
    Ignores text inside comments and tags:
    <nowiki>, <source>, <tt>, <code>, <pre>, <syntaxhighlight>, <templatedata>
    (see IGNORE_FILTER regexp)
    """
    error_048_title_link_in_text.title = title

    (text, ignored) = ignore(text, IGNORE_FILTER)

    fixed_errors = []
    for error in ENABLED_ERRORS:
        (text, count) = error(text)
        if count > 0:
            fixed_errors.append(get_error_num(error))

    text = deignore(text, ignored)
    return (text, fixed_errors)

def has_major(fixes_list):
    """Returns True if list, passed as parameter, has at least one major error fix."""
    return any(fix in MAJOR_ERRORS for fix in fixes_list)

def has_minor(fixes_list):
    """Returns True if list, passed as parameter, has at least one major error fix."""
    return any(not fix in MAJOR_ERRORS for fix in fixes_list)

def get_comment(fixes_list, extra_comment_parts=None):
    """
    Forms Wikipedia's edit comment from list of fixed errors (in russian language).

    Parameters:
        fixes_list - list of fixed errors, for example, returned by process_text function.
        extra_comment_parts - list of strings, which will be written in comma separated list.
    """
    if extra_comment_parts is None:
        comment_parts = []
    else:
        comment_parts = extra_comment_parts

    for fix in fixes_list:
        if fix in MAJOR_ERRORS:
            comment_parts.append(MAJOR_ERRORS[fix])
    comment_parts = unique(comment_parts)

    if comment_parts == []:
        comment_prefix = "[[ПРО:CW|CheckWiki]]"
        if has_minor(fixes_list):
            return comment_prefix + ": малые правки."
        else:
            return comment_prefix + "."
    else:
        comment_prefix = "[[ПРО:CW|CheckWiki]]: исправление "
        if has_minor(fixes_list):
            return comment_prefix + ", ".join(comment_parts) + "; малые правки."
        else:
            return comment_prefix + ", ".join(comment_parts) + "."

def process_page(page, force_minor=False):
    """
    Fixes errors in page and sends changes to the server.
    Function also marks corresponding errors in CheckWiki web interface.

    Parameters:
        page is an instance of pywikibot.Page.
        force_minor is boolean.
    If force_minor is True, the changes will be sent to the server even if there's no major fixes.

    Function returns (success, fixed_errors_list) tuple. Success is True if the page was saved.

    Note: if you added some additional functions to ENABLED_ERRORS list, make sure that all names of
    them contains error number; otherwise it will not marked as "Done" in CheckWiki project.
    """
    error_value = (False, [])
    if not page.exists():
        return error_value
    if not page.botMayEdit():
        return error_value

    text = page.text

    (text, fixed_errors) = process_text(text, page.title())
    if fixed_errors == []:
        return error_value

    need_to_fix = force_minor or has_major(fixed_errors)
    if not need_to_fix:
        return (False, fixed_errors)

    try:
        page.text = text
        page.save(get_comment(fixed_errors))
        mark_error_list_done(fixed_errors, page.title())
    except pywikibot.exceptions.Error:
        return error_value

    return (True, fixed_errors)

def log(title, errlist=None, success=True):
    """Prints log line to console, for example, "Portal Stories: Mel - [1, 2, 10] ... ok"."""
    title = title.strip()

    if errlist is None or errlist == []:
        list_string = ""
    else:
        list_string = " - [" + ", ".join(errlist) + "]"

    if success:
        state = "ok"
    else:
        state = "fail"

    pywikibot.output(title + list_string + " ... " + state, toStdout=True)

def process_list(site, titles, force_minor=False, log_needed=True):
    """
    Fixes errors in every page of the list and sends changes to the server.
    Function also marks corresponding errors in CheckWiki web interface.

    Parameters:
        site is an instance of pywikibot.Site.
        page is an instance of pywikibot.Page.
        force_minor is boolean.
        log_needed is boolean.
    If force_minor is True, the changes will be sent to the server even if there's no major fixes.
    If log_needed is True, function will be shown fixed errors list for every page.

    Returns fixed pages count.

    Note: if you added some additional functions to ENABLED_ERRORS list, make sure that all names of
    them contains error number; otherwise it will not marked as "Done" in CheckWiki project.
    """
    count = 0
    for title in titles:
        (success, errlist) = process_page(pywikibot.Page(site, title), force_minor)
        if success:
            count += 1
        if log_needed:
            log(title, errlist, success)
    return count

def main():
    """Parses console parameters and fixes corresponding pages."""
    if len(sys.argv) == 1:
        print(HELP_STRING)
        return

    site = pywikibot.Site()

    source = "title"
    force_minor = False
    for arg in sys.argv[1:]:
        # keys
        if arg == "--min":
            force_minor = True
        elif arg == "--maj":
            force_minor = False
        elif arg == "--f":
            source = "file"
        elif arg == "--p":
            source = "title"
        elif arg == "--s":
            source = "server"
        elif arg == "--t":
            process_list(site, [TEST_PAGE], force_minor)
        # arguments
        elif source == "file":
            with open(arg, encoding="utf-8") as listfile:
                process_list(site, list(listfile), force_minor)
        elif source == "server":
            process_list(site, load_page_list(arg), force_minor)
        elif source == "title":
            process_list(site, [arg], force_minor)

if __name__ == "__main__":
    main()
