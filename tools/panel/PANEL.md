# The panel test of the Reading Radar

Frozen 12 October 2026. Two artefacts belong to it: `features.json` (the feature list) and
`tasks.json` (the task catalogue). Both are frozen inside a round.

## 1. Why this test exists

The Reading Radar was rebuilt on 12 October 2026, after two weeks in which the cloud task could not
reach a single source. The rebuild works, but it was never tested by the people it is meant to serve.
This panel tests the features, the redesign follows the findings, and the retest measures whether the
redesign worked.

## 2. The brief that every reviewer receives

### 2.1 What the radar is for

A weekly watch on research and professional debate across eight themes, filtered hard for one reader:
Ferry Boschman, Lectoraat Urban Innovation, Windesheim. It is not a literature database and not a news
feed. The test for any item is: **does this change what he writes, teaches or argues this month?**

The eight themes: learning ecosystems (`eco`), transdisciplinary research (`td`), complexity in
education (`cx`), design-based research (`dbr`), participatory action research (`par`), AI and
curriculum (`ai`), decolonial and epistemic justice (`dec`), professional criticality (`pc`).

The five live projects that decide usefulness: the CDC Urban Innovation course (participatory research
in public space); Digital Twin Flevoland (a regional digital twin, multi-stakeholder); the CARN 2026
workshop "Substrate Matters" (Juarrero, Levin, Tsing, Santos); papers on AI and professional
criticality; and FUNGI, the Obsidian research wiki.

Three outputs for each weekly run: scored items, each with a `why` and a `caveat`; a short digest that
names authors and links findings to the live projects; and up to five roots documents that read a
paper's intellectual ancestry off its own reference list.

Scoring: 0 to 5 on fit, novelty, usefulness for the live projects, and the critical angle of the work
itself. Keep an item at or above the profile's `minScore` (3), add one or two wildcards, and stop at
30 items for one run. The reader's own triage (`keep`, `maybe`, `skip`) is the calibration signal: the
skipped titles are the most informative part of the corpus.

### 2.2 How the radar connects to the personal wiki

The wiki is FUNGI, an Obsidian vault on the reader's own machine, with a `/ingest` pipeline.

```
radar item (score 4 or 5)
      |
      v
intake note in raw/articles        <- written by tools/vault_notes.py
      |                               frontmatter: title, source, authors, year, published,
      |                               created, venue, doi, description, intake: reading-radar,
      |                               ingested: false, radar_score, radar_themes,
      |                               xray_confidence, thinker_candidates, tags
      v
/ingest pipeline
      |
      v
wiki pages: sources, concepts, thinkers, themes, tensions
      |
      v
the wiki's thinker candidates feed the next radar run
```

Two rules are absolute, and the panel tests them: **never write or edit anything in `wiki/`**, and
never touch `raw/fieldwork` or `raw/legacy`. The radar is a contributor to the vault, never its editor.

What is connected today: the intake note is written for every item at score 4 or higher. What is not
connected yet: the radar does not show whether a note exists, the note does not say which radar record
it came from, the `ingested` flag is never updated, and nothing extracts thinker candidates. The panel
must test that claim rather than assume it.

### 2.3 The rules of the test

- The features and the tasks are frozen. A finding that asks for a different specification changes
  the feature **for the next round**; it does not change the list inside a round.
- Every finding carries a severity, the evidence, and the fix you suggest. A finding without evidence
  is not counted.
- Judge the specification that is written. If the specification itself is wrong, say so plainly: that
  is a finding of the first order.
- There is no live browser in this environment. Most testing is a cognitive walkthrough of the code and
  the data, plus scripted runs through a page model. Findings about colour, motion or real pointer
  behaviour must be marked as "needs a human eye".
## 3. The panel

| Persona | Owns the judgement of | Tasks |
| --- | --- | --- |
| P1 The owner: lector, 20 minutes each Monday | Usefulness in a real week | T01, T02, T03, T07, T10, T11, T13, T14 |
| P2 Information-retrieval researcher | Ranking, recall, precision, duplicates | T02, T05, T06, T13 |
| P3 Research librarian and review methodologist | Coverage, journal watch, citable metadata | T05, T14 |
| P4 Knowledge-management specialist | The intake contract and the wiki connection | T03, T04 |
| P5 UX and accessibility researcher | Keyboard, semantics, contrast, mobile, errors | T09, T10 |
| P6 Research-data and reproducibility reviewer | Schema, determinism, auditability, and the claim of this test | T06, T08, T12 |
| P7 Subject expert: urban innovation and education | Relevance against the five live projects | T01, T07 |
| P8 Maintenance engineer | Unattended operation for a year, and how it fails | T08, T11 |

**Honesty about the method.** All eight reviewers are simulated by one agent. That weakens the claim,
and three rules limit the damage: the harness is frozen before the baseline; each reviewer writes from
its own brief and the raw artefacts; and P6 is instructed to attack the other findings and the claim
itself (T12). Even then the interval describes the **consistency of this simulated panel**, not the
population of researchers. The recommendation stands: run the same pack with three to five real
colleagues in 90 minutes, and let the owner's session settle the taste questions.

## 4. The gate

One round is 8 reviewers × 25 features = 200 cells. A cell is "accept" or "refuse", and every cell also
carries a usefulness rating from 0 to 5.

| Gate | Requirement | Why |
| --- | --- | --- |
| G1a | No open S1 defect | A blocking defect cannot be averaged away |
| G1b | No open S2 defect on one of the eight core features | The core loop must work |
| G2a | At least 7 of 8 reviewers accept each feature | Near unanimity for every feature |
| G2b | 8 of 8 on the core features | The core loop is not negotiable |
| G3 | Wilson 95% lower bound over the 200 cells ≥ 0.95, which needs 197 passes | The requested confidence |
| G4 | Median usefulness ≥ 4 of 5 on every feature | Accepted is not the same as good |

The core features are F01, F04, F06, F08, F09, F11, F16 and F23: open the radar, browse, search,
open an item, see the abstract, triage, see the wiki state, and work the queue.

**The statistical limit, stated plainly.** A per-feature 95% interval cannot be shown with eight
reviewers: at unanimity the lower bound for one feature is 8/(8+3.84) = 0.68. G3 is therefore the
pooled bound over 200 cells, and G2b is the protection for a single feature. A per-feature interval
would need about 73 judgements for that feature.

**Convergence.** Stop when a round passes all gates and the previous round passed G1. Maximum four
rounds. If the gate does not pass, the report names the failing cells and the reason, and claims no
number it cannot support.

## 5. Severity

| Level | Meaning |
| --- | --- |
| S1 | The reader cannot do the core job, or the data is wrong in a way that misleads. Stop and fix. |
| S2 | The reader can do the job with a workaround, or a promise in the documents is not kept. |
| S3 | Friction, polish, or a wish. Does not hold the gate. |

## 6. The rounds

| Round | Content | Files |
| --- | --- | --- |
| 1 | Baseline on commit `b158a49` | `round1/P1.md` to `round1/P8.md`, `round1/MEASURE.md`, `round1/SCORES.md` |
| Consolidation | Every finding accepted or refused with a reason; the redesign set R1 | `CONSOLIDATION.md` |
| 2 | The same eight reviewers and the same tasks, on the R1 build | `round2/` |
| 3 and 4 | Only if the gate still fails | `round3/`, `round4/` |

## 7. The score sheet format

Each reviewer file ends with a ratings block that `tools/panel/score.py` reads:

```
<!-- RATINGS
F01 | yes | 5 |
F02 | no  | 2 | S2: the digest names authors but no link reaches the item
-->
```

One line for each of the 25 features: the id, `yes` or `no`, the usefulness from 0 to 5, and the reason
when the answer is `no`. The findings table above it uses the columns `# | Sev | Feature | Finding |
Evidence | Fix`.

## 8. The outcome of the two rounds

| Round | Cells | Lower bound | S1 | S2 on a core feature | Below the floor | Below the quality median | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1, baseline | 142 of 200 | 0.644 | 15 | 4 | 14 | 16 | not yet |
| 2, after R1 | **196 of 200** | **0.9497** | **0** | 3 | **1** | **1** | not yet, by one cell |

The reports are in `round1/` and `round2/`; the findings and the decisions are in `CONSOLIDATION.md`;
the redesign that the evidence calls for is in `REDESIGN.md`.

The failing cells are named: F12 (the learning loop) is refused by four reviewers, and three S2 findings
sit on core features (F23 twice, F08 once). The pooled figure misses the gate by one cell.

**What this means for the claim.** The panel has not reached 0.95, and it says so rather than rounding
up. The distance is small, it is quantified in `REDESIGN.md` section 5, and a third round on the same
frozen instruments would confirm or refute it. The recommendation from round 1 stands unchanged: three
to five real colleagues, 90 minutes, this pack, before the redesign is called finished.
