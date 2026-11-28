import importlib.util
from pathlib import Path

from pypdf import PdfReader

TEST_DATA = Path(__file__).resolve().parent.parent / "test_data"


def load_generator():
    spec = importlib.util.spec_from_file_location("make_test_data", TEST_DATA / "make_test_data.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_english_pdf_matches_generator():
    gen = load_generator()
    assert gen.slides_pdf(gen.ENGLISH_SLIDES) == (TEST_DATA / "english_lecture.pdf").read_bytes()


def test_norwegian_pdf_matches_generator():
    gen = load_generator()
    assert gen.slides_pdf(gen.NORWEGIAN_SLIDES) == (TEST_DATA / "norwegian_lecture.pdf").read_bytes()


def test_scanned_pdf_text_is_whitespace_only():
    # Not byte-compared: zlib output can differ between builds.
    reader = PdfReader(TEST_DATA / "scanned_lecture.pdf", strict=True)
    text = "".join(page.extract_text() or "" for page in reader.pages)
    assert text.strip() == ""
