"""Fill a missing abstract from OpenAlex.

Crossref sends an abstract for some publishers only. OpenAlex holds an abstract for most works.
This step adds the missing text. The judgement pass can then write an honest caveat, and an item
can say where its abstract came from.

Usage:
    python tools/enrich.py --limit 60
    python tools/enrich.py --all
    python tools/enrich.py --items --all       # repair the collection itself
"""
import argparse
import sys
import urllib.parse

import radar_lib as lib


def enrich_one(doc):
    """Return 'filled', 'empty' or 'failed'."""
    doi = (doc.get("doi") or "").strip()
    if not doi:
        return "no-doi"
    url = "https://api.openalex.org/works/https://doi.org/%s?select=abstract_inverted_index,language,publication_date&mailto=%s" % (
        urllib.parse.quote(doi), lib.MAILTO)
    try:
        work = lib.fetch_json(url)
    except Exception:
        return "failed"
    text = lib.openalex_abstract(work.get("abstract_inverted_index"))
    if text:
        doc["abstract"] = text
        doc["abstractSource"] = "OpenAlex"
        if not doc.get("lang") and work.get("language"):
            doc["lang"] = work["language"]
        return "filled"
    doc["abstractSource"] = ""
    return "empty"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fill the abstracts of the candidates from OpenAlex.")
    parser.add_argument("--limit", type=int, default=60, help="maximum items to try")
    parser.add_argument("--all", action="store_true", help="try every candidate without an abstract")
    parser.add_argument("--items", action="store_true",
                        help="work on data/items instead of the inbox, to repair a record that lost its abstract")
    args = parser.parse_args(argv)

    folder = (lib.DATA / "items") if args.items else (lib.DATA / "inbox" / "items")
    todo = []
    for path in sorted(folder.glob("*.json")):
        doc = lib.load_json(path, {}) or {}
        if not doc.get("abstract") and doc.get("doi"):
            todo.append((path, doc))
    limit = len(todo) if args.all else args.limit
    counts = {"filled": 0, "empty": 0, "failed": 0, "no-doi": 0}
    for number, (path, doc) in enumerate(todo[:limit], start=1):
        result = enrich_one(doc)
        counts[result] = counts.get(result, 0) + 1
        if result in ("filled", "empty"):
            lib.save_json(path, doc)
        print("%3d/%d %-6s %s" % (number, min(limit, len(todo)), result, doc.get("id")))
    print("")
    print("candidates without an abstract:", len(todo))
    print("result:", counts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
