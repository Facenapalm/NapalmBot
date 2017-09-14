"""
This script collects ruwiki's validation statistics for further plotting.
Statfile structure: first line - any comment (will be ignored), other lines -
values, separated with tabs (date, unrev_main, old_main, unrev_file, old_file,
unrev_template, old_template, unrev_cat, old_cat, unrev_redir, old_redir).

Usage:
    python validstats.py statfile
"""

import sys
from datetime import datetime
import pywikibot
from pywikibot.data.api import Request

DEFAULT_SITE = pywikibot.Site()

def get_urlist(site=DEFAULT_SITE, namespace="0|6|10|14|100|828", redirects="nonredirects"):
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

def get_orlist(site=DEFAULT_SITE, namespace="0|6|10|14|100|828", redirects="nonredirects"):
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

def count(listname, namespace="0|6|10|14|100|828", redirects="nonredirects"):
    """Get element count in list of unreviewed or oldreviewed pages."""
    if listname == "unreviewedpages":
        return str(len(get_urlist(namespace=namespace, redirects=redirects)))
    else:
        return str(len(get_orlist(namespace=namespace, redirects=redirects)))

def main():
    """Main script function."""
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
    stats.append(count("unreviewedpages", redirects="redirects"))
    stats.append(count("oldreviewedpages", redirects="redirects"))

    with open(sys.argv[1], "a") as statfile:
        statfile.write("\t".join(stats))
        statfile.write("\n")

if __name__ == "__main__":
    main()
