"""The rewrite engine: find spoken-register spans in a paragraph, decide which are applied, apply them.

``find_changes`` never edits anything; it returns :class:`Change` objects (position, original, replacement, rule category,
confidence, reason).  ``select`` filters them by mode; ``apply`` builds the new text.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Sequence, Tuple

from . import lexicon
from .lexicon import CATS, ZW, normalise_key

MODES = {"safe": ("high",), "balanced": ("high", "medium"), "all": ("high", "medium", "low")}
from .lexicon import LETTER

# --- spans the engine must never touch ----------------------------------------------------------------------
_PROTECT = re.compile(
    r"«[^»\n]*»"                                  # «direct quotation»
    r"|“[^”\n]*”"                                  # “quotation”
    r'|"[^"\n]*"'                                  # "quotation"
    r"|`[^`\n]*`"                                  # markdown inline code
    r"|https?://\S+|www\.\S+|\b[\w.+-]+@[\w-]+\.[\w.-]+\b"
    r"|\]\([^)\n]*\)"                              # markdown link target
)


def protected_spans(text: str) -> List[Tuple[int, int]]:
    return [(m.start(), m.end()) for m in _PROTECT.finditer(text)]


def in_spans(pos: int, spans: Sequence[Tuple[int, int]]) -> bool:
    return any(a <= pos < b for a, b in spans)


# words after which «جهت» means "direction", not "in order to"
_DIRECTION_BEFORE = {"در", "این", "همین", "هر", "آن", "همان", "دو", "سه", "چند", "یک", "هم", "بدین", "به", "از", "برخلاف", "خلاف"}
# «رو» is the object marker only after a word and not before «به» («رو به رشد») or a verb of motion
_RO = re.compile(f"(?<=[{LETTER}] )رو(?![{LETTER}])(?! به)")


@dataclass
class Change:
    start: int
    end: int
    original: str
    replacement: str
    alts: Tuple[str, ...]
    conf: str            # high | medium | low
    cat: str             # N1xx / N2xx
    note: str = ""
    rule: str = ""       # the normalised spoken form (for the explanation)

    @property
    def severity(self) -> str:
        return {"high": "error", "medium": "warn", "low": "info"}[self.conf]

    @staticmethod
    def _info(cat: str):
        if cat in CATS:
            return CATS[cat]
        from .natural import NCATS
        return NCATS[cat]

    @property
    def why_en(self) -> str:
        return self._info(self.cat)[2] + ((" " + self.note) if self.note else "")

    @property
    def why_fa(self) -> str:
        return self._info(self.cat)[3]

    def to_dict(self) -> dict:
        return {"start": self.start, "end": self.end, "original": self.original, "replacement": self.replacement,
                "alternatives": list(self.alts), "confidence": self.conf, "code": self.cat,
                "category": self._info(self.cat)[0], "why": self.why_en, "why_fa": self.why_fa}


def find_changes(text: str, protect: bool = True) -> List[Change]:
    """All spoken-register spans of ``text``, longest match first, non-overlapping, sorted by position."""
    rx, table = lexicon.matcher()
    prot = protected_spans(text) if protect else []
    cands: List[Change] = []
    for m in rx.finditer(text):
        if in_spans(m.start(), prot):
            continue
        key = normalise_key(m.group(0))
        rule = table.get(key)
        if rule is None:
            continue
        if rule.surface == "جهت":
            prev = re.findall(f"[{LETTER}]+", text[:m.start()])[-1:]
            if prev and prev[0] in _DIRECTION_BEFORE:
                continue
        new, end = rule.written, m.end()
        if new == "‹حذف›":                           # filler: drop it together with a following comma and spaces
            tail = re.match(r"[،,]?[ \t]*", text[end:])
            end += tail.end()
            new = ""
            alts: Tuple[str, ...] = ("",)
        else:
            alts = rule.alts
        cands.append(Change(m.start(), end, text[m.start():end], new, alts, rule.conf, rule.cat, rule.note, rule.surface))
    for m in _RO.finditer(text):
        if in_spans(m.start(), prot):
            continue
        cands.append(Change(m.start(), m.end(), "رو", "را", ("را",), "high", "N104", "", "رو"))
    cands.sort(key=lambda c: (c.start, -(c.end - c.start)))
    out: List[Change] = []
    last = -1
    for c in cands:
        if c.start >= last:
            out.append(c)
            last = c.end
    return out


def select(changes: Iterable[Change], mode: str = "safe", skip_cats: Iterable[str] = ()) -> List[Change]:
    """The subset a mode applies. ``skip_cats``: categories to leave alone (e.g. N201 is only ever applied in mode «all»)."""
    tiers = MODES[mode]
    skip = set(skip_cats)
    out = []
    for c in changes:
        if c.conf not in tiers or c.cat in skip:
            continue
        if c.cat == "N201" and mode != "all":
            continue
        out.append(c)
    return out


def match_case_space(c: Change, text: str) -> str:
    return c.replacement


def apply(text: str, changes: Sequence[Change]) -> str:
    out, pos = [], 0
    for c in sorted(changes, key=lambda c: c.start):
        out.append(text[pos:c.start])
        out.append(c.replacement)
        pos = c.end
    out.append(text[pos:])
    return "".join(out)


def formalize(text: str, mode: str = "safe") -> str:
    """Convenience for the library: rewrite one string."""
    return apply(text, select(find_changes(text), mode))
