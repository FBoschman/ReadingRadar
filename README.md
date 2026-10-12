# Reading Radar

A weekly literature and discourse watch for Ferry Boschman (Lectoraat Urban Innovation, Windesheim),
plus a dashboard that reads the watch as a set of files.

This repository holds two things:

1. **The project kit** - the definition, the schema, the runbook, the blockers, and a full export of the
   radar in `data/`. See [The project kit](#the-project-kit) below.
2. **The dashboard app** - `index.html`, a single page that reads the export and shows the digest, the
   items, the intellectual lineage, the events, the configuration and the health of the watch.

## Quick start

1. Open `index.html` in a browser. Double-click the file, or drag it into a browser window.
2. Read the Digest section first. Then open the Health section. It tells you what to do next.

The app needs no server and no internet connection. It reads the file `data/radar-data.js`, which the
generator script builds from the `data/` folder.

If you prefer a local server, run this command in the repository folder:

```
python -m http.server 8000
```

Then open `http://localhost:8000` in a browser.

## What the app shows

| Section | Function |
| --- | --- |
| Digest | The week, the headline, the four paragraphs, and the must-read items of the last run |
| Items | All 134 items with filters for theme, status, kind, run and score, and a search box |
| Roots | The 14 lineage documents: the narrative, the strands, and every reference behind them |
| Events | Conference and call dates, with the dates that have passed |
| Config | The profile: themes, keywords, exclusions, limits, Bluesky, the vault and the 27 journal entries |
| Health | The checks, the blockers, the coverage, the triage state, and the actions to take next |

The Health section computes its checks from the data. It does not call any service.

## The state that the app reports

The export is from 12 October 2026, from a catch-up run on the reader's own machine. The app opens
with the verdict **the radar runs degraded**, because the last run of record reported two failures.

- Two sources failed in the cloud run of 12 October: Crossref and Bluesky.
- The cause is a fetch rule, not the sources: in a scheduled cloud run the fetch tool loads a URL only
  when that URL appeared word for word in a search result. No API and no constructed URL passes it.
- **The cycle now runs on this machine, where every source answers.** The catch-up run of 12 October
  swept 20 of 20 journals by ISSN, kept 28 of 209 candidates, filled 37 missing abstracts from
  OpenAlex, completed one lineage document and wrote 26 intake notes into the vault.
- Waiting for the reader: 181 candidates and 5 lineage drafts in `data/inbox/`, and 123 items with no
  triage decision.
- Still broken: the full text of ScienceDirect, Taylor and Francis and SAGE. Crossref and OpenAlex
  cover their metadata. See `BLOCKERS.md` for the current state of each blocker.

The dashboard reads the state from the data, so its Health section shows the picture of the last run
of record. After the next cycle it reads the new one.

## How to update the data

1. Run the weekly cycle in `RUNBOOK.md`.
2. Export the collections into `data/` as `<collection>/<doc_id>.json`.
3. Rebuild the bundle:

```
python tools/build_bundle.py
```

4. Open `index.html` again. The Health section shows the new state.
5. Commit and push the export.

## Files

```
index.html               the dashboard app
data/                    the export: items, lineage, lineageRequests, events, meta, MANIFEST.json
data/radar-data.js       generated bundle that the app reads (do not edit by hand)
tools/build_bundle.py    writes data/radar-data.js from data/
PROJECT.md               what the radar is for: purpose, reader, themes, scoring, exclusions
SCHEMA.md                every collection and field, with examples
RUNBOOK.md               the weekly cycle as ordered steps, with the source queries
BLOCKERS.md              what fails, why, and the workarounds that do work
```

## Limits

- The app is a reader of the export. It cannot fetch a paper, test a DOI, or update a record.
- The item dates are not always exact. 53 items carry a year or a month only, because the paper-search
  tool gives no exact day. The app marks those items.
- The lineage documents hold agent-written narrative. A hard rule applies: a strand may only name a work
  that is in the reference list of the same document. Read the `method` and `confidence` fields.
- The `why`, `caveat`, `score` and `themes` fields are written by the radar. All other metadata comes
  from a fetched source. The `source` field on each item says where.

## Text style

The interface text of the app and the text of this file use ASD-STE100 Simplified Technical English:
short sentences, one instruction at a time, the active voice, and no jargon. The text that the app shows
from the export is copied without a change.

## Licence and provenance

The interface code in `index.html` and `tools/build_bundle.py` is free to reuse. Add a licence file if
this repository becomes public.

The content is different. Item records hold bibliographic metadata from published sources, plus radar
notes. Lineage narratives come from the reference lists of the papers they describe, with the method
recorded in the same document. Check the source of an item before you cite it.

## The project kit

The original handover text of the kit:

> A self-contained handover pack so any agentic AI can take over the Reading Radar: a weekly literature
> and discourse watch for Ferry Boschman (Lectoraat Urban Innovation, Windesheim).
>
> Exported 12 October 2026 from the live dashboard at
> https://claude.ai/artifact/8EnWDz2BWtdGtGu8BqcQhJ
>
> Start here:
> 1. Read `PROJECT.md`, then `BLOCKERS.md`. The second one will save you a wasted run.
> 2. Load `data/meta/profile.json` as configuration. It is the single source of truth for themes,
>    journal watch, exclusions and the minimum score.
> 3. Read `data/meta/lastRun.json` for the previous run date and which sources worked.
> 4. Follow `RUNBOOK.md`.
>
> Porting notes:
> - The store is a document database: collection + document id + a flat JSON object. Any key-value or
>   document store works. `data/` is already laid out as `<collection>/<doc_id>.json`.
> - Writes must be idempotent and pinned to a version. Keep an equivalent of the original `if_version`
>   check, so that two runs cannot clobber each other.
> - Document ids are deterministic, so a re-run cannot create duplicates. The id rule is in `SCHEMA.md`
>   and matters more than anything else in this kit.
> - Nothing here needs an API key except the paper-search tool. See `RUNBOOK.md` step 2.
