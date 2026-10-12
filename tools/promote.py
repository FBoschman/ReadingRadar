"""Promote a judged candidate into the item collection.

The judgement pass is a decision by a person or an agent. It writes its decisions to
data/inbox/judgement.json:

    {
      "doi_10.1000_example": {
        "score": 4,
        "themes": ["td", "eco"],
        "why": "One or two sentences on why this matters to this reader.",
        "caveat": "One limitation to check.",
        "wildcard": false
      }
    }

This tool checks each decision against SCHEMA.md, writes the finished document into
data/items/<id>.json and removes the candidate from the inbox.

Usage:
    python tools/promote.py --dry-run
    python tools/promote.py
"""
import argparse
import pathlib
import sys

import radar_lib as lib

ITEM_FIELDS = ("kind", "title", "authors", "venue", "date", "url", "doi", "themes", "score",
               "why", "caveat", "lang", "wildcard", "source", "status", "run",
               "abstract", "abstractSource")


def theme_codes():
    return [theme.get("code") for theme in lib.profile().get("themes", [])]


def check(doc, decision):
    """Return a list of problems. An empty list means the decision is valid."""
    problems = []
    codes = theme_codes()
    if not isinstance(decision, dict):
        return ["the decision is not an object"]
    try:
        score = int(decision.get("score"))
    except (TypeError, ValueError):
        return ["the score is missing or not a number"]
    floor = int(lib.profile().get("minScore", 3) or 3)
    if score < floor:
        problems.append("the score is below the floor of the profile (%d). Raise it, or leave the item out" % floor)
    if score > 5:
        problems.append("the score must be between 0 and 5")
    if lib.is_noise_title(doc.get("title")):
        problems.append("the title looks like a correction, an erratum or a retraction")
    themes = decision.get("themes") or []
    if not isinstance(themes, list):
        problems.append("themes must be a list")
    else:
        for code in themes:
            if code not in codes:
                problems.append("unknown theme code: " + str(code))
    if len(str(decision.get("why") or "").strip()) < 20:
        problems.append("the why is too short to be useful")
    if len(str(decision.get("caveat") or "").strip()) < 10:
        problems.append("the caveat is missing. Name one limitation, or say why there is none")
    if not doc.get("title"):
        problems.append("the candidate has no title")
    if not doc.get("date"):
        problems.append("the candidate has no date")
    return problems


def build_item(doc, decision):
    item = {
        "kind": doc.get("kind") or "paper",
        "title": doc.get("title") or "",
        "authors": doc.get("authors") or "",
        "venue": doc.get("venue") or "",
        "date": doc.get("date") or "",
        "url": doc.get("url") or "",
        "doi": doc.get("doi") or "",
        "themes": list(decision.get("themes") or []),
        "score": int(decision.get("score")),
        "why": str(decision.get("why") or "").strip(),
        "caveat": str(decision.get("caveat") or "").strip(),
        "lang": doc.get("lang") or "en",
        "wildcard": bool(decision.get("wildcard")),
        "source": doc.get("source") or "",
        "status": "new",
        "run": doc.get("run") or lib.today(),
        "abstract": doc.get("abstract") or "",
        "abstractSource": doc.get("abstractSource") or "",
    }
    return {key: item[key] for key in ITEM_FIELDS if key in item}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Promote judged candidates into items.")
    parser.add_argument("--dry-run", action="store_true", help="check only, write nothing")
    args = parser.parse_args(argv)

    inbox = lib.DATA / "inbox" / "items"
    decisions = lib.load_json(lib.DATA / "inbox" / "judgement.json", {})
    if not decisions:
        raise SystemExit("No decisions found in data/inbox/judgement.json")

    promoted = 0
    rejected = 0
    for doc_id, decision in sorted(decisions.items()):
        candidate = lib.load_json(inbox / (doc_id + ".json"), None)
        if candidate is None:
            print("SKIP  %s: no candidate in the inbox" % doc_id)
            rejected += 1
            continue
        if (lib.DATA / "items" / (doc_id + ".json")).exists():
            print("SKIP  %s: the item already exists" % doc_id)
            rejected += 1
            continue
        problems = check(candidate, decision)
        if problems:
            print("FAIL  %s: %s" % (doc_id, "; ".join(problems)))
            rejected += 1
            continue
        item = build_item(candidate, decision)
        if args.dry_run:
            print("OK    %s  score %s  %s" % (doc_id, item["score"], item["title"][:60]))
        else:
            lib.write_document("items", doc_id, item)
            (inbox / (doc_id + ".json")).unlink()
            print("WROTE %s  score %s  %s" % (doc_id, item["score"], item["title"][:60]))
        promoted += 1

    print("")
    print("promoted:", promoted, "| rejected:", rejected, "| dry run:", bool(args.dry_run))
    return 0 if rejected == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
