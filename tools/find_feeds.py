"""Find the real feed URL of the sites the reader wants watched.

The profile has had an empty rssFeeds list since the start, although seven feeds are wanted. Most
sites publish the address of their feed in the page head. This tool reads that, and it tries the
usual paths as a fallback. It writes nothing: it prints what it finds, so that a person can add the
good ones to meta/profile.json.

Usage:
    python tools/find_feeds.py
    python tools/find_feeds.py --url https://example.org/
"""
import argparse
import html
import re
import sys

import radar_lib as lib

CANDIDATES = [
    ("ScienceGuide (NL)", "https://www.scienceguide.nl/"),
    ("Regieorgaan SIA", "https://www.regieorgaan-sia.nl/"),
    ("NRO", "https://www.nro.nl/"),
    ("Vereniging Hogescholen", "https://www.vereniginghogescholen.nl/"),
    ("td-net / ITD Alliance", "https://itd-alliance.org/"),
    ("CARN", "https://www.carn.org.uk/"),
    ("Silicon Reckoner", "https://siliconreckoner.substack.com/"),
]

FALLBACK_PATHS = ("feed/", "feed", "rss", "rss.xml", "atom.xml", "index.xml", "feeds/posts/default")


def from_head(page_html):
    """Feed links that the page itself declares."""
    found = []
    pattern = re.compile(r'<link[^>]+type=["\']application/(?:rss|atom)\+xml["\'][^>]*>', re.I)
    for tag in pattern.findall(page_html):
        href = re.search(r'href=["\']([^"\']+)', tag, re.I)
        title = re.search(r'title=["\']([^"\']*)', tag, re.I)
        if href:
            found.append((html.unescape(href.group(1)), html.unescape(title.group(1)) if title else ""))
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(description="Find the feed URL of a site.")
    parser.add_argument("--url", default=None, help="one site to check")
    args = parser.parse_args(argv)

    targets = [(args.url, args.url)] if args.url else CANDIDATES
    for label, url in targets:
        page = ""
        try:
            page = lib.fetch_text(url)
        except Exception as exc:
            print("%-24s page not readable: %s" % (label, str(exc)[:70]))
        declared = from_head(page)
        if declared:
            for feed_url, title in declared:
                print("%-24s DECLARED %s  %s" % (label, feed_url, title))
            continue
        for path in FALLBACK_PATHS:
            probe = url.rstrip("/") + "/" + path
            try:
                body = lib.fetch_text(probe)
            except Exception:
                continue
            if "<rss" in body[:400].lower() or "<feed" in body[:400].lower():
                print("%-24s FOUND    %s" % (label, probe))
                break
        else:
            print("%-24s none found. Check the site by hand." % label)
    return 0


if __name__ == "__main__":
    sys.exit(main())
