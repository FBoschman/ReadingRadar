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
        "exportedAt": datetime.date.today().isoformat(),
        "generatedBy": "tools/build_bundle.py (local cycle)",
        "firstExport": previous.get("sourceArtifact",
                                   "https://claude.ai/artifact/8EnWDz2BWtdGtGu8BqcQhJ"),
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

    # The inbox is the reader's work list. The dashboard shows the counts, so that the queue is
    # visible and does not grow in silence.
    inbox = {
        "items": len(list((data / "inbox" / "items").glob("*.json"))) if (data / "inbox" / "items").is_dir() else 0,
        "lineage": len(list((data / "inbox" / "lineage").glob("*.json"))) if (data / "inbox" / "lineage").is_dir() else 0,
        "run": None,
    }
    run_file = data / "inbox" / "run.json"
    if run_file.is_file():
        inbox["run"] = json.loads(run_file.read_text(encoding="utf-8"))
    bundle["inbox"] = inbox
    print("inbox: %d candidates, %d lineage drafts" % (inbox["items"], inbox["lineage"]))

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
