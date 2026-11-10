# Changelog

## [0.2.0] — 2026-11-09

### Added
- Evidence graph (`research_team/evidence_graph.py`): the analyst's evidence table is rebuilt as a claim↔source bipartite graph — source → claim `supports` edges weighted by credibility — and exported as `evidence_graph.json` alongside every CLI report.
- Contradiction detection: finding pairs from different sources with opposing polarity over shared terms are flagged, carried into the critic's critique, and reported in a new **Conflicting Evidence** section in the writer's report (the section is omitted when nothing conflicts).
- One new fixture source (S13) whose saliency-map result genuinely tensions with S1, so the healthcare demo surfaces a real in-corpus conflict.
- `notebooks/` — numbered working scripts: fixture-search debugging (`01`) and a contradiction scan across all fixture topics (`02`, writes `results/contradiction_scan.csv`).
- `docs/experiment_log.md` and this changelog.

### Changed
- CI hardening: `pythonpath = ["."]` in `pyproject.toml` plus a root `conftest.py`, so imports work under the plain `pytest` binary that GitHub Actions runs, not only under `python -m pytest`.
- Evaluation: citation coverage is now counted inside the Key Findings section only — counting cited quotes in Conflicting Evidence as well had pushed the ratio above 1.0.

## [0.1.0] — 2026-11-02

### Added
- Supervisor-orchestrated pipeline: researcher, analyst, writer, critic as separate agents over one shared state object, with an explicit state-machine router (`decide_next()`).
- Hard limits enforced by the supervisor: max iterations (10), max revisions (2), and a per-agent token/cost budget tracker.
- Mechanical critic: every Key Findings bullet must be cited, and every cited claim must exist in the analyst's evidence table.
- Offline fixture search over a small hand-written corpus, with a two-concept filter so off-topic papers cannot outrank on-topic ones on a single shared word.
- Credibility scoring heuristic (source type + age), evidence table in every report, JSON run checkpointing under `.runs/`, fixture evaluation script, and tests.
