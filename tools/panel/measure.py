"""The objective measurements of the panel test. No opinion, only counts.

P2 and P3 own these. They are written so that the numbers cannot be argued with a feeling.

    1. Coverage: for every watched journal that is switched on, take the journal's own list for the
       window from Crossref, then count how many of those papers the radar saw (as an item or as a
       candidate) and how many it kept. This is the recall of the harvest; the kept share is the
       effect of the scoring.
    2. Duplicates: normalised URLs and titles across the collection and the queue.
    3. The relevance sample: twenty items drawn with a fixed seed, printed with their record, so that
       the subject reviewer can judge each one.

Usage:
    python tools/panel/measure.py --round 1
    python tools/panel/measure.py --round 1 --window 2026-10-05
"""
import argparse
import pathlib
import random
import re
import sys
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import radar_lib as lib  # noqa: E402


def normalise(text):
    return re.sub(r"[^a-z0-9]+", " ", str(text or "").lower()).strip()


def coverage(window):
    """Recall of the harvest for each watched journal, measured against Crossref."""
    items = lib.collection("items")
    kept_dois = {str(v.get("doi", "")).lower() for v in items.values() if v.get("doi")}
    known = set(kept_dois)
    for path in (lib.DATA / "inbox" / "items").glob("*.json"):
        doc = lib.load_json(path, {}) or {}
        if doc.get("doi"):
            known.add(str(doc["doi"]).lower())

    rows = []
    for journal in lib.profile().get("journalWatch", []):
        if not journal.get("on") or not journal.get("issn"):
            continue
        params = {"filter": "from-pub-date:%s" % window, "rows": "60", "sort": "published",
                  "order": "desc", "select": "DOI,title,published", "mailto": lib.MAILTO}
        url = "https://api.crossref.org/journals/%s/works?%s" % (
            journal["issn"], urllib.parse.urlencode(params))
        try:
            data = lib.fetch_json(url)
        except Exception as exc:
            rows.append({"journal": journal["name"], "total": 0, "seen": 0, "kept": 0,
                         "error": str(exc)[:60]})
            continue
        listed = [entry for entry in data["message"]["items"] if entry.get("DOI")]
        seen = [entry for entry in listed if entry["DOI"].lower() in known]
        kept = [entry for entry in listed if entry["DOI"].lower() in kept_dois]
        rows.append({"journal": journal["name"], "total": len(listed), "seen": len(seen), "kept": len(kept)})
    return rows


def duplicates():
    """The same record twice, by normalised URL and by normalised title."""
    groups = {}
    for doc_id, doc in lib.collection("items").items():
        for key in (normalise(doc.get("url")), normalise(doc.get("title"))):
            if len(key) > 25:
                groups.setdefault(key, []).append(("items", doc_id))
    for path in (lib.DATA / "inbox" / "items").glob("*.json"):
        doc = lib.load_json(path, {}) or {}
        for key in (normalise(doc.get("url")), normalise(doc.get("title"))):
            if len(key) > 25:
                groups.setdefault(key, []).append(("queue", path.stem))
    return {key: value for key, value in groups.items()
            if len({doc_id for _, doc_id in value}) > 1}


def sample(count, seed):
    items = lib.collection("items")
    keys = sorted(items)
    random.seed(seed)
    return [(key, items[key]) for key in random.sample(keys, min(count, len(keys)))]


def main(argv=None):
    parser = argparse.ArgumentParser(description="The objective measurements of the panel test.")
    parser.add_argument("--round", type=int, default=1)
    parser.add_argument("--window", default=None, help="first publication date. Default: the last run minus 7 days")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args(argv)

    last = lib.load_json(lib.DATA / "meta" / "lastRun.json", {}) or {}
    window = args.window or last.get("since") or last.get("date") or "2026-10-05"

    out = ["# Objective measurements, round %d" % args.round, "",
           "Window: from %s. Written by tools/panel/measure.py. No opinion, only counts." % window, ""]

    out.append("## 1. Coverage and recall for each watched journal (T05)")
    out.append("")
    out.append("| Journal | Published in the window | Seen by the radar | Kept as an item | Recall | Kept share |")
    out.append("| --- | --- | --- | --- | --- | --- |")
    totals = {"total": 0, "seen": 0, "kept": 0}
    rows = coverage(window)
    for row in rows:
        if row.get("error"):
            out.append("| %s | - | - | - | failed: %s | - |" % (row["journal"], row["error"]))
            continue
        totals["total"] += row["total"]
        totals["seen"] += row["seen"]
        totals["kept"] += row["kept"]
        recall = (100.0 * row["seen"] / row["total"]) if row["total"] else 0
        kept = (100.0 * row["kept"] / row["seen"]) if row["seen"] else 0
        out.append("| %s | %d | %d | %d | %.0f%% | %.0f%% |" % (
            row["journal"], row["total"], row["seen"], row["kept"], recall, kept))
    out.append("| **all journals** | **%d** | **%d** | **%d** | **%.0f%%** | **%.0f%%** |" % (
        totals["total"], totals["seen"], totals["kept"],
        100.0 * totals["seen"] / totals["total"] if totals["total"] else 0,
        100.0 * totals["kept"] / totals["seen"] if totals["seen"] else 0))
    out.append("")
    out.append("Read this as: the harvest saw this share of what the journals published in the window.")
    out.append("A paper the radar saw but did not keep was scored below the minimum, or dropped by an exclusion.")
    out.append("")

    out.append("## 2. Duplicates (T06)")
    out.append("")
    found = duplicates()
    if not found:
        out.append("No duplicate URL and no duplicate title was found.")
    else:
        out.append("| Normalised key | Records |")
        out.append("| --- | --- |")
        for key, value in sorted(found.items()):
            out.append("| %s | %s |" % (key[:70], ", ".join("%s/%s" % pair for pair in value)))
    out.append("")

    out.append("## 3. The relevance sample (T07)")
    out.append("")
    out.append("Twenty items, seed %d. P7 judges each one against the five live projects." % args.seed)
    out.append("")
    for key, item in sample(20, args.seed):
        out.append("**%s** - %s" % (key, item.get("title")))
        out.append("")
        out.append("- %s | %s | %s | score %s | themes %s" % (
            item.get("venue"), item.get("date"), item.get("source"),
            item.get("score"), ", ".join(item.get("themes") or [])))
        out.append("- why: %s" % item.get("why"))
        out.append("- caveat: %s" % (item.get("caveat") or "none"))
        out.append("- abstract: %s" % ("yes" if item.get("abstract") else "not stored"))
        out.append("")

    target = lib.ROOT / "tools" / "panel" / ("round%d" % args.round) / "MEASURE.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    print("journals measured:", len([row for row in rows if not row.get("error")]))
    print("published in the window:", totals["total"], "| seen:", totals["seen"], "| kept:", totals["kept"])
    print("duplicate groups:", len(found))
    print("wrote", target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
