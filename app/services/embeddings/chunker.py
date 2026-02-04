from typing import List, Dict
import re


def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    metadata: Dict = None
) -> List[Dict]:
    """
    Split text into overlapping chunks with metadata.

    Returns list of dicts with 'content' and 'metadata' keys.
    """
    if not text.strip():
        return []

    # Clean text
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size

        # Try to break at sentence boundary
        if end < text_len:
            # Look for sentence end within last 100 chars of chunk
            search_start = max(end - 100, start)
            last_period = text.rfind('. ', search_start, end)
            last_newline = text.rfind('\n', search_start, end)
            break_point = max(last_period, last_newline)
            if break_point > start:
                end = break_point + 1

        chunk_text = text[start:end].strip()
        if chunk_text:
            chunk_data = {
                "content": chunk_text,
                "metadata": {
                    **(metadata or {}),
                    "start_char": start,
                    "end_char": end,
                }
            }
            chunks.append(chunk_data)

        start = end - chunk_overlap if end < text_len else text_len

    return chunks


def chunk_markdown(text: str, metadata: Dict = None) -> List[Dict]:
    """
    Split markdown by headers, then chunk each section.
    Preserves header context in metadata.
    """
    chunks = []

    # Split by headers (## or ###)
    sections = re.split(r'\n(#{2,3}\s+[^\n]+)\n', text)

    current_header = ""
    for i, section in enumerate(sections):
        if re.match(r'^#{2,3}\s+', section):
            current_header = section.strip()
            continue

        if section.strip():
            section_metadata = {
                **(metadata or {}),
                "header": current_header,
            }
            section_chunks = chunk_text(section, metadata=section_metadata)
            chunks.extend(section_chunks)

    return chunks
