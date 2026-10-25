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

---

# Addendum for 0.2.0: the naturalness mode (`neveshtar natural`)

Done 2026-10-25. Same modest wording as above: this is a packaging claim, not a claim that nobody has done it.

## Searches (2026-10-25)

Web searches: `Persian AI text humanizer tool Farsi humanize AI text 2026`; `github Persian AI writing patterns skill remove AI-sounding Farsi text rule-based`. I only read the search-result summaries and pages the search tool returned; I did not install or run any of the tools below, so
the comparisons describe what their own pages say, not what I measured.

## What already exists

| project | what it says it is | difference |
|---|---|---|
| [ali2000hos/persian-writing](https://github.com/ali2000hos/persian-writing) | an agent skill (Markdown instructions for an AI assistant) with 18 documented Persian "AI-tell" patterns with before/after fixes, register detection, orthography rules and a sentence-rhythm report | the closest in the *ideas* (many of the same patterns). It is a skill an AI model follows, not a standalone deterministic program that edits your Word file with tracked changes |
| [White-Wolf-dv/Natural-Writing-Skills-Claude](https://github.com/White-Wolf-dv/Natural-Writing-Skills-Claude) | Claude skills (including Persian) targeting nine AI-writing patterns from Wikipedia's "Signs of AI writing", with a 12-point self-check; says it declines to help evade detectors for dishonest purposes | prompts for a model, not a rule engine; no `.docx` output |
| [jurigis/avoid-ai-writing-multilingual](https://github.com/jurigis/avoid-ai-writing-multilingual) | multilingual skills built on documented over-represented patterns; flags and rewrites with severity | prompt-based; I did not see Persian in its description |
| obper-mcp (persian-writing-mcp, listed on Glama) | an MCP server that builds editing checklists for an agent to run | a checklist generator for a model's edit loop |
| SupWriter "Persian AI Humanizer", Evernote "Humanize Persian AI Text", Text2Human | online services that rewrite Persian text; SupWriter and Evernote describe it as natural rewriting, Text2Human's page openly markets avoiding AI detection | online paraphrasing with a model: the text is rewritten for you and sent to a service. Text2Human's detector-evasion framing is **the opposite purpose** of this tool |

## What is different here, honestly

- It is **offline, deterministic and dependency-free**: the same input gives the same findings, nothing is sent anywhere, there is no model to be wrong in a new way each run.
- It does **not rewrite your text for you** beyond a small set of unambiguous trims in `safe` mode. For everything that needs your facts it **asks a question**, because that is what makes thesis prose specific; a tool that fills in a plausible claim would be inventing content.
- Output is a **Word copy with tracked changes plus comments**, so a supervisor sees what moved.
- The report is **descriptive** (rhythm numbers, no score) and the tool makes **no claim about AI detectors**. It is not built to evade them and does not hide who wrote the text; the author stays responsible for the text and for the university's rules on AI assistance and disclosure.

What it does **not** do better: the skills above cover more of Persian orthography, RTL layout and genres than this tool; the online services produce fluent rewrites, which this tool does not attempt; and the rules here are a short hand-written list with no accuracy benchmark.
