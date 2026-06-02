# utils/resume_parser.py
# Handles PDF parsing using pdfplumber (fallback: PyMuPDF)

import io


def extract_text_from_pdf(uploaded_file) -> str:
    """
    Extract plain text from an uploaded PDF file object (Streamlit UploadedFile).
    Tries pdfplumber first, falls back to PyMuPDF (fitz).
    Returns the extracted text as a string.
    """
    text = ""

    # ── Try pdfplumber first ──────────────────────────────────────────
    try:
        import pdfplumber

        with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        uploaded_file.seek(0)  # reset file pointer for potential re-use
        return text.strip()

    except ImportError:
        pass  # pdfplumber not installed, try fitz
    except Exception as e:
        return f"Error reading PDF with pdfplumber: {str(e)}"

    # ── Fallback to PyMuPDF (fitz) ───────────────────────────────────
    try:
        import fitz  # PyMuPDF

        uploaded_file.seek(0)
        file_bytes = uploaded_file.read()
        doc = fitz.open(stream=file_bytes, filetype="pdf")

        for page in doc:
            text += page.get_text() + "\n"

        doc.close()
        uploaded_file.seek(0)
        return text.strip()

    except ImportError:
        return " No PDF library found. Please install pdfplumber: `pip install pdfplumber`"
    except Exception as e:
        return f"Error reading PDF with PyMuPDF: {str(e)}"


def clean_resume_text(text: str) -> str:
    """
    Basic cleanup of extracted resume text:
    - Remove excessive blank lines
    - Strip leading/trailing whitespace
    """
    lines = text.splitlines()
    cleaned = []
    prev_blank = False

    for line in lines:
        stripped = line.strip()
        if stripped == "":
            if not prev_blank:
                cleaned.append("")
            prev_blank = True
        else:
            cleaned.append(stripped)
            prev_blank = False

    return "\n".join(cleaned).strip()


def get_resume_stats(text: str) -> dict:
    """
    Return basic statistics about the extracted resume text.
    Useful for UI display before sending to AI.
    """
    words = text.split()
    lines = [l for l in text.splitlines() if l.strip()]
    return {
        "word_count": len(words),
        "line_count": len(lines),
        "char_count": len(text),
    }
