"""Build the dashboard data bundle from the project kit.

The dashboard app runs from a local file. A browser refuses to read JSON files with fetch() from a
local file. This script writes one JavaScript file that the page can load with a script tag instead.

Usage:
    python tools/build_bundle.py [repo root]

The default repo root is the parent folder of this script. The script writes data/radar-data.js.

It reads these collections from data/:
    items, lineage, lineageRequests, events, meta
and the counts from data/MANIFEST.json.
"""
import datetime
import json
import pathlib
import sys

COLLECTIONS = ("items", "lineage", "lineageRequests", "events", "meta")


def read_collection(folder):
    """Return {doc_id: document} for every JSON file in the folder."""
    out = {}
    if not folder.is_dir():
        return out
    for path in sorted(folder.glob("*.json")):
        try:
            out[path.stem] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print("SKIP (bad JSON):", path.name, "-", exc)
    return out


def write_manifest(root, bundle):
    """Regenerate data/MANIFEST.json from the data, so that the counts cannot go stale."""
    data = root / "data"
    previous = json.loads((data / "MANIFEST.json").read_text(encoding="utf-8")) if (data / "MANIFEST.json").is_file() else {}
    items = bundle.get("items", {})
    manifest = {
        "generatedAt": datetime.date.today().isoformat(),
        "generatedBy": "tools/build_bundle.py (local cycle)",
        "firstExport": previous.get("sourceArtifact",
                                   previous.get("firstExport",
                                                "https://claude.ai/artifact/8EnWDz2BWtdGtGu8BqcQhJ")),
        "lastRun": (bundle.get("meta", {}).get("lastRun", {}) or {}).get("date", ""),
        "collections": {name: {"documents": len(bundle.get(name, {})), "ids": sorted(bundle.get(name, {}))}
                        for name in COLLECTIONS},
        "itemStatusCounts": {},
        "itemRunCounts": {},
        "itemThemeCounts": {},
        "inbox": {"items": bundle.get("inbox", {}).get("items", 0),
                  "lineage": bundle.get("inbox", {}).get("lineage", 0)},
        "layout": "<collection>/<doc_id>.json ; each file is the document body (no wrapper)",
    }
    for item in items.values():
        status = item.get("status") or "unknown"
        manifest["itemStatusCounts"][status] = manifest["itemStatusCounts"].get(status, 0) + 1
        run = item.get("run") or "unknown"
        manifest["itemRunCounts"][run] = manifest["itemRunCounts"].get(run, 0) + 1
        for code in item.get("themes") or []:
            manifest["itemThemeCounts"][code] = manifest["itemThemeCounts"].get(code, 0) + 1
    save = json.dumps(manifest, ensure_ascii=False, indent=1, sort_keys=True)
    (data / "MANIFEST.json").write_text(save + "\n", encoding="utf-8", newline="\n")
    print("manifest rebuilt:", len(items), "items |", manifest["itemStatusCounts"])


def build(root):
    data = root / "data"
    bundle = {"generated": datetime.datetime.now().replace(microsecond=0).isoformat()}
    counts = {}
    for name in COLLECTIONS:
        bundle[name] = read_collection(data / name)
        counts[name] = len(bundle[name])
    manifest = data / "MANIFEST.json"
    if manifest.is_file():
        bundle["manifest"] = json.loads(manifest.read_text(encoding="utf-8"))
    else:
        print("WARNING: data/MANIFEST.json is missing. The health checks lose the export counts.")

    # The inbox is the reader's work list. The panel found that a queue nobody can read is a queue
    # nobody works (P1-3, P2-6), so the bundle now carries the candidates themselves, capped.
    queue = []
    decided = 0
    folder = data / "inbox" / "items"
    if folder.is_dir():
        for path in sorted(folder.glob("*.json")):
            doc = json.loads(path.read_text(encoding="utf-8"))
            status = doc.get("status") or "candidate"
            if status in ("keep", "maybe", "skip"):
                decided += 1
            queue.append({
                "id": path.stem,
                "kind": doc.get("kind") or "paper",
                "title": doc.get("title") or "",
                "authors": doc.get("authors") or "",
                "venue": doc.get("venue") or "",
                "date": doc.get("date") or "",
                "source": doc.get("source") or "",
                "themes": doc.get("themeGuess") or [],
                "hasAbstract": bool(doc.get("abstract")),
                "url": doc.get("url") or "",
                "status": status,
            })
    drafts = []
    draft_folder = data / "inbox" / "lineage"
    if draft_folder.is_dir():
        for path in sorted(draft_folder.glob("*.json")):
            doc = json.loads(path.read_text(encoding="utf-8"))
            drafts.append({"id": path.stem, "title": doc.get("title") or "",
                           "parsed": doc.get("parsed"), "refCount": doc.get("refCount"),
                           "median": doc.get("median"), "tracedAt": doc.get("tracedAt")})
    inbox = {
        "items": len(queue),
        "lineage": len(drafts),
        "run": None,
        "candidates": queue[:300],
        "candidatesCapped": max(0, len(queue) - 300),
        "lineageDrafts": drafts,
        "decided": decided,
        "undecided": len(queue) - decided,
    }
    for name in ("run", "expired"):
        path = data / "inbox" / (name + ".json")
        if path.is_file():
            inbox[name] = json.loads(path.read_text(encoding="utf-8"))
    bundle["inbox"] = inbox
    for name in ("status", "sourceHistory"):
        path = data / "meta" / (name + ".json")
        if path.is_file():
            bundle[name] = json.loads(path.read_text(encoding="utf-8"))
    print("inbox: %d candidates (%d carry a decision, %d wait), %d lineage drafts"
          % (inbox["items"], inbox["decided"], inbox["undecided"], inbox["lineage"]))

    write_manifest(root, bundle)

    text = "window.RADAR_DATA = " + json.dumps(bundle, ensure_ascii=False, separators=(",", ":")) + ";\n"
    out = data / "radar-data.js"
    out.write_text(text, encoding="utf-8")
    print("wrote", out, "with", f"{len(text):,}", "characters")
    for name in sorted(counts):
        print(f"  {name}: {counts[name]} documents")


def main(argv):
    if len(argv) > 1:
        root = pathlib.Path(argv[1]).resolve()
    else:
        root = pathlib.Path(__file__).resolve().parent.parent
    if not (root / "data").is_dir():
        raise SystemExit(f"No data folder in {root}. Give the repo root as the first argument.")
    build(root)


if __name__ == "__main__":
    main(sys.argv)
