"""Print the promotion queue from the inbox.

The harvest writes candidates to data/inbox/items. This tool ranks them so that the judgement
pass is quick. The rank is a simple keyword match against the theme keywords of the profile.
The rank is a hint only. The score, the why and the caveat stay a decision by a person or an agent.

Usage:
    python tools/queue.py
    python tools/queue.py --min-match 2 --limit 40
    python tools/queue.py --venue "Studies in Higher Education"
"""
import argparse
import pathlib
import sys

import radar_lib as lib


def keywords_of_profile():
    words = []
    for theme in lib.profile().get("themes", []):
        for word in theme.get("keywords", []):
            word = word.strip().lower()
            if word and word not in words and "/" not in word:
                words.append(word)
    return words


def match_score(doc, keywords):
    hay = ((doc.get("title") or "") + " " + (doc.get("abstract") or "")).lower()
    return sum(1 for word in keywords if word in hay)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Rank the candidates in the inbox.")
    parser.add_argument("--limit", type=int, default=50, help="rows to print")
    parser.add_argument("--min-match", type=int, default=0, help="minimum keyword matches")
    parser.add_argument("--venue", default=None, help="only this venue, part of the name is enough")
    parser.add_argument("--kind", default=None, choices=["paper", "discourse"])
    args = parser.parse_args(argv)

    folder = lib.DATA / "inbox" / "items"
    rows = []
    for path in sorted(folder.glob("*.json")):
        doc = lib.load_json(path, {}) or {}
        if args.kind and doc.get("kind") != args.kind:
            continue
        if args.venue and args.venue.lower() not in (doc.get("venue") or "").lower():
            continue
        score = match_score(doc, keywords_of_profile())
        if score < args.min_match:
            continue
        rows.append((score, doc))
    rows.sort(key=lambda pair: (-pair[0], pair[1].get("date") or "", pair[1].get("title") or ""))

    print("candidates in the inbox :", len(list(folder.glob('*.json'))))
    print("rows after the filter   :", len(rows))
    print("")
    print("match | date       | themes    | abstract | venue | title | id")
    for score, doc in rows[: args.limit]:
        print("%5d | %-10s | %-9s | %-8s | %-26s | %s | %s" % (
            score, doc.get("date") or "-", ",".join(doc.get("themeGuess") or []) or "-",
            "yes" if doc.get("abstract") else "no",
            (doc.get("venue") or "?")[:26], (doc.get("title") or "")[:70], doc.get("id")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
