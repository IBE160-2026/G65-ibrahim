---
title: 'Story 1.1: Set up the project and open the app'
type: 'chore'
created: '2026-11-22'
status: 'done'
baseline_commit: '8ee8339ca9f601914b501154e36e778242b76f2e'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The repository has planning documents but no application code, so there is no runnable app and no fixed place for later stories to add modules, tests and sample inputs.

**Approach:** Hand-build the minimum skeleton from the architecture Structural Seed: pinned `requirements.txt`, an `app.py` that shows only the title and caption, a gitignore that covers both secret files, `.env.example`, the four `test_data/` files and one pytest smoke test.

## Boundaries & Constraints

**Always:**
- Python 3.13. Direct dependencies pinned with `==`: streamlit 1.67.0, google-genai 3.3.0, pypdf 7.1.0, pydantic 2.14.3, python-dotenv 1.2.4, pytest 9.2.0.
- `app.py` is the only file importing `streamlit`. Stock theme, `layout="centered"`, no sidebar, no custom CSS, HTML or `.streamlit/config.toml`.
- UI text in plain English, with no hype, emoji or exclamation marks.

**Never:**
- No other modules (`ingest`, `llm`, `models`, …), `prompts/`, `demo/`, `PROMPTS.md` or README changes. Later stories create them.
- No real API key anywhere in the repo. No `pip freeze` yet (that happens before the Story 3.2 deploy).
- Don't remove existing `.gitignore` entries.

**Decision (test data, 2026-11-24):** Mixed. The four committed `test_data/` files are generated: synthetic lecture slides on a neutral topic, about 10 slides each (one page per slide: a heading and 4–6 bullets, about 60–80 words per page, about 700 words per PDF), one Norwegian and one English (amended 2026-11-24 after the spec review), plus a mixed-language text file and an image-only scanned PDF with no text layer. They are built by a committed standard-library script, so they stay free of copyright issues. Real course PDFs go in a gitignored `test_data/private/` for manual runs only and are never committed.

</frozen-after-approval>

## Code Map

- `.gitignore` -- existing (Next.js + Python template). Already ignores `.env`, `.env.*` (keeps `!.env.example`), `.venv/`, `__pycache__/`, `.pytest_cache/`. Missing: `.streamlit/secrets.toml`.
- `README.md` -- course stub in Norwegian. Not touched (Story 3.3).
- `_bmad-output/planning-artifacts/architecture/architecture-G65-ibrahim-2026-11-16/ARCHITECTURE-SPINE.md` -- Structural Seed (file layout) and Stack table, which are the source for paths and pins.
- `_bmad-output/planning-artifacts/ux-designs/ux-G65-ibrahim-2026-11-15/DESIGN.md`, `EXPERIENCE.md` -- title, caption and voice rules.
- No existing Python code, tests or test data. No `.gitattributes`. The system gitconfig sets `core.autocrlf=true`.
- `.claude/skills/**/tests/` -- the BMAD skills' own tests. pytest must not collect them.
- Python 3.13.17 is at `C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe`. It may not be on PATH in already-open shells, and `python` there may resolve to the Microsoft Store stub, so use the full path to create `.venv`. Windows Application Control blocks the uv-managed Pythons under `AppData\Roaming\uv`.

## Tasks & Acceptance

**Execution:**
- [x] `requirements.txt` -- the six `==` pins listed above, one per line, with pytest under a `# dev` comment. This is the single install file the story ACs require.
- [x] `.gitignore` -- append `.streamlit/secrets.toml` under the Secrets block, and `test_data/private/` in its own block with a comment that real course PDFs go there. This covers NFR8 and the test-data decision.
- [x] `.gitattributes` (new) -- `*.pdf binary`, `*.txt text eol=lf`. This file comes first: this machine has `core.autocrlf=true`, and without it a clone would convert the LF line endings in the uncompressed PDFs and break their xref offsets.
- [x] `.env.example` -- `GEMINI_API_KEY=your-gemini-api-key-here`, plus commented-out optional `GEMINI_MODEL=gemini-3.5-flash-lite` ("used from Story 1.3") and `MOCK_MODE=false` ("used from Story 3.1"), each with a one-line explanation.
- [x] `app.py` -- `st.set_page_config(page_title="AI Study Buddy", layout="centered")`, `st.title("AI Study Buddy")`, `st.caption("Turn a lecture PDF or your notes into a summary and a 5-question quiz.")`. Nothing else. This is UX-DR1 and UX-DR2.
- [x] `test_data/make_test_data.py` -- a standard-library-only script (no new dependencies) that writes the files below from text kept in the script.
  - **Text PDFs:**
    - Each PDF is about 10 slide pages on one neutral topic. Each slide covers a distinct subtopic, with no repeated bullets.
    - Each page has a larger heading line and then bullet lines. Long bullets are wrapped with `textwrap.wrap`.
    - Text uses Helvetica, and the font dict includes `/Encoding /WinAnsiEncoding`.
    - Strings are encoded with `str.encode("cp1252")`, with `\`, `(` and `)` escaped.
  - **Scanned PDF:** one page holding only an 8-bit DeviceGray image XObject (`/FlateDecode`, `zlib.compress(..., 9)`, fixed size) that draws dark bars looking like text lines. It has no `/Font`, no `BT`/`Tj` operators and no hidden text layer.
  - **Mixed text file:** Norwegian and English paragraphs, written with `encoding="utf-8"`, `newline="\n"` and no BOM.
  - **Determinism:** no `/CreationDate` and no `/ID`. Objects are written in a fixed order, files are written with `open(..., "wb")`, and output paths are resolved from `Path(__file__).parent`. Every run produces the same bytes.
  - The docstring explains how to run the script and why the data is synthetic.
- [x] `test_data/` -- `norwegian_lecture.pdf`, `english_lecture.pdf`, `mixed_language_notes.txt`, `scanned_lecture.pdf`, generated by the script and committed. This is NFR7. `make_test_data.py` and the gitignored `private/` folder are deliberate extras. Later tests name files explicitly and never glob `test_data/`.
- [x] `tests/test_test_data.py` -- one test asserting the four files above exist and are non-empty, with paths resolved from the test file's location, not the working directory.

**Acceptance Criteria:**
- Given a fresh Python 3.13 venv, when `pip install -r requirements.txt` runs, then it succeeds and `pip show` reports the exact pinned versions.
- Given the install, when the app is started (see Verification), then the page shows the title and caption, centered, with no sidebar, and the console shows no errors or deprecation warnings other than google-genai's known `SyntaxWarning` lines, which only appear once it is imported (Story 1.3).
- Given the repo, when `git check-ignore` runs on `.env`, `.streamlit/secrets.toml` and a file under `test_data/private/`, then all three are ignored, and `git ls-files .env.example` lists the file after the story commit.
- Given the install, when `pytest` runs from the repo root, then exactly 1 test passes. This relies on pytest's default `norecursedirs`, which skips `.claude/`, where the BMAD skills keep their own tests.
- Given the generated PDFs opened with `PdfReader(path, strict=True)`, when text is extracted, then:
  - every PDF opens without an xref error;
  - the English PDF returns non-empty text;
  - the Norwegian PDF's text contains "æ", "ø" and "å";
  - the scanned PDF returns whitespace only.

  This is checked with a command here, since Story 1.2 adds the automated tests.

## Implementation Notes

- Decks: Norwegian "Vannets kretsløp" and English "Introduction to Plate Tectonics", 10 landscape slides each with a heading and 6 bullets. They are about 670 words per PDF (726 tokens extracted for the Norwegian deck). The mixed notes are about photosynthesis.
- `.venv` was created with the full path to Python 3.13.17. The pins were verified with `pip freeze`.
- App: checked headless (HTTP 200, health ok, no console errors) and with `AppTest` (title, caption, empty sidebar). It has not been viewed in a real browser yet.

## Spec Change Log

## Review Triage Log

- 2026-11-24, pre-approval spec review (subagent). These findings were applied to the spec:
  - git autocrlf would break the PDFs → `.gitattributes` (high);
  - WinAnsi/cp1252 encoding detail and an æøå AC (medium);
  - determinism rules (medium);
  - 10 full pages was unrealistic → 10 slides, decided by the user (medium);
  - UTF-8 text file (medium);
  - scanned-PDF construction (medium);
  - extra files in `test_data/` (low);
  - headless streamlit run (low);
  - CLI checks for the ACs (low);
  - `.env.example` story notes (low);
  - pytest collection note (low).

Code review pass 1 (2026-11-24, reviewers: Blind Hunter (B), Edge Case Hunter (E), Verification Gap (V)):

| # | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|
| B1 | Docstring says "run from anywhere" but gives a relative, Windows-only path | low | The relative `test_data/...` path resolves only from the repo root, and `.venv/bin` is not mentioned | patch |
| B2+E4 | "Same bytes every run" fails across zlib builds | low | `zlib.compress(...,9)` output depends on the zlib implementation (CPython builds differ); a regenerated file on another machine shows a diff | patch (narrow the docstring claim) |
| B3+V2+E5 | No test that the committed fixtures match the generator | medium | `tests/test_test_data.py` checks only existence and size | defer → Story 1.2 (frozen intent: one smoke test) |
| V1 | No automated test of PDF strict open, æøå, scanned has no text | medium | Only a manual CLI check in Verification | defer → Story 1.2 |
| V3 | No AppTest of title/caption | low | No test imports `app.py` | defer → first story that extends `app.py` |
| B4 | pytest collection relies on default `norecursedirs` | low | Real, but already documented in the AC; fix adds a config file | reject (unlikely, adds surface) |
| B5 | Python version not recorded in repo | low | Cloud picks the version in Advanced settings (architecture); README is Story 3.3 | reject |
| B6 | pytest installed in prod | low | Deliberate: Story 1.1 AC requires one `requirements.txt` that installs pytest | reject |
| B7 | File list duplicated in test and generator | low | 4 names; a mismatch fails loudly | reject (cosmetic) |
| B8 | `.env.example` silent on `secrets.toml` | low | `.gitignore` adds it but the example never mentions it | patch |
| B9 | `.gitattributes` lacks `* text=auto` | low | Only PDFs are byte-sensitive; a repo-wide renormalize adds churn | reject |
| B10 | Wrapped bullet continuation slightly misaligned | low | "• " is wider than 2 spaces in Helvetica; cosmetic, extraction unaffected | reject (fix adds per-glyph offsets) |
| B11+E2 | No guard against vertical overflow | low | Current content fits; only a future edit could overflow | reject (adds a guard for an unshown state) |
| E1 | Non-cp1252 char crashes the generator | false | It fails loudly with UnicodeEncodeError on content nobody has written; correct behaviour | reject |
| E3 | Char-count wrap may exceed the right edge | false | 80 chars × ~7 pt average at 14 pt ≈ 560 pt < 648 pt usable; all current lines fit | reject |

## Verification

**Commands:**
- `python -m venv .venv` then `.venv/Scripts/python -m pip install -r requirements.txt` -- expected: success.
- `.venv/Scripts/python -m pytest` -- expected: 1 passed.
- `git check-ignore .env .streamlit/secrets.toml test_data/private/x.pdf` -- expected: all three paths printed.
- `.venv/Scripts/python test_data/make_test_data.py` then `git status --short test_data` -- expected: no diff (the output is deterministic).
- `.venv/Scripts/python -c "import pypdf,sys;[print(p, ascii(' '.join(pg.extract_text() for pg in pypdf.PdfReader(p,strict=True).pages)[:120])) for p in sys.argv[1:]]" test_data/norwegian_lecture.pdf test_data/english_lecture.pdf test_data/scanned_lecture.pdf` -- expected: no errors. The Norwegian line shows `\xe6`, `\xf8` and `\xe5`, and the scanned line is empty. `ascii()` avoids cp1252 console errors.

**Manual checks (if no CLI):**
- `.venv/Scripts/python -m streamlit run app.py --server.headless true`, then open the printed URL. Expected: the title and caption render, with a centered layout and no sidebar. Using `--server.headless` skips Streamlit's first-run email prompt.
