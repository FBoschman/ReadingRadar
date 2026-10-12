# Consolidation of round 1

Round 1: 200 cells, 142 passes, pooled lower bound 0.644 against a gate of 0.95. Gate: **not yet**
(15 S1 findings, 4 S2 on core features, 14 features below the 7/8 floor, 8 core features below 8/8,
16 features below the quality median).

This file decides what the redesign does. Every finding is accepted, refused, or deferred, with a reason.

## Cluster: the abstract never reaches the reader

| Finding | Verdict | Action |
| --- | --- | --- |
| P1-2, P2-4, P3-1, P6-1, P7-3: no item stores an abstract; `ITEM_FIELDS` drops it at promotion | **Accepted, R1** | Add `abstract` and `abstractSource` to `ITEM_FIELDS`; backfill the items of 12 October from OpenAlex; extend `enrich.py` with an items mode; add a promotion guard that refuses a candidate whose field would be lost |

## Cluster: the core loop has no write path

| Finding | Verdict | Action |
| --- | --- | --- |
| P1-1, P2-5, P6-5: no triage anywhere; the calibration signal cannot exist | **Accepted, R1** | Triage controls in the item view and in the queue; the app exports an actions file; `tools/apply_actions.py` writes the status into `items/` |
| P1-3, P2-6, P3-6, P8-2, P7-6: the 213 candidates cannot be read in the radar | **Accepted, R1** | The bundle ships the candidate list; a Queue section with the same filters; the queue can be triaged directly |
| P1-4, P4-1: the wiki state of an item is invisible | **Accepted, R1** | `vault_notes.py` writes `radar_id` into the note and `wikiNote`, `wikiWrittenAt`, `wikiIngested` into the item; the item view renders them |
| P4-2, P4-5: no back-link, and `ingested` is write-only | **Accepted, R1** | Add `radar_id` and `radar_url` to the note contract; `tools/wiki_status.py` reads the intake folder and updates the item flags |
| P1-5: a roots trace cannot be asked for from the interface; P1-6, P8-4: the drafts are a count | **Accepted, R1** | The actions file also carries roots requests; the Roots section lists the drafts |

## Cluster: the retrieval promise is not kept

| Finding | Verdict | Action |
| --- | --- | --- |
| P2-1, P3-2: harvest recall is 29% because the query asks for 10 rows per journal | **Accepted, R1** | Journal rows 60 with paging; record `total-results` per journal; report "returned R of P" in `lastRun` and in the Health card |
| P2-3, P6-2: the discourse id rule is not deterministic; one article is in twice | **Accepted, R1** | Id from a hash of the normalised URL; a title check before writing; merge the existing pair |
| P2-7, P7-1: a correction notice is filed as a paper | **Accepted, R1** | Drop titles that begin with Correction, Erratum, Retraction, Author Correction, Publisher Correction |
| P3-3, P7-2, P6-3: the collection breaks its own policy | **Accepted, R1** | `validate.py` gains policy rules (score floor, caveat, date, theme codes) with an explicit legacy allow-list; the four score-2 items are marked for the reader to re-score or drop |
| P1-6, P2-2, P3-5, P5-6: search cannot reach the abstract or the themes | **Accepted, R1** | The search text gains the abstract, the theme names and the date |
| P2-4, P5-5, P7-5: no order combines recency with strength; a single-theme item is common | **Deferred, R2** | Useful, but no core cell depends on it. R1 spends its effort on the core loop |

## Cluster: the instrument cannot be reached or used by everyone

| Finding | Verdict | Action |
| --- | --- | --- |
| P5-1, P5-3: the item list is unreachable by keyboard | **Accepted, R1** | `role="button"`, `tabindex`, Enter and Space, a visible focus ring, and a selected state that is not only a shadow |
| P5-2: the radar is not published, so a phone cannot open it | **Accepted, R1** | Publish on GitHub Pages, attempted through the API, with the manual setting as the fallback |
| P5-4: no live announcement when a filter changes the count | **Accepted, R1** | `aria-live="polite"` on the count |

## Cluster: a silent stop, and a queue that grows forever

| Finding | Verdict | Action |
| --- | --- | --- |
| P8-1, P3-4, P8-7, P6-4: a failed or missed run is invisible, and a failure streak is one run deep | **Accepted, R1** | The task writes `data/meta/status.json`; the app shows a banner when the data is stale or the last run failed; `sourceHistory.json` records each run's source states |
| P8-2: nothing bounds the queue | **Accepted, R1** | Expire an unjudged candidate after 4 runs or 30 days, and record what was dropped |
| P8-3: an unattended push to a public repository | **Refused, with a reason** | The alternative is a manual merge step that the owner will skip. Instead `validate.py` runs before the commit, the commit message names the run, and the risk is written into `RUNBOOK.md` |
| P8-4: no catch-up after a long gap | **Accepted, R1** | The weekly cycle widens the window to the gap, capped at 14 days |
| P8-5, P8-6: no log rotation; the mail address and the vault path are hard-coded | **Deferred, R3** | Housekeeping. The log stays small at this rate |

## Cluster: the claim of this test

| Finding | Verdict | Action |
| --- | --- | --- |
| P6/T12: the eight reviewers are one model, so the interval is a consistency check, not a population estimate | **Accepted, R1** | Every score report states it above the table, not in a footnote. A real mini-panel of three colleagues remains the recommended confirmation |
| P6-6: `MANIFEST.json` changed meaning | **Accepted, R1** | Rename the field to `generatedAt`, keep `firstExport` |

## Findings that are noted and take no code change

| Finding | Verdict | Reason |
| --- | --- | --- |
| P4-3, P4-6: a rewritten note has no history line; the note carries codes but no theme names | Deferred, R2 | Real, but the note is regenerable and the vault is not under version control |
| P7-4: the score scale clusters high (30 items at 5) | Noted | A judgement rule: reserve 5 for what the reader would cite this month. It belongs in `PROJECT.md`, not in a validator |
| P4-6, P3-6: `xray_confidence` and `thinker_candidates` are always empty | Accepted, R1 | Fill `thinker_candidates` where the judgement pass names thinkers; otherwise remove the field and say why in `SCHEMA.md` |
| P2-2: report the two losses apart | Accepted, R1 | "Not returned by the query" and "returned but not kept" are different numbers and need different fixes |

## The R1 build list

1. `tools/radar_lib.py`: a URL hash for discourse ids; a correction-title guard.
2. `tools/harvest.py`: journal rows 60 with paging and `total-results`; drop corrections; queue expiry; the window cap.
3. `tools/enrich.py`: an `--items` mode, so a promoted item can be repaired.
4. `tools/promote.py`: keep the abstract and the provenance; refuse a candidate below the score floor.
5. `tools/apply_actions.py` (new): apply a triage and roots-request file that the app exports.
6. `tools/wiki_status.py` (new): read the intake folder and update the item flags.
7. `tools/vault_notes.py`: write `radar_id` and `radar_url` into the note, and the wiki fields into the item.
8. `tools/validate.py`: policy rules with a legacy allow-list.
9. `tools/weekly.py`: the status file, the source history, the widened window, the expiry call.
10. `tools/build_bundle.py`: ship the queue (capped), the wiki fields, the digest `related` ids, `generatedAt`, and the drafts.
11. `index.html`: keyboard and semantics; search over the abstract, themes and date; the abstract and the provenance in the item view; triage controls and the actions export; the Queue section; the wiki state; the digest links; the staleness banner; `aria-live`.
12. `data/`: backfill the abstracts; merge the duplicate pair; flag the four score-2 items; extend the digest with `related`.

## What the redesign is not

The panel did not ask for more sources, a database, an account system, a mobile app, or a cloud service.
It asked for the loop to close, the evidence to be visible, the retrieval to be honest, the interface to
be reachable, and the instrument to say when it stops. That is the shape of this redesign: small,
surgical, and all inside the existing single-file page and the existing tools.
