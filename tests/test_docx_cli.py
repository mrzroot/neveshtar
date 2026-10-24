import json
import re
import zipfile

import pytest

from neveshtar import cli, docx as dx, sample

docx_lib = pytest.importorskip("docx")


def parts(path):
    with zipfile.ZipFile(path) as z:
        return z.read("word/document.xml").decode("utf-8")


def accepted(xml):      # what Word shows after "accept all"
    xml = re.sub(r"<w:del\b.*?</w:del>", "", xml, flags=re.S)
    return "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", xml))


def rejected(xml):      # what Word shows after "reject all"
    xml = re.sub(r"<w:ins\b.*?</w:ins>", "", xml, flags=re.S)
    return "".join(re.findall(r"<w:(?:t|delText)[^>]*>([^<]*)</w:(?:t|delText)>", xml))


@pytest.fixture()
def draft(tmp_path):
    return sample.thesis(str(tmp_path / "ch.docx"))


def test_tracked_changes_roundtrip(draft, tmp_path):
    out = str(tmp_path / "ch.fixed.docx")
    assert cli.main(["fix", draft, "-o", out]) == 0
    before, after = parts(draft), parts(out)
    assert "<w:ins " in after and "<w:del " in after and 'w:author="neveshtar"' in after
    assert rejected(after) == "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", before))     # reject all == original
    assert "می‌خواهم" in accepted(after) and "می‌خوام" not in accepted(after)
    ids = re.findall(r'<w:(?:ins|del) w:id="(\d+)"', after)
    assert len(ids) == len(set(ids))
    docx_lib.Document(out)                                  # python-docx can open it


def test_clean_mode_has_no_tracked_markup(draft, tmp_path):
    out = str(tmp_path / "clean.docx")
    assert cli.main(["fix", draft, "-o", out, "--clean"]) == 0
    xml = parts(out)
    assert "<w:ins " not in xml and "<w:del " not in xml and "می‌خواهم" in xml
    assert "می‌خوام" not in xml
    d = docx_lib.Document(out)
    assert any("اکنون" in p.text for p in d.paragraphs)


def test_input_is_never_modified(draft, tmp_path):
    raw = open(draft, "rb").read()
    cli.main(["fix", draft, "-o", str(tmp_path / "o.docx")])
    assert open(draft, "rb").read() == raw
    assert cli.main(["fix", draft, "-o", draft]) == 2        # refuses to overwrite


def test_formatting_of_runs_survives(draft, tmp_path):
    out = str(tmp_path / "o.docx")
    cli.main(["fix", draft, "-o", out, "--clean"])
    d = docx_lib.Document(out)
    bold = [r.text for p in d.paragraphs for r in p.runs if r.bold]
    assert any(t.startswith("نکته") for t in bold)           # the bold lead-in run is intact
    assert any(p.style.name.lower().startswith("heading") for p in d.paragraphs)


def test_field_paragraph_is_fixed_around_the_field(draft, tmp_path):
    out = str(tmp_path / "o.docx")
    cli.main(["fix", draft, "-o", out, "--clean"])
    xml = parts(out)
    assert "SEQ Figure" in xml and "fldChar" in xml
    assert "دیر می‌خوابند" in accepted(xml)


def test_safe_mode_leaves_suggestions_alone(draft, tmp_path):
    out = str(tmp_path / "o.docx")
    cli.main(["fix", draft, "-o", out, "--clean"])
    txt = accepted(parts(out))
    assert "بخاطر" in txt and "ولی" in txt           # medium/low: reported, not applied in safe mode
    out2 = str(tmp_path / "o2.docx")
    cli.main(["fix", draft, "-o", out2, "--clean", "--mode", "balanced"])
    assert "بخاطر" not in accepted(parts(out2))


def test_quote_is_not_rewritten(draft, tmp_path):
    out = str(tmp_path / "o.docx")
    cli.main(["fix", draft, "-o", out, "--clean", "--mode", "all"])
    assert "نمی‌تونم چشمامو باز کنم" in accepted(parts(out))


def test_check_exit_codes_and_json(draft, tmp_path, capsys):
    assert cli.main(["check", draft]) == 1
    capsys.readouterr()
    cli.main(["check", draft, "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["tool"] == "neveshtar" and data["summary"]["errors"] > 0
    assert all("code" in f and "message_fa" in f and "where" in f for f in data["findings"])
    clean = sample.thesis(str(tmp_path / "c.docx"), flawed=False)
    assert cli.main(["check", clean, "--no-style"]) in (0, 1)
    assert cli.main(["check", str(tmp_path / "nope.docx")]) == 2


def test_strict(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("قطعاً این روش بهترین است.\n", encoding="utf-8")
    assert cli.main(["check", str(p)]) == 0
    assert cli.main(["check", str(p), "--strict"]) == 1


def test_text_input_and_fix(tmp_path):
    p = tmp_path / "a.md"
    p.write_text("# مقدمه\n\nخیلی مهمه.\n\n```\nخیلی\n```\n\nرو میز.\n", encoding="utf-8")
    out = tmp_path / "b.md"
    assert cli.main(["fix", str(p), "-o", str(out)]) == 0
    t = out.read_text(encoding="utf-8")
    assert "بسیار مهم است." in t and "```\nخیلی\n```" in t
    assert p.read_text(encoding="utf-8").count("خیلی") == 2


def test_html_report_is_self_contained(draft, tmp_path):
    h = tmp_path / "r.html"
    cli.main(["check", draft, "--html", str(h)])
    s = h.read_text(encoding="utf-8")
    assert "<del" in s and "<ins" in s and "http://" not in s.replace("http://www.w3.org", "") and "https://" not in s
    assert "script src" not in s and "<link" not in s


def test_damaged_docx_is_reported_not_crashing(tmp_path, capsys):
    bad = tmp_path / "bad.docx"
    bad.write_bytes(b"not a zip")
    assert cli.main(["check", str(bad)]) == 2


def test_scaffold_and_rules(capsys):
    assert cli.main(["scaffold", "list"]) == 0
    assert cli.main(["scaffold", "method", "--lang", "both"]) == 0
    out = capsys.readouterr().out
    assert "[" in out and "]" in out
    assert cli.main(["scaffold", "nonsense"]) == 2
    assert cli.main(["rules"]) == 0


def test_demo_runs_offline(capsys):
    assert cli.main(["demo"]) == 0
    assert "tracked changes" in capsys.readouterr().out
