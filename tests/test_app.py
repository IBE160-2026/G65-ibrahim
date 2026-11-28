import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import ingest  # noqa: E402
from errors import StudyBuddyError  # noqa: E402

APP = str(ROOT / "app.py")

NO_INPUT = "Upload a PDF or paste some text first."
PRIVACY = "Your material is sent to Google Gemini for processing. Nothing is saved."


def fresh_app():
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    return at


def generate(at):
    buttons = [b for b in at.button if b.label == "Generate"]
    assert len(buttons) == 1
    buttons[0].click().run()


def test_landing_page_renders():
    at = fresh_app()
    assert not at.exception
    assert at.title[0].value == "AI Study Buddy"
    assert any(s.value == "Your material" for s in at.subheader)
    assert any(c.value == PRIVACY for c in at.caption)
    assert [t.label for t in at.tabs] == ["Upload PDF", "Paste text"]
    assert [b.label for b in at.button] == ["Generate"]
    assert at.text_area(key="paste_text").label == "Your notes"
    assert len(at.error) == 0
    assert len(at.success) == 0


def test_blank_paste_shows_one_no_input_error():
    at = fresh_app()
    at.session_state["source_tab"] = "Paste text"
    at.text_area(key="paste_text").input("   \n  ")
    generate(at)
    assert not at.exception
    assert [e.value for e in at.error] == [NO_INPUT]
    assert len(at.success) == 0
    assert at.text_area(key="paste_text").value == "   \n  "
    assert at.session_state["is_running"] is False


def test_pdf_tab_without_upload_shows_one_no_input_error():
    at = fresh_app()
    generate(at)
    assert not at.exception
    assert [e.value for e in at.error] == [NO_INPUT]


def test_valid_paste_shows_word_count():
    at = fresh_app()
    at.session_state["source_tab"] = "Paste text"
    at.text_area(key="paste_text").input("Photosynthesis turns light into sugar in plants.")
    generate(at)
    assert not at.exception
    assert len(at.error) == 0
    assert [s.value for s in at.success] == ["Read 7 words from your material."]


def test_failed_generate_keeps_previous_result():
    at = fresh_app()
    at.session_state["source_tab"] = "Paste text"
    at.text_area(key="paste_text").input("One two three")
    generate(at)
    at.text_area(key="paste_text").input("")
    generate(at)
    assert not at.exception
    assert [e.value for e in at.error] == [NO_INPUT]
    assert [s.value for s in at.success] == ["Read 3 words from your material."]


# --- upload path and every ERROR_UI row ------------------------------------

TEST_DATA = ROOT / "test_data"
FALLBACK = "Something went wrong. Try Generate again."
UNREADABLE = (
    "This PDF can't be opened. It may be password-protected or damaged. "
    "Try another file, or paste the text instead."
)
SCANNED = (
    "This PDF has no readable text. It's probably scanned. "
    "Try a text-based version, or paste the text instead."
)


def upload(at, name, data):
    at.file_uploader(key="pdf_upload").set_value((name, data, "application/pdf")).run()


def english_word_count():
    pdf = (TEST_DATA / "english_lecture.pdf").read_bytes()
    return len(ingest.read_material("pdf", "english_lecture.pdf", pdf, None).split())


def test_valid_upload_shows_word_count():
    at = fresh_app()
    upload(at, "english_lecture.pdf", (TEST_DATA / "english_lecture.pdf").read_bytes())
    generate(at)
    assert not at.exception
    assert len(at.error) == 0
    assert [s.value for s in at.success] == [f"Read {english_word_count():,} words from your material."]


@pytest.mark.parametrize(
    "name, data, message",
    [
        ("empty.pdf", b"", "This file is empty. Choose another PDF."),
        ("notes.pdf", b"Plain text notes, not a PDF.", "Only PDF files are supported."),
        ("damaged.pdf", b"%PDF-1.4\n" + b"\x8f\x00garbage" * 20, UNREADABLE),
        ("scanned_lecture.pdf", (TEST_DATA / "scanned_lecture.pdf").read_bytes(), SCANNED),
    ],
)
def test_invalid_upload_shows_one_exact_error(name, data, message):
    at = fresh_app()
    upload(at, name, data)
    generate(at)
    assert not at.exception
    assert [e.value for e in at.error] == [message]
    assert len(at.success) == 0


def test_paste_tab_uses_only_pasted_text_when_both_filled():
    at = fresh_app()
    upload(at, "english_lecture.pdf", (TEST_DATA / "english_lecture.pdf").read_bytes())
    at.session_state["source_tab"] = "Paste text"
    at.text_area(key="paste_text").input("One two three")
    generate(at)
    assert not at.exception
    assert [s.value for s in at.success] == ["Read 3 words from your material."]


class UnmappedError(StudyBuddyError):
    """A StudyBuddyError subclass with no ERROR_UI row."""


@pytest.mark.parametrize("error", [UnmappedError(), RuntimeError("boom")])
def test_unmapped_errors_show_fallback(monkeypatch, error):
    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(ingest, "read_material", fail)
    at = fresh_app()
    at.session_state["source_tab"] = "Paste text"
    at.text_area(key="paste_text").input("Some notes")
    generate(at)
    assert not at.exception
    assert [e.value for e in at.error] == [FALLBACK]
    assert at.session_state["is_running"] is False
