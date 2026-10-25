# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-10-25

### Added
- `neveshtar natural FILE`: a **naturalness check** for stiff, template-like Persian prose (R-codes): R101 stock openers, R102 stock phrases, R103 empty intensifiers, R104 stacked connectors, R201 uniform rhythm, R202 repeated sentence frames, R301 three-item lists, R302 vague generalities, R401 English calques, R501 nominalisation, R601 passive pile-ups. Each finding has a location, a reason (English and Persian), a confidence tier and a rewrite or a question for the author.
- `safe` mode applies only unambiguous `high` trims (a stock opener, a doubled intensifier); everything else stays a suggestion. Options: `--mode`, `--skip`, `--with-register`, `--fix`, `-o`, `--clean`, `--no-comments`, `--json`, `--html`, `--strict`.
- `neveshtar rhythm FILE`: plain readability and rhythm numbers (sentence length, variation, opener diversity, connector / three-item / passive share). Descriptive only: no score, no verdict.
- `.docx` output now also writes **Word comments** that hold the open questions (new `word/comments.xml`, or extends an existing one). Not opened in Word; checked by reading the XML back.
- `neveshtar check --natural`, `neveshtar sample --natural`; JSON output carries a `notice` and `notice_fa`.
- Every naturalness output (text, JSON, HTML) carries the same notice: a writing-quality aid, no claim about AI detectors, not built to evade them or hide authorship, the author stays responsible for the text and for the university's AI-assistance rules.
- 55 new tests (99 in total).
- README (English and Persian) rewritten with a banner, contents, real example output and a codes table; `CITATION.cff`, issue and pull-request templates.

### Changed
- `.txt` / `.md`: lines starting with `#` are headings in `.txt` as well.
- `NOVELTY.md` has an addendum for the naturalness mode.

## [0.1.0] - 2026-10-25

First release.

### Added
- `neveshtar check FILE` (`.docx`, `.txt`, `.md`): spoken → written rewrites (N1xx: words, verb forms, copula, particles and clitics, connectives, slang, spoken nouns; about 1,300 forms, generated verb tables) and thesis-style checks (S1xx-S9xx: first person, hedges and boosters, vague quantifiers, repeated sentence openers, sentence length, mixed register, claim cues without a citation, exclamation marks).
- Every rewrite carries a reason (English and Persian), a confidence tier (`high`, `medium`, `low`) and, where there are several readings, the alternatives.
- `neveshtar fix FILE`: writes a **copy** with the rewrites of `--mode` (`safe` = high only, `balanced`, `all`); `.docx` output uses real Word tracked changes (`--clean` to apply silently); the input is never modified; the copy is re-checked.
- Protected spans: quotation marks and guillemets, code, URLs. Fields, tabs and images inside a paragraph are never edited.
- `--json`, `--strict`, `--skip CODES`, `--max-words`, `--html OUT` (self-contained diff report with before / after toggle).
- `neveshtar scaffold SECTION`: fill-in-the-blank frames for the usual thesis sections (guidance, not generated text).
- `neveshtar rules`, `neveshtar demo`, `neveshtar sample`.
