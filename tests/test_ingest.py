import sys
from io import BytesIO
from pathlib import Path

import pytest
from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import ingest  # noqa: E402
from errors import (  # noqa: E402
    EmptyFile,
    EmptyInput,
    NoExtractableText,
    NotPdf,
    UnreadablePdf,
)
from models import Source  # noqa: E402

TEST_DATA = ROOT / "test_data"
FIXTURE_PDFS = ["english_lecture.pdf", "norwegian_lecture.pdf", "scanned_lecture.pdf"]


def fixture_bytes(name):
    return (TEST_DATA / name).read_bytes()


def read_pdf(name, data):
    return ingest.read_material(Source.PDF, name, data, None)


def encrypted_english(user_password, owner_password):
    writer = PdfWriter(clone_from=TEST_DATA / "english_lecture.pdf")
    writer.encrypt(user_password=user_password, owner_password=owner_password, algorithm="RC4-128")
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


# --- the committed fixtures --------------------------------------------------


@pytest.mark.parametrize("name", FIXTURE_PDFS)
def test_fixture_opens_strictly(name):
    reader = PdfReader(TEST_DATA / name, strict=True)
    assert len(reader.pages) >= 1


# --- PDF ok ------------------------------------------------------------------


def test_english_pdf_extracts_text():
    text = read_pdf("english_lecture.pdf", fixture_bytes("english_lecture.pdf"))
    assert isinstance(text, str)
    assert "Plate Tectonics" in text


def test_norwegian_pdf_keeps_special_letters():
    text = read_pdf("norwegian_lecture.pdf", fixture_bytes("norwegian_lecture.pdf"))
    assert text.strip()
    for letter in "æøå":
        assert letter in text


def test_pages_are_joined_with_newline():
    data = fixture_bytes("english_lecture.pdf")
    pages = [page.extract_text() or "" for page in PdfReader(BytesIO(data)).pages]
    assert read_pdf("english_lecture.pdf", data) == "\n".join(pages)


def test_upper_case_extension_is_accepted():
    assert read_pdf("LECTURE.PDF", fixture_bytes("english_lecture.pdf")).strip()


def test_owner_password_only_pdf_extracts():
    data = encrypted_english(user_password="", owner_password="owner-secret")
    assert PdfReader(BytesIO(data)).is_encrypted
    assert "Plate Tectonics" in read_pdf("locked.pdf", data)


# --- paste --------------------------------------------------------------------


def test_pasted_text_is_returned_as_given():
    text = "  Notes about photosynthesis.\n\nChlorophyll is green.  \n"
    assert ingest.read_material(Source.TEXT, None, None, text) == text


def test_text_source_ignores_pdf():
    data = fixture_bytes("english_lecture.pdf")
    assert ingest.read_material(Source.TEXT, "english_lecture.pdf", data, "Only this") == "Only this"


# --- errors, in check order -----------------------------------------------------


@pytest.mark.parametrize("text", [None, "", "   ", "\n\t \n"])
def test_blank_text_is_empty_input(text):
    with pytest.raises(EmptyInput):
        ingest.read_material(Source.TEXT, None, None, text)


def test_no_upload_is_empty_input():
    with pytest.raises(EmptyInput):
        ingest.read_material(Source.PDF, None, None, None)


def test_pdf_source_ignores_pasted_text():
    with pytest.raises(EmptyInput):
        ingest.read_material(Source.PDF, None, None, "Some pasted notes")


def test_zero_byte_pdf_is_empty_file():
    with pytest.raises(EmptyFile):
        read_pdf("empty.pdf", b"")


def test_zero_byte_non_pdf_is_empty_file_not_not_pdf():
    with pytest.raises(EmptyFile):
        read_pdf("notes.txt", b"")


def test_wrong_extension_is_not_pdf():
    with pytest.raises(NotPdf):
        read_pdf("english_lecture.txt", fixture_bytes("english_lecture.pdf"))


def test_missing_name_is_not_pdf():
    with pytest.raises(NotPdf):
        read_pdf(None, fixture_bytes("english_lecture.pdf"))


def test_wrong_header_is_not_pdf():
    with pytest.raises(NotPdf):
        read_pdf("notes.pdf", b"Hello, these are plain text notes.")


def test_garbage_without_header_is_not_pdf_not_unreadable():
    with pytest.raises(NotPdf):
        read_pdf("notes.pdf", b"\x00\x01garbage")


def test_user_password_pdf_is_unreadable():
    data = encrypted_english(user_password="student", owner_password="owner-secret")
    with pytest.raises(UnreadablePdf):
        read_pdf("locked.pdf", data)


def test_damaged_pdf_is_unreadable():
    with pytest.raises(UnreadablePdf):
        read_pdf("damaged.pdf", b"%PDF-1.4\n" + b"\x8f\x00garbage that is not a pdf" * 20)


def test_header_only_pdf_is_unreadable():
    with pytest.raises(UnreadablePdf):
        read_pdf("cut.pdf", b"%PDF-1.4\n")


def test_scanned_pdf_has_no_extractable_text():
    with pytest.raises(NoExtractableText):
        read_pdf("scanned_lecture.pdf", fixture_bytes("scanned_lecture.pdf"))
