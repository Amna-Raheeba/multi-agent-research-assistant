# Research Report: explainable AI in healthcare

## Executive Summary
This report synthesises 6 sources on explainable AI in healthcare. Saliency maps alone did not measurably increase clinician trust [S1]. Pairing explanations with confidence and uncertainty improved appropriate reliance [S1]. Clinicians valued guidance on when to override the model [S1].

## Key Findings
- Saliency maps alone did not measurably increase clinician trust [S1]
- Pairing explanations with confidence and uncertainty improved appropriate reliance [S1]
- Clinicians valued guidance on when to override the model [S1]
- Saliency maps alone measurably increased clinician trust [S13]
- Trust gains appeared in both junior and senior clinicians in the sample [S13]
- Trust was self-reported in a single-site sample, and live behaviour was not observed [S13]
- Popular attribution methods often disagree on the same prediction [S2]
- Fidelity testing should accompany accuracy reporting before deployment [S2]
- Disagreement between methods is itself a useful warning signal [S2]
- High-risk clinical AI requires documented explanation methods [S4]
- Logging of outputs and human oversight are expected controls [S4]
- Explanation quality is becoming a regulatory, not only technical, concern [S4]
- Counterfactual explanations were rated more actionable than feature rankings [S3]
- Modifiable factors matter more to clinicians than static risk factors [S3]
- Prospective clinical validation is still missing [S3]
- Long generic explanations contributed to alert fatigue [S5]
- Explanations shown for every alert were eventually ignored [S5]
- Brevity and selectivity matter for explanation design [S5]

## Evidence Table
| Claim | Source | Credibility |
|---|---|---|
| Saliency maps alone did not measurably increase clinician trust | S1 | 0.84 |
| Pairing explanations with confidence and uncertainty improved appropriate reliance | S1 | 0.84 |
| Clinicians valued guidance on when to override the model | S1 | 0.84 |
| Saliency maps alone measurably increased clinician trust | S13 | 0.80 |
| Trust gains appeared in both junior and senior clinicians in the sample | S13 | 0.80 |
| Trust was self-reported in a single-site sample, and live behaviour was not observed | S13 | 0.80 |
| Popular attribution methods often disagree on the same prediction | S2 | 0.71 |
| Fidelity testing should accompany accuracy reporting before deployment | S2 | 0.71 |
| Disagreement between methods is itself a useful warning signal | S2 | 0.71 |
| High-risk clinical AI requires documented explanation methods | S4 | 0.65 |
| Logging of outputs and human oversight are expected controls | S4 | 0.65 |
| Explanation quality is becoming a regulatory, not only technical, concern | S4 | 0.65 |
| Counterfactual explanations were rated more actionable than feature rankings | S3 | 0.54 |
| Modifiable factors matter more to clinicians than static risk factors | S3 | 0.54 |
| Prospective clinical validation is still missing | S3 | 0.54 |
| Long generic explanations contributed to alert fatigue | S5 | 0.13 |
| Explanations shown for every alert were eventually ignored | S5 | 0.13 |
| Brevity and selectivity matter for explanation design | S5 | 0.13 |

## Conflicting Evidence
The evidence graph flagged 1 pair(s) of findings that pull in opposite directions on overlapping terms. Both sides are reported here; neither is silently dropped.
- "Saliency maps alone did not measurably increase clinician trust" [S1] conflicts with "Saliency maps alone measurably increased clinician trust" [S13] — shared terms: saliency, maps, measurably, clinician, trust (source credibility 0.84 vs 0.80).

## Discussion
The findings above are limited to what the collected sources state. Higher-credibility sources should weigh more heavily where findings conflict, and no claim in this report extends beyond a cited source.

## Limitations
- Source collection is limited to the searched corpus; this is not a systematic review.
- Credibility scores are a simple heuristic based on source type and age, not peer review of each paper.
- Summaries in the corpus are short, so nuance from full texts may be missing.

## References
- [S1] Lena Hartmann, Priya Nair (2024). Clinician trust in post-hoc explanations for medical imaging models. Journal of Medical AI Systems.
- [S2] Marcus Webb, Aisha Khan, Tom Becker (2023). Evaluating explanation fidelity in healthcare risk prediction. ML for Healthcare Conference.
- [S3] Sofia Rossi (2024). Counterfactual explanations for treatment decision support. arXiv preprint.
- [S4] European Health AI Working Group (2025). Regulatory expectations for explainable AI in clinical software. Policy report.
- [S5] Anonymous Clinician Blog (2022). Why our hospital turned off its sepsis alert explanations. Clinical Informatics Blog.
- [S13] Ingrid Solberg, David Osei (2025). When saliency maps are enough: trust responses in a single-site chest imaging study. Clinical AI Evaluation Workshop.
