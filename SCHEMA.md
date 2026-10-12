# SCHEMA

Five collections. Every document is a flat JSON object (except `lineage`, which nests). Files in
`data/` are laid out as `<collection>/<doc_id>.json`.

---

## Document ids — read this first

Deterministic ids are what stop a re-run creating duplicates. Three rules:

**Papers with a DOI**

```
"doi_" + DOI, with every character outside [A-Za-z0-9_-.~:@+] replaced by "_"
```

`10.1007/s11625-026-01903-y` → `doi_10.1007_s11625-026-01903-y`

**Papers found through a semantic-search tool with no DOI**

```
"cons_" + first 12 hex characters of the tool's paper hash
```

`https://consensus.app/papers/details/4d983246661e5d249ec39031a63cece9/` → `cons_4d983246661e`

**Everything else (discourse, news, posts)**

A short readable slug of the source URL, prefixed by the source: `sg-` for ScienceGuide,
e.g. `sg-geveke-ai-cursus`.

Before writing, check the id against the existing set. If it exists, skip it — do not overwrite a
record the reader may have triaged. When the same paper arrives from several sources, keep one
document and list all sources in its `source` field, comma-separated.

---

## `items`

One paper or discourse piece. 134 documents in this export.

| Field | Type | Notes |
| --- | --- | --- |
| `kind` | string | `"paper"` or `"discourse"` |
| `title` | string | Verbatim from source |
| `authors` | string | First three surnames, comma-separated; `"X et al."` where the source gives no more. For discourse, the display name or outlet |
| `venue` | string | Journal, book, outlet or `"Bluesky"` |
| `date` | string | `YYYY-MM-DD`, or `YYYY-MM`, or `YYYY` when the source gives no more |
| `url` | string | `https://doi.org/<doi>` for papers with a DOI, else the source URL |
| `doi` | string | Bare DOI, or `""` |
| `themes` | string[] | Theme codes, see `PROJECT.md` |
| `score` | number | 0–5 |
| `why` | string | 1–2 sentences on why it matters to this reader. Agent-written |
| `caveat` | string | One limitation to check, or `""`. Agent-written |
| `lang` | string | `en`, `nl` or `de` |
| `wildcard` | boolean | `true` for the 1–2 deliberate off-pattern picks per run |
| `source` | string | e.g. `"Crossref"`, `"Journal watch: Futures"`, `"Consensus"`, `"RSS: <label>"`, `"Bluesky: @handle"`, `"Springer article listing: <journal>"` |
| `status` | string | `new`, `keep`, `maybe`, `skip`. The agent only ever writes `new` |
| `run` | string | `YYYY-MM-DD` of the run that added it |

---

## `meta/profile`

Configuration. The only document the agent edits as settings rather than output. Keep every field
you do not understand; the reader's own choices live here.

| Field | Type | Notes |
| --- | --- | --- |
| `themes` | array | `{code, name, keywords[]}`. Order is the search rotation order |
| `journalWatch` | array | `{name, issn, publisher, why, on, status?}`. `on: false` means parked, not deleted. Write a short reason into `status` whenever a sweep fails or an ISSN resolves to the wrong journal |
| `rssFeeds` | array | `{label, url, status?}`. Currently empty |
| `consensus` | object | `{on, perWeek, nextTheme, monthlyQuota, note}`. `perWeek` is a hard cap, never exceed it. Advance `nextTheme` after each run |
| `bluesky` | object | `{handle, listName, accounts[], maxAccounts, status}`. Public data only; never sign in |
| `exclusions` | string[] | Hard drops |
| `minScore` | number | Currently 3 |
| `feeds` | string[] | Human-readable list of what the reader wants watched |
| `journals` | string[] | Legacy list, superseded by `journalWatch` |
| `vault` | object | Obsidian handoff config. See `PROJECT.md` |
| `libraryProxy` | string | `windesheim.idm.oclc.org`, for the reader's own full-text access |
| `cadence` | string | Human-readable schedule |

---

## `meta/lastRun`

Written once per run, replacing the previous one.

```json
{
  "date": "2026-10-12",
  "label": "Weekly run",
  "harvested": 51,
  "unique": 34,
  "kept": 18,
  "sources": [{ "name": "Crossref topic search (8 themes)", "status": "failed - <short reason>" }],
  "notes": "Free text. Where the run went wrong and what would fix it."
}
```

`sources` must carry one line for the journal watch (e.g. `"Journal watch: 18/20 journals ok"`),
one for the paper-search tool, one for Bluesky, and one per RSS feed. `status` is `"ok"` or a short
reason. This document is the audit trail: a future run reads it to learn what not to retry.

---

## `meta/digest`

The weekly write-up, replacing the previous one.

```json
{
  "week": "Week 42 - 5 to 12 October 2026",
  "created": "2026-10-12",
  "headline": "One sentence on the week's main shift.",
  "paras": ["3-4 short paragraphs, British English, naming authors and linking to live projects."],
  "mustRead": ["doc_id", "doc_id", "doc_id"]
}
```

`mustRead` holds 3–5 ids from this run only.

---

## `events`

Conferences, calls and deadlines. 4 documents. Only add an event whose dates you actually read on
the source page.

| Field | Type |
| --- | --- |
| `title`, `url`, `location`, `note` | string |
| `start`, `end`, `deadline` | `YYYY-MM-DD` or `""` |
| `deadlineLabel` | string, e.g. `"Full application closes 17 November 2026, 14.00"` |
| `themes` | string[] |

---

## `lineageRequests`

The reader's queue. The agent reads it, never seeds it.

```json
{ "itemId": "doi_...", "doi": "10.xxxx/...", "title": "...", "requestedAt": "ISO", "status": "queued" }
```

`status`: `queued` → `done`, or `no-references` with a `note` when the source carries no reference
list. Work the queue first, then this run's must-reads that have no lineage document yet.

---

## `lineage`

One per traced paper, id = the item's id. 14 documents.

| Field | Type | Notes |
| --- | --- | --- |
| `itemId` | string | Matches `items` |
| `refs` | array | `{a, y, t, j, d}` = first-author surname, year (number or `null`), title, journal/publisher, DOI. Spellings copied exactly from the reference list |
| `strands` | array | 3–8 of `{name, kind, note, refs[]}`. `kind` is one of `root` (the older tradition it grows from), `frame`, `method`, `debate` (a controversy it enters), `context`. `refs` are zero-based indexes into `refs`, sorted by year. Unassigned refs go in a final `Other / case context` strand |
| `narrative` | string | 2–3 short paragraphs, British English, naming authors and years, describing how the thinking developed |
| `forYou` | string | One sentence linking the lineage to the reader's work |
| `absent` | string | One sentence on notable absences — PAR's Latin American roots, Global South or decolonial sources, and so on |
| `refCount` | number | What the source says the total is |
| `parsed` | number | How many were actually read |
| `median` | number | Median year |
| `tracedAt` | string | `YYYY-MM-DD` |
| `source` | string | Where the reference text came from, verbatim about the method |
| `method` | string | How strands and narrative were produced, and any merged or unparseable entries |
| `confidence` | string | `"low"` if fewer than 10 refs, else `"medium"` |

**The hard constraint:** `narrative` and `strands` may only mention works that appear in `refs`.
No reconstruction from memory, ever. If the reference list cannot be read, write
`lineageRequests/<id>` with `status: "no-references"` and move on.
