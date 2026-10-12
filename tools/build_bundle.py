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
