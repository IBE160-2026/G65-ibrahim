---
stepsCompleted: ["step-01-validate-prerequisites", "step-02-design-epics", "step-03-create-stories", "step-04-final-validation"]
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-G65-ibrahim-2026-10-18/prd.md
  - _bmad-output/planning-artifacts/architecture/architecture-G65-ibrahim-2026-11-16/ARCHITECTURE-SPINE.md
  - _bmad-output/planning-artifacts/ux-designs/ux-G65-ibrahim-2026-11-15/DESIGN.md
  - _bmad-output/planning-artifacts/ux-designs/ux-G65-ibrahim-2026-11-15/EXPERIENCE.md
---

# AI Study Buddy (G65-ibrahim) - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for AI Study Buddy (G65-ibrahim), decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: User can upload a text-based PDF as Course Material; the system extracts its text directly, with no OCR.
FR2: User can paste plain text as Course Material instead of uploading a PDF; it is used exactly like extracted PDF text.
FR3: A PDF with no extractable text (scanned or image-based) produces a specific, human-readable error, not a blank result or an unhandled exception.
FR4: Invalid uploads (wrong file type, 0-byte file) are rejected with a clear error before any Gemini API call.
FR5: User selects summary Length before generating: short (<150 words), medium (150–400), long (400–800).
FR6: User selects Output Language (Norwegian or English), independent of the source language; it applies to both Summary and Quiz.
FR7: The system generates a structured Summary via the Gemini API using an engineered prompt (not a raw pass-through), respecting Length and Output Language.
FR8: The system generates a Quiz of at least 5 questions in the same request as the Summary; each question is multiple choice with exactly 4 options and exactly 1 correct option, stored as the Answer Key before the user answers.
FR9: User can submit Quiz answers and see, per question, whether each matched the Answer Key.
FR10: Summary and Quiz are shown together in one results view, reachable without extra navigation.
FR11: A visible loading indicator is shown while waiting for the Gemini response.
FR12: User can turn on Demo mode with an in-app toggle (on at start when `MOCK_MODE=true`); Generate then returns a saved example Summary and Quiz without calling Gemini, always labelled as example output.

### NonFunctional Requirements

NFR1 (Performance): Summary + Quiz for a typical 10–20 slide PDF return within ~30 seconds under normal free-tier conditions.
NFR2 (Cost): Gemini free tier only, for development, demo and grading; rate limits are handled by waiting/retrying, not by upgrading.
NFR3 (Privacy): No accounts and no server-side storage of uploads or results. The README discloses that material is sent to Google Gemini, and that free-tier input is used to improve Google products.
NFR4 (Maintainability): Stack and feature set stay narrow enough that a Python beginner can build, test and explain all of it.
NFR5 (AI governance): Prompt engineering is deliberate and documented; output is requested as structured JSON; prompt iterations are logged durably (`PROMPTS.md`).
NFR6 (Testing): Automated tests for PDF extraction (success and scanned-PDF failure), invalid-upload rejection, length/language handling and answer checking; a manual checklist for summary quality, run against real lecture notes.
NFR7 (Test data): A dedicated test-data folder with a Norwegian PDF, an English PDF, mixed-language text and a scanned/invalid PDF, used to verify FR1–FR9 before submission.
NFR8 (Secrets): API key in `.env` or `.streamlit/secrets.toml`, both gitignored; `.env.example` with placeholder values is committed.
NFR9 (Runnability): A README lets someone unfamiliar with the project set up, get a free Gemini key and run the app end to end; a grader can also run it in Demo mode without a key (SM-2).
NFR10 (Deployment): Runs locally and on Streamlit Community Cloud (free tier).
NFR11 (Counter-metric): Summary length compliance must not be reached by padding output with filler (SM-C1).

### Additional Requirements

From the architecture spine (`ARCHITECTURE-SPINE.md`):

- **No starter template.** Epic 1 Story 1 sets up the project skeleton by hand: the module layout from the Structural Seed, `requirements.txt` with `==` pins, `.gitignore`, `.env.example`, and a runnable empty `app.py`.
- **Pinned stack:** Python 3.13, streamlit 1.67.0, google-genai 3.3.0, pypdf 7.1.0, pydantic 2.14.3, python-dotenv 1.2.4, pytest 9.2.0 (dev); model `gemini-3.5-flash-lite`, overridable with `GEMINI_MODEL`.
- **AD-1:** Only `app.py` imports `streamlit`; core modules (`ingest`, `llm`, `demo`, `quiz`, `models`, `errors`, `config`) are plain Python. Pipeline modules never import each other or `app.py`.
- **AD-2:** Exactly one `generate_content` call per Generate, returning one `StudyPack` JSON via `response_mime_type="application/json"` and `response_schema=StudyPack`; no automatic retries.
- **AD-3:** `StudyPack` (summary: title + sections of heading/bullets; quiz: ≥5 questions, 4 options, `correct_index` 0–3, explanation) is defined once in `models.py`; live and demo output are both validated through it.
- **AD-4:** Only `llm.py` creates `genai.Client`; entry point `generate_study_pack(text, length, language, settings) -> StudyPack`; missing key raises `MissingApiKey` before any call.
- **AD-5:** Core raises only `StudyBuddyError` subclasses (`EmptyInput`, `EmptyFile`, `NotPdf`, `NoExtractableText`, `MissingApiKey`, `RateLimited`, `GeminiUnavailable`, `BadModelResponse`); `app.py` maps each to exactly one UX message.
- **AD-6:** `ingest.py` validates input and returns one non-empty `str` (whitespace-only counts as empty) before any API call.
- **AD-7:** Fixed session-state keys: `study_pack`, `is_demo`, `input_fingerprint` (written only by Generate); `quiz_answers`, `quiz_checked` (written only by the quiz form and Try again, cleared by Generate). Nothing written to disk.
- **AD-8:** Prompt templates live in `prompts/`; the schema is passed only via `response_schema`; every prompt change is logged in `PROMPTS.md`.
- **AD-9:** `config.load_settings(secrets)` is the only reader of `GEMINI_API_KEY`, `MOCK_MODE` and `GEMINI_MODEL`; `app.py` passes `st.secrets` in; the key is never logged or displayed.
- **AD-10:** Demo mode calls `demo.load_study_pack()` (reads `demo/study_pack.json`, validated as `StudyPack`) and skips `ingest` and `llm`.
- **AD-11:** Tests never call the live API; `llm`'s network call is monkeypatched; sample inputs live in `test_data/`.
- **Conventions:** `Length` enum (`short`/`medium`/`long`) and `Language` enum (`en`/`no`) plus the word-range table live in `models.py`; word count is `len(text.split())` over headings and bullets, computed by the app; `quiz_answers` is `list[int | None]` in quiz order.
- **Deployment:** local `streamlit run app.py`; Streamlit Community Cloud from GitHub `main` with Python 3.13 chosen in Advanced settings and the key in Cloud Secrets. No CI, no database, no logging service.

### UX Design Requirements

From `DESIGN.md` and `EXPERIENCE.md`:

UX-DR1: Stock Streamlit theme with no custom CSS, injected HTML or `config.toml` theme overrides; `layout="centered"`, no sidebar.
UX-DR2: Fixed top-to-bottom order: title "AI Study Buddy" with a one-line caption → "Your material" input → options → error area → Generate button → divider → results.
UX-DR3: Input tabs "Upload PDF" (`st.file_uploader(type=["pdf"])`, one file) and "Paste text" (`st.text_area`); only the active tab's content is used, and switching tabs does not clear the other tab. Implementation note: the active tab is read with `st.tabs(..., key=..., on_change="rerun")` and `st.session_state[key]` (current Streamlit API).
UX-DR4: An always-visible privacy caption under the input tabs: "Your material is sent to Google Gemini for processing. Nothing is saved."
UX-DR5: Length as a horizontal radio (Short / Medium / Long), default Medium, each option captioned with its word range.
UX-DR6: Output Language as a horizontal radio (English / Norsk), default English, side by side with Length.
UX-DR7: Demo mode `st.toggle` under the options, labelled "Demo mode (example output, no API key needed)", off by default unless `MOCK_MODE=true`; never primary-styled.
UX-DR8: Generate is the only primary button on the page (full width); it is disabled while running and shows the spinner "Reading your material and writing the summary and quiz…".
UX-DR9: Error area directly above Generate, one message per problem, with the exact texts from the State Patterns table: no input, wrong file type, empty file, scanned PDF, missing API key (pointing to the README and Demo mode), rate limit (`st.warning`), timeout/network, unusable model response. Every error keeps what the user entered.
UX-DR10: Results tabs "Summary" and "Quiz" appear only after a successful Generate, opening on Summary.
UX-DR11: Summary rendered as markdown topic headings with bullets, plus the caption "{N} words · {length} · {language}"; raw model output is never shown.
UX-DR12: Quiz in one `st.form`: 5 numbered questions, each a 4-option radio with no preselected answer; "Check answers" (not primary) runs only when all are answered, otherwise `st.warning` "Answer all questions first. Missing: 2, 4." with choices kept.
UX-DR13: After checking: score line `st.info` "You got X of 5 right"; under each question `st.success` "✅ Correct" or `st.error` "❌ Incorrect — correct answer: …"; radios keep the user's choices; "Try again" clears answers and results with no new API call.
UX-DR14: Stale-results note `st.info` "Settings changed. Press Generate to update." when input, Length, Output Language or Demo mode changes after a generation; old results stay until regenerated.
UX-DR15: In Demo mode, a persistent `st.warning` banner "Demo mode — example output, not generated from your material." at the top of the results, visible on both tabs.
UX-DR16: Accessibility floor: every widget has a visible label; correct/incorrect never by colour alone; summary uses real headings; tab order follows the visual order.
UX-DR17: Microcopy in plain English for all UI chrome (no hype, emoji or exclamation marks except the quiz result icons); generated content follows Output Language.

### FR Coverage Map

FR1: Epic 1 - Upload a text-based PDF and extract its text
FR2: Epic 1 - Paste text as an alternative input
FR3: Epic 1 - Clear error for scanned/image PDFs
FR4: Epic 1 - Reject wrong file type and empty files before any API call
FR5: Epic 1 - Choose summary Length
FR6: Epic 1 - Choose Output Language for Summary and Quiz
FR7: Epic 1 - Generate the structured Summary with an engineered prompt
FR8: Epic 1 - Generate the Quiz and Answer Key in the same request
FR9: Epic 2 - Answer the Quiz and see per-question results
FR10: Epic 1 + Epic 2 - Summary view (Epic 1), Summary and Quiz tabs together (Epic 2)
FR11: Epic 1 - Loading indicator while Gemini responds
FR12: Epic 3 - Demo mode with saved example output

## Epic List

### Epic 1: Turn course material into a summary
Abdiaziz uploads a lecture PDF or pastes notes, chooses Length and Output Language, and gets a structured summary, with clear messages for every invalid input and every Gemini failure. Includes the hand-built project setup and the test-data folder.
**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR6, FR7, FR8, FR10 (Summary), FR11

### Epic 2: Self-test with the quiz
Abdiaziz answers the 5 questions in the Quiz tab, checks them, and sees the score, which answers were right or wrong, and the correct answers. Try again resets without a new request, and a note appears when settings change after a generation.
**FRs covered:** FR9, FR10 (Quiz tab)

### Epic 3: Ready to hand in and run by anyone
A grader can run the app from the README, in Demo mode without a key or live with a free key, locally or on Streamlit Community Cloud. The prompt log and the privacy notice are in place for submission.
**FRs covered:** FR12 (plus NFR3, NFR5, NFR8, NFR9, NFR10)

## Epic 1: Turn course material into a summary

Abdiaziz uploads a lecture PDF or pastes notes, chooses Length and Output Language, and gets a structured summary, with clear messages for every invalid input and every Gemini failure.

### Story 1.1: Set up the project and open the app

As Abdiaziz (the builder),
I want a runnable project skeleton with pinned dependencies and sample test files,
So that I can open the app locally and every later story has a fixed place to go.

**Acceptance Criteria:**

**Given** a fresh clone of the repository
**When** I install `requirements.txt` with Python 3.13
**Then** streamlit 1.67.0, google-genai 3.3.0, pypdf 7.1.0, pydantic 2.14.3, python-dotenv 1.2.4 and pytest 9.2.0 are installed from `==` pins
**And** `app.py`, `test_data/` and `tests/` exist at the places given in the architecture Structural Seed; other modules and folders are created by the first story that needs them

**Given** the project is installed
**When** I run `streamlit run app.py`
**Then** the page shows the title "AI Study Buddy" and a one-line caption explaining the app, in `layout="centered"` with no sidebar (UX-DR1, UX-DR2)
**And** there is no custom CSS, injected HTML or theme override

**Given** the repository
**When** I check `.gitignore` and the root files
**Then** `.env` and `.streamlit/secrets.toml` are ignored and `.env.example` is committed with a placeholder `GEMINI_API_KEY` (NFR8)

**Given** `test_data/`
**When** I list it
**Then** it holds a Norwegian text-based PDF, an English text-based PDF, a mixed-language text file and a scanned (image-only) PDF (NFR7)

**Given** the project is installed
**When** I run `pytest`
**Then** the run succeeds with one smoke test that checks the four `test_data/` files are present

### Story 1.2: Provide course material and get clear input errors

As Abdiaziz,
I want to upload a PDF or paste text and be told clearly when the input can't be used,
So that I never waste a Gemini request on input that won't work.

**Acceptance Criteria:**

**Given** the app is open
**When** I look at the "Your material" section
**Then** I see tabs "Upload PDF" (a PDF-only uploader, one file) and "Paste text" (a labelled text area), and below them the caption "Your material is sent to Google Gemini for processing. Nothing is saved." (UX-DR3, UX-DR4)
**And** a full-width primary Generate button below the input area (UX-DR8)
**And** all labels and messages use plain English microcopy with no hype, emoji or exclamation marks (UX-DR17)

**Given** I have content in both tabs
**When** I press Generate
**Then** only the active tab's content is used, read via `st.tabs(..., key=..., on_change="rerun")`, and switching tabs never clears the other tab's content
**And** this tab behaviour is confirmed to work on Streamlit 1.67.0

**Given** a text-based PDF from `test_data/`
**When** `ingest.py` reads it
**Then** it returns one non-empty `str` with the PDF's text, with no OCR (FR1, AD-6)

**Given** pasted text
**When** `ingest.py` reads it
**Then** it returns the same kind of `str` as for a PDF (FR2)

**Given** invalid input
**When** I press Generate
**Then** exactly one message appears in the error area directly above Generate, and no API call is made (FR3, FR4, UX-DR9):
- nothing provided, or whitespace only → "Upload a PDF or paste some text first."
- a 0-byte file → "This file is empty. Choose another PDF."
- a non-PDF file → "Only PDF files are supported."
- a scanned PDF from `test_data/` → "This PDF has no readable text. It's probably scanned. Try a text-based version, or paste the text instead."
**And** what I entered stays in place

**Given** the error mapping
**When** I read the code
**Then** `ingest.py` raises only `EmptyInput`, `EmptyFile`, `NotPdf` or `NoExtractableText` (subclasses of `StudyBuddyError` in `errors.py`), and `app.py` maps each type to its message in one place (AD-5)

**Given** valid input
**When** I press Generate
**Then** the app confirms it was read (e.g. "Read 1,234 words from your material.") — a temporary result that Story 1.3 replaces with the summary

**Given** `tests/`
**When** I run `pytest`
**Then** tests cover PDF extraction success, the scanned-PDF failure, the empty-file and non-PDF rejections, and whitespace-only paste (NFR6)

### Story 1.3: Generate a structured summary in the chosen length and language

As Abdiaziz,
I want to choose a length and language and get a structured summary from Gemini,
So that I can study a dense lecture quickly in the language I want.

**Acceptance Criteria:**

**Given** the app is open
**When** I look under the input area
**Then** I see two horizontal radios side by side: Length (Short / Medium / Long, default Medium, each captioned with its word range) and Output Language (English / Norsk, default English) (FR5, FR6, UX-DR5, UX-DR6)

**Given** `models.py`
**When** I read it
**Then** it defines the `Length` enum (`short`/`medium`/`long`), the `Language` enum (`en`/`no`), the word-range table (<150, 150–400, 400–800), and the Pydantic `StudyPack` (summary title + sections of heading/bullets; quiz of at least 5 questions with exactly 4 options and `correct_index` 0–3, plus explanation) (AD-3)

**Given** valid input and a configured `GEMINI_API_KEY`
**When** I press Generate
**Then** `llm.generate_study_pack(text, length, language, settings)` makes exactly one `generate_content` call to `gemini-3.5-flash-lite` (or `GEMINI_MODEL`) with `response_mime_type="application/json"` and `response_schema=StudyPack`, and returns a validated `StudyPack` that already contains the Quiz and Answer Key (FR7, FR8, AD-2, AD-4)
**And** the Generate button is disabled and the spinner reads "Reading your material and writing the summary and quiz…" until the result arrives (FR11, UX-DR8)

**Given** the prompt
**When** I read `prompts/`
**Then** the system and user templates are text files filled with the chosen word range and Output Language, the JSON schema is not repeated in the prompt, and `PROMPTS.md` has a first entry describing version 1 (AD-8, NFR5)

**Given** a successful generation
**When** the result appears
**Then** the Summary is rendered as markdown topic headings with bullets, followed by the caption "{N} words · {length} · {language}", where N is `len(text.split())` over headings and bullets (UX-DR11)
**And** the raw JSON is never shown
**And** `study_pack` and `input_fingerprint` are stored in `st.session_state`, written only by the Generate handler (AD-7)

**Given** `config.py`
**When** the app starts
**Then** `config.load_settings(st.secrets)` returns the key from secrets or `.env`, and the key is never logged or displayed (AD-9)

**Given** the Norwegian PDF in `test_data/` with Medium + English
**When** I generate
**Then** the summary is in English and 150–400 words (manual check, FR5, FR6)
**And** a manual summary-quality checklist (what a good summary must contain) is written and run against one of my real lecture PDFs, with no filler padding (NFR6, NFR11)

**Given** `tests/`
**When** I run `pytest`
**Then** the network call is monkeypatched, and tests cover: `StudyPack` validation (rejects 3 options, `correct_index` 4, fewer than 5 questions), the prompt containing the right word range and language, and word counting (AD-11)

### Story 1.4: Clear messages when Gemini fails

As Abdiaziz,
I want a plain explanation when Gemini can't answer,
So that I know whether to wait, fix my setup or just try again, without the app crashing.

**Acceptance Criteria:**

**Given** no `GEMINI_API_KEY` in secrets or `.env`
**When** I press Generate with valid input
**Then** `llm.py` raises `MissingApiKey` before any call, and the error area shows "No Gemini API key found. See the README section 'Get a free Gemini API key'."

**Given** Gemini returns HTTP 429
**When** I press Generate
**Then** `RateLimited` is raised and an `st.warning` reads "Gemini's free limit was reached. Wait a minute and try again."

**Given** a timeout, network failure or any other `errors.APIError`
**When** I press Generate
**Then** `GeminiUnavailable` is raised and the message reads "Couldn't reach Gemini. Check your connection and try again."

**Given** a response that is not valid JSON or fails `StudyPack` validation
**When** I press Generate
**Then** `BadModelResponse` is raised and the message reads "The answer from Gemini couldn't be read. Try Generate again."
**And** there is no automatic retry (AD-2)

**Given** any of these failures
**When** the message appears
**Then** my input, Length and Output Language are kept, any earlier results stay as they were, the app does not crash, and the original exception is printed to the console (UX-DR9, AD-5)

**Given** `tests/`
**When** I run `pytest`
**Then** each failure is simulated with the network call monkeypatched and maps to the right error type

## Epic 2: Self-test with the quiz

Abdiaziz answers the 5 questions in the Quiz tab, checks them, and sees the score, which answers were right or wrong, and the correct answers. Try again resets without a new request, and a note appears when settings change after a generation.

### Story 2.1: Answer the quiz and see which answers were right

As Abdiaziz,
I want to answer the quiz next to my summary and see which answers I got wrong,
So that I know exactly which topics to re-read.

**Acceptance Criteria:**

**Given** a successful generation
**When** the results appear
**Then** they are shown as two tabs, "Summary" and "Quiz", below a divider, opening on Summary, with no other navigation needed (FR10, UX-DR10)

**Given** the Quiz tab
**When** I open it
**Then** I see the generated questions numbered 1–5 in one `st.form`, each a labelled 4-option radio with no option preselected, and a "Check answers" button that is not primary-styled (UX-DR12, UX-DR16)
**And** the questions and options are in the chosen Output Language

**Given** at least one question unanswered
**When** I press Check answers
**Then** nothing is checked, an `st.warning` reads "Answer all questions first. Missing: 2, 4." (listing the actual numbers), and my chosen answers are kept

**Given** all questions answered
**When** I press Check answers
**Then** `quiz.py` compares each chosen index in `quiz_answers` (`list[int | None]`, in quiz order) with `correct_index`, and the app shows an `st.info` score line "You got X of 5 right" above the questions (FR9, UX-DR13)
**And** under each question it shows `st.success` "✅ Correct" or `st.error` "❌ Incorrect — correct answer: …" with the correct option's text, so the result is never shown by colour alone
**And** the radios keep my choices

**Given** checked results
**When** I press Try again
**Then** `quiz_answers` and `quiz_checked` are cleared, the same questions are shown unanswered, and no Gemini request is made

**Given** any quiz interaction (selecting, checking, Try again)
**When** Streamlit reruns
**Then** `study_pack` is unchanged and no Gemini request is made; only the quiz form and Try again write `quiz_answers` and `quiz_checked`, and Generate clears them (AD-7)

**Given** `tests/`
**When** I run `pytest`
**Then** `quiz.py` tests cover all correct, all wrong, a mix, and the list of unanswered question numbers (NFR6)

### Story 2.2: Notice when results no longer match the settings

As Abdiaziz,
I want to be told when I've changed the input or settings after generating,
So that I don't mistake an old summary and quiz for ones that match my new choices.

**Acceptance Criteria:**

**Given** results from a generation
**When** I change the input source content, Length or Output Language
**Then** an `st.info` above the results reads "Settings changed. Press Generate to update." (UX-DR14)
**And** the old Summary and Quiz stay visible and nothing is regenerated automatically

**Given** the stale note is showing
**When** I press Generate
**Then** new results replace the old ones, the quiz answers are cleared, and the note disappears

**Given** the inputs are changed back to exactly what was used for the results
**When** the page reruns
**Then** the note disappears

**Given** the fingerprint
**When** I read the code
**Then** `input_fingerprint` is a hash of the source text, Length and Output Language (Story 3.1 adds the demo flag), stored only by the Generate handler and compared on every rerun (AD-7)
**And** a `pytest` test confirms that changing any one of the three inputs changes the fingerprint and that equal inputs give equal fingerprints

## Epic 3: Ready to hand in and run by anyone

A grader can run the app from the README, in Demo mode without a key or live with a free key, locally or on Streamlit Community Cloud. The prompt log and the privacy notice are in place for submission.

### Story 3.1: Try the app in Demo mode without an API key

As a grader without a Gemini API key,
I want to switch on Demo mode and see example output,
So that I can try the whole summary and quiz flow before setting up a key.

**Acceptance Criteria:**

**Given** the app is open
**When** I look under the Length and Language options
**Then** I see a toggle labelled "Demo mode (example output, no API key needed)", off by default, not primary-styled (FR12, UX-DR7)

**Given** `MOCK_MODE=true` in the environment or secrets
**When** the app starts
**Then** the toggle starts switched on (read through `config.load_settings`, AD-9)

**Given** Demo mode is on and no API key is configured
**When** I press Generate
**Then** `demo.load_study_pack()` reads `demo/study_pack.json`, validates it as a `StudyPack`, and the Summary and Quiz tabs show it; `ingest.py` and `llm.py` are not called and no Gemini request is made (AD-10)
**And** the quiz can be answered, checked and reset exactly as in Story 2.1

**Given** demo results are shown
**When** I look at either tab
**Then** a persistent `st.warning` at the top of the results reads "Demo mode — example output, not generated from your material." (UX-DR15)
**And** `is_demo` in session state is set only by the Generate handler

**Given** results exist
**When** I switch Demo mode on or off
**Then** the stale-results note from Story 2.2 appears, because the demo flag is now part of `input_fingerprint`

**Given** no API key and Demo mode off
**When** I press Generate
**Then** the missing-key message now reads "No Gemini API key found. See the README section 'Get a free Gemini API key', or turn on Demo mode to see example output."

**Given** `demo/study_pack.json`
**When** I read it
**Then** it is a realistic example (a summary with several headed sections and 5 quiz questions) produced from one of the `test_data/` files

**Given** `tests/`
**When** I run `pytest`
**Then** tests confirm the demo file validates as a `StudyPack`, Demo mode makes no network call (the call is monkeypatched to fail if used), and the fingerprint changes when the demo flag changes

### Story 3.2: Run the app on Streamlit Community Cloud

As Abdiaziz,
I want the app deployed on Streamlit Community Cloud,
So that I and the grader can use it in a browser without installing anything.

**Acceptance Criteria:**

**Given** the repository on GitHub `main`
**When** I deploy it on Streamlit Community Cloud
**Then** Python 3.13 is selected in Advanced settings, dependencies install from `requirements.txt`, and `GEMINI_API_KEY` is set in the app's Secrets, never in the repo (NFR8, NFR10)

**Given** the deployed app
**When** I generate from the Norwegian PDF in `test_data/` with Medium + English
**Then** the Summary and Quiz appear within about 30 seconds (NFR1)
**And** the quiz can be checked and reset

**Given** the deployed app
**When** I switch on Demo mode and press Generate
**Then** the example output and demo banner appear

**Given** the deployed app
**When** I upload the scanned PDF from `test_data/`
**Then** the scanned-PDF message appears and the app does not crash

**Given** the deployment
**When** it is done
**Then** the public app URL is recorded for the README

### Story 3.3: Hand-in README, prompt log and privacy notice

As a grader who has never seen the project,
I want a README that gets me from clone to a working app and explains how the AI is used,
So that I can run, test and assess the project without help from the builder.

**Acceptance Criteria:**

**Given** the README
**When** I read it
**Then** it explains: what the app does; local setup with Python 3.13 and `requirements.txt`; how to get a free Gemini API key from Google AI Studio (no credit card) and put it in `.env` (based on `.env.example`) or `.streamlit/secrets.toml`; how to run `streamlit run app.py`; how to use Demo mode or `MOCK_MODE=true` without a key; how to run `pytest`; and the deployed app URL from Story 3.2 (NFR9)
**And** it has a section titled "Get a free Gemini API key", which the missing-key message points to

**Given** the README
**When** I read the privacy section
**Then** it states that uploaded material is sent to Google Gemini for processing, that nothing is stored by the app, and that on the free tier Google uses submitted content to improve its products (NFR3)

**Given** the README
**When** I read how the AI is used
**Then** it describes the single structured Gemini request, the `StudyPack` output, the model used, and links to `PROMPTS.md` and the architecture spine (NFR5)

**Given** `PROMPTS.md`
**When** I read it
**Then** every prompt change since version 1 is logged with what changed and why, matching the history of `prompts/` (AD-8, NFR5)

**Given** a person unfamiliar with the project and a fresh clone
**When** they follow only the README
**Then** they can run the app locally in Demo mode without a key, and live with their own free key, with no help from the builder (SM-2)
**And** any step they got stuck on is fixed in the README
