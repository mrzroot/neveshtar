"""Output: terminal text, JSON, and a self-contained HTML report (no external files, no network)."""
from __future__ import annotations

import html
import json
from collections import Counter
from typing import Dict, List, Optional, Sequence

from . import __version__
from .analyse import Result
from .engine import Change
from .lexicon import CATS
from .model import Finding, Para
from .style import STYLE

RLI, PDI = "\u2067", "\u2069"
SEV_MARK = {"error": "✗", "warn": "!", "info": "·"}


def _b(s: str) -> str:
    return f"{RLI}{s}{PDI}"


def summary(res: Result) -> Dict[str, int]:
    c = Counter(f.severity for f in res.findings)
    return {"errors": c["error"], "warnings": c["warn"], "notes": c["info"],
            "rewrites": sum(1 for f in res.findings if f.kind == "rewrite"),
            "applied": sum(1 for f in res.findings if f.kind in ("rewrite", "natural") and f.applied),
            "style": sum(1 for f in res.findings if f.kind == "style"),
            "natural": sum(1 for f in res.findings if f.kind == "natural")}


def as_json(res: Result, name: str, mode: str) -> str:
    extra = {}
    if res.natural:
        from . import natural as nat
        extra = {"notice": nat.NOTICE, "notice_fa": nat.NOTICE_FA, "rhythm": nat.rhythm(res.paras)}
    return json.dumps({"tool": "neveshtar", "version": __version__, "file": name, "mode": mode,
                       "paragraphs": len(res.paras), "summary": summary(res), **extra,
                       "findings": [f.to_dict() | {"where": res.paras[f.para - 1].where} for f in res.findings]},
                      ensure_ascii=False, indent=2)


def _context(p: Para, f: Finding, w: int = 18) -> str:
    a, b = max(0, f.start - w), min(len(p.text), f.end + w)
    return ("…" if a else "") + p.text[a:b].replace("\n", " ") + ("…" if b < len(p.text) else "")


def text(res: Result, name: str, mode: str, tail: str = "", explain: bool = True) -> str:
    s = summary(res)
    lines = [f"neveshtar {__version__} · {name} · {len(res.paras)} paragraphs · mode {mode}" + (" · naturalness" if res.natural else ""), ""]
    if res.natural:
        from . import natural as nat
        lines += [nat.NOTICE, ""]
    seen_code = set()
    last_para = 0
    for f in res.findings:
        p = res.paras[f.para - 1]
        if f.para != last_para:
            lines.append(f"{p.where}")
            last_para = f.para
        if f.kind == "natural":
            tag = f"{f.conf}" + (" · applied by this mode" if f.applied else (" · rewrite suggested" if f.suggestion else " · for you to decide"))
            sug = f"  →  {_b(f.suggestion)}" if f.suggestion else ("  →  (drop it)" if f.applied else "")
            lines.append(f"  {SEV_MARK[f.severity]} {f.code}  {_b(f.text.strip())}{sug}   [{tag}]")
            if f.ask:
                lines.append(f"       ask: {f.ask}")
        elif f.kind == "rewrite":
            tag = f"{f.conf}" + (" · applied by this mode" if f.applied else " · suggestion only")
            lines.append(f"  {SEV_MARK[f.severity]} {f.code}  {_b(f.text.strip())}  →  {_b(f.suggestion) if f.suggestion else '(drop it)'}   [{tag}]")
            if len(f.alts or []) > 1:
                lines.append(f"       alternatives: " + " / ".join(_b(a) for a in f.alts))
        else:
            adv = f"  → {_b(f.suggestion)}" if f.suggestion else ""
            lines.append(f"  {SEV_MARK[f.severity]} {f.code}  {_b(f.text.strip())}{adv}")
        if explain and f.code not in seen_code:
            seen_code.add(f.code)
            lines.append(f"       why: {f.message}")
    if not res.findings:
        lines.append("no findings.")
    if res.natural:
        from . import natural as nat
        lines += ["", nat.rhythm_text(nat.rhythm(res.paras)).rstrip()]
    lines += ["", f"{s['errors']} error(s) (spoken forms with one written form), {s['warnings']} warning(s), {s['notes']} note(s); "
                  f"{s['applied']} rewrite(s) would be applied in mode {mode} (neveshtar fix)."]
    if tail:
        lines += ["", tail]
    return "\n".join(lines) + "\n"


def rules_text() -> str:
    from . import lexicon
    rs = lexicon.rules()
    n = {k: 0 for k in CATS}
    t = Counter()
    for r in rs:
        n[r.cat] += 1
        t[r.conf] += 1
    out = ["Rewrite rules (spoken → written; the diff shows each one with its reason)", ""]
    for code, (en, fa, why, _) in CATS.items():
        out.append(f"  {code}  {en:<28} {n[code]:>5} forms   {why}")
    out += ["", "Naturalness checks (R-codes; `neveshtar natural`): stiff, template-like prose. Each finding asks the author a question or offers a rewrite", ""]
    from .natural import NCATS
    for code, (en, fa, why, _) in NCATS.items():
        out.append(f"  {code}  {en:<22} {why}")
    out += ["", f"  confidence: high {t['high']}, medium {t['medium']}, low {t['low']}   (safe applies high; balanced high+medium; all adds low and the optional N201)", "",
            "Style checks (report only)", ""]
    for code, (sev, en, _) in STYLE.items():
        out.append(f"  {code}  {sev:<5} {en}")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------------------------------------------------
# HTML report
# --------------------------------------------------------------------------------------------------------------------
CSS = """
:root{--bg:#f7f5ef;--fg:#1d2433;--mut:#5d6677;--card:#fff;--line:#d9d5c8;--del:#b4232c;--delbg:#fde9e9;--ins:#146c43;--insbg:#e2f5ea;--sug:#8a5a00;--sugbg:#fff4d6;--sty:#25479b;--stybg:#e8eefc;--acc:#25479b;--nat:#6b3fa0;--natbg:#f1e8fb}
@media(prefers-color-scheme:dark){:root{--bg:#12151d;--fg:#e8e6df;--mut:#9aa3b5;--card:#1a1f2b;--line:#2d3446;--del:#ff9aa0;--delbg:#3a1d22;--ins:#7fdca6;--insbg:#16301f;--sug:#f2c46d;--sugbg:#35290f;--sty:#9db7ff;--stybg:#1b2744;--acc:#9db7ff;--nat:#d3b5ff;--natbg:#2c1f40}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.9 "Vazirmatn","Noto Naskh Arabic","Segoe UI",Tahoma,sans-serif}
header,main{max-width:60rem;margin:auto;padding:1rem 1.2rem}h1{margin:.3em 0;font-size:1.5rem}.mut{color:var(--mut);font-size:.9rem}
.bar{display:flex;flex-wrap:wrap;gap:.5rem;margin:1rem 0;position:sticky;top:0;background:var(--bg);padding:.5rem 0;z-index:2}
.bar button{font:inherit;font-size:.85rem;padding:.2rem .8rem;border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:99px;cursor:pointer}
.bar button[aria-pressed=true]{background:var(--acc);color:var(--bg);border-color:var(--acc)}
.p{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:.7rem 1rem;margin:.6rem 0}.p .n{font-size:.75rem;color:var(--mut);direction:ltr;text-align:left}
del{background:var(--delbg);color:var(--del);text-decoration:line-through;border-radius:3px;padding:0 .1em}ins{background:var(--insbg);color:var(--ins);text-decoration:none;border-radius:3px;padding:0 .1em}
.sug{background:var(--sugbg);color:var(--sug);border-bottom:2px dotted var(--sug);border-radius:3px;cursor:help}.nat{background:var(--natbg);color:var(--nat);border-bottom:2px double var(--nat);cursor:help}.sty{background:var(--stybg);color:var(--sty);border-bottom:2px wavy var(--sty);cursor:help}
[data-view=before] ins,[data-view=before] .sty,[data-view=before] .nat{display:none}[data-view=before] del{background:none;color:inherit;text-decoration:none}
[data-view=after] del,[data-view=after] .sty,[data-view=after] .nat{display:none}[data-view=after] ins{background:none;color:inherit}
.hide-sug .sug{background:none;border:0;color:inherit}.hide-nat .nat{background:none;border:0;color:inherit}.notice{border:1px solid var(--line);border-inline-start:4px solid var(--nat);background:var(--card);padding:.5rem .9rem;border-radius:8px;font-size:.88rem;margin:.6rem 0}.hide-sty .sty{background:none;border:0;color:inherit}
table{width:100%;border-collapse:collapse;font-size:.88rem;margin:1rem 0}th,td{border-bottom:1px solid var(--line);padding:.35rem .5rem;text-align:start;vertical-align:top}.code{font-family:ui-monospace,monospace;direction:ltr;unicode-bidi:isolate}
.badge{display:inline-block;font-size:.7rem;padding:0 .45em;border-radius:99px;border:1px solid currentColor;margin-inline-start:.3em;vertical-align:middle;direction:ltr}
footer{max-width:60rem;margin:2rem auto;padding:0 1.2rem 2rem;color:var(--mut);font-size:.85rem}
"""
JS = """
const r=document.documentElement;document.querySelectorAll('[data-view-btn]').forEach(b=>b.onclick=()=>{r.dataset.view=b.dataset.viewBtn;document.querySelectorAll('[data-view-btn]').forEach(x=>x.setAttribute('aria-pressed',x===b))});
document.querySelectorAll('[data-toggle]').forEach(b=>b.onclick=()=>{const on=b.getAttribute('aria-pressed')!=='true';b.setAttribute('aria-pressed',on);r.classList.toggle(b.dataset.toggle,!on)});
"""


def _tip(f: Finding) -> str:
    t = f"{f.code}: {f.message}"
    if f.kind in ("rewrite", "natural"):
        t += f" [{f.conf}]"
    if f.kind == "natural" and f.ask:
        t += f" ? {f.ask}"
    if f.suggestion:
        t += f" → {f.suggestion}"
    return html.escape(t, quote=True)


def html_report(res: Result, name: str, mode: str) -> str:
    s = summary(res)
    by_para: Dict[int, List[Finding]] = {}
    for f in res.findings:
        by_para.setdefault(f.para, []).append(f)
    body = []
    for p in res.paras:
        fs = by_para.get(p.index, [])
        if not fs:
            continue
        # one pass of non-overlapping spans: rewrite findings take precedence, style findings fill gaps
        marks = []
        rew = [f for f in fs if f.kind == "rewrite"]
        rew += [f for f in fs if f.kind == "natural" and f.applied]
        sty = [f for f in fs if f.kind in ("style", "natural") and f not in rew]
        taken = [(f.start, f.end) for f in rew]
        for f in rew:
            marks.append((f.start, f.end, f))
        for f in sty:
            if not any(a < f.end and f.start < b for a, b in taken):
                marks.append((f.start, f.end, f))
                taken.append((f.start, f.end))
        marks.sort(key=lambda m: m[0])
        out, pos = [], 0
        for a, b, f in marks:
            if a < pos:
                continue
            out.append(html.escape(p.text[pos:a]))
            seg = html.escape(p.text[a:b])
            if f.kind in ("rewrite", "natural") and f.applied:
                out.append(f'<del title="{_tip(f)}">{seg}</del><ins title="{_tip(f)}">{html.escape(f.suggestion)}</ins>')
            elif f.kind == "natural":
                out.append(f'<span class="nat" title="{_tip(f)}">{seg}</span>')
            elif f.kind == "rewrite":
                out.append(f'<span class="sug" title="{_tip(f)}">{seg}</span>')
            else:
                out.append(f'<span class="sty" title="{_tip(f)}">{seg}</span>')
            pos = b
        out.append(html.escape(p.text[pos:]))
        body.append(f'<div class="p"><div class="n">{html.escape(p.where)}</div><div>{"".join(out)}</div></div>')
    rows = []
    for f in res.findings:
        p = res.paras[f.para - 1]
        rows.append(f'<tr><td class="code">{html.escape(f.code)}</td><td>{html.escape(p.where)}</td><td>{html.escape(f.text.strip())}'
                    + (f' → {html.escape(f.suggestion)}' if f.kind in ("rewrite", "natural") and f.suggestion else (f' <span class="mut">({html.escape(f.suggestion)})</span>' if f.suggestion else ""))
                    + (f'<span class="badge">{f.conf}{"· applied" if f.applied else ""}</span>' if f.kind in ("rewrite", "natural") else "")
                    + (f'<div class="mut">? {html.escape(f.ask)}</div>' if f.kind == "natural" and f.ask else "")
                    + f'</td><td class="mut">{html.escape(f.message_fa)}</td></tr>')
    nat_btn = nat_notice = ""
    if res.natural:
        from . import natural as nat
        nat_btn = '<button data-toggle="hide-nat" aria-pressed="true">طبیعی‌بودن / naturalness</button>'
        nat_notice = f'<div class="notice">{html.escape(nat.NOTICE_FA)}<br><span class="mut">{html.escape(nat.NOTICE)}</span></div>'
    return (f'<!doctype html><html lang="fa" dir="rtl" data-view="diff"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>neveshtar · {html.escape(name)}</title><style>{CSS}</style></head><body>'
            f'<header><h1>نوشتار · گزارش {html.escape(name)}</h1><div class="mut">neveshtar {__version__} · {len(res.paras)} paragraphs · mode {mode} · '
            f'{s["errors"]} errors, {s["warnings"]} warnings, {s["notes"]} notes · {s["applied"]} rewrites applied in this view</div>'
            f'<div class="bar" role="toolbar" aria-label="view"><button data-view-btn="diff" aria-pressed="true">تغییرات / diff</button>'
            f'<button data-view-btn="before" aria-pressed="false">پیش از / before</button><button data-view-btn="after" aria-pressed="false">پس از / after</button>'
            f'<button data-toggle="hide-sug" aria-pressed="true">پیشنهادها / suggestions</button><button data-toggle="hide-sty" aria-pressed="true">سبک / style</button>{nat_btn}</div>{nat_notice}</header>'
            f'<main>{"".join(body) or "<p>no findings.</p>"}'
            f'<h2>همه‌ی یافته‌ها / all findings</h2><table><thead><tr><th>code</th><th>where</th><th>text</th><th>why</th></tr></thead><tbody>{"".join(rows)}</tbody></table></main>'
            f'<footer>A writing-quality aid: you review every change. It does not write your thesis, does not guarantee academic quality, makes no claim about AI detectors, and is not built to evade them or to hide who wrote a text. '
            f'Self-contained file; nothing was sent anywhere.</footer><script>{JS}</script></body></html>')
