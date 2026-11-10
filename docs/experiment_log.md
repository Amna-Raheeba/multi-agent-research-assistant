# Experiment log

Short notes, written when the work happened. Failures included — they
are usually the entry that saves time later.

## 2026-11-03 — A maintenance paper outranked the healthcare papers

First version of fixture search was plain keyword overlap, and for
"explainable AI in healthcare" a predictive-maintenance paper scored
near the top because it shares the word "explainable". I added clean
concept groups and a rule that a multi-concept query needs hits in at
least two groups. Healthcare went to 5/5 on-topic sources after that.
Lesson I keep re-learning: check *why* something ranked, not just the
final list — that is what `notebooks/01_fixture_search_debug.py` is for.

## 2026-11-06 — Two sources disagreed and the report said nothing

Re-reading a generated report, I noticed S1 says saliency maps alone
did not increase clinician trust, while the newer chest-imaging study
(S13) reports the opposite — and my report listed both findings in the
same bullet list with no sign of the tension. A reader would have to
catch it themselves. That is the gap the evidence graph work came
from: first make claim↔source structure explicit, then scan it for
opposing claims instead of hoping a human notices.

## 2026-11-09 — Contradiction scan over the fixture topics

Ran the detector across all three fixture topics
(`notebooks/02_contradiction_scan.py`, output in
`results/contradiction_scan.csv`). Healthcare flags exactly the one
pair I expected — S1 vs S13 on saliency maps and clinician trust,
shared terms: saliency, maps, measurably, clinician, trust. The other
two topics flag nothing, which matches my reading of those sources.
Two misses I already know about: the detector needs 3 shared content
terms, so a paraphrased disagreement slips through, and "did not"
phrasing is doing most of the polarity work. An entailment model is
the honest upgrade; the heuristic stays until then because I can unit
test exactly when it fires.
