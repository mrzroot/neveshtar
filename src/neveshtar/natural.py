"""Naturalness check (R-codes): finds stiff, template-like Persian prose and helps the author rewrite it.

What this is: a writing-quality aid made of hand-written, human-checkable rules and counts.  Every finding says where,
why it reads stiff, and either gives a concrete rewrite or asks a question that only the author can answer (a number, a
source, an observation, a decision).  ``safe`` mode applies only unambiguous trims; everything else is for the author to review.

What this is not: it does not claim, test or promise that any text passes an AI detector, it is not built to evade
detectors or to hide who wrote something, and it produces no score about detectors.  The author stays responsible for the text
and for the university's rules on AI assistance and disclosure.
"""
from __future__ import annotations

import re
import statistics
from collections import Counter
from typing import Dict, List, Optional, Sequence, Tuple

from .engine import Change, in_spans, protected_spans
from .lexicon import LETTER
from .model import Finding, Para
from .style import CITE, DIG, sentences, _words

NOTICE = ("Writing-quality aid: you review every suggestion. It makes no claim about AI detectors and is not built to evade them or to "
          "hide who wrote a text; you remain responsible for the text and for your university's rules on AI assistance and disclosure.")
NOTICE_FA = ("ابزار کمک‌نگارش: هر پیشنهاد را شما بازبینی می‌کنید. دربارهٔ آشکارسازهای هوش مصنوعی هیچ ادعایی ندارد و برای دورزدن آن‌ها "
             "یا پنهان‌کردن نویسندهٔ متن ساخته نشده است؛ مسئولیت متن و رعایت مقررات دانشگاه دربارهٔ استفاده از هوش مصنوعی و اعلام آن با شماست.")

Z = "\u200c"
B0 = f"(?<![{LETTER}])"
B1 = f"(?![{LETTER}])"

# code -> (name EN, name FA, why EN, why FA)   (same layout as lexicon.CATS so Change can look it up)
NCATS: Dict[str, Tuple[str, str, str, str]] = {
    "R101": ("filler opener", "آغازگر پرکننده",
             "A stock opener that says nothing about your topic; the sentence works without it.",
             "آغازگری قالبی که دربارهٔ موضوع شما چیزی نمی‌گوید؛ جمله بدون آن هم کامل است."),
    "R102": ("stock phrase", "عبارت قالبی",
             "A stock phrase that sounds weighty but claims nothing checkable (what effect, on what, how much?).",
             "عبارتی قالبی که سنگین به گوش می‌رسد اما ادعای سنجش‌پذیری ندارد (چه اثری، بر چه، چقدر؟)."),
    "R103": ("empty intensifier", "قید تأکید تهی",
             "An intensifier adds volume, not information; a number or a comparison does the job.",
             "قید تأکید فقط صدا را بلند می‌کند، اطلاعات نمی‌افزاید؛ عدد یا مقایسه همین کار را می‌کند."),
    "R104": ("stacked connectors", "حرف‌های ربط انباشته",
             "Sentence after sentence opens with a connector, so the links sound mechanical rather than argued.",
             "جمله‌به‌جمله با حرف ربط آغاز می‌شود و پیوندها به‌جای استدلال، مکانیکی به گوش می‌رسند."),
    "R201": ("uniform rhythm", "ریتم یکنواخت",
             "Sentences are almost the same length, which reads flat; real argument has a long sentence and a short one.",
             "جمله‌ها تقریباً هم‌اندازه‌اند و متن یکنواخت خوانده می‌شود؛ استدلال واقعی هم جملهٔ بلند دارد هم کوتاه."),
    "R202": ("repeated frame", "چارچوب تکراری",
             "The same sentence frame comes back again and again; the reader sees the template, not the content.",
             "یک چارچوب جمله بارها تکرار می‌شود؛ خواننده الگو را می‌بیند، نه محتوا را."),
    "R301": ("triplet habit", "عادت سه‌تایی",
             "Lists of exactly three items («الف، ب و ج») in many places read as a formula rather than a finding.",
             "فهرست‌های دقیقاً سه‌عضوی («الف، ب و ج») در جاهای زیاد، مثل فرمول خوانده می‌شوند نه مثل یافته."),
    "R302": ("vague generality", "کلی‌گویی",
             "A sweeping statement with no number, source, quotation or named case; the reader cannot check it.",
             "جمله‌ای کلی بی‌عدد، بی‌منبع و بی‌نمونه؛ خواننده نمی‌تواند آن را وارسی کند."),
    "R401": ("English calque", "ترجمه‌زدگی",
             "A phrase that follows English word order or idiom rather than Persian usage.",
             "عبارتی که از ترتیب یا اصطلاح انگلیسی پیروی می‌کند، نه از کاربرد فارسی."),
    "R501": ("nominalisation", "اسم‌محوری",
             "A verbal noun plus a light verb («مورد بررسی قرار گرفت») where one plain verb («بررسی شد») would do.",
             "اسم فعلی به‌همراه فعل سبک («مورد بررسی قرار گرفت») در جایی که یک فعل ساده («بررسی شد») کافی است."),
    "R601": ("passive pile-up", "انباشت مجهول",
             "Several passives in a row hide who did what. Passive is normal in a methods section; check the actor matters here.",
             "چند مجهول پشت‌سرهم معلوم نمی‌کند چه کسی چه کرده. مجهول در روش‌شناسی طبیعی است؛ ببینید اینجا فاعل مهم است یا نه."),
}
ASK: Dict[str, Tuple[str, str]] = {
    "R101": ("Start with the first sentence that says something specific to this thesis.", "از نخستین جمله‌ای شروع کنید که چیزی مشخص دربارهٔ همین پایان‌نامه می‌گوید."),
    "R102": ("What exactly does it do: which effect, on what, shown by which result or source?", "دقیقاً چه می‌کند: چه اثری، بر چه چیزی، با کدام نتیجه یا منبع؟"),
    "R103": ("How much? Give a number or a comparison, or drop the intensifier.", "چقدر؟ عدد یا مقایسه بیاورید، یا قید را بردارید."),
    "R104": ("Does each sentence really add, contrast or give a cause? Name that relation once, or let the order of sentences carry it.", "آیا هر جمله واقعاً می‌افزاید، تقابل می‌سازد یا علت می‌آورد؟ آن رابطه را یک‌بار بگویید یا بگذارید ترتیب جمله‌ها آن را برساند."),
    "R201": ("Read it aloud. Where does the idea turn? Let a short sentence carry the key point and one longer sentence hold the detail.", "بلند بخوانید. فکر کجا می‌چرخد؟ بگذارید جمله‌ای کوتاه نکتهٔ اصلی را بگوید و یک جملهٔ بلندتر جزئیات را."),
    "R202": ("Rebuild the later sentences around what is different in each: the subject, the data, your decision.", "جمله‌های بعدی را حول آنچه در هرکدام فرق دارد بازسازی کنید: موضوع، داده، تصمیم شما."),
    "R301": ("Are all three equally important? Keep the ones you can support and say which matters most.", "آیا هر سه به یک اندازه مهم‌اند؟ آن‌هایی را که می‌توانید پشتیبانی کنید نگه دارید و بگویید کدام مهم‌تر است."),
    "R302": ("Add one of: a number, a citation, your own observation or decision, a named example.", "یکی از این‌ها را بیفزایید: عدد، ارجاع، مشاهده یا تصمیم خودتان، مثالی با نام."),
    "R401": ("Say it the way you would in a Persian paper of your field.", "همان‌گونه بنویسید که در یک مقالهٔ فارسی رشتهٔ خودتان می‌نویسند."),
    "R501": ("Which of these nouns can become the verb of the sentence?", "کدام‌یک از این اسم‌ها را می‌شود فعل جمله کرد؟"),
    "R601": ("If the actor matters (you, a cited study, an instrument), name it; if not, keep the passive.", "اگر فاعل مهم است (شما، پژوهشی با ارجاع، یک ابزار) نامش را بیاورید؛ اگر نه، مجهول بماند."),
}

# -- R101: unambiguous trims, only at the start of a sentence ------------------------------------------------------------
_OPEN_TRIMS = [re.compile(p + r"[،,:]?[ \t]*") for p in [
    r"در (?:دنیا|جهان)ی?(?: [^\s،.؟!]+){0,3} امروز(?:ی)?",
    r"در عصر(?: [^\s،.؟!]+){1,2} امروز(?:ی)?",
    rf"همان[{Z} ]?(?:طور|گونه) که (?:(?:همه|همگان|ما) )?(?:می[{Z} ]?دانیم|می[{Z} ]?دانند|آگاهیم|مشخص است|واضح است|پیداست)",
    rf"(?:لازم به|شایان|درخور|قابل) (?:ذکر|توضیح|یادآوری|اشاره|توجه)(?: است| می[{Z} ]?باشد)(?: که)?",
    r"ناگفته نماند(?: که)?",
    r"باید (?:توجه|دقت) (?:داشت|کرد) که",
    rf"(?:نکته|مورد)ی? (?:مهم|قابل[{Z} ]?توجه|قابل[{Z} ]?ذکر)ی? (?:این است|آن است) که",
]]
# stock openers that need the author's decision
_OPEN_SOFT = re.compile(rf"(?:امروزه|در عصر حاضر|در دنیای مدرن|در سال[{Z} ]?های اخیر|در دهه[{Z} ]?های اخیر|با پیشرفت (?:روزافزون )?(?:علم|فناوری|تکنولوژی)(?: و (?:علم|فناوری|تکنولوژی))?)[،,]?[ \t]*")

# -- R102 / R401 / R501 rewrites -----------------------------------------------------------------------------------------
_ROLE_V = [(f"می[{Z} ]?کند", "دارد"), (f"می[{Z} ]?کنند", "دارند"), (f"می[{Z} ]?نماید", "دارد"), (f"می[{Z} ]?کرد", "داشت"), ("کردند", "داشتند"), ("کرد", "داشت"),
           (f"کرده[{Z} ]?است", "داشته است"), (f"کرده[{Z} ]?اند", "داشته‌اند"), ("خواهد کرد", "خواهد داشت"), (f"می[{Z} ]?نمایند", "دارند")]
_ROLE = re.compile(B0 + rf"نقش (?:(?:بسیار|بسی) )?(?:مهم|مهمی|بسزایی|کلیدی|حیاتی|اساسی|محوری|مؤثری|تعیین[{Z} ]?کننده[{Z}]?ای) ایفا (" + "|".join(v for v, _ in _ROLE_V) + ")" + B1)

_VN = "بررسی|مطالعه|تحلیل|ارزیابی|آزمایش|سنجش|مقایسه|استفاده|پیگیری|آزمون|تأیید|تایید|اندازه[‌ ]?گیری|ارزش[‌ ]?یابی|بحث|مرور|اجرا"
_QV = [(f"گرفت", "شد"), ("گرفتند", "شدند"), (f"می[{Z} ]?گیرد", f"می{Z}شود"), (f"می[{Z} ]?گیرند", f"می{Z}شوند"), (f"گرفته[{Z} ]?است", "شده است"),
       (f"گرفته[{Z} ]?اند", f"شده{Z}اند"), (f"گرفته بود", "شده بود"), ("خواهد گرفت", "خواهد شد"), ("خواهند گرفت", "خواهند شد")]
_QV_RX = "|".join(sorted((v for v, _ in _QV), key=len, reverse=True))
_MORED = re.compile(B0 + rf"مورد ({_VN}) قرار ({_QV_RX})" + B1)
_SORAT = re.compile(B0 + rf"({_VN}) صورت ({_QV_RX.replace('گرفت', 'گرفت').replace('می' + '[' + Z + ' ]?گیرد', 'می[' + Z + ' ]?گیرد')})" + B1)

_CALQUES = [
    ("در پایان روز", "در نهایت", ("در نهایت", "در پایان"), "medium", "«At the end of the day».", "medium"),
    ("بر روی", "روی", ("روی", "بر"), "medium", "", "medium"),
    ("در داخل", "در", ("در", "درون"), "low", "", "low"),
    (rf"با توجه به این (?:واقعیت|امر|حقیقت) که", "از آنجا که", ("از آنجا که", "چون"), "medium", "«Given the fact that».", "medium"),
    ("در رابطه با", f"درباره{Z}ی", (f"درباره{Z}ی", "در خصوص"), "medium", "«In relation to».", "medium"),
    (rf"نقش بازی می[{Z} ]?کند", "نقش دارد", ("نقش دارد", "ایفای نقش می‌کند"), "medium", "«Plays a role».", "medium"),
    (rf"ما می[{Z} ]?توانیم (?:ببینیم|مشاهده کنیم) که", "دیده می‌شود که", ("دیده می‌شود که", "مشاهده می‌شود که"), "medium", "«We can see that».", "medium"),
    (rf"ما می[{Z} ]?توانیم نتیجه بگیریم که", "می‌توان نتیجه گرفت که", ("می‌توان نتیجه گرفت که",), "medium", "«We can conclude that».", "medium"),
]
_CAL = [(re.compile(B0 + p + B1), new, alts, conf, note) for p, new, alts, conf, note, _ in _CALQUES]

# question-only stock phrases (no safe replacement)
_STOCK = re.compile(B0 + rf"(?:گام (?:مهم|بزرگ|اساسی)ی|حائز اهمیت(?: (?:فراوان|بسیار|ویژه))?|بستر مناسبی(?: را)? فراهم|افق[{Z} ]?های (?:جدید|تازه)ی?|تحول(?:ی)? (?:عظیم|شگرف|بنیادین)|طیف گسترده[{Z} ]?ای از|گستره[{Z} ]?ی وسیعی از|نقش (?:مهم|کلیدی|مؤثر|بسزا)ی? (?:در [^،.؟!]{{2,40}}? )?(?:دارد|دارند)|از اهمیت (?:ویژه|بالا|فراوان|زیاد)ی? برخوردار(?: است| بود| هستند| می[{Z} ]?باشد)?)" + B1)
_STRONG_ADJ = "ضروری|حیاتی|بنیادین|بی[‌ ]?نظیر|منحصر[‌ ]?به[‌ ]?فرد|عظیم|شگرف|اساسی|کلیدی|ضروری"
_INTENS = rf"(?:بسیار|خیلی|فوق[{Z} ]?العاده|بی[{Z} ]?نهایت|به[{Z} ]?شدت|کاملاً|کاملا)"
_INT_STRONG = re.compile(B0 + rf"{_INTENS} ({_STRONG_ADJ})" + B1)
_INT_DOUBLE = re.compile(B0 + rf"(بسیار|خیلی|فوق[{Z} ]?العاده|بی[{Z} ]?نهایت) (?:بسیار|خیلی)" + B1)
_INT_ANY = re.compile(B0 + _INTENS + B1)

# -- R104 connectors -------------------------------------------------------------------------------------------------------
_CONN_LIST = ["علاوه بر این", "علاوه بر آن", "افزون بر این", "افزون بر آن", "از سوی دیگر", "از طرف دیگر", "از طرفی", "در نتیجه", "بنابراین", "از این رو", "به همین دلیل",
              "به همین ترتیب", "در این راستا", "در همین راستا", "به[‌ ]?طور کلی", "در مجموع", "در کل", "همچنین", "به[‌ ]?علاوه", "لازم به ذکر است", "شایان ذکر است", "شایان توجه است", "لذا"]
_CONN = "(?:" + "|".join(sorted(_CONN_LIST, key=len, reverse=True)) + ")"
_CONN_START = re.compile(rf"^\s*({_CONN})(?![{LETTER}])")
_CONN_PAIR = re.compile(rf"^(\s*)({_CONN})[،,]?[ \t]+({_CONN})(?![{LETTER}])[،,]?[ \t]*")

# -- R202 templates ------------------------------------------------------------------------------------------------------
_TEMPLATES = [
    ("«یکی از مهم‌ترین … است»", re.compile(rf"یکی از (?:مهم[{Z}]?ترین|اصلی[{Z}]?ترین|بزرگ[{Z}]?ترین|مؤثرترین|رایج[{Z}]?ترین|کلیدی[{Z}]?ترین)[^.؟!]{{0,70}}? (?:است|می[{Z} ]?باشد|بود)")),
    ("«نقش … دارد»", re.compile(rf"نقش (?:مهم|مهمی|کلیدی|بسزایی|اساسی|مؤثری)[^.؟!]{{0,40}}?(?:دارد|دارند|ایفا)")),
    ("«این امر باعث … می‌شود»", re.compile(rf"این (?:امر|موضوع|مسئله|مساله) (?:باعث|سبب|موجب)[^.؟!]{{0,60}}?(?:می[{Z} ]?شود|شد)")),
    ("«می‌تواند … باشد/شود»", re.compile(rf"می[{Z} ]?تواند[^.؟!]{{0,60}}?(?:باشد|شود|کند)")),
]
# -- R302 cues -----------------------------------------------------------------------------------------------------------
_VAGUE_CUE = re.compile(B0 + rf"(?:در دنیای امروز|امروزه|روز[{Z} ]?به[{Z} ]?روز|به[{Z} ]?طور فزاینده[{Z}]?ای|نقش (?:مهم|مؤثر|بسزا|کلیدی)ی?|اهمیت (?:زیاد|فراوان|روزافزون|بالا)ی?|بسیار مهم|تأثیر (?:زیاد|فراوان|بسزا)ی?|یکی از مهم[{Z}]?ترین|به[{Z} ]?طور قابل[{Z}]?توجه[{Z}]?ی|در بسیاری از (?:موارد|حوزه[{Z}]?ها|زمینه[{Z}]?ها)|در (?:همه|تمام)[{Z}]?ی? (?:حوزه[{Z}]?ها|زمینه[{Z}]?ها|جنبه[{Z}]?ها)|جنبه[{Z}]?های (?:مختلف|گوناگون))")
# -- R301 triplets -------------------------------------------------------------------------------------------------------
_ITEM = rf"[^\s،,.؛:;()\[\]«»\"{DIG}]+(?: [^\s،,.؛:;()\[\]«»\"{DIG}]+){{0,2}}"
_TRIPLET = re.compile(rf"(?<![{LETTER}،])(?<!، )({_ITEM})، ({_ITEM}) و ({_ITEM})(?![،{LETTER}])")
# -- R601 passive --------------------------------------------------------------------------------------------------------
_PASSIVE = re.compile(B0 + rf"(?:می[{Z} ]?شود|می[{Z} ]?شوند|شد|شدند|شده[{Z} ]?(?:است|اند)|شده بود|گردید|گردیدند|می[{Z} ]?گردد|می[{Z} ]?گردند|گردیده(?: است)?|خواهد شد|خواهند شد|قرار (?:گرفت|گرفتند|می[{Z} ]?گیرد|می[{Z} ]?گیرند|گرفته[{Z} ]?است)|صورت (?:گرفت|می[{Z} ]?گیرد|گرفته[{Z} ]?است))" + B1)
# -- R501 noun pile --------------------------------------------------------------------------------------------------------
_NOUNS = re.compile(B0 + rf"(?:بررسی|تحلیل|ارزیابی|استفاده|بهره[{Z} ]?گیری|دستیابی|انجام|ایجاد|توسعه|پیاده[{Z} ]?سازی|اجرا|بهبود|تعیین|شناسایی|تبیین|تدوین|تحقق|اعمال|ارائه|اتخاذ|اقدام|مبادرت)" + B1)

_C = {"high": "warn", "medium": "warn", "low": "info"}


def _mk(code: str, p: Para, a: int, b: int, conf: str, sug: str = "", alts: Sequence[str] = (), note: str = "", ask: bool = True) -> Tuple[Finding, Optional[Change]]:
    en, fa = NCATS[code][2], NCATS[code][3]
    q = ASK[code] if ask else ("", "")
    f = Finding(code, _C[conf], p.index, a, b, p.text[a:b], "natural", en + ((" " + note) if note else ""), fa, sug, conf, False, list(alts) or None,
                q[0], q[1])
    ch = None
    if sug != "" or (conf == "high" and code == "R101"):
        ch = Change(a, b, p.text[a:b], sug, tuple(alts) or (sug,), conf, code, note, p.text[a:b])
    return f, ch


def check_paragraph(p: Para) -> List[Tuple[Finding, Optional[Change]]]:
    t = p.text
    if p.kind in ("code",) or not t.strip():
        return []
    prot = protected_spans(t)
    out: List[Tuple[Finding, Optional[Change]]] = []
    sents = sentences(t)
    taken: List[Tuple[int, int]] = []

    def free(a: int, b: int) -> bool:
        return not any(x < b and a < y for x, y in taken)

    def add(code, a, b, conf, sug="", alts=(), note="", ask=True, change=True):
        if in_spans(a, prot) or not free(a, b):
            return
        f, ch = _mk(code, p, a, b, conf, sug, alts, note, ask)
        taken.append((a, b))
        out.append((f, ch if change else None))

    for a0, b in sents:
        s = t[a0:b]
        lead = len(s) - len(s.lstrip())
        a = a0 + lead
        s2 = s.lstrip()
        if p.kind == "heading":
            continue
        # R104 connector pairs at the start (drop the second one)
        mp = _CONN_PAIR.match(s)
        if mp and mp.group(2) != mp.group(3):
            add("R104", a0 + mp.start(2), a0 + mp.end(), "medium", mp.group(2) + "، ", (mp.group(2) + "، ",), "Two connectors back to back; keep the one that names the relation.")
        # R101 trims
        for rx in _OPEN_TRIMS:
            m = rx.match(s2)
            if m and len(_words(s2[m.end():])) >= 3:
                add("R101", a, a + m.end(), "high", "", ("",))
                break
        else:
            m = _OPEN_SOFT.match(s2)
            if m and len(_words(s2[m.end():])) >= 3:
                add("R101", a, a + m.end(), "low", "", (), "", True, False)
    # R102 / R401 / R501 rewrites
    for m in _ROLE.finditer(t):
        verb = next(new for v, new in _ROLE_V if re.fullmatch(v, m.group(1)))
        add("R102", m.start(), m.end(), "medium", "نقش " + verb, ("نقش " + verb,), "«played a significant role» keeps the claim but drops the empty adjective.")
    for m in _STOCK.finditer(t):
        if re.match(r"از اهمیت", m.group(0)):
            add("R102", m.start(), m.end(), "low", "مهم است" if re.search("برخوردار(?: است| می[‌ ]?باشد)?$", m.group(0)) else "", ("مهم است",) if re.search("برخوردار(?: است| می[‌ ]?باشد)?$", m.group(0)) else (), "", True)
        else:
            add("R102", m.start(), m.end(), "low", "", (), "", True, False)
    for m in _MORED.finditer(t):
        verb = next(new for v, new in _QV if re.fullmatch(v, m.group(2)))
        add("R501", m.start(), m.end(), "medium", f"{m.group(1)} {verb}", (f"{m.group(1)} {verb}",))
    for m in _SORAT.finditer(t):
        verb = next(new for v, new in _QV if re.fullmatch(v, m.group(2)))
        add("R501", m.start(), m.end(), "medium", f"{m.group(1)} {verb}", (f"{m.group(1)} {verb}",))
    for rx, new, alts, conf, note in _CAL:
        for m in rx.finditer(t):
            add("R401", m.start(), m.end(), conf, new, alts, note)
    # R103
    for m in _INT_DOUBLE.finditer(t):
        add("R103", m.start(), m.end(), "high", m.group(1), (m.group(1),), "Doubled intensifier.", False)
    for m in _INT_STRONG.finditer(t):
        add("R103", m.start(), m.end(), "medium", m.group(1), (m.group(1),), "The adjective is already strong.")
    ints = [m for m in _INT_ANY.finditer(t) if not in_spans(m.start(), prot)]
    if len(ints) >= 3 and len(ints) * 2 >= max(1, len(sents)):
        m = ints[2]
        add("R103", m.start(), m.end(), "low", "", (), f"{len(ints)} intensifiers in one paragraph.", True, False)
    # R104: stacked connectors in the paragraph
    cs = []
    for a0, b in sents:
        m = _CONN_START.match(t[a0:b])
        if m:
            cs.append((a0 + m.start(1), a0 + m.end(1), m.group(1)))
    if len(sents) >= 4 and len(cs) >= 3 and len(cs) * 2 >= len(sents):
        a, b, _ = cs[1]
        add("R104", a, b, "medium", "", (), f"{len(cs)} of {len(sents)} sentences open with a connector.", True, False)
    seen: Dict[str, int] = {}
    for a, b, w in cs:
        k = re.sub(r"[\u200c ]", "", w)
        seen[k] = seen.get(k, 0) + 1
        if seen[k] == 2:
            add("R104", a, b, "medium", "", (), f"«{w}» opens two sentences of this paragraph.", True, False)
    # R201 uniform rhythm
    ls = [len(_words(t[a:b])) for a, b in sents]
    if len(ls) >= 5 and statistics.mean(ls) >= 8:
        mean = statistics.mean(ls)
        if statistics.pstdev(ls) / mean < 0.2 and max(ls) - min(ls) <= max(6, 0.35 * mean):
            add("R201", sents[0][0], min(sents[0][1], sents[0][0] + 30), "low", "", (), f"{len(ls)} sentences of {min(ls)}–{max(ls)} words.", True, False)
    # R301 triplets
    sp = [(m.start(), m.end()) for m in CITE.finditer(t)]
    trip = [m for m in _TRIPLET.finditer(t) if not in_spans(m.start(), prot) and not in_spans(m.start(), sp)]
    if len(trip) >= 2:
        m = trip[1]
        add("R301", m.start(), m.end(), "low", "", (), f"{len(trip)} three-item lists in one paragraph.", True, False)
    # R302 vague generalities
    for a0, b in sents:
        s = t[a0:b]
        if p.kind == "heading" or len(_words(s)) < 7:
            continue
        if CITE.search(s) or re.search(f"[{DIG}]", s) or re.search(r"[A-Za-z]{3}", s) or "«" in s or "“" in s:
            continue
        for m in _VAGUE_CUE.finditer(s):
            if free(a0 + m.start(), a0 + m.end()):
                add("R302", a0 + m.start(), a0 + m.end(), "low", "", (), "", True, False)
                break
    # R601 passive pile-up
    flags = []
    for a0, b in sents:
        ms = [m for m in _PASSIVE.finditer(t[a0:b]) if not in_spans(a0 + m.start(), prot)]
        flags.append((a0, b, ms))
        if len(ms) >= 3:
            add("R601", a0 + ms[0].start(), a0 + ms[-1].end(), "low", "", (), f"{len(ms)} passives in one sentence.", True, False)
    run = 0
    for i, (a0, b, ms) in enumerate(flags):
        run = run + 1 if ms else 0
        if run == 4:
            f0 = flags[i - 3]
            add("R601", f0[0] + f0[2][0].start(), f0[0] + f0[2][0].end(), "low", "", (), "4 passive sentences in a row.", True, False)
    # R501 noun pile
    for a0, b in sents:
        ms = [m for m in _NOUNS.finditer(t[a0:b]) if not in_spans(a0 + m.start(), prot)]
        if len(ms) >= 3 and p.kind != "heading":
            add("R501", a0 + ms[0].start(), a0 + ms[-1].end(), "low", "", (), f"{len(ms)} verbal nouns in one sentence.", True, False)
    out.sort(key=lambda x: (x[0].start, x[0].code))
    return out


def check_document(paras: Sequence[Para]) -> List[Finding]:
    """Patterns that only show over several paragraphs: repeated sentence frames and openers, connector repeats, triplet share."""
    out: List[Finding] = []
    flat = []                                   # (para, a, b, text)
    for p in paras:
        if p.kind in ("code", "heading") or not p.text.strip():
            continue
        for a, b in sentences(p.text):
            flat.append((p, a, b, p.text[a:b]))
    # repeated opener bigram in a window of 8 sentences
    ops = []
    for p, a, b, s in flat:
        w = _words(s)
        ops.append(" ".join(w[:2]) if len(w) >= 5 else None)
    done = set()
    for i, k in enumerate(ops):
        if not k or k in done:
            continue
        idx = [j for j in range(max(0, i - 7), min(len(ops), i + 8)) if ops[j] == k]
        win = [j for j in idx if idx[0] <= j < idx[0] + 8]
        if len(win) >= 3:
            j = win[2]
            p, a, b, s = flat[j]
            done.add(k)
            f, _ = _mk("R202", p, a, a + len(k.split()[0]) + 1 + len(k.split()[1]), "low", "", (), f"«{k}» opens {len(win)} sentences within 8.")
            out.append(f)
    # sentence frames
    full = [(p, a, b, s) for p, a, b, s in flat]
    for name, rx in _TEMPLATES:
        hits = [(p, a + m.start(), a + m.end()) for p, a, b, s in full for m in rx.finditer(s) if not in_spans(a + m.start(), protected_spans(p.text))]
        if len(hits) >= 3:
            p, a, b = hits[2]
            f, _ = _mk("R202", p, a, b, "low", "", (), f"Frame {name} appears {len(hits)} times in this text.")
            out.append(f)
    # the same connector over and over, across paragraphs
    cnt: Dict[str, List[Tuple[Para, int, int]]] = {}
    for p, a, b, s in flat:
        m = _CONN_START.match(s)
        if m:
            k = re.sub(r"[\u200c ]", "", m.group(1))
            cnt.setdefault(k, []).append((p, a + m.start(1), a + m.end(1)))
    for k, hs in cnt.items():
        if len(hs) >= 4:
            p, a, b = hs[3]
            f, _ = _mk("R104", p, a, b, "medium", "", (), f"«{p.text[a:b]}» opens {len(hs)} sentences in this text.")
            out.append(f)
    # triplet share over the whole text
    trips = []
    nsent_t = 0
    for p, a, b, s in flat:
        sp = [(m.start(), m.end()) for m in CITE.finditer(p.text)]
        ms = [m for m in _TRIPLET.finditer(s) if not any(x <= a + m.start() < y for x, y in sp)]
        if ms:
            nsent_t += 1
            trips.append((p, a + ms[0].start(), a + ms[0].end()))
    if len(flat) >= 8 and len(trips) >= 4 and nsent_t / len(flat) >= 0.3:
        p, a, b = trips[3]
        f, _ = _mk("R301", p, a, b, "low", "", (), f"{nsent_t} of {len(flat)} sentences contain a three-item list.")
        out.append(f)
    # drop duplicates (same code and place)
    seen, res = set(), []
    for f in out:
        k = (f.para, f.start, f.code)
        if k not in seen:
            seen.add(k)
            res.append(f)
    return res


# -- the plain rhythm / readability report --------------------------------------------------------------------------------------
def rhythm(paras: Sequence[Para]) -> dict:
    """Descriptive numbers about sentence length and openers. Not a score and not a verdict; it only makes patterns visible."""
    lens, openers, conn, trip, pas, nums, cited = [], [], 0, 0, 0, 0, 0
    per_para = []
    for p in paras:
        if p.kind in ("code", "heading") or not p.text.strip():
            continue
        pl = []
        sp = [(m.start(), m.end()) for m in CITE.finditer(p.text)]
        for a, b in sentences(p.text):
            s = p.text[a:b]
            w = _words(s)
            if not w:
                continue
            lens.append(len(w))
            pl.append(len(w))
            openers.append(w[0])
            if _CONN_START.match(s):
                conn += 1
            if any(not any(x <= a + m.start() < y for x, y in sp) for m in _TRIPLET.finditer(s)):
                trip += 1
            if _PASSIVE.search(s):
                pas += 1
            if re.search(f"[{DIG}]", s):
                nums += 1
            if CITE.search(s):
                cited += 1
        if len(pl) >= 3:
            m = statistics.mean(pl)
            per_para.append({"paragraph": p.index, "where": p.where, "sentences": len(pl), "mean": round(m, 1),
                             "variation": round(statistics.pstdev(pl) / m, 2) if m else 0.0})
    n = len(lens)
    if n == 0:
        return {"sentences": 0}
    mean = statistics.mean(lens)
    bins = Counter(min(l // 5, 8) for l in lens)
    top = Counter(openers).most_common(5)
    pct = lambda k: round(100 * k / n)
    return {"sentences": n, "words_per_sentence": {"mean": round(mean, 1), "median": statistics.median(lens), "min": min(lens), "max": max(lens),
                                                    "stdev": round(statistics.pstdev(lens), 1), "variation": round(statistics.pstdev(lens) / mean, 2)},
            "histogram": {f"{i * 5}-{i * 5 + 4}" if i < 8 else "40+": bins.get(i, 0) for i in range(9)},
            "opener_diversity": round(len(set(openers)) / n, 2), "top_openers": [{"word": w, "count": c} for w, c in top],
            "connector_openers_pct": pct(conn), "three_item_lists_pct": pct(trip), "passive_sentences_pct": pct(pas),
            "sentences_with_number_pct": pct(nums), "sentences_with_citation_pct": pct(cited),
            "paragraphs": per_para,
            "note": "Descriptive numbers to make patterns visible. They are not a score, say nothing about who wrote the text, and are not a prediction of how any detector would react."}


def rhythm_text(r: dict) -> str:
    if not r.get("sentences"):
        return "rhythm: no sentences.\n"
    w = r["words_per_sentence"]
    mx = max(r["histogram"].values()) or 1
    bars = "▁▂▃▄▅▆▇█"
    spark = "".join(bars[min(7, round(7 * v / mx))] if v else "·" for v in r["histogram"].values())
    lines = ["Rhythm and readability (plain numbers, not a score)", "",
             f"  sentences            {r['sentences']}",
             f"  words per sentence   mean {w['mean']} · median {w['median']} · min {w['min']} · max {w['max']} · variation {w['variation']}",
             f"  length histogram     {spark}   (0-4, 5-9 … 40+ words)",
             f"  opener diversity     {r['opener_diversity']}   (1.0 = every sentence opens differently)",
             "  common openers       " + ", ".join(f"{o['word']}×{o['count']}" for o in r["top_openers"]),
             f"  connector openers    {r['connector_openers_pct']}% of sentences",
             f"  three-item lists     {r['three_item_lists_pct']}% of sentences",
             f"  passive sentences    {r['passive_sentences_pct']}% of sentences",
             f"  with a number        {r['sentences_with_number_pct']}%   with a citation {r['sentences_with_citation_pct']}%"]
    flat = [q for q in r["paragraphs"] if q["variation"] < 0.2]
    if flat:
        lines.append("  flat paragraphs      " + ", ".join(f"{q['where']} (variation {q['variation']})" for q in flat[:6]))
    lines += ["", "  " + r["note"], ""]
    return "\n".join(lines)
