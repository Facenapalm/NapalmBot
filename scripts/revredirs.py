"""This script automatically reviews obvious redirects in ruwiki."""
import re
import pywikibot
from pywikibot.data.api import Request

def get_review_token(site):
    """Get a review token on the given site."""
    return site.get_tokens(["csrf"])["csrf"]

def review(site, token, page):
    """Review the latest revision of the given page."""
    revid = page.latest_revision_id
    request = Request(site=site,
                      action="review",
                      token=token,
                      revid=revid)
    request.submit()

def get_unreviewed_redirects(site, namespace="0"):
    """Get a list of the unreviewed redirects with their targets."""
    result = []

    def _submit_and_parse(request):
        """Divide the answer to the list of values and continue info."""
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

def primary_check(redirect, target):
    """Checks if redirect→target pair seeems to be legal."""

    def compare(redirect, target):
        """Return true if redirect == target except 'е'' → 'ё', '-' → '—' and other replaces."""
        replaces = {
            "е": "ё",
            "'": "’",
            "\"": "«»„“",
            "-": "—"
        }
        if len(redirect) != len(target):
            return False
        for idx, rchar in enumerate(redirect):
            tchar = target[idx]
            if rchar == tchar:
                continue
            if rchar in replaces:
                if tchar in replaces[rchar]:
                    continue
            return False
        return True

    # redirects that help people typing page titles
    if compare(redirect, target):
        return True

    # redirects to pages with disambiguations
    match = re.match(r"^([^\(\)]+) \([^\(\)]+\)$", target)
    if match:
        if redirect == match.group(1):
            return True

    # persones redirect
    match = re.match(r"^([а-яё\-]+), ([а-яё]+) ([а-яё]{5,})$", target, flags=re.I)
    if match:
        candidates = [
            "{surname} {name} {fathername}",
            "{name} {fathername} {surname}",
            "{surname}, {name}",
            "{surname} {name}",
            "{name} {surname}",
            "{surname}"
        ]
        for candidate in candidates:
            if compare(redirect, candidate.format(surname=match.group(1), name=match.group(2),
                                                  fathername=match.group(3))):
                return True

    match = re.match(r"^([а-яё\-]+), ([а-яё]+)$", target, flags=re.I)
    if match:
        candidates = [
            "{surname} {name}",
            "{name} {surname}",
            "{surname}"
        ]
        for candidate in candidates:
            if compare(redirect, candidate.format(surname=match.group(1), name=match.group(2))):
                return True

    match = re.match(r"^([а-яё\-]+), ([а-яё ]+ (?:фон|де|оглы))$", target, flags=re.I)
    if match:
        candidates = [
            "{name} {surname}",
            "{surname}"
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

def main():
    """Main script function."""
    site = pywikibot.Site()
    lst = filter(lambda x: primary_check(x[0], x[1]), get_unreviewed_redirects(site))
    pywikibot.output("List loaded")
    token = get_review_token(site)
    for redirect, target in lst:
        rpage = pywikibot.Page(site, redirect)
        tpage = pywikibot.Page(site, target)
        if not secondary_check(rpage, tpage):
            pywikibot.output("[[{}]] → [[{}]]: secondary check failed".format(redirect, target))
            continue
        review(site, token, rpage)
        pywikibot.output("[[{}]] → [[{}]]: reviewed".format(redirect, target))

if __name__ == "__main__":
    main()
