"""Glue: paragraphs in, findings out."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

from . import engine, natural, style
from .engine import Change
from .model import Finding, Para


@dataclass
class Options:
    mode: str = "safe"                 # which rewrites count as «applied»: safe | balanced | all
    max_words: int = 45
    skip: Tuple[str, ...] = ()         # finding codes to ignore (N102, S301 …)
    style: bool = True
    rewrites: bool = True
    natural: bool = False              # add the naturalness check (R-codes)


@dataclass
class Result:
    paras: List[Para]
    findings: List[Finding]
    changes: Dict[int, List[Change]] = field(default_factory=dict)      # all rewrite candidates by paragraph
    chosen: Dict[int, List[Change]] = field(default_factory=dict)       # the ones the mode applies
    natural: bool = False


def analyse(paras: Sequence[Para], opt: Options = Options()) -> Result:
    res = Result(list(paras), [])
    res.natural = opt.natural
    skip = set(opt.skip)
    for p in paras:
        if p.kind == "code":
            continue
        ch = [c for c in engine.find_changes(p.text) if c.cat not in skip] if opt.rewrites else []
        res.changes[p.index] = ch
        chosen = engine.select(ch, opt.mode)
        res.chosen[p.index] = chosen
        ids = {id(c) for c in chosen}
        for c in ch:
            res.findings.append(Finding(c.cat, c.severity, p.index, c.start, c.end, c.original, "rewrite", c.why_en, c.why_fa,
                                        c.replacement, c.conf, id(c) in ids, list(c.alts)))
        if opt.style:
            informal = sum(1 for c in ch if c.conf in ("high", "medium") and c.cat != "N201")
            res.findings += [f for f in style.check_paragraph(p, opt.max_words, informal) if f.code not in skip]
    if opt.natural:
        tiers = engine.MODES[opt.mode]
        for p in paras:
            if p.kind == "code":
                continue
            taken = [(c.start, c.end) for c in res.changes.get(p.index, [])]
            for f, ch in natural.check_paragraph(p):
                if f.code in skip:
                    continue
                if ch is not None and f.conf in tiers and not any(a < ch.end and ch.start < b for a, b in taken):
                    f.applied = True
                    taken.append((ch.start, ch.end))
                    res.chosen.setdefault(p.index, []).append(ch)
                res.findings.append(f)
        res.findings += [f for f in natural.check_document(paras) if f.code not in skip]
    res.findings.sort(key=lambda f: (f.para, f.start, f.code))
    return res
