from typing import Dict, List


def chunk_sentences(
    sentences: List[Dict],
    max_chars: int = 1000,
    overlap_chars: int = 150,
) -> List[Dict]:
    """
    Group sentences into chunks preserving section boundaries.
    Each chunk has: text, section, page_start, page_end, chunk_index.
    """
    chunks: List[Dict] = []
    buf: List[Dict] = []
    buf_len = 0
    chunk_index = 0
    current_section = None

    def flush_buffer():
        nonlocal buf, buf_len, chunk_index
        if not buf:
            return
        text = " ".join(s["text"] for s in buf).strip()
        section = buf[0]["section"] if buf else current_section or "Unknown"
        page_start = buf[0]["page"]
        page_end = buf[-1]["page"]
        chunks.append(
            {
                "text": text,
                "section": section,
                "page_start": page_start,
                "page_end": page_end,
                "chunk_index": chunk_index,
            }
        )
        chunk_index += 1
        # overlap: keep tail sentences until overlap_chars
        if overlap_chars > 0:
            tail = []
            tail_len = 0
            for s in reversed(buf):
                if tail_len + len(s["text"]) + 1 > overlap_chars:
                    break
                tail.insert(0, s)
                tail_len += len(s["text"]) + 1
            buf = tail
            buf_len = tail_len
        else:
            buf = []
            buf_len = 0

    for s in sentences:
        sec = s.get("section") or "Unknown"
        if current_section is None:
            current_section = sec
        # If section changes and buffer not empty, flush to keep sections isolated
        if sec != current_section and buf:
            flush_buffer()
            current_section = sec

        # If adding this sentence exceeds max_chars, flush first
        s_len = len(s["text"]) + 1
        if buf_len + s_len > max_chars and buf:
            flush_buffer()
        buf.append(s)
        buf_len += s_len

    # Final flush
    flush_buffer()

    return chunks
