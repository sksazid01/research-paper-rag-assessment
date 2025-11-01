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
        """
        Flush the current buffer of sentences into a finalized text chunk.

        Allocate the chunk and store the overlapping portion in the new buffer
        """
        # Use variables from parent scope (outside this inner function)
        nonlocal buf, buf_len, chunk_index

        # If the buffer is empty → nothing to flush
        if not buf:
            return

        # Join all sentence texts in the buffer into one single string
        # This becomes the actual text content of the chunk
        text = " ".join(s["text"] for s in buf).strip()

        # Determine the section name for this chunk
        # If buffer exists, take section of the first sentence;
        # otherwise, fall back to current_section or "Unknown"
        section = buf[0]["section"] if buf else current_section or "Unknown"

        # Get the starting and ending page numbers of this chunk
        page_start = buf[0]["page"]
        page_end = buf[-1]["page"]

        # Add the completed chunk to the list of chunks
        chunks.append(
            {
                "text": text,               # merged text from buffer sentences
                "section": section,         # section label (e.g., Introduction)
                "page_start": page_start,   # starting page number
                "page_end": page_end,       # ending page number
                "chunk_index": chunk_index, # sequential index (0, 1, 2, …)
            }
        )

        # Increment chunk counter for next chunk
        chunk_index += 1

        # Handle overlapping region between consecutive chunks
        if overlap_chars > 0:
            # We'll keep a short "tail" of recent sentences
            # whose combined length is roughly overlap_chars
            tail = []
            tail_len = 0

            # Walk backward through the buffer until overlap length reached
            for s in reversed(buf):
                if tail_len + len(s["text"]) + 1 > overlap_chars:
                    # Stop once we exceed the overlap threshold
                    break
                # Insert at beginning (to maintain original order)
                tail.insert(0, s)
                # Update the current overlap length counter
                tail_len += len(s["text"]) + 1

            # Retain only this tail as new buffer (for continuity)
            buf = tail
            buf_len = tail_len

        else:
            # If overlap disabled, clear buffer completely
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
