"""Thesis-style checks (S-codes).  They report; they never rewrite.

Grounding: the hedge / booster / self-mention / attitude-marker categories follow Hyland's metadiscourse model for academic
writing (Hyland 2005); the Persian word lists are hand-written for this tool and deliberately short, so every hit is
explainable.  Conventions such as «avoid من» differ between universities and fields: findings are advice, not rules.
"""
from __future__ import annotations

import re
from typing import Callable, Dict, List, Sequence, Tuple

from .engine import in_spans, protected_spans
from .lexicon import LETTER, ZW
from .model import Finding, Para

DIG = "0-9۰-۹٠-٩"
B0 = f"(?<![{LETTER}])"
B1 = f"(?![{LETTER}])"
MI = f"ن?می[{ZW} ]?"

CITE = re.compile(rf"\([^()\n]{{0,90}}?(?:[12][0-9]{{3}}|[۱-۹][۰-۹]{{3}}|[1-9][0-9]{{3}})[a-z]?\)|\[[{DIG},\s\-–]+\]|\(ر\.ک[^)]*\)")
SENT_END = re.compile(r"(?<=[.!?؟؛…])\s+|\n+")

# code -> (severity, EN, FA)
STYLE: Dict[str, Tuple[str, str, str]] = {
    "S101": ("warn", "First-person singular. Many universities ask for «نگارنده» / «پژوهشگر» or an impersonal passive; check your faculty's guide.",
             "اول‌شخصِ مفرد. بسیاری از دانشگاه‌ها «نگارنده» / «پژوهشگر» یا ساخت مجهول را می‌خواهند؛ راهنمای دانشکده‌ی خود را ببینید."),
    "S102": ("info", "«من» and «ما» in the same paragraph: pick one voice.", "«من» و «ما» در یک بند: یک لحن را برگزینید."),
    "S103": ("info", "Addressing the reader directly («شما»); thesis prose usually speaks of «خواننده» or states the point impersonally.",
             "خطاب مستقیم به خواننده («شما»)؛ در پایان‌نامه معمولاً از «خواننده» سخن می‌رود یا مطلب بی‌شخص بیان می‌شود."),
    "S301": ("warn", "Booster: it claims more certainty than a thesis can usually show. Say what the evidence supports, or hedge.",
             "واژه‌ی قطعیت‌ساز: یقینی بیش از آنچه پایان‌نامه معمولاً می‌تواند نشان دهد. بگویید شواهد چه چیزی را پشتیبانی می‌کنند، یا محتاطانه‌تر بنویسید."),
    "S302": ("warn", "Stacked hedges (3 or more in one sentence): the claim dissolves. Keep the one hedge that matches your uncertainty.",
             "احتیاط‌های انباشته (سه مورد یا بیشتر در یک جمله): ادعا حل می‌شود. فقط همان احتیاطی را نگه دارید که با عدم‌قطعیت شما می‌خواند."),
    "S401": ("warn", "Vague quantifier with no number or citation in the sentence. Give the count, the share, or the source.",
             "کمّیت‌نمای مبهم، بی‌عدد و بی‌منبع در جمله. شمار، سهم یا منبع را بیاورید."),
    "S501": ("info", "Three sentences of this paragraph open with the same word.", "سه جمله‌ی این بند با یک واژه شروع می‌شوند."),
    "S601": ("warn", "Very long sentence; the reader may lose the subject. Consider splitting at a connective.",
             "جمله‌ی بسیار بلند؛ ممکن است خواننده نهاد را گم کند. در یک حرف ربط آن را بشکنید."),
    "S701": ("warn", "Mixed register: spoken forms and formal connectives in one paragraph.",
             "ترکیب سطح زبان: صورت‌های گفتاری و حرف‌های ربطِ رسمی در یک بند."),
    "S801": ("warn", "Claim cue with no citation in the sentence («studies show …»). Name the source.",
             "نشانه‌ی ادعا بی‌ارجاع در جمله («پژوهش‌ها نشان می‌دهند …»). منبع را نام ببرید."),
    "S901": ("warn", "Exclamation mark, emoji or repeated punctuation is out of register for a thesis.",
             "علامت تعجب، شکلک یا تکرار نشانه‌گذاری در پایان‌نامه نابه‌جاست."),
    "S902": ("info", "Sentence opens with a spoken-style conjunction («و», «پس», «چون»).", "جمله با حرف ربطِ گفتاری («و»، «پس»، «چون») آغاز شده است."),
}

# -- S101 ---------------------------------------------------------------------------------------------------------------
_S101_ADVICE = [
    (re.compile(B0 + "به نظر(?:م| من)" + B1), "به نظر می‌رسد"),
    (re.compile(B0 + "به عقیده[‌ ]?ی من" + B1), "بر اساس یافته‌ها"),
    (re.compile(B0 + MI + "فکر[ ‌]?می[ ‌]?کنم" + B1), "به نظر می‌رسد"),
    (re.compile(B0 + "فکر[ ‌]?می[ ‌]?کنم" + B1), "به نظر می‌رسد"),
    (re.compile(B0 + "معتقدم" + B1), "نگارنده معتقد است"),
    (re.compile(B0 + "من" + B1), "نگارنده"),
    (re.compile(B0 + "مرا" + B1), "نگارنده را"),
    (re.compile(B0 + MI + "(?:خواه|توان|دان|ده|بین|گوی|یاب|پرداز|پندار|شمار|گیر|آور|کوش|پذیر|نویس|شناس|کن)م" + B1), "ساخت مجهول یا «نگارنده … می‌…»"),
    (re.compile(B0 + "(?:کردم|نمودم|دادم|دیدم|گرفتم|یافتم|پرداختم|نوشتم|خواندم|ساختم|رسیدم|گفتم|پنداشتم|دانستم|انتخاب کردم|بررسی کردم)" + B1), "ساخت مجهول («بررسی شد») یا «نگارنده … کرد»"),
]
_SING = re.compile(B0 + "من" + B1)
_PLUR = re.compile(B0 + "ما" + B1)
_S103 = re.compile(B0 + "(?:شما|می[ ‌]?بینید|ببینید|دیدید)" + B1)

# -- S301 / S302 --------------------------------------------------------------------------------------------------------
_BOOSTERS = [
    ("قطعاً|قطعا|به[ ‌]?طور قطع|بی[ ‌]?شک|بی[ ‌]?گمان|بدون شک|بدون تردید|بی[ ‌]?تردید|مسلماً|مسلما", "warn", "به نظر می‌رسد / احتمالاً"),
    ("بدیهی است|واضح است که|روشن است که|همگان می[ ‌]?دانند|همه می[ ‌]?دانند|همه‌ی ما می[ ‌]?دانیم", "warn", "نشان دهید یا منبع بیاورید"),
    ("ثابت می[ ‌]?(?:شود|کند)|اثبات (?:شد|می[ ‌]?کند)|ثابت (?:شد|کرد)", "warn", "نشان می‌دهد / پشتیبانی می‌کند"),
    ("صد[ ‌]?درصد|صد در صد|۱۰۰ درصد|تنها راه|بهترین روش", "warn", "نتیجه‌ی مقایسه را با عدد بیاورید"),
    ("هرگز|همیشه|همواره|هیچ[ ‌]?گاه|کاملاً|کاملا|تماماً", "info", "«اغلب»، «معمولاً» یا قید دقیق‌تر"),
]
_BOOST = [(re.compile(B0 + f"(?:{p})" + B1), sev, adv) for p, sev, adv in _BOOSTERS]
_HEDGE = re.compile(B0 + "(?:شاید|احتمالاً|احتمالا|ممکن است|می[ ‌]?تواند|به نظر می[ ‌]?رسد|تا حدی|تا حدودی|به[ ‌]?نوعی|گویا|ظاهراً|ظاهرا|کمابیش)" + B1)

# -- S401 ---------------------------------------------------------------------------------------------------------------
_VAGUE = re.compile(B0 + "(?:بسیاری از|تعداد زیادی|تعدادی از|گروه زیادی|عده[‌ ]?ای|برخی از|اکثر|اغلب|بیشتر مردم|همه[‌ ]?ی مردم|چندین|مقدار زیادی|حجم زیادی|درصد بالایی|درصد زیادی|تعداد کمی|گروهی از)" + B1)

# -- S801 ---------------------------------------------------------------------------------------------------------------
_CLAIM = re.compile(B0 + r"(?:طبق (?:تحقیقات|مطالعات|پژوهش[‌ ]?ها|آمار)|بر اساس (?:تحقیقات|مطالعات|پژوهش[‌ ]?ها|آمار)|(?:پژوهش|تحقیق|مطالعه)[‌ ]?(?:ها)?\s+(?:نشان\s+(?:داده[‌ ]?اند|می[‌ ]?دهند|می[‌ ]?دهد)|می[‌ ]?گویند)|آمار(?:ها)? نشان می[‌ ]?دهد|کارشناسان (?:معتقدند|می[‌ ]?گویند)|به اعتقاد (?:بسیاری|کارشناسان)|گفته می[‌ ]?شود|می[‌ ]?گویند|ثابت شده است|به اثبات رسیده است|اثبات شده است)")

# -- S701 ---------------------------------------------------------------------------------------------------------------
_FORMAL = re.compile(B0 + "(?:لذا|بنابراین|مذکور|پژوهش حاضر|مطالعه‌ی حاضر|به[ ‌]?منظور|بدین[ ‌]?ترتیب|علاوه بر این|چنانچه|می[ ‌]?باشد|گردید|اینجانب|نگارنده)" + B1)

_S901 = re.compile(r"[!！]+|[؟?]{2,}|\.{3,}|…|[\U0001F300-\U0001FAFF\u2600-\u27BF]")
_S902 = re.compile(r"^\s*(?:و|پس|چون|ولی|خب)\s")


def sentences(text: str) -> List[Tuple[int, int]]:
    out, pos = [], 0
    for m in SENT_END.finditer(text):
        if m.start() > pos:
            out.append((pos, m.start()))
        pos = m.end()
    if pos < len(text):
        out.append((pos, len(text)))
    return [(a, b) for a, b in out if text[a:b].strip()]


def _words(s: str) -> List[str]:
    return [w for w in re.findall(r"[^\s،,.؟?!؛;:()«»\"“”\[\]]+", s)]


def _f(code: str, para: Para, a: int, b: int, suggestion: str = "", sev: str = "") -> Finding:
    sv, en, fa = STYLE[code]
    return Finding(code, sev or sv, para.index, a, b, para.text[a:b], "style", en, fa, suggestion)


def check_paragraph(p: Para, max_words: int = 45, informal: int = 0) -> List[Finding]:
    """Style findings of one paragraph. ``informal`` = number of spoken-register changes found in it (for S701)."""
    t = p.text
    if p.kind in ("code",) or not t.strip():
        return []
    prot = protected_spans(t)
    out: List[Finding] = []

    # S101 / S102 / S103
    taken: List[Tuple[int, int]] = []
    for rx, adv in _S101_ADVICE:
        for m in rx.finditer(t):
            if in_spans(m.start(), prot) or any(a <= m.start() < b for a, b in taken):
                continue
            taken.append((m.start(), m.end()))
            out.append(_f("S101", p, m.start(), m.end(), adv))
    if _SING.search(t) and _PLUR.search(t) and not all(in_spans(m.start(), prot) for m in _SING.finditer(t)):
        m = _PLUR.search(t)
        out.append(_f("S102", p, m.start(), m.end(), "یکی از دو را در سراسر بند نگه دارید"))
    for m in _S103.finditer(t):
        if not in_spans(m.start(), prot):
            out.append(_f("S103", p, m.start(), m.end(), "خواننده / پاسخ‌دهنده"))

    sents = sentences(t)
    for a, b in sents:
        s = t[a:b]
        cited = bool(CITE.search(s))
        has_num = bool(re.search(f"[{DIG}]", s))
        # S301
        for rx, sev, adv in _BOOST:
            for m in rx.finditer(s):
                if not in_spans(a + m.start(), prot):
                    out.append(_f("S301", p, a + m.start(), a + m.end(), adv, sev))
        # S302
        hedges = [m for m in _HEDGE.finditer(s) if not in_spans(a + m.start(), prot)]
        if len(hedges) >= 3:
            out.append(_f("S302", p, a + hedges[0].start(), a + hedges[-1].end(), f"{len(hedges)} احتیاط در یک جمله"))
        # S401
        if not cited and not has_num:
            for m in _VAGUE.finditer(s):
                if not in_spans(a + m.start(), prot):
                    out.append(_f("S401", p, a + m.start(), a + m.end(), "عدد، درصد یا منبع"))
        # S801
        if not cited:
            for m in _CLAIM.finditer(s):
                if not in_spans(a + m.start(), prot):
                    out.append(_f("S801", p, a + m.start(), a + m.end(), "ارجاع درون‌متنی: (نام، سال)"))
        # S601
        n = len(_words(s))
        if n > max_words:
            out.append(_f("S601", p, a, min(b, a + 40), f"{n} واژه (حد: {max_words})"))
        # S902
        if _S902.match(s) and p.kind != "heading":
            m = _S902.match(s)
            out.append(_f("S902", p, a + m.start(), a + m.end() - 1, "با «اما» / «از این رو» یا بدون حرف ربط"))
    # S501
    keys: Dict[str, List[int]] = {}
    for a, b in sents:
        w = _words(t[a:b])
        if len(w) < 4:
            continue
        key = w[0] if len(w[0]) >= 3 else " ".join(w[:2])
        keys.setdefault(key, []).append(a)
    for key, starts in keys.items():
        if len(starts) >= 3:
            out.append(_f("S501", p, starts[2], starts[2] + len(key), f"«{key}» × {len(starts)}"))
    # S901
    for m in _S901.finditer(t):
        if not in_spans(m.start(), prot):
            out.append(_f("S901", p, m.start(), m.end(), "حذف یا جمله‌ی خبری"))
    # S701
    if informal >= 1:
        formal = [m for m in _FORMAL.finditer(t) if not in_spans(m.start(), prot)]
        if len(formal) >= 2:
            out.append(_f("S701", p, formal[0].start(), formal[0].end(), f"{informal} گفتاری + {len(formal)} رسمی"))
    out.sort(key=lambda f: (f.start, f.code))
    return out
