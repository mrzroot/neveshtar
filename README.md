# neveshtar

**Write the way a thesis is written.** `neveshtar` (نوشتار, "written Persian / the act of writing") is an offline, rule-based aid for the *register* of Persian academic prose. It finds
the spoken forms that creep into a draft (`می‌خوام`, `مهمه`, `خیلی`, `رو`, `اینجوری`), shows **each change with its reason and a confidence tier**, and writes the rewrite as a **Word tracked change** you accept or
reject one by one. It also checks the usual thesis conventions (first person, hedges and boosters, vague quantifiers, repeated sentence openers, very long sentences, claims with no citation) and prints
**fill-in-the-blank frames** for sections. No cloud, no model, no network, no dependencies.

![python](https://img.shields.io/badge/python-3.9%2B-blue)
![deps](https://img.shields.io/badge/dependencies-none-brightgreen)
![license](https://img.shields.io/badge/license-MIT-lightgrey)

English | [فارسی](README.fa.md)

> **What it is not.** It is not an AI author: it never writes your content, citations or numbers. It is **not designed to disguise machine-written text or to get past AI detectors**, and it does not
> claim to. It does not guarantee academic quality, and a document with zero findings can still be a weak thesis. It is a rewriting aid; you read every change.

```text
$ neveshtar chapter.docx            # a synthetic chapter from `neveshtar demo`; excerpt
neveshtar 0.1.0 · chapter.docx · 11 paragraphs · mode safe

¶3
  ! S101  ⁧به نظرم⁩  → ⁧به نظر می‌رسد⁩
  ✗ N103  ⁧مهمه⁩  →  ⁧مهم است⁩   [high · applied by this mode]
       why: The copula is written as a separate word «است» (the spoken -ه / -ست is a contraction).
  ! N101  ⁧بخاطر⁩  →  ⁧به دلیل⁩   [medium · suggestion only]
  ✗ N102  ⁧میاد⁩  →  ⁧می‌آید⁩   [high · applied by this mode]
  ! S301  ⁧قطعاً⁩  → ⁧به نظر می‌رسد / احتمالاً⁩
       why: Booster: it claims more certainty than a thesis can usually show. Say what the evidence supports, or hedge.
  · N104  ⁧بهش⁩  →  ⁧به آن⁩   [low · suggestion only]
       alternatives: ⁧به آن⁩ / ⁧به او⁩
  ! S401  ⁧بسیاری از⁩  → ⁧عدد، درصد یا منبع⁩
       why: Vague quantifier with no number or citation in the sentence. Give the count, the share, or the source.
[…]
22 error(s) (spoken forms with one written form), 15 warning(s), 9 note(s); 22 rewrite(s) would be applied in mode safe (neveshtar fix).

$ neveshtar fix chapter.docx
wrote chapter.neveshtar.docx: 22 rewrite(s) applied (tracked changes: accept / reject each one in Word (Review → Tracking)). The input file was not modified.
re-check of the copy: 0 high-confidence spoken form(s) left.
```

(Persian lines are wrapped in invisible isolate marks so they print the same in any terminal. The full, unedited output is in [docs/demo.txt](docs/demo.txt).)

## Why

A first draft is usually typed the way we speak: `داره`, `میشه`, `اونو`, `بخاطر`. Some of those have exactly one written form («دارد», «می‌شود», «آن را») and are safe to fix mechanically. Others depend on
context («ولی» → «اما» is a taste; «بره» is a verb or a lamb) and must stay *suggestions*. Machine rewriting tools blur that line; `neveshtar` keeps it visible: every change has a tier, a reason in two languages, and
`safe` mode (the default) applies only the unambiguous ones. Because the output is a tracked change, a supervisor, or you tomorrow, can see exactly what moved.

## Install

Python 3.9+, no dependencies. Tested on Linux only.

```sh
pipx install git+https://github.com/mrzroot/neveshtar        # PyPI release not published yet
uvx --from git+https://github.com/mrzroot/neveshtar neveshtar demo
pip install -e .                                             # from a clone
```

## Usage

```sh
neveshtar chapter.docx                       # = neveshtar check; exit 1 only if there is a high-confidence spoken form
neveshtar check chapter.md --strict          # exit 1 on warnings too (for scripts / CI)
neveshtar check chapter.docx --json          # machine-readable: code, text, suggestion, confidence, reason (en + fa), paragraph
neveshtar check chapter.docx --html r.html   # self-contained diff report: before / after / diff toggle, hover for the reason
neveshtar fix chapter.docx                   # chapter.neveshtar.docx, SAFE mode, Word tracked changes (author "neveshtar")
neveshtar fix chapter.docx --mode balanced   # also the likely ones (بخاطر → به دلیل)
neveshtar fix chapter.docx --clean           # apply silently instead of as tracked changes
neveshtar fix notes.md -o notes.formal.md    # .txt/.md: a plain copy, code fences untouched
neveshtar check chapter.docx --skip S101,N201 --max-words 60 --no-style
neveshtar scaffold list                      # abstract, intro, problem, significance, questions, literature, method, results, discussion, conclusion
neveshtar scaffold method --lang both        # a fill-in-the-blank frame (guidance, not generated text)
neveshtar rules                              # every category and style check
neveshtar demo                               # generate a synthetic draft and run check + fix, offline
```

Library: `from neveshtar import engine; engine.formalize("این مهمه", mode="safe")` → `'این مهم است'`.

## What it reports

| code | meaning | applied by |
|---|---|---|
| N101 | spoken word (`خیلی`, `الان`, `یه`, `تو`) | `safe` if high |
| N102 | spoken verb form (`می‌خوام`, `میاد`, `نمی‌تونن`; about 1,000 generated forms) | `safe` if high |
| N103 | spoken copula (`مهمه` → `مهم است`) | `safe` |
| N104 | object marker and clitic pronouns (`رو`, `اینو`, `ازش`) | `safe` for `رو`, `اینو`; `بهش`, `ازش` are `low` (to a thing or to a person?) |
| N105 | spoken phrase or connective (`اینجوری`, `چون که`, `ولی`) | tier varies |
| N106-N108 | slang, spoken demonstratives and plurals, spoken nouns (`خونه`, `زبون`) | tier varies |
| N201 | over-formal filler (`می‌باشد`, `گردید`, `جهت`): optional, **never** in `safe` / `balanced` | `all` |
| S101-S103 | first person «من / ما», direct address «شما» | report |
| S301, S302 | boosters (`قطعاً`, `بدون شک`) and three or more hedges piled in one sentence (after Hyland's metadiscourse) | report |
| S401 | vague quantifier (`بسیاری از`, `تعداد زیادی`) with no number or citation | report |
| S501, S601 | three sentence openers repeated; sentence longer than `--max-words` (default 45) | report |
| S701, S902 | spoken forms and formal connectives mixed in one paragraph; sentence opened by `و` / `پس` / `چون` | report |
| S801 | claim cue (`طبق تحقیقات`, `پژوهش‌ها نشان داده‌اند`) with no citation in the sentence | report |
| S901 | `!`, emoji, `؟؟` | report |

Confidence tiers: **high** = one written form, safe to apply; **medium** = very likely but context decides; **low** = a taste, or two readings. `--mode safe` applies *high*; `balanced` adds *medium*; `all` adds *low*
and the optional N201. Style findings are advice because conventions differ between universities (some require «نگارنده», others accept the passive; some accept «من»).

### How `fix` treats a `.docx`

Text is edited **inside plain text runs only**: run properties (bold, fonts) stay, and a replacement inherits the formatting of the word it replaces. Fields (SEQ, PAGE), tabs, images, content
controls and paragraphs that already hold tracked changes are skipped and reported. Direct quotes (`«…»`, `"…"`), code and URLs are never rewritten, because interview speech is allowed to be colloquial.
In tracked mode "reject all" in Word restores your original text exactly (this is a test). The input file is never overwritten, and the output is re-checked.

## Limits (please read)

- **A review aid, not an author and not an evasion tool.** It will not write your thesis, does not generate content, and is not designed to hide machine-written text or to make text pass AI detectors; I make no claim about detectors either way.
  It does not guarantee academic quality, correct citations, or that your supervisor will agree with a register choice. Zero findings does not mean good writing.
- **Rule-based means a fixed list.** About 1,300 spoken forms (mostly generated verb conjugations and a hand-written table), no morphological analyser, no context model. Forms it does not know are not flagged, and a form with two
  readings is a suggestion, not a fix. There is no accuracy benchmark; the tests check the rules, not Persian in general. Regional or dialect forms beyond the usual Tehran-style speech are mostly absent.
- **Not a spell checker or grammar checker.** It does not check spelling, agreement, or terminology; Virastyar or a human proofreader does that. Typing slips (ZWNJ, Arabic ي/ك) are [payanlint](https://github.com/mrzroot/payanlint)'s job (this tool reads Arabic ي/ك but does not fix them).
- **The style checks are Hyland-style heuristics.** A "booster" or a "hedge" is a word list, not an understanding of the claim. S401 and S801 look for a number or an author-year in the same sentence and will miss numbered citations (`[۳]`) in some forms.
- **I have not opened any output in Microsoft Word.** The tracked changes were produced from the OOXML structure, checked with python-docx and by reading the XML back (accept-all and reject-all both reproduce the expected text); Word and Word for Mac behaviour is reasoned, not observed.
- Linux only tested. Only the main body (`word/document.xml`, table cells included) is read: footnotes, endnotes, headers, footers, comments and text boxes are not analysed, and the report does not mention them. A `.doc` file must be saved as `.docx` first.
- Persian only. It does not touch English text, and it does not translate.

## Sample data

Everything in `neveshtar.sample`, the tests and the README is invented: an invented topic (sleep and concentration), invented numbers, generated at run time. No real thesis was used.

## Related

[payanlint](https://github.com/mrzroot/payanlint) (Word typing and formatting), [vazhgun](https://github.com/mrzroot/vazhgun) (RTL and bidi problems in `.docx`), [arjaa](https://github.com/mrzroot/arjaa) (citations and references).
See [NOVELTY.md](NOVELTY.md) for what already exists.

MIT · Mohammadreza Zare
