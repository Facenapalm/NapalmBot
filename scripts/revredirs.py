"""This script automatically reviews obvious redirects in ruwiki."""
import re
import pywikibot
from pywikibot.data.api import Request

def get_list(site, namespace="0"):
    """Get list of unreviewed redirects with their targets."""
    result = []

    def _submit_and_parse(request):
        """Divide answer to list of values and continue info."""
        answer = request.submit()
        if "pages" not in answer["query"]:
            return ([], {})
        values = list(answer["query"]["pages"].values())
        if "query-continue" in answer:
            contin = answer["query-continue"]
        else:
            contin = {}
        return (values, contin)

    kwargs = {
        "action": "query",
        "prop": "links",
        "pllimit": "5000",
        "generator": "unreviewedpages",
        "gurnamespace": namespace,
        "gurfilterredir": "redirects",
        "gurlimit": "5000"
    }

    while True:
        # iterate for gurstart, get list of redirects
        request = Request(site=site, **kwargs)
        (values, contin) = _submit_and_parse(request)
        chunk = [{"title": value["title"], "links": []} for value in values]

        while True:
            # iterate for plcontinue, get list of links (ie target candidates)
            for key, value in enumerate(values):
                if "links" in value:
                    chunk[key]["links"] += [links["title"] for links in value["links"]]
            if "links" in contin:
                request["plcontinue"] = contin["links"]["plcontinue"]
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

    # filter result: redirects with two or more links aren't any interesting for us
    result = [(x["title"], x["links"][0]) for x in filter(lambda x: len(x["links"]) == 1, result)]
    return result

def compare(redirect, target):
    """Return true if redirect == target except е → ё, - → — and other transitions."""
    if len(redirect) != len(target):
        return False

    # «Елочная ёлка» → «Ёлочная ёлка» doesn't seems to be a legal redirect
    have_yo = "ё" in redirect
    have_apo = "’" in redirect
    have_quote = "«" in redirect or "»" in redirect
    have_dash = "—" in redirect

    for idx, rchar in enumerate(redirect):
        tchar = target[idx]
        if rchar == tchar:
            continue
        if rchar == "е" and tchar == "ё":
            if have_yo:
                return False
            else:
                continue
        if rchar == "'" and tchar == "’":
            if have_apo:
                return False
            else:
                continue
        if (rchar == "\"" and tchar == "«") or (rchar == "\"" and tchar == "»"):
            if have_quote:
                return False
            else:
                continue
        if rchar == "-" and tchar == "—":
            if have_dash:
                return False
            else:
                continue
        return False
    return True

def primary_check(redirect, target):
    """Checks if redirect seeems to be legal."""
    if compare(redirect, target):
        return True
    # redirects from one precision to another
    parser = re.compile(r"^([^\(\)]+) \([^\(\)]+\)$")
    rmatch = parser.match(redirect)
    tmatch = parser.match(target)
    if rmatch and tmatch:
        # something (one) → something (two)
        if rmatch.group(1) == tmatch.group(1):
            return True
    elif rmatch:
        # something (one) → something
        if rmatch.group(1) == target:
            return True
    elif tmatch:
        # something → something (two)
        if redirect == tmatch.group(1):
            return True
    # persones redirect
    match = re.match(r"([а-яё]+), ([а-яё]+) ([а-яё]+)", target, flags=re.I)
    if match:
        candidates = [
            "{surname} {name} {fathername}",
            "{name} {fathername} {surname}",
            "{surname}, {name}",
            "{surname} {name}",
            "{name} {surname}",
            "{name}"
        ]
        for candidate in candidates:
            if compare(redirect, candidate.format(surname=match.group(1), name=match.group(2),
                                                  fathername=match.group(3))):
                return True
    match = re.match(r"([а-яё]+), ([а-яё]+)", target, flags=re.I)
    if match:
        candidates = [
            "{surname} {name}",
            "{name} {surname}",
            "{name}"
        ]
        for candidate in candidates:
            if compare(redirect, candidate.format(surname=match.group(1), name=match.group(2))):
                return True
    return False

def secondary_check(rpage, tpage):
    """
    Check if redirect have no implicit problems: for example, if this is not an article replaced
    by redirect.
    """
    matcher = re.compile(r"^\s*#(redirect|перенаправление)\s*:?\s*\[\[[^\[\]\|\n]+\]\]\s*$", flags=re.I)
    for revision in rpage.revisions(content=True):
        if not matcher.match(revision["text"]):
            return False
    if not tpage.exists():
        return False
    if tpage.isRedirectPage():
        return False
    if rpage.namespace().id != tpage.namespace().id:
        return False
    return True

def get_review_token(site):
    """Get rveiew token on given site."""
    return site.get_tokens(["csrf"])["csrf"]

def review(site, token, page):
    """Review given page."""
    revid = page.latest_revision_id
    request = Request(site=site,
                      action="review",
                      token=token,
                      revid=revid)
    request.submit()

def review_list(lst):
    """Do secondary check and review all redirects from list."""
    site = pywikibot.Site()
    token = get_review_token(site)
    for redirect, target in lst:
        rpage = pywikibot.Page(site, redirect)
        tpage = pywikibot.Page(site, target)
        if not secondary_check(rpage, tpage):
            continue
        review(site, token, rpage)

def main():
    """Main script function."""
    site = pywikibot.Site()
    lst = filter(lambda x: primary_check(x[0], x[1]), get_list(site))
    review_list(lst)

if __name__ == "__main__":
    main()
