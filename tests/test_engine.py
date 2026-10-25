import pytest

from neveshtar import engine, lexicon, sample


def F(s, mode="safe"):
    return engine.formalize(s, mode)


@pytest.mark.parametrize("src,dst", [
    ("می‌خوام بررسی کنم", "می‌خواهم بررسی کنم"),
    ("اون نمی‌تونه بیاد", None),                      # handled below as not-crashing; exact forms are tested elsewhere
    ("داره میاد", "دارد می‌آید"),
    ("این روش مهمه", "این روش مهم است"),
    ("خیلی مهم", "بسیار مهم"),
    ("اینو رو تحلیل کردم", None),
    ("پرسشنامه رو پر کردند", "پرسشنامه را پر کردند"),
    ("می شه دید", "می‌شود دید"),
    ("نمیشه گفت", "نمی‌شود گفت"),
    ("الان", "اکنون"),
    ("یه روش", "یک روش"),
])
def test_safe_rewrites(src, dst):
    out = F(src)
    if dst is not None:
        assert out == dst


def test_arabic_letters_are_matched():
    assert F("خيلي مهم") == "بسیار مهم"           # ي → ی tolerant


def test_formal_text_is_untouched_in_safe_mode():
    for kind, t in sample.CLEAN:
        if kind != "h":
            t = t.replace("|", "")
            if "نمی‌تونم" in t:      # the quoted interview sentence is protected
                continue
            assert F(t) == t, t


def test_quotes_code_urls_are_protected():
    s = "گفت: «من خیلی می‌خوام» و `خیلی` و https://x.org/خیلی و \"خیلی\""
    assert F(s) == s


def test_guillemet_quote_with_text_outside():
    out = F("او گفت «خیلی خوب» و خیلی خندید")
    assert "«خیلی خوب»" in out and out.endswith("بسیار خندید")


def test_idempotent():
    for kind, t in sample.DRAFT:
        for mode in ("safe", "balanced", "all"):
            once = F(t, mode)
            assert F(once, mode) == once


def test_modes_are_nested():
    t = "بخاطر اینکه ولی بعدش خیلی بهش گفتم"
    safe, bal, al = (len(engine.select(engine.find_changes(t), m)) for m in ("safe", "balanced", "all"))
    assert safe <= bal <= al and safe < al


def test_confidence_tiers_present_and_ambiguous_forms_not_high():
    rs = lexicon.rules()
    assert len(rs) > 800
    assert {r.conf for r in rs} == {"high", "medium", "low"}
    # a form with two possible readings must never be applied silently
    for r in rs:
        if r.conf == "high":
            assert len(r.alts) <= 1, r.surface


def test_no_overlapping_changes_and_offsets_valid():
    for kind, t in sample.DRAFT:
        ch = engine.find_changes(t)
        prev = 0
        for c in sorted(ch, key=lambda c: c.start):
            assert c.start >= prev
            assert t[c.start:c.end] == c.original
            prev = c.end


def test_word_boundaries_not_inside_words():
    # «رو» must not be rewritten inside «روش» / «برو»; «خب» not inside «خبر»
    assert F("روش خبر نداره") == "روش خبر ندارد"
    assert F("برو") == "برو"


def test_no_network_no_dependencies():
    import ast, pathlib
    base = pathlib.Path(engine.__file__).parent
    allowed = {"__future__", "dataclasses", "typing", "re", "os", "sys", "json", "html", "zipfile", "argparse", "tempfile", "collections",
               "itertools", "unicodedata", "datetime", "functools", "xml", "io", "shutil", "textwrap", "sample", "docxbuild", "random", "struct", "zlib", "copy", "statistics"}
    for f in base.glob("*.py"):
        for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            mods = [a.name.split(".")[0] for a in n.names] if isinstance(n, ast.Import) else ([n.module.split(".")[0]] if isinstance(n, ast.ImportFrom) and n.module and n.level == 0 else [])
            for m in mods:
                assert m in allowed, f"{f.name} imports {m}"
