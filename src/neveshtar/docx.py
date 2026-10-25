"""Read paragraphs from a .docx and write a copy with the rewrites as real Word tracked changes (<w:ins> / <w:del>).

Standard library only.  The writer edits document.xml as text, paragraph by paragraph, so every other part of the package
(styles, numbering, footers, images, comments) stays byte-identical.  A paragraph is only touched when
  * every changed character sits in a plain run (a run whose children are only w:rPr and w:t);
  * the paragraph has no tracked changes yet, no text box, no field result at the changed place.
Everything else is reported as «skipped» with the reason, never silently dropped.
"""
from __future__ import annotations

import dataclasses
import re
import zipfile
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Set, Tuple
from xml.sax.saxutils import escape, unescape

from .engine import Change
from .model import Para

P_TOKEN = re.compile(r"<w:p(?=[\s>/])[^>]*?(/?)>|</w:p>|<w:txbxContent[\s>]|</w:txbxContent>")
OBJ = "\ufffc"          # stands for «a run that is not plain text» in the paragraph's character map


def paragraph_spans(xml: str) -> List[Tuple[int, int]]:
    """(start, end) of every block-level paragraph (text boxes excluded), in document order."""
    spans, stack, tx = [], [], 0
    for m in P_TOKEN.finditer(xml):
        tok = m.group(0)
        if tok.startswith("<w:txbxContent"):
            tx += 1
        elif tok == "</w:txbxContent>":
            tx -= 1
        elif tok.startswith("<w:p"):
            if m.group(1) == "/":
                if tx == 0:
                    spans.append((m.start(), m.end()))
                continue
            stack.append((m.start(), tx))
        else:
            s, t = stack.pop()
            if t == 0:
                spans.append((s, m.end()))
    spans.sort()
    return spans


_RUN = re.compile(r"<w:r(?=[\s>])[^>]*?(?<!/)>.*?</w:r>|<w:r(?=[\s>/])[^>]*?/>", re.S)
_RPR = re.compile(r"<w:rPr>.*?</w:rPr>|<w:rPr\s*/>", re.S)
_T = re.compile(r"<w:t(?=[\s>/])[^>]*?(?:/>|>(.*?)</w:t>)", re.S)
_STYLE = re.compile(r'<w:pStyle w:val="([^"]*)"')


@dataclass
class RunInfo:
    start: int            # offset in the paragraph xml
    end: int
    open: str             # <w:r ...>
    rpr: str
    text: Optional[str]   # None when the run is not plain
    xml: str


def _runs(pxml: str) -> List[RunInfo]:
    out = []
    for m in _RUN.finditer(pxml):
        x = m.group(0)
        if x.endswith("/>") and "</w:r>" not in x:
            out.append(RunInfo(m.start(), m.end(), x, "", "", x))
            continue
        open_tag = re.match(r"<w:r(?=[\s>])[^>]*>", x).group(0)
        body = x[len(open_tag):-len("</w:r>")]
        rpr = ""
        mr = _RPR.match(body)
        if mr:
            rpr, body = mr.group(0), body[mr.end():]
        # plain = only <w:t> elements left
        rest = _T.sub("", body)
        if rest.strip():
            out.append(RunInfo(m.start(), m.end(), open_tag, rpr, None, x))
        else:
            txt = "".join(unescape(t.group(1) or "") for t in _T.finditer(body))
            out.append(RunInfo(m.start(), m.end(), open_tag, rpr, txt, x))
    return out


def para_text(pxml: str) -> Tuple[str, List[RunInfo]]:
    runs = _runs(pxml)
    return "".join((r.text if r.text is not None else OBJ) for r in runs), runs


def _has_tracked(pxml: str) -> bool:
    return bool(re.search(r"<w:(ins|del|moveFrom|moveTo)\s", pxml))


def _kind(pxml: str) -> str:
    m = _STYLE.search(pxml)
    if m and re.match(r"(?i)(heading|title|عنوان)", m.group(1)):
        return "heading"
    return "p"


def read(path: str) -> List[Para]:
    """Paragraphs of the document body (including table cells), in order, as plain text. Paragraphs without text are skipped,
    but each reported paragraph carries its real position (``where``: «¶n of document.xml»)."""
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    out: List[Para] = []
    for i, (a, b) in enumerate(paragraph_spans(xml), 1):
        full, _ = para_text(xml[a:b])
        omap = [k for k, ch in enumerate(full) if ch != OBJ]
        txt = "".join(full[k] for k in omap)
        if txt.strip():
            out.append(Para(len(out) + 1, txt, _kind(xml[a:b]), f"¶{i}", omap))
    return out


def _wdate(date: Optional[str]) -> str:
    return date or "2026-01-01T00:00:00Z"


def _t(text: str, tag: str = "w:t") -> str:
    sp = ' xml:space="preserve"' if text != text.strip() or "  " in text else ""
    return f"<{tag}{sp}>{escape(text)}</{tag}>"


def _run_xml(open_tag: str, rpr: str, text: str, tag: str = "w:t") -> str:
    return f"{open_tag}{rpr}{_t(text, tag)}</w:r>" if text else ""


def edit_paragraph(pxml: str, changes: Sequence[Change], tracked: bool, author: str, date: str, ids: List[int], omap: Optional[List[int]] = None) -> Tuple[str, List[Change], List[Tuple[Change, str]]]:
    """Apply ``changes`` (offsets into the paragraph's plain text) to one paragraph's XML.
    Returns (new xml, applied changes, [(skipped change, reason)])."""
    if _has_tracked(pxml):
        return pxml, [], [(c, "paragraph already contains tracked changes") for c in changes]
    text, runs = para_text(pxml)
    # char -> run index
    owner: List[int] = []
    for k, r in enumerate(runs):
        owner.extend([k] * (len(r.text) if r.text is not None else 1))
    good, skipped = [], []
    mapped: List[Change] = []
    for c in sorted(changes, key=lambda c: c.start):
        if omap is not None:                      # shown-text offsets -> full-paragraph offsets
            if c.end > len(omap):
                skipped.append((c, "offsets do not fit the paragraph"))
                continue
            a2, b2 = omap[c.start], omap[c.end - 1] + 1
            if b2 - a2 != c.end - c.start:
                skipped.append((c, "the span crosses a field, tab, image or other non-plain run"))
                continue
            c = dataclasses.replace(c, start=a2, end=b2)
        mapped.append(c)
    good = []
    for c in mapped:
        if c.start >= len(text) or text[c.start:c.end] != c.original:
            skipped.append((c, "text of the change does not match the paragraph (field, or edited between check and fix)"))
        elif any(runs[owner[i]].text is None for i in range(c.start, c.end)):
            skipped.append((c, "the span crosses a field, tab, image or other non-plain run"))
        else:
            good.append(c)
    if not good:
        return pxml, [], skipped
    # character range of every run in the paragraph text
    bounds: Dict[int, Tuple[int, int]] = {}
    pos = 0
    for k, r in enumerate(runs):
        ln = len(r.text) if r.text is not None else 1
        bounds[k] = (pos, pos + ln)
        pos += ln
    new_runs: Dict[int, str] = {}
    inserted: Set[int] = set()
    for k, r in enumerate(runs):
        if r.text is None:
            new_runs[k] = r.xml
            continue
        a0, b0 = bounds[k]
        cuts = [c for c in good if c.start < b0 and c.end > a0]
        if not cuts:
            new_runs[k] = r.xml
            continue
        out, cur = [], a0
        for c in cuts:
            s, e = max(c.start, a0), min(c.end, b0)
            out.append(_run_xml(r.open, r.rpr, text[cur:s]))
            piece = text[s:e]
            if tracked:
                ids[0] += 1
                out.append(f'<w:del w:id="{ids[0]}" w:author="{escape(author)}" w:date="{date}">{_run_xml(r.open, r.rpr, piece, "w:delText")}</w:del>')
            cur = e
            # the insertion is attached to the run that holds the START of the change
            if c.start >= a0 and c.start < b0 and id(c) not in inserted:
                inserted.add(id(c))
                if c.replacement:
                    if tracked:
                        ids[0] += 1
                        out.append(f'<w:ins w:id="{ids[0]}" w:author="{escape(author)}" w:date="{date}">{_run_xml(r.open, r.rpr, c.replacement)}</w:ins>')
                    else:
                        out.append(_run_xml(r.open, r.rpr, c.replacement))
        out.append(_run_xml(r.open, r.rpr, text[cur:b0]))
        new_runs[k] = "".join(out)
    # rebuild
    res, last = [], 0
    for k, r in enumerate(runs):
        res.append(pxml[last:r.start])
        res.append(new_runs[k])
        last = r.end
    res.append(pxml[last:])
    return "".join(res), good, skipped


def write(src: str, dst: str, plan: Dict[int, List[Change]], tracked: bool = True, author: str = "neveshtar", date: Optional[str] = None, comments: Optional[Dict[int, List[str]]] = None) -> Tuple[List[Change], List[Tuple[Change, str]]]:
    """Write ``dst`` = ``src`` with ``plan`` (paragraph number as returned by :func:`read` → changes) applied.
    Returns (applied, skipped-with-reason)."""
    date = _wdate(date)
    with zipfile.ZipFile(src) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    spans = paragraph_spans(xml)
    # map reported paragraph number -> span index
    number, omaps, n = {}, {}, 0
    for i, (a, b) in enumerate(spans):
        full, _ = para_text(xml[a:b])
        if full.replace(OBJ, "").strip():
            n += 1
            number[n] = i
            omaps[n] = [k for k, ch in enumerate(full) if ch != OBJ]
    ids = [900]
    applied: List[Change] = []
    skipped: List[Tuple[Change, str]] = []
    out, last = [], 0
    comments = comments or {}
    cid = [1000]
    cxml: List[str] = []
    edits = sorted(((number[p], p) for p in set(plan) | set(comments) if p in number))
    for si, p in edits:
        a, b = spans[si]
        out.append(xml[last:a])
        if p in plan:
            new, ok, sk = edit_paragraph(xml[a:b], plan[p], tracked, author, date, ids, omaps[p])
        else:
            new, ok, sk = xml[a:b], [], []
        if p in comments:
            starts, ends = "", ""
            for txt in comments[p]:
                cid[0] += 1
                starts += f'<w:commentRangeStart w:id="{cid[0]}"/>'
                ends += f'<w:commentRangeEnd w:id="{cid[0]}"/><w:r><w:commentReference w:id="{cid[0]}"/></w:r>'
                cxml.append(f'<w:comment w:id="{cid[0]}" w:author="{escape(author)}" w:date="{date}" w:initials="N"><w:p><w:r><w:t xml:space="preserve">{escape(txt)}</w:t></w:r></w:p></w:comment>')
            m0 = re.search(r"</w:pPr>", new)
            m1 = re.match(r"<w:p(?=[\s>/])[^>]*>", new)
            ins_at = m0.end() if m0 else (m1.end() if m1 else 0)
            new = new[:ins_at] + starts + new[ins_at:]
            new = new[:-len("</w:p>")] + ends + "</w:p>" if new.endswith("</w:p>") else new
        out.append(new)
        applied += ok
        skipped += sk
        last = b
    out.append(xml[last:])
    newxml = "".join(out)
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        names = set(zin.namelist())
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                data = newxml.encode("utf-8")
            elif cxml and item.filename == "word/comments.xml":
                t = data.decode("utf-8")
                data = t.replace("</w:comments>", "".join(cxml) + "</w:comments>").encode("utf-8")
            elif cxml and item.filename == "[Content_Types].xml" and "word/comments.xml" not in names:
                t = data.decode("utf-8")
                data = t.replace("</Types>", '<Override PartName="/word/comments.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/></Types>').encode("utf-8")
            elif cxml and item.filename == "word/_rels/document.xml.rels" and "word/comments.xml" not in names:
                t = data.decode("utf-8")
                data = t.replace("</Relationships>", '<Relationship Id="rIdNvComments" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" Target="comments.xml"/></Relationships>').encode("utf-8")
            zout.writestr(item, data)
        if cxml and "word/comments.xml" not in names:
            zout.writestr("word/comments.xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">' + "".join(cxml) + "</w:comments>")
    return applied, skipped
