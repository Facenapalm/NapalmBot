"""This script collects ruwiki's validation statistics for further plotting."""

import sys
from datetime import datetime
import pywikibot
from pywikibot.data.api import Request

DEFAULT_SITE = pywikibot.Site()

def get_urlist(site=DEFAULT_SITE, namespace="*", redirects="nonredirects"):
    """Get list of unreviewed pages."""
    request = Request(site=site,
                      action="query",
                      list="unreviewedpages",
                      urnamespace=namespace,
                      urfilterredir=redirects,
                      urlimit="5000")
    result = []
    while True:
        answer = request.submit()
        result += [page["title"] for page in answer["query"]["unreviewedpages"]]
        if "query-continue" in answer:
            request["urstart"] = answer["query-continue"]["unreviewedpages"]["urstart"]
        else:
            break
    return result

def get_orlist(site=DEFAULT_SITE, namespace="*", redirects="nonredirects"):
    """Get list of oldreviewed pages."""
    request = Request(site=site,
                      action="query",
                      list="oldreviewedpages",
                      ornamespace=namespace,
                      orfilterredir=redirects,
                      orlimit="5000")
    result = []
    while True:
        answer = request.submit()
        result += [page["title"] for page in answer["query"]["oldreviewedpages"]]
        if "query-continue" in answer:
            request["orstart"] = answer["query-continue"]["oldreviewedpages"]["orstart"]
        else:
            break
    return result

def count(listname, namespace="*", redirects="nonredirects"):
    if listname == "unreviewedpages":
        return str(len(get_urlist(namespace=namespace, redirects=redirects)))
    else:
        return str(len(get_orlist(namespace=namespace, redirects=redirects)))

def main():
    """Collect statistics and write to file."""
    if len(sys.argv) == 1:
        return

    stats = []
    stats.append(datetime.strftime(datetime.utcnow(), "%Y-%m-%d"))
    stats.append(count("unreviewedpages", "0"))
    stats.append(count("oldreviewedpages", "0"))
    stats.append(count("unreviewedpages", "6"))
    stats.append(count("oldreviewedpages", "6"))
    stats.append(count("unreviewedpages", "10"))
    stats.append(count("oldreviewedpages", "10"))
    stats.append(count("unreviewedpages", "14"))
    stats.append(count("oldreviewedpages", "14"))
    stats.append(count("unreviewedpages", "*", "redirects"))
    stats.append(count("oldreviewedpages", "*", "redirects"))

    with open(sys.argv[1], "a") as statfile:
        statfile.write("\t".join(stats))
        statfile.write("\n")

if __name__ == "__main__":
    main()
