from __future__ import annotations

import argparse
import os
import sys
import tempfile
from typing import Dict, List, Optional

from . import __version__, analyse as an, docx as dx, engine, render, scaffold, textio
from .analyse import Options, Result
from .engine import Change

COMMANDS = ("check", "fix", "natural", "rhythm", "scaffold", "rules", "sample", "demo")


def _load(path: str):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".docx":
        return "docx", dx.read(path), None
    if ext in (".txt", ".md", ".markdown", ""):
        paras, lines = textio.read_text(path)
        return "text", paras, lines
    raise ValueError(f"unsupported file type {ext!r} (use .docx, .txt or .md)")


def _opts(a) -> Options:
    skip = tuple(x.strip().upper() for x in (a.skip or "").split(",") if x.strip())
    return Options(mode=a.mode, max_words=a.max_words, skip=skip, style=not a.no_style, rewrites=not getattr(a, "no_rewrites", False), natural=getattr(a, "natural", False))


def _common(sp):
    sp.add_argument("file", help=".docx, .txt or .md")
    sp.add_argument("--mode", choices=["safe", "balanced", "all"], default="safe",
                    help="which rewrites are applied: safe = unambiguous only (default), balanced = + likely, all = + suggestions")
    sp.add_argument("--max-words", type=int, default=45, help="S601 sentence-length limit in words (default 45)")
    sp.add_argument("--skip", default="", help="comma-separated finding codes to ignore, e.g. N201,S101")
    sp.add_argument("--no-style", action="store_true", help="only the spoken → written rewrites")
    sp.add_argument("--json", action="store_true", help="machine-readable output")
    sp.add_argument("--html", metavar="OUT", help="write a self-contained HTML diff report")
    sp.add_argument("--no-color", action="store_true")
    sp.add_argument("--natural", action="store_true", help="also run the naturalness check (R-codes)")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="neveshtar", description=(
        "Offline Persian academic-register aid for theses: spoken → written rewrites with a per-change reason and confidence, "
        "thesis style checks, section scaffolds, and Word tracked changes. A rewriting aid you review; not an AI author."))
    ap.add_argument("--version", action="version", version=f"neveshtar {__version__}")
    sub = ap.add_subparsers(dest="cmd")
    c = sub.add_parser("check", help="report spoken forms and style problems (never edits)")
    _common(c)
    c.add_argument("--strict", action="store_true", help="exit 1 on warnings too (default: only on errors = high-confidence spoken forms)")
    f = sub.add_parser("fix", help="write a COPY with the rewrites of --mode applied (docx: as tracked changes)")
    _common(f)
    f.add_argument("-o", "--output", help="path of the copy (default: <name>.neveshtar.<ext>)")
    f.add_argument("--clean", action="store_true", help="docx: apply the changes silently instead of as tracked changes")
    f.add_argument("--author", default="neveshtar", help="docx: author name on the tracked changes")
    f.add_argument("--date", help="docx: ISO date on the tracked changes (default: a fixed neutral date, so output is reproducible)")
    n = sub.add_parser("natural", help="naturalness check: stiff, template-like prose, with a question or a rewrite for each finding (a review aid)")
    n.add_argument("file", help=".docx, .txt or .md")
    n.add_argument("--mode", choices=["safe", "balanced", "all"], default="safe", help="which rewrites --fix applies: safe = unambiguous trims only (default)")
    n.add_argument("--skip", default="", help="comma-separated codes to ignore, e.g. R104,R301")
    n.add_argument("--with-register", action="store_true", help="also run the spoken → written rewrites and the S-style checks")
    n.add_argument("--fix", action="store_true", help="write a COPY with the --mode rewrites applied (docx: tracked changes, plus a comment per open question)")
    n.add_argument("-o", "--output", help="path of the copy (with --fix)")
    n.add_argument("--clean", action="store_true", help="docx: apply silently, no tracked changes")
    n.add_argument("--no-comments", action="store_true", help="docx: do not add Word comments for the open questions")
    n.add_argument("--author", default="neveshtar")
    n.add_argument("--date")
    n.add_argument("--json", action="store_true")
    n.add_argument("--html", metavar="OUT")
    n.add_argument("--no-color", action="store_true")
    n.add_argument("--strict", action="store_true")
    rh = sub.add_parser("rhythm", help="plain readability / rhythm numbers: sentence-length variation, opener diversity (descriptive, not a score)")
    rh.add_argument("file")
    rh.add_argument("--json", action="store_true")
    s = sub.add_parser("scaffold", help="print a fill-in-the-blank section scaffold (guidance, not generated text)")
    s.add_argument("section", nargs="?", default="list", help="one of: " + ", ".join(scaffold.names()) + " (or: list)")
    s.add_argument("--lang", choices=["fa", "en", "both"], default="fa")
    r = sub.add_parser("rules", help="list the rule categories and style checks")
    r.add_argument("--json", action="store_true")
    sm = sub.add_parser("sample", help="write the synthetic demo draft (.docx or .txt/.md by extension)")
    sm.add_argument("path")
    sm.add_argument("--clean", action="store_true", help="write the already-formal version")
    sm.add_argument("--natural", action="store_true", help="write the formal-but-stiff draft used to demonstrate `neveshtar natural`")
    sub.add_parser("demo", help="offline: generate a sample draft and run check + fix on it")
    return ap


def _report(path: str, res: Result, a, tail: str = "") -> int:
    s = render.summary(res)
    if a.html:
        with open(a.html, "w", encoding="utf-8") as fh:
            fh.write(render.html_report(res, os.path.basename(path), a.mode))
        tail = (tail + "\n" if tail else "") + f"HTML report: {a.html}"
    if a.json:
        sys.stdout.write(render.as_json(res, os.path.basename(path), a.mode) + "\n")
    else:
        sys.stdout.write(render.text(res, os.path.basename(path), a.mode, tail=tail))
    return s["errors"], s["warnings"]


def cmd_check(a) -> int:
    kind, paras, _ = _load(a.file)
    res = an.analyse(paras, _opts(a))
    errs, warns = _report(a.file, res, a)
    return 1 if errs or (a.strict and warns) else 0


def cmd_fix(a) -> int:
    kind, paras, lines = _load(a.file)
    ext = os.path.splitext(a.file)[1]
    dst = a.output or os.path.splitext(a.file)[0] + ".neveshtar" + ext
    if os.path.abspath(dst) == os.path.abspath(a.file):
        print("neveshtar: refusing to overwrite the input file", file=sys.stderr)
        return 2
    opt = _opts(a)
    res = an.analyse(paras, opt)
    plan: Dict[int, List[Change]] = {k: v for k, v in res.chosen.items() if v}
    n_ok, skipped = 0, []
    if kind == "docx":
        notes: Dict[int, List[str]] = {}
        if getattr(a, "comments", False) and not a.clean:
            for f_ in res.findings:
                if f_.kind == "natural" and not f_.applied:
                    notes.setdefault(f_.para, []).append(f"{f_.code} «{f_.text.strip()[:60]}»: {f_.message}" + (f" → {f_.suggestion}" if f_.suggestion else "") + f" ? {f_.ask}")
        applied, skipped = dx.write(a.file, dst, plan, tracked=not a.clean, author=a.author, date=a.date, comments=notes)
        n_ok = len(applied)
        applied_ids = {id(c) for c in applied}
        for f_ in res.findings:     # mark in the report what was really written
            pass
        mode_txt = "clean (no tracked changes)" if a.clean else "tracked changes: accept / reject each one in Word (Review → Tracking)"
    else:
        by_line = {int(p.where.split()[1]) - 1: p for p in paras}
        out = list(lines)
        for ln, p in by_line.items():
            ch = plan.get(p.index)
            if ch:
                out[ln] = engine.apply(p.text, ch)
                n_ok += len(ch)
        open(dst, "w", encoding="utf-8", newline="\n").write("\n".join(out))
        mode_txt = "text copy"
    tail = f"wrote {dst}: {n_ok} rewrite(s) applied ({mode_txt}). The input file was not modified."
    if skipped:
        tail += f"\n{len(skipped)} rewrite(s) skipped:\n" + "\n".join(f"  ¶ {c.original!r}: {why}" for c, why in skipped[:10])
    # re-check the copy
    kind2, paras2, _ = _load(dst)
    after = an.analyse(paras2, Options(mode=opt.mode, max_words=opt.max_words, skip=opt.skip, style=False, rewrites=opt.rewrites))
    left = sum(1 for f_ in after.findings if f_.kind == "rewrite" and f_.conf in ("high",))
    tail += f"\nre-check of the copy: {left} high-confidence spoken form(s) left."
    _report(a.file, res, a, tail)
    return 0 if left == 0 or opt.mode != "safe" else 0


def cmd_natural(a) -> int:
    ns = argparse.Namespace(file=a.file, mode=a.mode, max_words=45, skip=a.skip, no_style=not a.with_register, no_rewrites=not a.with_register,
                            natural=True, json=a.json, html=a.html, no_color=True, strict=a.strict, output=a.output, clean=a.clean,
                            author=a.author, date=a.date, comments=not a.no_comments)
    return cmd_fix(ns) if a.fix else cmd_check(ns)


def cmd_rhythm(a) -> int:
    from . import natural
    import json
    kind, paras, _ = _load(a.file)
    r = natural.rhythm(paras)
    sys.stdout.write((json.dumps(r, ensure_ascii=False, indent=2) + "\n") if a.json else natural.rhythm_text(r))
    return 0


def cmd_scaffold(a) -> int:
    if a.section == "list":
        for k in scaffold.names():
            fa, en, _ = scaffold.SECTIONS[k]
            print(f"{k:<13} {fa} / {en}")
        return 0
    try:
        sys.stdout.write(scaffold.render(a.section, a.lang))
    except KeyError:
        print(f"neveshtar: unknown section {a.section!r}; try: neveshtar scaffold list", file=sys.stderr)
        return 2
    return 0


def cmd_rules(a) -> int:
    if a.json:
        import json
        from . import lexicon
        from .style import STYLE
        print(json.dumps({"rewrite_categories": {k: {"name": v[0], "name_fa": v[1], "why": v[2], "forms": sum(1 for r in lexicon.rules() if r.cat == k)} for k, v in lexicon.CATS.items()},
                          "style": {k: {"severity": v[0], "why": v[1]} for k, v in __import__("neveshtar.style", fromlist=["STYLE"]).STYLE.items()}}, ensure_ascii=False, indent=2))
    else:
        sys.stdout.write(render.rules_text())
    return 0


def cmd_sample(a) -> int:
    from . import sample
    if a.natural:
        if a.path.lower().endswith(".docx"):
            sample.natural_thesis(a.path)
        else:
            open(a.path, "w", encoding="utf-8").write(sample.natural_lines())
    elif a.path.lower().endswith(".docx"):
        sample.thesis(a.path, flawed=not a.clean)
    else:
        open(a.path, "w", encoding="utf-8").write(sample.text_lines(flawed=not a.clean))
    print(a.path)
    return 0


def cmd_demo(a) -> int:
    from . import sample
    with tempfile.TemporaryDirectory() as td:
        p = sample.thesis(os.path.join(td, "chapter.docx"))
        ns = argparse.Namespace(file=p, mode="safe", max_words=45, skip="", no_style=False, json=False, html=None, no_color=True, strict=False)
        cmd_check(ns)
        out = os.path.join(td, "chapter.neveshtar.docx")
        fx = argparse.Namespace(file=p, mode="safe", max_words=45, skip="", no_style=True, json=False, html=None, no_color=True, output=out, clean=False, author="neveshtar", date=None)
        print("\n" + "=" * 70 + "\n$ neveshtar fix chapter.docx\n")
        cmd_fix(fx)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and not argv[0].startswith("-") and argv[0] not in COMMANDS:
        argv = ["check"] + argv                      # `neveshtar thesis.docx` = check
    ap = build_parser()
    a = ap.parse_args(argv)
    if not a.cmd:
        ap.print_help()
        return 0
    if a.cmd in ("check", "fix", "natural", "rhythm") and not os.path.exists(a.file):
        print(f"neveshtar: no such file: {a.file}", file=sys.stderr)
        return 2
    try:
        return {"check": cmd_check, "fix": cmd_fix, "natural": cmd_natural, "rhythm": cmd_rhythm, "scaffold": cmd_scaffold, "rules": cmd_rules, "sample": cmd_sample, "demo": cmd_demo}[a.cmd](a)
    except (ValueError, OSError, KeyError) as e:
        print(f"neveshtar: {e}", file=sys.stderr)
        return 2
    except Exception as e:        # a damaged .docx, for instance
        if "zip" in type(e).__name__.lower() or "BadZip" in repr(e):
            print(f"neveshtar: cannot read {getattr(a, 'file', '')}: {e}", file=sys.stderr)
            return 2
        raise


if __name__ == "__main__":
    raise SystemExit(main())
