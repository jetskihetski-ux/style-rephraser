"""
Text extraction from PDF, DOCX, and TXT files.
"""

import io


def extract_text(file_bytes: bytes, filename: str) -> str:
    ext = filename.lower().split(".")[-1]

    if ext == "pdf":
        return _from_pdf(file_bytes)
    elif ext in ("docx", "doc"):
        return _from_docx(file_bytes)
    elif ext == "txt":
        return file_bytes.decode("utf-8", errors="ignore")
    else:
        return file_bytes.decode("utf-8", errors="ignore")


def _from_pdf(data: bytes) -> str:
    try:
        import fitz  # PyMuPDF
        doc  = fitz.open(stream=data, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
        return text.strip()
    except ImportError:
        return "[PyMuPDF not installed — pip install pymupdf]"
    except Exception as e:
        return f"[PDF extraction error: {e}]"


def _from_docx(data: bytes) -> str:
    try:
        from docx import Document
        doc  = Document(io.BytesIO(data))
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        return text.strip()
    except ImportError:
        return "[python-docx not installed — pip install python-docx]"
    except Exception as e:
        return f"[DOCX extraction error: {e}]"


def summarise_for_style(texts: list[str], max_chars: int = 6000) -> str:
    """Combine and trim reference texts to fit context window."""
    combined = "\n\n---\n\n".join(texts)
    if len(combined) > max_chars:
        combined = combined[:max_chars] + "\n\n[...truncated for context...]"
    return combined
