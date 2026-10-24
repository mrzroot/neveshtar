# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

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
