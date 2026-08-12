"""
Simple, dependency-free document chunker (section 20).
Splits on paragraphs first, then hard-wraps overly long paragraphs.
"""

def chunk_text(text: str, max_chars: int = 1000, overlap: int = 100) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks, buffer = [], ""
    for para in paragraphs:
        if len(buffer) + len(para) + 1 <= max_chars:
            buffer = f"{buffer}\n{para}".strip()
        else:
            if buffer:
                chunks.append(buffer)
            if len(para) > max_chars:
                for i in range(0, len(para), max_chars - overlap):
                    chunks.append(para[i:i + max_chars])
                buffer = ""
            else:
                buffer = para
    if buffer:
        chunks.append(buffer)
    return chunks
