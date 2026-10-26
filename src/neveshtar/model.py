from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Para:
    index: int            # 1-based position among the paragraphs reported
    text: str
    kind: str = "p"       # p | heading | code (code is never scanned)
    where: str = ""       # e.g. "¶7", "line 12"
    omap: Optional[List[int]] = None   # docx: offset in the shown text -> offset in the run text (non-plain runs removed)


@dataclass
class Finding:
    code: str
    severity: str          # error | warn | info
    para: int
    start: int
    end: int
    text: str              # the matched text
    kind: str              # "rewrite" | "style"
    message: str
    message_fa: str
    suggestion: str = ""   # replacement (rewrite) or advice (style)
    conf: str = ""         # rewrite: high | medium | low
    applied: bool = False
    alts: Optional[List[str]] = None
    ask: str = ""          # natural: the question for the author (EN)
    ask_fa: str = ""

    def to_dict(self) -> dict:
        d = {"code": self.code, "severity": self.severity, "paragraph": self.para, "start": self.start, "end": self.end,
             "text": self.text, "kind": self.kind, "message": self.message, "message_fa": self.message_fa,
             "suggestion": self.suggestion}
        if self.kind == "natural":
            d["confidence"] = self.conf
            d["applied"] = self.applied
            d["alternatives"] = self.alts or []
            d["question"] = self.ask
            d["question_fa"] = self.ask_fa
        if self.kind == "rewrite":
            d["confidence"] = self.conf
            d["applied"] = self.applied
            d["alternatives"] = self.alts or []
        return d
