"""Turn the user's course material (a PDF or pasted text) into plain text."""

from io import BytesIO

from pypdf import PdfReader

from errors import EmptyFile, EmptyInput, NoExtractableText, NotPdf, UnreadablePdf
from models import Source


def read_material(source, pdf_name, pdf_bytes, text) -> str:
    """Return the material as text, or raise a StudyBuddyError subclass.

    Checks run in this order: EmptyInput, EmptyFile, NotPdf, UnreadablePdf,
    NoExtractableText.
    """
    if source == Source.TEXT:
        if text is None or not text.strip():
            raise EmptyInput()
        return text

    if pdf_bytes is None:
        raise EmptyInput()
    if len(pdf_bytes) == 0:
        raise EmptyFile()
    if not (pdf_name or "").lower().endswith(".pdf") or not pdf_bytes.startswith(b"%PDF"):
        raise NotPdf()

    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        if reader.is_encrypted and not reader.decrypt(""):
            raise UnreadablePdf()
        page_texts = [page.extract_text() or "" for page in reader.pages]
    except UnreadablePdf:
        raise
    except Exception as exc:
        print(f"Could not read PDF {pdf_name!r}: {exc!r}")
        raise UnreadablePdf() from exc

    pdf_text = "\n".join(page_texts)
    if not pdf_text.strip():
        raise NoExtractableText()
    return pdf_text
