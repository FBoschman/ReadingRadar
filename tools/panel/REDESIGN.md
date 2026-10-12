# The redesign of the Reading Radar

Written after two panel rounds on 12 October 2026. This is the deliverable that the test was for.

## 1. The result in one table

| Measure | Round 1 (baseline) | Round 2 (after R1) |
| --- | --- | --- |
| Cells that pass | 142 of 200 | **196 of 200** |
| Wilson 95% lower bound | 0.644 | **0.9497** (gate 0.95) |
| S1 findings | 15 | **0** |
| S2 findings on a core feature | 4 | 3 |
| Features below the 7-of-8 floor | 14 | **1** (F12) |
| Features below the quality median | 16 | **1** (F12) |
| Core features at 8 of 8 | 0 | **8** |

**The gate is not met, and the margin is one cell.** The failing cells are known by name, and none of
them is a surprise: they are the learning loop and two pieces of polish.

## 2. What the first redesign (R1) changed, with proof

| Change | Proof |
| --- | --- |
| The abstract is no longer dropped at promotion, and the collection was repaired | 0 of 160 items carried an abstract before; **105 of 160** do now, all from OpenAlex |
| The discourse id is a hash of the normalised URL, and a URL or title that exists is refused | 0 duplicates in a sweep of 540 rows; the existing pair was merged |
| The journal watch pages through the journal's own total | **540 of 540 papers returned**, against 115 of 395 before |
| Corrections, errata and retractions are dropped | 19 noise titles refused in one sweep, and the validator refuses one at promotion |
| The written policy is enforced, with a named allow-list for legacy records | `validate.py` returns **0 problems** on the whole collection |
| The interface is usable by keyboard | 160 of 160 rows are `role="button"` with `tabindex`, Enter and Space, and a focus ring |
| The radar is published, so a phone can open it | https://fboschman.github.io/ReadingRadar/ |
| The queue can be read, filtered and marked | 213 candidates, 200 rendered, with search, theme, source and abstract filters |
| The wiki connection is a round trip | the note carries `radar_id` and `radar_url`; the item carries `wikiNote`, `wikiWrittenAt`, `wikiIngested`; `wiki_status.py` reads the note back |
| Triage exists and reaches the data | keep/maybe/skip in both views, an exported actions file, and `apply_actions.py` writes the status |
| A silent stop is visible | `status.json`, a banner for a failed run or stale data, and an append-only `sourceHistory.json` |
| The queue is bounded | expiry after four runs or thirty days, with the drop list written to `data/inbox/expired.json` |
| The run reports its own coverage honestly | "20 of 20 journals swept, returned 540 of 540 papers" replaces "20 of 20 swept" |

## 3. What still holds the gate

| Cell | Refused by | The panel's words | The redesign |
| --- | --- | --- | --- |
| **F12** See what the radar learned from the triage (4 of 8, median 2.5) | P1, P2, P6, P7 | "My decisions are counted but not used." "No relevance feedback reaches anything." "The radar knows what I skipped and does nothing with it." | 4.1: the decisions become proposals the reader accepts, and the harvest reads them |
| **F23** S2: promotion from the queue | P1, P2 | "A candidate I like still needs `promote.py`, a judgement file and a score." | 4.2: promote from the queue in one command |
| **F23** S2: the tab-stop count | P5 | "Four tab stops per row, 800 for the list." | 4.3: one control per row, with keys |
| **F08** S2: the selected state | P5 | "The visual mark is weaker than the semantic one." | 4.3: a border and a bolder title |
| **G3** Pooled bound 0.9497 against 0.95 | the four F12 cells | one cell short | 4.1 is the whole of it |
| **F18** S3: the note history | P4 | "A rewrite replaces the note in place." | 4.3: a change line in the note |

## 4. The new finding that the retest produced

Full recall changed the problem. With the journal watch returning 540 of 540 papers for one week, the
harvest produced **376 new candidates in a single sweep**. A queue of that size cannot be judged by one
reader, and an expiry rule that drops it would throw away good papers.

**The design conclusion: the bottleneck moved from finding papers to filtering them.** The radar does
not need a bigger queue or a faster reader. It must do more of the filtering before the queue, and only
on the reader's own terms.

### 4.1 Close the learning loop (F12) - the first priority

The panel is right that the criterion itself was wrong: a radar whose scoring is a human judgement
cannot show "the effect on scoring" as a function. The criterion is restated, and then a mechanism is
built.

**Restated criterion:** a decision by the reader becomes a *proposal* that the reader accepts in the
profile, and the next run shows the effect on what reaches the queue.

The mechanism:

1. The radar computes proposals from the triage: a theme or a source that is skipped repeatedly with no
   keep becomes a proposal to down-weight or exclude it; a theme that is kept becomes a proposal to
   widen it.
2. The reader accepts or rejects a proposal in the calibration view. An accepted proposal is written
   into `meta/profile.json` as `weights` or `exclusions`, with the date and the evidence count.
3. The harvest reads the weights: an excluded source or theme never reaches the queue, and a weighted
   theme is ranked up. The effect is a number: "this run: 376 candidates before the filter, 96 after,
   of which 41 are from themes you kept."
4. The next calibration view shows the effect against the reader's own decisions.

That single change closes the loop, answers the four refusals, and turns full recall from a problem into
a benefit.

### 4.2 Promote from the queue (F23)

The queue becomes a working surface, not a reading list:

- Mark a candidate `keep` and write one line of reason in the queue.
- The actions file carries a `promotions` block: the id, a score, the themes and the reason.
- `apply_actions.py` writes the item through the same validator as `promote.py`, so a promotion cannot
  break the schema or the policy.

The reader then never leaves the radar, and the judgement stays a judgement.

### 4.3 The small residue

| Item | Fix |
| --- | --- |
| F08 selected state | A left border and a bolder title, not a shadow alone |
| F23 tab stops | One mark control per row, with the keys k, m and s and a visible hint |
| F18 note history | `radar_updated` and a one-line change note in the note |
| F19 theme names | A quoted list instead of one comma-joined string |
| F25 log | One line per run in an index file, and the last 90 days kept |
| F25 source trend | A three-run trend per source in the Health card, read from `sourceHistory.json` |
| P5 abstract on a phone | A disclosure under 700 pixels |
| P3 evidence ceiling | A flag in the digest for an item whose reason rests on a title alone |

## 5. What would reach the gate

The arithmetic is small and exact. Four cells hold F12. If the loop is closed and F12 is accepted by
seven reviewers with a median of four, the round becomes:

- F12 accepted 7 or 8 of 8, median 4: the floor and the quality gate both pass.
- Pooled passes rise from 196 to 200: the lower bound becomes **0.9808**, above the 0.95 gate.
- The three S2 findings on core features (F23 twice, F08 once) must be closed as well, or G1b keeps the
  gate shut even with a perfect cell count.

So: **one more build round, containing 4.1, 4.2 and 4.3, is the whole distance to the gate.** A third
panel round on the frozen instruments would then confirm it.

## 6. The design principles the panel established

1. **The judgement stays human.** The radar may propose, rank and filter. It may not score on its own.
   Every item carries a `why` and a `caveat` written by a person or an agent, and the caveat is where the
   uncertainty lives.
2. **Honesty beats the appearance of coverage.** Report "returned 540 of 540" and "20 of 20 swept", and
   never let one stand for the other. Name the sample where it is a sample.
3. **The loop must close inside the tool.** A reader's decision that lands nowhere is worse than no
   decision, because it costs attention and returns nothing.
4. **The instrument stays personal.** No server, no accounts, no database, one page and a handful of
   scripts. Every addition must earn its place against that constraint.
5. **Say when it stops.** A silent stop is the failure mode of every personal tool. The banner, the
   status file and the source history exist for that reason alone.
6. **The queue is a promise.** Whatever enters it must be reachable, judgeable and either promoted or
   dropped with a written reason.

## 7. Limits, stated plainly

- **The panel is simulated.** Eight reviewers, one model, 200 correlated cells. The interval is a
  consistency check on a frozen specification, not an estimate for real researchers. The recommendation
  stands: run the same pack with three to five colleagues for 90 minutes.
- **The gate applies to the frozen feature set.** Change the features or the tasks and the number
  changes with them.
- **The owner's own session is still missing.** T01, T02, T03 and T10 require a human hand: the Monday
  review, the citation decision, the wiki decision and the phone. Everything else is a walkthrough of
  code and data.
- **The unattended push is accepted, not solved.** The risk is written into `RUNBOOK.md`, with a
  one-command revert.
- **A third round is a forecast, not a result.** The arithmetic in section 5 says the distance is small.
  Until the build exists and the panel has seen it, it is a prediction.
