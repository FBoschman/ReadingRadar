"""Build a lineage draft from the reference list of a paper.

Crossref holds the reference list of most papers. This tool reads it and writes a draft to
data/inbox/lineage/<id>.json with the references and the counts.

The strands, the narrative, the forYou and the absent fields stay a decision by a person or an
agent. That step writes the finished document into data/lineage/<id>.json and removes the draft.

A hard rule from SCHEMA.md: the narrative and the strands may only name a work that appears in
refs. No reconstruction from memory.

Usage:
    python tools/lineage.py --item doi_10.3390_jintelligence14100254
    python tools/lineage.py --top 5
    python tools/lineage.py --queue
"""
import argparse
import re
import statistics
import sys

import radar_lib as lib


def parse_unstructured(text):
    """Return (first author surname, year, title) from an unstructured reference string."""
    author = ""
    year = None
    title = ""
    match = re.match(r"^([A-Z][A-Za-z'\-]+)[ ,]", text)
    if match:
        author = match.group(1)
    match = re.search(r"\((\d{4})\)", text)
    if match:
        year = int(match.group(1))
    else:
        match = re.search(r"\b(19|20)\d{2}\b", text)
        if match:
            year = int(match.group(0))
    match = re.search(r"\((?:19|20)\d{2}\)\s*(.+?)(?:\.\s|$)", text)
    if match:
        title = match.group(1).strip()
    if not title:
        title = text[:180]
    return author, year, title


def normalise_reference(reference):
    """Turn one Crossref reference entry into the shape of SCHEMA.md."""
    doi = (reference.get("DOI") or "").strip()
    author = reference.get("author") or ""
    if author:
        author = re.split(r"[, ]", author.strip())[0]
    year = reference.get("year")
    try:
        year = int(year) if year else None
    except (TypeError, ValueError):
        year = None
    title = reference.get("article-title") or reference.get("volume-title") or ""
    journal = reference.get("journal-title") or ""
    unstructured = reference.get("unstructured") or ""
    if not author and not year and not title and unstructured:
        parsed_author, parsed_year, parsed_title = parse_unstructured(unstructured)
        author = author or parsed_author
        year = year or parsed_year
        title = title or parsed_title
    if not title and unstructured:
        title = unstructured[:180]
    return {"a": author, "y": year, "t": title, "j": journal, "d": doi}


def fetch_references(doi):
    url = "https://api.crossref.org/works/%s?mailto=%s" % (doi, lib.MAILTO)
    message = lib.fetch_json(url)["message"]
    refs = [normalise_reference(entry) for entry in message.get("reference", [])]
    return refs, message.get("reference-count") or len(refs)


def build_draft(item_id, doi, title, refs, ref_count):
    years = [ref["y"] for ref in refs if isinstance(ref.get("y"), int)]
    median = int(statistics.median(years)) if years else None
    earliest = min(years) if years else None
    method = ("Parsed the Crossref reference array for %s. Author, year and title were taken from "
              "the structured fields where Crossref carried them, and from the unstructured string "
              "where it did not. No reference was reconstructed from memory." % doi)
    return {
        "itemId": item_id,
        "title": title,
        "doi": doi,
        "refs": refs,
        "refCount": ref_count,
        "parsed": len(refs),
        "median": median,
        "earliest": earliest,
        "tracedAt": lib.today(),
        "source": "Crossref reference list for " + doi + " (mailto " + lib.MAILTO + ")",
        "method": method,
        "confidence": "low" if len(refs) < 10 else "medium",
        "strands": [],
        "narrative": "",
        "forYou": "",
        "absent": "",
    }


def candidates(args):
    items = lib.collection("items")
    done = set(lib.collection("lineage").keys())
    queue = lib.collection("lineageRequests")
    out = []
    if args.item:
        out = [args.item]
    elif args.queue:
        out = [doc_id for doc_id, doc in queue.items() if doc.get("status") == "queued"]
    else:
        ranked = sorted(items.items(), key=lambda pair: -int(pair[1].get("score") or 0))
        for doc_id, doc in ranked:
            if doc_id in done or not doc.get("doi"):
                continue
            out.append(doc_id)
            if len(out) >= args.top:
                break
    return [(doc_id, items[doc_id]) for doc_id in out if doc_id in items and doc_id not in done]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Draft a lineage document from a Crossref reference list.")
    parser.add_argument("--item", default=None, help="one item id")
    parser.add_argument("--top", type=int, default=3, help="the highest scoring items without a lineage document")
    parser.add_argument("--queue", action="store_true", help="the queued requests")
    args = parser.parse_args(argv)

    for doc_id, item in candidates(args):
        doi = (item.get("doi") or "").strip()
        if not doi:
            print("SKIP  %s: no DOI" % doc_id)
            continue
        try:
            refs, ref_count = fetch_references(doi)
        except Exception as exc:
            print("FAIL  %s: %s" % (doc_id, str(exc)[:90]))
            continue
        draft = build_draft(doc_id, doi, item.get("title") or "", refs, ref_count)
        lib.save_json(lib.DATA / "inbox" / "lineage" / (doc_id + ".json"), draft)
        print("DRAFT %s: %d of %d references, median %s, confidence %s" % (
            doc_id, draft["parsed"], draft["refCount"], draft["median"], draft["confidence"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
