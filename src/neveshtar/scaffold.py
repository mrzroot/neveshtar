"""Fill-in-the-blank section scaffolds: guidance, not generated content.

Each scaffold is a list of «moves» (what a reader expects the section to do) with a sentence frame whose blanks you fill in
with your own material.  Nothing here knows your topic, and no text is ever produced for you.  Conventions differ between
fields and universities, so treat the order as a starting point.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

# key -> (title FA, title EN, [(move FA, move EN, frame FA, frame EN)], note)
SECTIONS: Dict[str, Tuple[str, str, List[Tuple[str, str, str, str]]]] = {
    "abstract": ("چکیده", "Abstract", [
        ("زمینه", "context", "[موضوع] یکی از مسائل مهم در [حوزه] است.", "[topic] is an important issue in [field]."),
        ("هدف", "aim", "هدف این پژوهش [هدف در یک جمله] است.", "The aim of this study is [aim in one sentence]."),
        ("روش", "method", "برای این منظور، [روش] بر روی [نمونه / داده‌ها، با شمار] اجرا شد.", "To this end, [method] was applied to [sample / data, with the number]."),
        ("یافته", "main finding", "نتایج نشان داد که [یافته‌ی اصلی، با عدد].", "The results showed that [main finding, with the number]."),
        ("نتیجه", "implication", "این یافته‌ها [پیامد یا کاربرد].", "These findings [implication or use]."),
    ]),
    "intro": ("مقدمه", "Introduction", [
        ("زمینه‌ی کلی", "broad context", "[حوزه] در [دوره / زمینه] اهمیت یافته است (منبع، سال).", "[field] has become important in [period / setting] (source, year)."),
        ("آنچه شناخته شده", "what is known", "پژوهش‌های پیشین [آنچه نشان داده‌اند] را نشان داده‌اند (منبع، سال؛ منبع، سال).", "Previous studies have shown [what they showed] (source, year; source, year)."),
        ("شکاف", "the gap", "با این حال، [آنچه هنوز روشن نیست].", "However, [what is still unclear]."),
        ("هدف پژوهش", "this study", "پژوهش حاضر می‌کوشد [هدف] را [با چه روشی] بررسی کند.", "The present study seeks to examine [aim] [by what means]."),
        ("ساختار", "roadmap", "در ادامه، فصل دوم [محتوا]، فصل سوم [محتوا] و فصل چهارم [محتوا] را بیان می‌کند.", "Chapter 2 presents [content], chapter 3 [content] and chapter 4 [content]."),
    ]),
    "problem": ("بیان مسئله", "Problem statement", [
        ("پدیده", "the phenomenon", "[پدیده] در [جامعه / زمینه‌ی مشخص] [چگونه دیده می‌شود، با شاهد].", "[phenomenon] appears in [specific population / setting] as [how, with evidence]."),
        ("مشکل", "why it is a problem", "این وضعیت [پیامد نامطلوب] را در پی دارد (منبع، سال).", "This situation leads to [undesirable consequence] (source, year)."),
        ("آنچه کم است", "what is missing", "تاکنون [آنچه بررسی نشده یا نتایج متناقض] .", "So far, [what has not been studied, or conflicting results]."),
        ("پرسش", "the question", "پرسش اصلی این است که [پرسش].", "The main question is [question]."),
    ]),
    "significance": ("اهمیت و ضرورت", "Significance", [
        ("نظری", "theoretical value", "از نظر نظری، این پژوهش به [چه چیز در نظریه] می‌افزاید.", "Theoretically, this study adds to [what in the theory]."),
        ("کاربردی", "practical value", "از نظر کاربردی، [چه گروهی] می‌تواند از [چه یافته‌ای] برای [چه کاری] بهره ببرد.", "Practically, [which group] can use [which finding] for [what]."),
    ]),
    "objectives": ("اهداف و پرسش‌ها", "Aims and questions", [
        ("هدف کلی", "general aim", "هدف کلی: [فعل مصدری + موضوع].", "General aim: [verb + object]."),
        ("اهداف جزئی", "specific aims", "اهداف اختصاصی: ۱) [..] ۲) [..] ۳) [..]", "Specific aims: 1) [..] 2) [..] 3) [..]"),
        ("پرسش‌ها / فرضیه‌ها", "questions / hypotheses", "فرضیه‌ی ۱: [متغیر الف] بر [متغیر ب] [جهت رابطه] تأثیر دارد.", "Hypothesis 1: [variable A] has a [direction] effect on [variable B]."),
    ]),
    "method": ("روش‌شناسی", "Methodology", [
        ("طرح", "design", "این پژوهش از نظر هدف [بنیادی / کاربردی] و از نظر روش [توصیفی / آزمایشی / ...] است.", "In aim this study is [basic / applied]; in method [descriptive / experimental / ...]."),
        ("جامعه و نمونه", "population and sample", "جامعه‌ی آماری [تعریف] و نمونه [شمار] نفر / مورد است که با روش [روش نمونه‌گیری] انتخاب شد.", "The population is [definition]; the sample is [n], chosen by [sampling method]."),
        ("ابزار", "instruments", "داده‌ها با [ابزار، سازنده، سال] گردآوری شد؛ پایایی [شاخص = عدد] بود.", "Data were collected with [instrument, author, year]; reliability was [index = value]."),
        ("روند", "procedure", "ابتدا [گام ۱]، سپس [گام ۲] و در پایان [گام ۳] انجام شد.", "First [step 1], then [step 2] and finally [step 3] were carried out."),
        ("تحلیل", "analysis", "داده‌ها با [آزمون / نرم‌افزار، نسخه] در سطح معناداری [عدد] تحلیل شد.", "Data were analysed with [test / software, version] at a significance level of [value]."),
        ("اخلاق", "ethics", "[ملاحظات اخلاقی: رضایت، ناشناس‌ماندن، شماره‌ی مصوبه].", "[ethics: consent, anonymity, approval number]."),
    ]),
    "results": ("یافته‌ها", "Results", [
        ("توصیف", "describe", "جدول [شماره] [آنچه نشان می‌دهد] را نشان می‌دهد.", "Table [n] shows [what it shows]."),
        ("آزمون", "test", "نتیجه‌ی آزمون [نام] نشان داد [یافته] ([آماره = عدد]، [p = عدد]).", "The [name] test showed [finding] ([statistic = value], [p = value])."),
        ("بدون تفسیر", "no interpretation here", "[فقط گزارش؛ تفسیر را به فصل بحث ببرید].", "[report only; move interpretation to the discussion]."),
    ]),
    "limitations": ("محدودیت‌ها", "Limitations", [
        ("محدودیت", "limitation", "این پژوهش با محدودیت [نوع] روبه‌رو بود: [توضیح].", "This study had a limitation of [type]: [explanation]."),
        ("اثر بر تعمیم", "effect on generalisation", "از این رو، تعمیم نتایج به [گروه دیگر] باید با احتیاط انجام شود.", "Therefore, generalising to [other group] should be done with caution."),
    ]),
    "conclusion": ("نتیجه‌گیری", "Conclusion", [
        ("بازگشت به پرسش", "answer the question", "در پاسخ به پرسش اصلی، [پاسخ در یک جمله].", "In answer to the main question, [one-sentence answer]."),
        ("خلاصه‌ی یافته‌ها", "summary", "مهم‌ترین یافته‌ها [۱..۳ یافته با عدد] بود.", "The most important findings were [1-3 findings with numbers]."),
        ("پیوند با پیشینه", "tie to literature", "این یافته با [پژوهش] (منبع، سال) [همسو / ناهمسو] است؛ دلیل احتمالی [..].", "This agrees / disagrees with [study] (source, year); a possible reason is [..]."),
        ("پیشنهادها", "recommendations", "پیشنهاد می‌شود [پیشنهاد کاربردی] و در پژوهش‌های آینده [پیشنهاد پژوهشی].", "It is suggested that [practical proposal]; future research could [research proposal]."),
    ]),
}

ALIASES = {"مقدمه": "intro", "بیان مسئله": "problem", "روش": "method", "روش‌شناسی": "method", "نتیجه‌گیری": "conclusion", "چکیده": "abstract",
           "introduction": "intro", "methodology": "method", "methods": "method", "problem-statement": "problem", "statement": "problem"}


def names() -> List[str]:
    return list(SECTIONS)


def get(name: str) -> str:
    key = ALIASES.get(name, name)
    if key not in SECTIONS:
        raise KeyError(name)
    return key


def render(name: str, lang: str = "fa") -> str:
    key = get(name)
    fa, en, moves = SECTIONS[key]
    out = [f"{fa} / {en}" if lang == "both" else (fa if lang == "fa" else en),
           ("هر «[...]» جای مطلب خود شماست؛ این قالب متنی تولید نمی‌کند." if lang != "en" else
            "Each «[...]» is for your own material; this scaffold writes nothing for you."), ""]
    for i, (mf, me, ff, fe) in enumerate(moves, 1):
        if lang == "fa":
            out += [f"{i}. {mf}", f"   {ff}", ""]
        elif lang == "en":
            out += [f"{i}. {me}", f"   {fe}", ""]
        else:
            out += [f"{i}. {mf} / {me}", f"   {ff}", f"   {fe}", ""]
    return "\n".join(out).rstrip() + "\n"
