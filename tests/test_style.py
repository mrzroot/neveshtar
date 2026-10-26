"""Writing style checks (S-codes): sentence length, repeated words, punctuation habits; each runs on one paragraph."""
from neveshtar import analyse, model, sample


def run(text, **kw):
    p = model.Para(1, text, "body", "line 1")
    return analyse.analyse([p], analyse.Options(**kw))


def codes(text, **kw):
    return {f.code for f in run(text, **kw).findings}


def test_first_person():
    assert "S101" in codes("در این پژوهش من بررسی کردم.")
    assert "S101" not in codes("در این پژوهش، تأثیر خواب بررسی شد.")


def test_booster_and_hedge():
    assert "S301" in codes("قطعاً این روش بهترین است.")
    assert "S302" in codes("شاید احتمالاً ممکن است شاید کار کند.")      # hedges piled up


def test_vague_quantifier_needs_number():
    assert "S401" in codes("بسیاری از دانشجویان دیر می‌خوابند.")
    assert "S401" not in codes("بسیاری از دانشجویان (۴۲ درصد) دیر می‌خوابند.")
    assert "S401" not in codes("بسیاری از دانشجویان دیر می‌خوابند (احمدی، ۱۳۹۸).")


def test_claim_cue_without_citation():
    assert "S801" in codes("طبق تحقیقات، خواب مهم است.")
    assert "S801" not in codes("طبق تحقیقات احمدی (۱۳۹۸)، خواب مهم است.")


def test_repeated_openers_and_exclamation():
    assert "S501" in codes("این روش خوب است. این روش ارزان است. این روش ساده است.")
    assert "S901" in codes("نتیجه عالی بود!")


def test_long_sentence_limit_is_configurable():
    s = " ".join(["واژه"] * 50) + "."
    assert "S601" in codes(s)
    assert "S601" not in codes(s, max_words=60)


def test_skip_and_no_style():
    assert "S101" not in codes("من بررسی کردم.", skip=("S101",))
    assert not [f for f in run("من خیلی می‌خوام.", style=False).findings if f.kind == "style"]


def test_clean_sample_has_no_rewrite_errors():
    paras = [model.Para(i + 1, t.replace("|", ""), "body", f"line {i}") for i, (k, t) in enumerate(sample.CLEAN) if k != "h"]
    res = analyse.analyse(paras)
    bad = [f for f in res.findings if f.kind == "rewrite" and f.severity == "error" and "تونم" not in f.text]
    assert not bad, [(f.code, f.text) for f in bad]


def test_draft_sample_trips_every_family():
    paras = [model.Para(i + 1, t.replace("|", ""), "body", f"line {i}") for i, (k, t) in enumerate(sample.DRAFT) if k != "h"]
    got = {f.code for f in analyse.analyse(paras).findings}
    for must in ("N101", "N102", "N103", "N104", "S101", "S301", "S401", "S601", "S801", "S901"):
        assert must in got, must
