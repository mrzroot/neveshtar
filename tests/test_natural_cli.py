"""`neveshtar natural` from the command line and on .docx files (tracked changes, comments, untouched input)."""
import json
import re
import zipfile

import pytest

from neveshtar import cli, sample

def test_cli_natural_text(tmp_path, capsys):
    p = tmp_path / "s.txt"
    p.write_text(sample.natural_lines(), encoding="utf-8")
    cli.main(["natural", str(p)])
    out = capsys.readouterr().out
    assert "not built to evade" in out and "R101" in out and "Rhythm and readability" in out


def test_cli_natural_json(tmp_path, capsys):
    p = tmp_path / "s.txt"
    p.write_text(sample.natural_lines(), encoding="utf-8")
    cli.main(["natural", str(p), "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["summary"]["natural"] >= 20 and "not built to evade" in d["notice"]
    nat = [f for f in d["findings"] if f["code"].startswith("R")]
    assert nat and all(f["question"] or f["alternatives"] for f in nat)


def test_cli_natural_skip(tmp_path, capsys):
    p = tmp_path / "s.txt"
    p.write_text(sample.natural_lines(), encoding="utf-8")
    cli.main(["natural", str(p), "--json", "--skip", "R104,R301"])
    d = json.loads(capsys.readouterr().out)
    assert not any(f["code"] in ("R104", "R301") for f in d["findings"])


def test_cli_rhythm(tmp_path, capsys):
    p = tmp_path / "s.txt"
    p.write_text(sample.natural_lines(), encoding="utf-8")
    cli.main(["rhythm", str(p), "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d["sentences"] > 20


def test_cli_natural_html(tmp_path, capsys):
    p = tmp_path / "s.txt"
    p.write_text(sample.natural_lines(), encoding="utf-8")
    o = tmp_path / "r.html"
    cli.main(["natural", str(p), "--html", str(o)])
    h = o.read_text(encoding="utf-8")
    assert 'class="nat"' in h and "not built to evade" in h and "<script src" not in h and "http" not in re.sub(r"https?://[^\"' ]*example", "", h).replace("http-equiv", "")


def test_text_input_is_not_modified_by_natural(tmp_path):
    p = tmp_path / "s.txt"
    p.write_text(sample.natural_lines(), encoding="utf-8")
    before = p.read_bytes()
    cli.main(["natural", str(p)])
    assert p.read_bytes() == before


docx_lib = pytest.importorskip("docx")


def test_docx_natural_fix_adds_tracked_changes_and_comments(tmp_path):
    src = tmp_path / "s.docx"
    sample.natural_thesis(str(src))
    out = tmp_path / "o.docx"
    cli.main(["natural", str(src), "--fix", "-o", str(out)])
    with zipfile.ZipFile(out) as z:
        doc = z.read("word/document.xml").decode("utf-8")
        com = z.read("word/comments.xml").decode("utf-8")
        ct = z.read("[Content_Types].xml").decode("utf-8")
        rels = z.read("word/_rels/document.xml.rels").decode("utf-8")
    assert "<w:del " in doc and "<w:ins " in doc or "<w:del " in doc
    assert com.count("<w:comment ") >= 10 and "commentRangeStart" in doc and "commentReference" in doc
    assert "comments+xml" in ct and "comments.xml" in rels
    ids = re.findall(r'<w:commentRangeStart w:id="(\d+)"', doc)
    assert sorted(ids) == sorted(re.findall(r'<w:comment w:id="(\d+)"', com))
    d = docx_lib.Document(str(out))
    assert len(d.paragraphs) == len(docx_lib.Document(str(src)).paragraphs)


def test_docx_reject_all_restores_original_text(tmp_path):
    src = tmp_path / "s.docx"
    sample.natural_thesis(str(src))
    out = tmp_path / "o.docx"
    cli.main(["natural", str(src), "--fix", "--mode", "all", "--with-register", "-o", str(out)])
    def txt(path, rej):
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8")
        if rej:
            xml = re.sub(r"<w:ins\b.*?</w:ins>", "", xml, flags=re.S)
            return "".join(re.findall(r"<w:(?:t|delText)[^>]*>([^<]*)</w:(?:t|delText)>", xml))
        return "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", xml))
    assert txt(out, True) == txt(src, False)


def test_docx_input_untouched_and_no_comments_flag(tmp_path):
    src = tmp_path / "s.docx"
    sample.natural_thesis(str(src))
    before = src.read_bytes()
    out = tmp_path / "o.docx"
    cli.main(["natural", str(src), "--fix", "--no-comments", "-o", str(out)])
    assert src.read_bytes() == before
    with zipfile.ZipFile(out) as z:
        assert "word/comments.xml" not in z.namelist()


def test_docx_existing_comments_part_is_extended(tmp_path):
    src = tmp_path / "s.docx"
    sample.natural_thesis(str(src))
    # inject an existing comments part
    mid = tmp_path / "m.docx"
    with zipfile.ZipFile(src) as zi, zipfile.ZipFile(mid, "w") as zo:
        for it in zi.infolist():
            zo.writestr(it, zi.read(it.filename))
        zo.writestr("word/comments.xml", '<?xml version="1.0" encoding="UTF-8"?><w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:comment w:id="1" w:author="x" w:date="2020-01-01T00:00:00Z"><w:p><w:r><w:t>old</w:t></w:r></w:p></w:comment></w:comments>')
    out = tmp_path / "o.docx"
    cli.main(["natural", str(mid), "--fix", "-o", str(out)])
    with zipfile.ZipFile(out) as z:
        com = z.read("word/comments.xml").decode("utf-8")
    assert ">old<" in com and com.count("<w:comment ") > 5
    docx_lib.Document(str(out))
