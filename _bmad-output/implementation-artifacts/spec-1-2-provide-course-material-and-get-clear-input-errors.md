---
title: 'Story 1.2: Provide course material and get clear input errors'
type: 'feature'
created: '2026-11-28'
status: 'done'
baseline_commit: '5ee77b42d3cbbcb71b740b41aa603bd2fef91ff1'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The app shows only a title. There is no way to give it course material, and nothing stops unusable input from reaching Gemini later.

**Approach:** Add the "Your material" input (PDF tab and paste tab), the Generate button with the `is_running` mechanism, `errors.py`, `ingest.read_material` and the `ERROR_UI` table. A successful Generate shows a temporary "Read N words" confirmation that Story 1.3 replaces with the summary.

## Boundaries & Constraints

**Always:**
- Only `app.py` imports `streamlit`. `ingest.py` imports only `models`, `errors`, `pypdf` and the standard library.
- `ingest.read_material(source, pdf_name, pdf_bytes, text) -> str` checks in this order: `EmptyInput` → `EmptyFile` → `NotPdf` → `UnreadablePdf` → `NoExtractableText`. It tries `decrypt("")` on an encrypted PDF first. Any other exception while reading the PDF is printed and becomes `UnreadablePdf`. No bare `except:`, no OCR.
- Message texts exist only in `ERROR_UI`, exactly as in the I/O matrix, all with style `"error"`. There is one fallback row for unmapped `StudyBuddyError` types and one last-resort row for other exceptions, both "Something went wrong. Try Generate again."
- AD-7 mechanism: the button is drawn with `type="primary"`, `width="stretch"`, `disabled=is_running`, and an `on_click` that clears `last_error` and sets `is_running=True`. The pipeline runs at the error-area position under `st.spinner("Reading your material and writing the summary and quiz…")`, stores the result or `last_error`, sets `is_running=False` and calls `st.rerun()`. A failed Generate changes only `is_running` and `last_error`.
- Tabs come from `st.tabs(["Upload PDF", "Paste text"], key="source_tab", on_change="rerun")`. Widget keys are `pdf_upload` (`type=["pdf"]`, one file) and `paste_text`. Every widget has a visible label. Plain English, no emoji or exclamation marks.

**Never:**
- No Length/Language radios, no `llm`, `config`, `helpers` or `prompts/` (Story 1.3), no Gemini error rows (Story 1.4), no Demo mode (Story 3.1).
- No new dependencies and no new committed fixtures: encrypted and damaged PDFs are built inside the tests.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| PDF ok | `english_lecture.pdf` / `norwegian_lecture.pdf` | non-empty `str`; Norwegian text has æ, ø, å | N/A |
| Owner-password-only PDF | encrypted with `user_password=""`, owner set | text extracts | N/A |
| Paste ok | non-blank text | the same text as `str` | N/A |
| Nothing / blank | PDF tab with no upload, or text `None` / whitespace | — | `EmptyInput` → "Upload a PDF or paste some text first." |
| Empty file | 0 bytes | — | `EmptyFile` → "This file is empty. Choose another PDF." |
| Not a PDF | name not ending `.pdf` (case-insensitive), or bytes not starting `%PDF` | — | `NotPdf` → "Only PDF files are supported." |
| Locked / damaged | user password set, or `%PDF` header followed by garbage | — | `UnreadablePdf` → "This PDF can't be opened. It may be password-protected or damaged. Try another file, or paste the text instead." |
| Scanned | `scanned_lecture.pdf` | — | `NoExtractableText` → "This PDF has no readable text. It's probably scanned. Try a text-based version, or paste the text instead." |

</frozen-after-approval>

## Code Map

- `app.py` -- currently 5 lines: page config, title, caption. Keep them. Page order: title → `st.subheader("Your material")` → tabs → privacy caption → error area → Generate → `st.divider()` → result.
- `test_data/make_test_data.py` -- `slides_pdf(slides)`, `scanned_pdf()`, `NORWEGIAN_SLIDES`, `ENGLISH_SLIDES`; `main()` writes the files. Import it in a test with `importlib.util.spec_from_file_location` (it is not a package). Do not change it.
- `tests/test_test_data.py` -- existing existence test; keep it unchanged.
- `_bmad-output/implementation-artifacts/deferred-work.md` -- three Story 1.1 entries aimed at this story (fixture text checks, generator byte-compare, AppTest smoke). This spec covers all three.
- Streamlit 1.67.0: `st.tabs` accepts `key` and `on_change="rerun"`. Before the first render, `st.session_state.get("source_tab", "Upload PDF")` is the safe default.
- Run tools from `.venv/Scripts/python` (Python 3.13.17).

## Tasks & Acceptance

**Execution:**
- [x] `models.py` (new) -- only `Source(str, Enum)` with `PDF="pdf"` and `TEXT="text"`, plus `SOURCE_BY_TAB_LABEL = {"Upload PDF": Source.PDF, "Paste text": Source.TEXT}`. Story 1.3 adds the rest (staging rule).
- [x] `errors.py` (new) -- `StudyBuddyError(Exception)` and the five ingest subclasses, each with a one-line docstring.
- [x] `ingest.py` (new) -- `read_material` as in Boundaries. PDF text is page texts joined with `"\n"`. Pasted text is returned as given (not stripped).
- [x] `app.py` -- the input section, `ERROR_UI` with `show_error(exc)`, the Generate mechanism and the temporary result. On success, store `st.session_state.read_word_count = len(text.split())` (a temporary key, removed in Story 1.3) and show `st.success(f"Read {n:,} words from your material.")` under the divider. On failure, keep the previous `read_word_count`. Uploader label "Lecture PDF", text-area label "Your notes".
- [x] `tests/test_ingest.py` (new) -- every matrix row, the text path, and the check order (e.g. a 0-byte `.txt` gives `EmptyFile`, not `NotPdf`). Encrypted PDFs use `PdfWriter(clone_from=english_lecture.pdf)` plus `.encrypt(...)` into `BytesIO`. Also: each fixture opens with `PdfReader(strict=True)`.
- [x] `tests/test_fixtures_match_generator.py` (new) -- the two text PDFs from `slides_pdf(...)` equal the committed bytes. The scanned PDF is not byte-compared (zlib output varies between builds); its text extracts as whitespace only.
- [x] `tests/test_app.py` (new) -- `AppTest.from_file("app.py")`: title, subheader, privacy caption and button present, no exception. Blank paste plus Generate shows exactly one `st.error` with the no-input text. Valid paste on the Paste tab shows the "Read N words" success. Set the active tab through `at.session_state["source_tab"]` if `AppTest` cannot click tabs.

**Acceptance Criteria:**
- Given the app is open, when I look at "Your material", then I see the two tabs, the caption "Your material is sent to Google Gemini for processing. Nothing is saved." below them, and one full-width primary Generate button.
- Given content in both tabs with "Paste text" active, when I press Generate, then only the pasted text is used, and switching tabs afterwards keeps both the upload and the text.
- Given any invalid input from the matrix, when I press Generate, then exactly one `st.error` appears directly above Generate, the input stays in place, and no result is written.
- Given `.venv/Scripts/python -m pytest`, then all tests pass with no live API calls.

## Implementation Notes

- `models.py` is created here with only `Source` and `SOURCE_BY_TAB_LABEL`. Story 1.3 extends it rather than creating it.
- The encrypted-PDF tests use RC4-128. In the app, AES-encrypted PDFs need the `cryptography` package, which is installed today only as a transitive dependency.

## Spec Change Log

## Review Triage Log

Code review pass 1 (2026-11-28, reviewers: Blind Hunter (B), Edge Case Hunter (E), Verification Gap (V)):

| # | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|
| E4 | Generate is never drawn disabled during a run | medium | The pipeline block sets `is_running=False` and calls `st.rerun()` before `st.button` is reached, so `disabled=` is always False when drawn, and the stale button stays clickable under the spinner | patch (container for the error area, button drawn before the pipeline) |
| B1+E2 | Tab lookup outside `try` can leave `is_running` stuck | low | `SOURCE_BY_TAB_LABEL[...]` and the `pdf_upload` read run before the `try`; the fix moves two lines | patch |
| V1+V3+B4 | App upload path, tab routing with both inputs, 4 of 5 messages and both fallback rows untested | medium | `tests/test_app.py` only ever produces `EmptyInput` and never uploads | patch (AppTest cases) |
| V2 | Fallback rows in `show_error` untested | medium | Same evidence as above; a deleted row would be a `KeyError` crash that no test catches | patch (merged with V1 tests) |
| E1 | A rerun interrupt during the pipeline leaves `is_running` True | low | The next run repeats the pipeline with the current input, then resets. That is a restart, not a crash, and a `finally` would silently drop the run instead | reject |
| B3+E3 | An old error stays visible after the input changes | false | AD-7: `last_error` is cleared at the next Generate click, by design | reject |
| B5 | The `"warning"` branch in `show_error` is dead | false | AD-5 requires the style field; Story 1.4 adds the warning row for rate limits | reject |
| B6 | The spinner text mentions a summary and quiz | false | The UX text is fixed in the spec Boundaries; Story 1.3 makes it true | reject |
| B7+E5 | `%PDF` must be at byte 0 | low | AD-5 defines `NotPdf` as "bytes don't start with %PDF"; browser uploads don't prepend bytes | reject |
| B8+E6 | No size or page cap | low | Streamlit caps uploads at 200 MB by default; lecture PDFs are small; a cap would need a new error type outside the architecture | reject |
| B9 | `print` instead of `logging` | false | The architecture says to print the original exception to the console | reject |
| B10 | Streamlit pin not explained; the tests set `source_tab` directly | low | The version is pinned with `==`; AppTest cannot click tabs | reject |
| B11 | `sys.path` hack only in `test_ingest.py` | low | Only that file imports project modules; cosmetic | reject |
| E7 | Zero-width-only paste is accepted | low | Unlikely in normal use; the guard adds Unicode filtering | reject |

## Verification

**Commands:**
- `.venv/Scripts/python -m pytest -q` -- expected: all pass.
- `grep -l "import streamlit" *.py` -- expected: only `app.py`.

**Manual checks (if no CLI):**
- `.venv/Scripts/python -m streamlit run app.py --server.headless true`: upload `test_data/scanned_lecture.pdf` and press Generate to see the scanned message. Switch to Paste text, paste text and press Generate to see "Read N words". Switch back: the upload is still there.
