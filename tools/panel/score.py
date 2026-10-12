"""Score a panel round against the gate and compare it with the previous round.

The gate, from tools/panel/PANEL.md:
    G1  no open S1 defect, and no open S2 defect on a core-loop feature
    G2  at least 7 of 8 reviewers accept every feature, and 8 of 8 on the core loop
    G3  the Wilson 95% lower bound over the 200 cells is 0.95 or more (197 passes)
    G4  the median usefulness is 4 of 5 or more on every feature

Usage:
    python tools/panel/score.py --round 1
    python tools/panel/score.py --round 2
"""
import argparse
import json
import math
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
FEATURES = json.loads((ROOT / "features.json").read_text(encoding="utf-8"))
GATE = {"lower_bound": 0.95, "feature_floor": 7, "core_floor": 8, "quality_median": 4}
RATING_LINE = re.compile(r"^(F\d\d)\s*\|\s*(yes|no)\s*\|\s*([0-5])\s*\|\s*(.*)$")


def wilson_lower(passes, total, z=1.96):
    """The lower bound of the Wilson score interval for a proportion."""
    if total == 0:
        return 0.0
    p = passes / total
    denominator = 1 + z * z / total
    centre = p + z * z / (2 * total)
    spread = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total)
    return max(0.0, (centre - spread) / denominator)


def parse_report(path):
    text = path.read_text(encoding="utf-8")
    ratings = {}
    block = re.search(r"<!--\s*RATINGS(.*?)-->", text, re.S)
    if block:
        for line in block.group(1).splitlines():
            match = RATING_LINE.match(line.strip())
            if match:
                ratings[match.group(1)] = {"accept": match.group(2) == "yes",
                                           "useful": int(match.group(3)),
                                           "note": match.group(4).strip()}
    severities = []
    for line in text.splitlines():
        if line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 4 and re.fullmatch(r"S[123]", cells[1]):
                severities.append({"sev": cells[1], "feature": cells[2], "finding": cells[3][:140]})
    return ratings, severities


def median(values):
    if not values:
        return 0
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return round((ordered[middle - 1] + ordered[middle]) / 2, 1)


def collect(round_number):
    folder = ROOT / ("round%d" % round_number)
    reports = {}
    for path in sorted(folder.glob("P*.md")):
        ratings, severities = parse_report(path)
        reports[path.stem] = {"ratings": ratings, "severities": severities, "path": path}
    return reports


def score(round_number):
    reports = collect(round_number)
    names = sorted(reports)
    rows = []
    cells = passes = 0
    for feature in FEATURES["features"]:
        fid = feature["id"]
        accepted = [name for name in names if reports[name]["ratings"].get(fid, {}).get("accept")]
        usefulness = [reports[name]["ratings"][fid]["useful"] for name in names
                      if fid in reports[name]["ratings"]]
        failures = [name for name in names if not reports[name]["ratings"].get(fid, {}).get("accept")]
        cells += len(names)
        passes += len(accepted)
        rows.append({"id": fid, "core": fid in FEATURES["coreLoop"], "name": feature["name"],
                     "accepted": len(accepted), "of": len(names), "failed_by": failures,
                     "median": median(usefulness)})
    severities = [s for name in names for s in reports[name]["severities"]]
    s1 = [s for s in severities if s["sev"] == "S1"]
    core = set(FEATURES["coreLoop"])
    s2_core = [s for s in severities if s["sev"] == "S2" and s["feature"] in core]
    below_floor = [r for r in rows if r["accepted"] < GATE["feature_floor"]]
    below_core = [r for r in rows if r["core"] and r["accepted"] < GATE["core_floor"]]
    below_quality = [r for r in rows if r["median"] < GATE["quality_median"]]
    lower = wilson_lower(passes, cells)
    verdict = (not s1) and (not s2_core) and (not below_floor) and (not below_core) \
        and lower >= GATE["lower_bound"] and (not below_quality)
    return {"round": round_number, "reviewers": names, "rows": rows, "cells": cells, "passes": passes,
            "lower": lower, "s1": s1, "s2_core": s2_core, "below_floor": below_floor,
            "below_core": below_core, "below_quality": below_quality, "verdict": verdict,
            "severities": severities}


def write_report(result):
    previous = None
    if result["round"] > 1 and (ROOT / ("round%d" % (result["round"] - 1))).is_dir():
        try:
            previous = score(result["round"] - 1)
        except Exception:
            previous = None
    out = ["# Panel score, round %d" % result["round"], ""]
    out.append("Reviewers: %d (%s)" % (len(result["reviewers"]), ", ".join(result["reviewers"])))
    out.append("Cells: %d | passes: %d | Wilson 95%% lower bound: %.4f (gate %.2f)"
               % (result["cells"], result["passes"], result["lower"], GATE["lower_bound"]))
    out.append("")
    out.append("## The gate")
    out.append("")
    out.append("| Gate | Requirement | Result |")
    out.append("| --- | --- | --- |")
    out.append("| G1a | no open S1 defect | %s |" % ("pass" if not result["s1"] else "FAIL (%d)" % len(result["s1"])))
    out.append("| G1b | no S2 defect on a core-loop feature | %s |" % ("pass" if not result["s2_core"] else "FAIL (%d)" % len(result["s2_core"])))
    out.append("| G2a | 7 of 8 reviewers accept every feature | %s |" % ("pass" if not result["below_floor"] else "FAIL (%d features)" % len(result["below_floor"])))
    out.append("| G2b | 8 of 8 on the eight core features | %s |" % ("pass" if not result["below_core"] else "FAIL (%d features)" % len(result["below_core"])))
    out.append("| G3 | pooled lower bound 0.95 or more | %s |" % ("pass at %.4f" % result["lower"] if result["lower"] >= GATE["lower_bound"] else "FAIL at %.4f" % result["lower"]))
    out.append("| G4 | median usefulness 4 or more on every feature | %s |" % ("pass" if not result["below_quality"] else "FAIL (%d features)" % len(result["below_quality"])))
    out.append("")
    out.append("**Verdict: %s**" % ("PASS" if result["verdict"] else "NOT YET"))
    if not result["verdict"]:
        out.append("")
        out.append("The cells that hold the gate:")
        for row in (result["below_floor"] or result["below_core"]):
            out.append("- %s (%s): accepted by %d of %d%s" % (
                row["id"], row["name"], row["accepted"], row["of"],
                " - refused by " + ", ".join(row["failed_by"]) if row["failed_by"] else ""))
        if result["lower"] < GATE["lower_bound"]:
            need = int(math.ceil(GATE["lower_bound"] * result["cells"]))
            out.append("- the pooled bound needs about %d passes of %d; this round has %d"
                       % (need, result["cells"], result["passes"]))
    out.append("")
    out.append("## Every feature")
    out.append("")
    out.append("| Feature | Core | Accepted | Median usefulness | Refused by |")
    out.append("| --- | --- | --- | --- | --- |")
    for row in result["rows"]:
        out.append("| %s %s | %s | %d of %d | %s | %s |" % (
            row["id"], row["name"][:44], "yes" if row["core"] else "", row["accepted"], row["of"],
            row["median"], ", ".join(row["failed_by"]) or "-"))
    out.append("")
    for level in ("S1", "S2", "S3"):
        items = [s for s in result["severities"] if s["sev"] == level]
        out.append("## %s findings (%d)" % (level, len(items)))
        out.append("")
        for item in items:
            out.append("- **%s** %s" % (item["feature"], item["finding"]))
        out.append("")
    if previous:
        out.append("## Change since round %d" % previous["round"])
        out.append("")
        out.append("- lower bound: %.3f to %.3f" % (previous["lower"], result["lower"]))
        out.append("- S1 findings: %d to %d" % (len(previous["s1"]), len(result["s1"])))
        out.append("- features below the floor: %d to %d" % (len(previous["below_floor"]), len(result["below_floor"])))
        out.append("- features below the quality median: %d to %d" % (len(previous["below_quality"]), len(result["below_quality"])))
        out.append("")
    path = ROOT / ("round%d" % result["round"]) / "SCORES.md"
    path.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(out[:20]))
    print("")
    print("wrote", path)
    return result["verdict"]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Score a panel round against the gate.")
    parser.add_argument("--round", type=int, default=1)
    args = parser.parse_args(argv)
    return 0 if write_report(score(args.round)) else 1


if __name__ == "__main__":
    sys.exit(main())
