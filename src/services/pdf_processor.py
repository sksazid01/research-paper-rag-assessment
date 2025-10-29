import re
from typing import Dict, List, Tuple

from PyPDF2 import PdfReader
from pdfminer.high_level import extract_text


SECTION_PATTERNS = [
    ("Abstract", re.compile(r"^\s*(abstract|summary)\s*$", re.I)),
    ("Introduction", re.compile(r"^\s*(introduction|background)\s*$", re.I)),
    ("Methods", re.compile(r"^\s*(methods?|methodology|materials? and methods?)\s*$", re.I)),
    ("Results", re.compile(r"^\s*(results?|findings)\s*$", re.I)),
    ("Discussion", re.compile(r"^\s*(discussion)\s*$", re.I)),
    ("Conclusion", re.compile(r"^\s*(conclusions?|concluding\s+remarks)\s*$", re.I)),
    ("References", re.compile(r"^\s*(references|bibliography)\s*$", re.I)),
]


def _extract_pdf_metadata(file_path: str) -> Dict:
    reader = PdfReader(file_path)
    info = reader.metadata or {}
    title = getattr(info, "title", None) or None
    authors = getattr(info, "author", None) or None

    # Fallback heuristics from first page text
    first_page_text = reader.pages[0].extract_text() or ""
    if not title:
        # Use first non-empty line before Abstract
        for line in first_page_text.splitlines():
            if line.strip() and not any(pat.search(line) for _, pat in SECTION_PATTERNS):
                title = line.strip()
                break
    if not authors:
        lines = [l.strip() for l in first_page_text.splitlines() if l.strip()]
        if lines:
            # assume authors appear right after title until Abstract
            try:
                t_idx = lines.index(title) if title in lines else 0
            except ValueError:
                t_idx = 0
            author_lines = []
            for l in lines[t_idx + 1 : t_idx + 6]:
                if any(pat.search(l) for _, pat in SECTION_PATTERNS):
                    break
                author_lines.append(l)
            if author_lines:
                authors = ", ".join(author_lines)

    year_match = re.search(r"(19|20)\d{2}", first_page_text)
    year = year_match.group(0) if year_match else None

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "pages": len(reader.pages),
    }


def extract_pages_text(file_path: str) -> List[Tuple[int, str]]:
    """Return list of (page_number starting at 1, text) using pdfminer for better layout.
    """
    reader = PdfReader(file_path)
    num_pages = len(reader.pages)
    pages: List[Tuple[int, str]] = []
    for i in range(num_pages):
        # pdfminer works across entire doc; we can extract per-page by caching page numbers
        # Simpler: fall back to PyPDF2 per page to avoid overhead
        text = reader.pages[i].extract_text() or ""
        pages.append((i + 1, text))
    return pages


def extract_sections_and_sentences(file_path: str):
    """
    Parse PDF with basic section awareness and return:
    - meta: {title, authors, year, pages}
    - sentences: [{text, page, section}]
    """
    meta = _extract_pdf_metadata(file_path)
    pages = extract_pages_text(file_path)

    current_section = "Unknown"
    sentences: List[Dict] = []

    # iterate pages and lines to detect headings
    for page_no, page_text in pages:
        lines = [ln.strip() for ln in (page_text or "").splitlines()]
        for ln in lines:
            if not ln:
                continue
            # Heading detection
            matched = False
            for section_name, pattern in SECTION_PATTERNS:
                if pattern.match(ln):
                    current_section = section_name
                    matched = True
                    break
            if matched:
                continue
            # Split into sentences (simple heuristic)
            for sent in re.split(r"(?<=[.!?])\s+(?=[A-Z(\[])", ln):
                st = sent.strip()
                if st:
                    sentences.append({"text": st, "page": page_no, "section": current_section})

    return meta, sentences


