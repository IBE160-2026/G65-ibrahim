import streamlit as st

import ingest
from errors import (
    EmptyFile,
    EmptyInput,
    NoExtractableText,
    NotPdf,
    StudyBuddyError,
    UnreadablePdf,
)
from models import SOURCE_BY_TAB_LABEL, Source

TAB_LABELS = ["Upload PDF", "Paste text"]

FALLBACK_MESSAGE = "Something went wrong. Try Generate again."

# The only place message texts live. Each exact error type maps to (style, text).
ERROR_UI = {
    EmptyInput: ("error", "Upload a PDF or paste some text first."),
    EmptyFile: ("error", "This file is empty. Choose another PDF."),
    NotPdf: ("error", "Only PDF files are supported."),
    UnreadablePdf: (
        "error",
        "This PDF can't be opened. It may be password-protected or damaged. "
        "Try another file, or paste the text instead.",
    ),
    NoExtractableText: (
        "error",
        "This PDF has no readable text. It's probably scanned. "
        "Try a text-based version, or paste the text instead.",
    ),
    StudyBuddyError: ("error", FALLBACK_MESSAGE),  # fallback for unmapped StudyBuddyError types
    Exception: ("error", FALLBACK_MESSAGE),  # last resort for any other exception
}


def show_error(exc):
    """Show the one message ERROR_UI gives for this exception."""
    if type(exc) in ERROR_UI:
        style, text = ERROR_UI[type(exc)]
    elif isinstance(exc, StudyBuddyError):
        style, text = ERROR_UI[StudyBuddyError]
    else:
        style, text = ERROR_UI[Exception]
    if style == "warning":
        st.warning(text)
    else:
        st.error(text)


def start_generate():
    st.session_state.last_error = None
    st.session_state.is_running = True


def run_pipeline():
    """Read the material from the active tab only. Writes the result or last_error."""
    try:
        source = SOURCE_BY_TAB_LABEL[st.session_state.get("source_tab", TAB_LABELS[0])]
        upload = st.session_state.get("pdf_upload")
        if source == Source.PDF and upload is not None:
            text = ingest.read_material(source, upload.name, upload.getvalue(), None)
        elif source == Source.PDF:
            text = ingest.read_material(source, None, None, None)
        else:
            text = ingest.read_material(source, None, None, st.session_state.get("paste_text"))
        st.session_state.read_word_count = len(text.split())  # temporary, replaced in Story 1.3
    except Exception as exc:
        if not isinstance(exc, StudyBuddyError):
            print(f"Unexpected error during Generate: {exc!r}")
        st.session_state.last_error = exc


st.set_page_config(page_title="AI Study Buddy", layout="centered")

st.session_state.setdefault("is_running", False)
st.session_state.setdefault("last_error", None)

st.title("AI Study Buddy")
st.caption("Turn a lecture PDF or your notes into a summary and a 5-question quiz.")

st.subheader("Your material")
pdf_tab, text_tab = st.tabs(TAB_LABELS, key="source_tab", on_change="rerun")
with pdf_tab:
    st.file_uploader("Lecture PDF", type=["pdf"], accept_multiple_files=False, key="pdf_upload")
with text_tab:
    st.text_area("Your notes", key="paste_text", height=200)
st.caption("Your material is sent to Google Gemini for processing. Nothing is saved.")

# Error area: directly above Generate. Filled after the button is drawn,
# so the button is drawn disabled while the pipeline runs.
error_area = st.container()

st.button(
    "Generate",
    type="primary",
    width="stretch",
    disabled=st.session_state.is_running,
    on_click=start_generate,
)

with error_area:
    if st.session_state.is_running:
        with st.spinner("Reading your material and writing the summary and quiz…"):
            run_pipeline()
        st.session_state.is_running = False
        st.rerun()
    if st.session_state.last_error is not None:
        show_error(st.session_state.last_error)

st.divider()

if "read_word_count" in st.session_state:
    st.success(f"Read {st.session_state.read_word_count:,} words from your material.")
