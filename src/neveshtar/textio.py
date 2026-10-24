"""Plain-text and Markdown input: one Para per non-empty line; fenced code, indented code and front matter are skipped."""
from __future__ import annotations

import re
from typing import List, Tuple

from .model import Para


def read_text(path: str) -> Tuple[List[Para], List[str]]:
    """Returns (paragraphs, raw lines). A Para's ``where`` is «line N»; its index is its position in the list."""
    raw = open(path, encoding="utf-8-sig").read().replace("\r\n", "\n")
    lines = raw.split("\n")
    md = path.lower().endswith((".md", ".markdown"))
    out: List[Para] = []
    fence = False
    front = md and lines[:1] == ["---"]
    for i, ln in enumerate(lines, 1):
        if front:
            if i > 1 and ln.strip() == "---":
                front = False
            continue
        if md and re.match(r"^\s*(```|~~~)", ln):
            fence = not fence
            continue
        if fence or not ln.strip():
            continue
        kind = "p"
        if md:
            if re.match(r"^( {4}|\t)\S", ln):
                kind = "code"
            elif re.match(r"^\s{0,3}#{1,6}\s", ln):
                kind = "heading"
        out.append(Para(len(out) + 1, ln, kind, f"line {i}"))
    return out, lines


def line_numbers(paras: List[Para]) -> List[int]:
    return [int(p.where.split()[1]) for p in paras]
