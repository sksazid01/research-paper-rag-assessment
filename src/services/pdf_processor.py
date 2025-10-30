import re
from typing import Dict, List, Tuple

from PyPDF2 import PdfReader
from pdfminer.high_level import extract_text


SECTION_PATTERNS = [
    # Flexible patterns: numbered sections, punctuation, case-insensitive
    ("Abstract", re.compile(r"^\s*(\d+[\.\)]\s*)?(abstract|summary)[\s:]*", re.I)),
    ("Introduction", re.compile(r"^\s*(\d+[\.\)]\s*)?(introduction|background)[\s:]*", re.I)),
    ("Methods", re.compile(r"^\s*(\d+[\.\)]\s*)?(research\s+)?method(ology|s)?|materials?\s*(and|&)\s*methods?[\s:]*", re.I)),
    ("Results", re.compile(r"^\s*(\d+[\.\)]\s*)?(results?|findings|experiments?|evaluation)[\s:]*", re.I)),
    ("Discussion", re.compile(r"^\s*(\d+[\.\)]\s*)?(discussion|analysis)[\s:]*", re.I)),
    ("Conclusion", re.compile(r"^\s*(\d+[\.\)]\s*)?(conclusions?|concluding\s+remarks|future\s+(work|directions?))[\s:]*", re.I)),
    ("References", re.compile(r"^\s*(\d+[\.\)]\s*)?(references|bibliography|citations?|works?\s+cited)[\s:]*", re.I)),
]


def _is_valid_title(text: str) -> bool:
    """Check if extracted text is a valid paper title."""
    if not text or len(text.strip()) < 10:
        return False
    
    text = text.strip()
    
    # Reject if it's just numbers, dots, or too short
    if re.match(r'^[\d\s\.\,\-]+$', text):
        return False
    
    # Reject if it's mostly numbers (like "253 255..260")
    words = text.split()
    if len(words) > 0:
        numeric_words = sum(1 for w in words if re.match(r'^\d+[\.\,\-\:]*$', w))
        if numeric_words / len(words) > 0.5:  # More than 50% numeric
            return False
    
    # Reject common non-title patterns
    reject_patterns = [
        r'^(page|pg\.?)\s*\d+',  # "Page 1"
        r'^\d+\s*(of|\/)?\s*\d+$',  # "1 of 10" or "1/10"
        r'^[\d\s\-\.]+$',  # Only numbers and separators
        r'^(figure|fig|table|tbl)\.?\s*\d+',  # "Figure 1"
    ]
    
    for pattern in reject_patterns:
        if re.match(pattern, text, re.I):
            return False
    
    return True


def _extract_pdf_metadata(file_path: str) -> Dict:
    reader = PdfReader(file_path)
    info = reader.metadata or {}
    title = getattr(info, "title", None) or None
    
    # Validate metadata title
    if title and not _is_valid_title(title):
        title = None
    
    authors = getattr(info, "author", None) or None

    # Fallback heuristics from first page text
    first_page_text = reader.pages[0].extract_text() or ""
    if not title:
        # Use first non-empty line before Abstract that looks like a title
        for line in first_page_text.splitlines()[:20]:  # Check first 20 lines only
            line_stripped = line.strip()
            if line_stripped and _is_valid_title(line_stripped):
                # Check it's not a section heading
                is_section = any(pat.search(line_stripped) for _, pat in SECTION_PATTERNS)
                if not is_section:
                    title = line_stripped
                    break
    
    if not authors:
        lines = [l.strip() for l in first_page_text.splitlines() if l.strip()]
        if lines:
            # assume authors appear right after title until Abstract
            try:
                t_idx = lines.index(title) if title and title in lines else 0
            except ValueError:
                t_idx = 0
            author_lines = []
            for l in lines[t_idx + 1 : min(t_idx + 8, len(lines))]:
                # Stop at section headers
                if any(pat.search(l) for _, pat in SECTION_PATTERNS):
                    break
                # Stop at lines that look like institutions/affiliations (contain numbers or URLs)
                if re.search(r'(university|institute|department|@|http|www\.|\d{5})', l, re.I):
                    break
                # Only include if it looks like names (has proper capitalization, reasonable length)
                if 5 < len(l) < 100 and not l.isupper() and not l.islower():
                    author_lines.append(l)
            if author_lines:
                authors = ", ".join(author_lines[:3])  # Limit to first 3 lines

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
            
            # Check if line matches any section pattern first (more lenient)
            matched = False
            for section_name, pattern in SECTION_PATTERNS:
                # Match if pattern found and line is reasonably short (not body text)
                if pattern.search(ln) and len(ln) < 100:
                    # Extra check: line should start with the pattern or be mostly the heading
                    match_obj = pattern.search(ln)
                    if match_obj and (match_obj.start() < 10 or ln.isupper()):
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


