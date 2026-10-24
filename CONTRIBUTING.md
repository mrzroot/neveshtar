# Contributing

Thanks for helping! neveshtar is small on purpose: standard library only, no telemetry, no network.

```sh
git clone https://github.com/mrzroot/neveshtar && cd neveshtar
python -m venv .venv && . .venv/bin/activate
pip install -e ".[test]"
pytest
python -m neveshtar demo
```

Ground rules

- **No new runtime dependencies**, and Python 3.9 must keep working.
- Tests use synthetic, generated fixtures only (`neveshtar.sample`). Never commit a real thesis or any real person's document.
- A rewrite rule needs: the spoken form, the written form, a confidence tier, a category, and a test. `high` means the spoken form has exactly one written reading in thesis prose; if it can also be an ordinary word (like «بره»: lamb or goes), it is `medium` or `low` and is never applied in `safe` mode.
- The `.docx` writer may change text inside plain runs only, must keep run properties, must skip fields / tabs / images, and `reject all` in Word must give back the original text (see `tests/test_docx_cli.py`).
- Style rules report, they do not rewrite: conventions differ between universities.
- This tool is not for disguising machine-written text or beating AI detectors; changes in that direction will not be merged.
- Add your change to `CHANGELOG.md`.
- Found a tool that already does this? Open an issue; it will be linked in the README and NOVELTY.md.
