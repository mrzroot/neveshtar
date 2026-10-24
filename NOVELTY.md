# Novelty check: neveshtar

Done 2026-10-25 before publishing. Wording is deliberately modest. **Persian informal-to-formal conversion is not new** (Hazm, cpia, several T5 models, academic papers on it for years);
neither are style checkers for academic English. What I found no tool for, as of October 2026, is the *combination*: an **offline, dependency-free, rule-based** converter aimed at the register of a
**Persian thesis**, where every change has a reason and a confidence tier, `safe` mode applies only the unambiguous ones, the thesis conventions (first person, hedges/boosters, vague quantifiers,
claims without a citation) are reported as advice, and the output is a **Word tracked-changes copy** you accept or reject. That is not a claim that no such tool exists; if you know one, please open an issue.

## Searches (2026-10-25)

Web searches: `Persian informal to formal text converter thesis academic register tool GitHub`; `Persian academic writing checker hedging first person thesis style tool 2026`;
`Persian colloquial to formal rule-based docx tracked changes`; `neveshtar Persian`. Earlier in the same project (2026-10-24 and 2026-10-25): GitHub repository search, npm and PyPI name lookups
for `neveshtar` (free on PyPI and npm; the GitHub name is used by unrelated repos: two blog / CMS projects).

## Closest existing work

| project | what it is | difference |
|---|---|---|
| [Hazm](https://github.com/roshan-research/hazm) `Normalizer` / informal-to-formal | Persian NLP toolkit with a rule-based informal-to-formal converter, used as a baseline in the 2024 formality-transfer paper | a string-in, string-out library: no per-change reason or confidence, no thesis-style checks, no `.docx` |
| [dhpour/cpia](https://github.com/dhpour/cpia) | Contemporary Persian Inflectional Analyzer: finite-state analyser for formal and informal words (Foma) | linguistic infrastructure, far broader coverage than neveshtar's list; not an editing tool |
| [Persian-NLP-Toolkit/Persian-text-preprocessing](https://github.com/Persian-NLP-Toolkit/Persian-text-preprocessing) (`preproc-pkg`) | normalisation, spell correction, informal-to-formal pipelines; the formal pipeline uses a transformer model | model-based and for general text; no thesis conventions, no tracked changes |
| [Sharif-SLPL/unsupervised-style-transformation](https://github.com/Sharif-SLPL/unsupervised-style-transformation), [pardissz/PersianEase](https://github.com/pardissz/PersianEase) | T5 formality style transfer (trained on product reviews / the Mohavere corpus) | a neural model that rewrites whole sentences with no per-change explanation; needs a model download |
| [mhyrzt/virastar](https://github.com/mhyrzt/virastar) | an agent skill for report-first scholarly editing of Persian theses (orthography, terminology, claims, LaTeX/XePersian) | the nearest in spirit (audit before rewrite, separates language rules from house style); it is guidance for an AI agent plus a static auditor, not a rule engine that writes tracked changes |
| [Hedging Expressions in English and Persian MA and PhD Theses](https://doi.org/10.5901/mjss.2014.v5n20p2339) (2014); [Elon.io: Academic Persian](https://elon.io/grammar/farsi/register-diglossia/c1-formal-and-literary-style/academic-persian-22) | research and teaching material on Persian hedging markers | where the style-check word lists come from conceptually; no tool |
| [ProofreaderPro formality checker](https://proofreaderpro.ai/fa/formality-checker) | web checker: informal words, contractions, direct address, exclamation marks, click-to-fix | an online English-oriented service with a Persian page; first person is deliberately not flagged; not Persian morphology |
| [balalofernandez/docx-revisions](https://github.com/balalofernandez/docx-revisions) | python-docx extension for tracked changes | a general library for the tracked-changes part; neveshtar writes its own small writer to stay dependency-free |
| TextPulse "Persian AI humanizer" and similar | services that rewrite machine-written Persian to evade detectors | **the opposite purpose.** neveshtar does not generate, paraphrase or humanise text and is not for evading detectors |

## What is new here, honestly

Probably only the packaging of known ideas: Persian thesis register rules + explainable tiers + `safe` default + tracked-changes output + offline and stdlib-only. The rules themselves are small and
hand-curated; Hazm and cpia know far more words.
