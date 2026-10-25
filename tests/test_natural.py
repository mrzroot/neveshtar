import json
import re
import zipfile

import pytest

from neveshtar import analyse as an, cli, natural, sample, render
from neveshtar.model import Para

Z = "\u200c"


def P(text, kind="p"):
    return Para(1, text, kind, "¶1")


def codes(text, kind="p"):
    return [f.code for f, _ in natural.check_paragraph(P(text, kind))]


def fixes(text):
    return {f.code: c.replacement for f, c in natural.check_paragraph(P(text)) if c is not None}


# --- R101 openers ---------------------------------------------------------------------------------------------------------
def test_r101_trim_is_high_confidence_and_applied_in_safe_mode():
    t = "در دنیای امروز، دقت جست‌وجو اهمیت دارد."
    res = an.analyse([P(t)], an.Options(natural=True, rewrites=False, style=False))
    f = [f for f in res.findings if f.code == "R101"][0]
    assert f.conf == "high" and f.applied
    from neveshtar import engine
    assert engine.apply(t, res.chosen[1]).strip() == "دقت جست‌وجو اهمیت دارد."


@pytest.mark.parametrize("t", ["همان‌طور که می‌دانیم، دقت مهم است.", "لازم به ذکر است که دقت مهم است.", "ناگفته نماند که دقت مهم است.",
                               "شایان ذکر است که دقت مهم است.", "در عصر حاضر، دقت مهم است و باید سنجیده شود."])
def test_r101_variants_found(t):
    assert "R101" in codes(t)


def test_r101_not_when_nothing_would_remain():
    assert "R101" not in codes("لازم به ذکر است.")


def test_r101_soft_opener_is_question_only():
    out = natural.check_paragraph(P("امروزه دقت جست‌وجو برای کاربران اهمیت دارد."))
    f, c = [x for x in out if x[0].code == "R101"][0]
    assert f.conf == "low" and c is None and f.ask


# --- R102 ----------------------------------------------------------------------------------------------------------------
def test_r102_role_rewrite():
    assert fixes("این روش نقش بسزایی ایفا می‌کند.")["R102"] == "نقش دارد"
    assert fixes("این روش نقش مهمی ایفا کرد.")["R102"] == "نقش داشت"


def test_r102_stock_phrase_asks():
    out = natural.check_paragraph(P("این پژوهش گام مهمی در این راه است."))
    assert any(f.code == "R102" and f.ask and c is None for f, c in out)


# --- R103 ----------------------------------------------------------------------------------------------------------------
def test_r103_double_intensifier_high():
    out = natural.check_paragraph(P("نتیجه بسیار بسیار خوب است."))
    f, c = [x for x in out if x[0].code == "R103"][0]
    assert f.conf == "high" and c.replacement == "بسیار"


def test_r103_strong_adjective_medium_not_safe():
    out = natural.check_paragraph(P("این گام بسیار حیاتی است."))
    f, c = [x for x in out if x[0].code == "R103"][0]
    assert f.conf == "medium" and c.replacement == "حیاتی"
    res = an.analyse([P("این گام بسیار حیاتی است.")], an.Options(natural=True, rewrites=False, style=False))
    assert not any(f.applied for f in res.findings)


def test_r103_plain_bisyar_is_left_alone():
    assert "R103" not in codes("نتیجه بسیار خوب بود.")


# --- R104 ----------------------------------------------------------------------------------------------------------------
def test_r104_two_connectors_back_to_back():
    assert fixes("بنابراین در نتیجه دقت بالا رفت.")["R104"].startswith("بنابراین")


def test_r104_stacked_connectors_in_paragraph():
    t = "همچنین دقت بالا رفت. علاوه بر این زمان کم شد. بنابراین رضایت زیاد شد. در نتیجه استفاده بیشتر شد. دقت ثبت شد."
    assert "R104" in codes(t)


def test_r104_single_connector_is_fine():
    assert "R104" not in codes("دقت بالا رفت. بنابراین زمان کم شد. رضایت زیاد شد. استفاده بیشتر شد.")


def test_r104_document_level_repeat():
    paras = [Para(i, "همچنین دقت بالا رفت.", "p", f"¶{i}") for i in range(1, 6)]
    assert any(f.code == "R104" for f in natural.check_document(paras))


# --- R201 / R202 / R301 / R302 -----------------------------------------------------------------------------------------
def test_r201_uniform_rhythm():
    t = " ".join(["پرسشنامه شامل بیست سؤال دربارهٔ رضایت کاربران بود."] * 2 + ["پاسخ‌دهندگان از میان دانشجویان چهار دانشکده انتخاب شدند."] * 2 + ["داده‌ها در پایان هر روز در جدول ثبت شدند."])
    assert "R201" in codes(t)


def test_r201_varied_rhythm_is_fine():
    t = "پرسشنامه بیست سؤال داشت. پاسخ‌دهندگان از میان دانشجویان چهار دانشکده که در نیمسال دوم در کتابخانهٔ مرکزی حضور داشتند و حاضر به همکاری بودند انتخاب شدند. داده‌ها ثبت شد. بعد از آن همه را دوباره بررسی کردیم تا خطا نماند. تمام."
    assert "R201" not in codes(t)


def test_r202_repeated_opener_in_document():
    paras = [P("این امر باعث افزایش رضایت می‌شود. این امر باعث کاهش زمان می‌شود. این امر باعث بهبود تجربه می‌شود.")]
    assert any(f.code == "R202" for f in natural.check_document(paras))


def test_r202_frame_across_paragraphs():
    paras = [Para(i, "یکی از مهم‌ترین عوامل در این حوزه، دسترسی است.", "p", f"¶{i}") for i in range(1, 4)]
    assert any(f.code == "R202" and "یکی از" in f.message + f.text for f in natural.check_document(paras))


def test_r301_two_triplets_in_paragraph():
    assert "R301" in codes("دقت، سرعت و رضایت سنجیده شد. هزینه، زمان و کیفیت هم سنجیده شد.")


def test_r301_single_triplet_is_fine():
    assert "R301" not in codes("دقت، سرعت و رضایت سنجیده شد.")


def test_r302_vague_generality_flagged_without_evidence():
    assert "R302" in codes("امروزه این فناوری در بسیاری از حوزه‌ها تأثیر زیادی دارد و روزبه‌روز بیشتر می‌شود.")


def test_r302_not_flagged_with_number_or_citation():
    assert "R302" not in codes("در بسیاری از حوزه‌ها، ۴۰ درصد کاربران این روش را دیده‌اند و پذیرفته‌اند.")
    assert "R302" not in codes("در بسیاری از حوزه‌ها این روش پذیرفته شده است (رضایی، ۱۳۹۸).")


# --- R401 / R501 / R601 --------------------------------------------------------------------------------------------------
def test_r401_calques():
    f = fixes("این روش بر روی داده‌ها در رابطه با دقت آزموده شد.")
    assert f["R401"] in ("روی", "درباره‌ی".replace("‌", Z))


def test_r401_we_can_conclude():
    assert fixes("ما می‌توانیم نتیجه بگیریم که روش مناسب است.")["R401"] == "می‌توان نتیجه گرفت که"


@pytest.mark.parametrize("t,new", [("روش مورد بررسی قرار گرفت.", "بررسی شد"), ("داده‌ها مورد استفاده قرار می‌گیرد.", "استفاده می‌شود"),
                                   ("نتایج مورد تحلیل قرار گرفته‌اند.", "تحلیل شده‌اند")])
def test_r501_light_verb_rewrites(t, new):
    assert fixes(t)["R501"].replace(Z, "‌") == new.replace(Z, "‌")


def test_r501_noun_pile_asks():
    out = natural.check_paragraph(P("ارزیابی، تحلیل و بهبود کیفیت خدمات هدف اصلی است."))
    assert any(f.code == "R501" and c is None for f, c in out)


def test_r601_four_passives_in_a_row():
    assert "R601" in codes("داده‌ها گردآوری شد. پرسشنامه تهیه گردید. نمونه انتخاب شد. نتایج تحلیل شد. گزارش نوشته شد.")


def test_r601_two_passives_are_fine():
    assert "R601" not in codes("داده‌ها گردآوری شد. نتایج تحلیل شد. من آن‌ها را خواندم.")


# --- safety ---------------------------------------------------------------------------------------------------------------
def test_protected_spans_are_never_touched():
    t = "در `بر روی` و «در رابطه با» و https://example.com/بر-روی آمده است."
    assert "R401" not in codes(t)


def test_code_and_heading_paragraphs_skipped():
    assert codes("در دنیای امروز، دقت مهم است.", kind="code") == []
    assert "R101" not in codes("در دنیای امروز، دقت مهم است.", kind="heading")


def test_every_natural_finding_has_reason_and_a_question_or_rewrite():
    text = sample.natural_lines()
    paras = [Para(i + 1, l, "p", f"¶{i + 1}") for i, l in enumerate(x for x in text.split("\n") if x and not x.startswith("#"))]
    n = 0
    for p in paras:
        for f, c in natural.check_paragraph(p):
            n += 1
            assert f.message and f.message_fa
            assert f.ask or f.suggestion
    assert n >= 20


def test_changes_do_not_overlap():
    paras = [Para(i + 1, l, "p", f"¶{i + 1}") for i, l in enumerate(x for x in sample.natural_lines().split("\n") if x and not x.startswith("#"))]
    res = an.analyse(paras, an.Options(natural=True, mode="all"))
    for ch in res.chosen.values():
        ch = sorted(ch, key=lambda c: c.start)
        for a, b in zip(ch, ch[1:]):
            assert a.end <= b.start


def test_safe_mode_applies_only_high_confidence():
    paras = [Para(i + 1, l, "p", f"¶{i + 1}") for i, l in enumerate(x for x in sample.natural_lines().split("\n") if x and not x.startswith("#"))]
    res = an.analyse(paras, an.Options(natural=True, mode="safe", rewrites=False, style=False))
    app = [f for f in res.findings if f.applied]
    assert app and all(f.conf == "high" for f in app)
    assert all(f.kind == "natural" for f in app)


def test_trims_leave_a_sentence_that_still_reads():
    res = an.analyse([P("در دنیای امروز، دقت مهم است. لازم به ذکر است که زمان کم شد.")], an.Options(natural=True, rewrites=False, style=False))
    from neveshtar import engine
    out = engine.apply(res.paras[0].text, res.chosen[1])
    assert "امروز" not in out and out.strip().startswith("دقت") and "ذکر" not in out


# --- rhythm report ---------------------------------------------------------------------------------------------------------
def test_rhythm_numbers():
    r = natural.rhythm([P("دقت بالا رفت. زمان کم شد. رضایت زیاد شد.")])
    assert r["sentences"] == 3 and r["words_per_sentence"]["mean"] == 3.0 and r["words_per_sentence"]["variation"] == 0.0
    assert r["opener_diversity"] == 1.0


def test_rhythm_opener_diversity_drops():
    r = natural.rhythm([P("این روش خوب است. این روش ارزان است. این روش ساده است. آن دیگری سخت بود.")])
    assert r["opener_diversity"] == 0.5 and r["top_openers"][0] == {"word": "این", "count": 3}


def test_rhythm_has_no_verdict_or_detector_wording():
    r = natural.rhythm([P("دقت بالا رفت. زمان کم شد.")])
    blob = json.dumps(r, ensure_ascii=False).lower()
    for bad in ("human-like", "ai-like", "bypass", "undetect", "verdict"):
        assert bad not in blob
    assert not any(k in r for k in ("score", "ai_probability", "human_likeness"))


def test_rhythm_empty():
    assert natural.rhythm([])["sentences"] == 0
    assert "no sentences" in natural.rhythm_text({"sentences": 0})


# --- honesty rule in every output ------------------------------------------------------------------------------------------
def _res():
    paras = [Para(i + 1, l, "p", f"¶{i + 1}") for i, l in enumerate(x for x in sample.natural_lines().split("\n") if x and not x.startswith("#"))]
    return an.analyse(paras, an.Options(natural=True))


def test_notice_in_text_json_html():
    res = _res()
    assert "not built to evade" in render.text(res, "s.txt", "safe")
    j = json.loads(render.as_json(res, "s.txt", "safe"))
    assert "not built to evade" in j["notice"] and j["notice_fa"] and "rhythm" in j
    assert "not built to evade" in render.html_report(res, "s.txt", "safe")


def test_no_detector_marketing_words_in_package():
    import pathlib
    base = pathlib.Path(natural.__file__).parent
    for f in base.glob("*.py"):
        low = f.read_text(encoding="utf-8").lower()
        for bad in ("humanizer", "undetectable", "detector score", "bypass detect", "evade detection"):
            assert bad not in low, (f.name, bad)


# --- CLI / docx ------------------------------------------------------------------------------------------------------------
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
    from neveshtar import docx as dx
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
