<!-- Paste into AGENTS.md, CLAUDE.md, .cursorrules or your agent's rules file. Requires `pipx install git+https://github.com/mrzroot/neveshtar`. -->

## Persian (Farsi) theses: register check before you rewrite

When asked to "make this Persian text more formal / academic", do not paraphrase from scratch and do not invent content, citations or numbers.
Run the offline rule checker first and work from its report:

```sh
neveshtar chapter.docx                 # report: spoken forms (N-codes) and thesis-style findings (S-codes)
neveshtar chapter.docx --json          # machine-readable, with a reason and a confidence per change
neveshtar fix chapter.docx             # writes chapter.neveshtar.docx: safe mode, Word TRACKED CHANGES; never overwrites
neveshtar scaffold method              # a fill-in-the-blank section frame (guidance only)
```

- Apply `high` confidence rewrites; show `medium` and `low` ones to the user as suggestions and let them decide.
- Style findings (first person, vague quantifiers, claim cues without a citation) are advice that depends on the university's guide: report them, do not rewrite the argument.
- Quoted speech is left alone on purpose (interviews are legitimately colloquial).
- Do not use this to disguise machine-written text as human, and do not promise it will pass an AI detector. It is a register aid, not an author.
