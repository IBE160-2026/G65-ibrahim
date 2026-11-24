# Epic 1 Context: Turn course material into a summary

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Build the core of AI Study Buddy, a single-user Streamlit app. The user uploads a text-based lecture PDF or pastes notes, picks a summary Length and an Output Language, and gets a structured Summary from one Gemini request. That same request also returns the Quiz and Answer Key, which Epic 2 renders. Every invalid input and every Gemini failure shows a clear, plain-English message instead of a crash. The epic also covers setting up the project by hand (there is no starter template) and the test-data folder. Every later epic builds on what this one establishes: the module layout, the shared `StudyPack` shape, the error table and the session-state contract.

## Stories

- Story 1.1: Set up the project and open the app
- Story 1.2: Provide course material and get clear input errors
- Story 1.3: Generate a structured summary in the chosen length and language
- Story 1.4: Clear messages when Gemini fails

## Requirements & Constraints

- Input is a text-based PDF (direct text extraction, no OCR) or pasted text, and both are treated the same way. Only the active input tab is used.
- Invalid input is rejected before any Gemini call, with exactly one message: no input or whitespace only, 0-byte file, non-PDF, scanned PDF with no extractable text, password-protected or damaged PDF. A PDF protected only by an owner password must still extract.
- Length ranges: short <150, medium 150–400, long 400–800 words. Output Language is English or Norwegian, independent of the source language, and applies to both Summary and Quiz.
- A summary outside its range ±10 % is still shown, with an info note. The bounds are inclusive: Short 0–165, Medium 135–440, Long 360–880. Summary length must not be reached by padding with filler.
- The quiz always has exactly 5 multiple-choice questions, each with 4 options and 1 correct option. It is generated together with the summary.
- A visible loading indicator is shown while waiting, and the result should arrive within about 30 s on the free tier.
- Gemini failures map to distinct messages: missing key, invalid key, rate limit (a warning: wait and retry), material rejected, timeout or network, unusable response. There are no automatic retries and the app never crashes.
- Only the Gemini free tier is used. There are no accounts, nothing is stored and nothing is written to disk. The API key lives in a gitignored `.env` or `.streamlit/secrets.toml`, and `.env.example` is committed.
- Tests never call the live API. Automated tests cover extraction (success and scanned failure), upload rejections, length/language handling, the helpers and config. One manual live smoke call (Norwegian PDF, Medium, English) and a manual summary-quality checklist are run against real lecture notes.
- `test_data/` holds a Norwegian PDF, an English PDF, a mixed-language text file and a scanned PDF.
- The stack stays simple enough for a Python beginner to build and explain.

## Technical Decisions

- **Stack (pinned with `==`):** Python 3.13, streamlit 1.67.0, google-genai 3.3.0, pypdf 7.1.0, pydantic 2.14.3, python-dotenv 1.2.4, pytest 9.2.0 (dev). The model is `gemini-3.5-flash-lite`, overridable with `GEMINI_MODEL`.
- **Functional core, imperative shell:**
  - Only `app.py` imports `streamlit`.
  - The core modules are plain Python: `ingest`, `llm`, `demo`, `quiz`, `helpers`, `models`, `errors`, `config`.
  - Pipeline modules never import each other or `app.py`.
  - Each module is created by the first story that needs it.
- **`models.py`** holds the following, defined once:
  - The `Length` (`short`/`medium`/`long`), `Language` (`en`/`no`) and `Source` (`pdf`/`text`) enums.
  - `SOURCE_BY_TAB_LABEL`, `LENGTH_LABELS`, `LANGUAGE_LABELS` (English/Norsk) and `LANGUAGE_PROMPT_NAMES` (English/Norwegian Bokmål).
  - The word-range table.
  - The Pydantic `StudyPack`, which has two parts:
    - summary: a title plus sections, each with a heading and bullets;
    - quiz: exactly 5 questions, each with exactly 4 options, a `correct_index` from 0 to 3 and an explanation.

  `app.py` always holds a `StudyPack` instance, never a dict.
- **Ingest:**
  - The single entry point is `ingest.read_material(source, pdf_name, pdf_bytes, text) -> str`.
  - Checks run in this order: `EmptyInput` → `EmptyFile` → `NotPdf` (no `.pdf` extension, or the file doesn't start with `%PDF`) → `UnreadablePdf` → `NoExtractableText`.
  - For an encrypted PDF it tries `decrypt("")` first. Any other pypdf exception becomes `UnreadablePdf`.
- **Gemini gateway:**
  - Only `llm.py` creates `genai.Client`, with `HttpOptions(timeout=60_000)`.
  - `_call_gemini(prompt, settings) -> str | None` makes the raw call and translates nothing. It is the test seam that tests monkeypatch.
  - `generate_study_pack(text, length, language, settings) -> StudyPack` does the rest:
    - raises `MissingApiKey` before any call when there is no key;
    - makes exactly one `generate_content` call with `response_mime_type="application/json"` and `response_schema=StudyPack`;
    - translates every exception;
    - maps a `None` or empty reply to `BadModelResponse`;
    - validates the reply with `StudyPack.model_validate_json`.
- **Errors:**
  - Core modules raise only `StudyBuddyError` subclasses from `errors.py`.
  - `llm.py` maps failures like this:
    - 400 with reason `API_KEY_INVALID` → `InvalidApiKey` (checked first);
    - any other 400 → `MaterialRejected`;
    - 429 → `RateLimited`;
    - any other `APIError`, or any `httpx2.TransportError` → `GeminiUnavailable`;
    - empty, blocked, invalid-JSON or schema-invalid reply → `BadModelResponse`.
  - The original exception is printed to the console before it is translated. Bare `except:` is not allowed.
  - `app.py` holds the only `ERROR_UI` table. It maps each exact error type to a `("error" | "warning", text)` pair, plus a fallback row for unmapped `StudyBuddyError` types and a last-resort row, "Something went wrong. Try Generate again." Message texts change only in this table.
- **Prompts:**
  - Prompt templates are text files in `prompts/`, using the `string.Template` placeholders `$word_range`, `$language_name` and `$material`, filled with `safe_substitute`.
  - The JSON schema is never repeated in the prompt.
  - Every prompt change gets an entry in `PROMPTS.md`, starting with version 1.
- **Config:**
  - `app.py` converts `st.secrets` to a dict inside try/except (falling back to `{}`) and passes it to `config.load_settings(...)`, which returns `Settings(api_key, model, mock_mode)`.
  - The key comes from secrets, or else from `.env`. It is stripped, and an empty value becomes `None`.
  - `MOCK_MODE` accepts `True`, `"true"` or `"1"`.
  - `config.py` is the only reader of these variables, and the key is never logged or displayed.
- **Helpers (`helpers.py`):**
  - `word_count(summary)`: `len(text.split())` over headings and bullets.
  - `within_word_range(count, length)`.
  - `input_fingerprint(source, raw, length, language, demo)`: SHA-256 over `source|length|language|0|` followed by the raw bytes or text. In Epic 1, demo is always `False`.
- **Session state:**
  - App keys: `study_pack`, `is_demo`, `input_fingerprint`, `generated_with` (length, language), `generation_id`, `is_running`, `last_error`, plus the quiz keys used in Epic 2.
  - Widget keys: `source_tab`, `pdf_upload`, `paste_text`, `length`, `language`. The radios use enum members as options, with labels supplied through `format_func`.
  - Only a successful Generate writes the result keys. A failed Generate changes only `is_running` and `last_error`.
- **Generate mechanism:**
  - The button is drawn with `disabled=is_running`. Its `on_click` clears `last_error` and sets `is_running`.
  - On the next rerun, the pipeline runs under `st.spinner`, stores either the result or `last_error`, sets `is_running=False`, then calls `st.rerun()`.
- **Conventions:** identifiers use `snake_case` and `PascalCase`, in English. Use `width="stretch"`, not `use_container_width`.
- **Staging rule:** a story may ship part of a list (some messages, some fingerprint inputs) when a later named story completes it. The finished app must match every architecture decision in full.

## UX & Interaction Patterns

- **Theme:** stock Streamlit, with no custom CSS, HTML or theme overrides. `layout="centered"`, no sidebar.
- **Page order:** title "AI Study Buddy" with a one-line caption → "Your material" → options → error area → Generate → divider → results.
- **Input:**
  - Two tabs: "Upload PDF" (`type=["pdf"]`, one file) and "Paste text".
  - The tabs are created with `key="source_tab", on_change="rerun"`.
  - Switching tabs never clears the other tab's content.
  - The caption "Your material is sent to Google Gemini for processing. Nothing is saved." is always visible below the tabs.
- **Options:** two horizontal radios side by side. Length (Short / Medium / Long, default Medium, each with its word range as caption) and Output Language (English / Norsk, default English).
- **Generate:**
  - It is the only primary button, at full width.
  - It is disabled while running, with the spinner "Reading your material and writing the summary and quiz…".
  - Validation runs on Generate, not on upload.
- **Error area:** sits directly above Generate and shows one message per problem. The input is always kept. The exact texts are listed in the story acceptance criteria.
- **Summary:**
  - Rendered as markdown topic headings with bullets. Raw JSON is never shown.
  - The caption "{N} words · {length} · {language}" is built from `generated_with`, not from the live widgets.
  - When needed, the word-range note appears under the caption: "This summary has {N} words. {Length} aims for {range} words." Short uses "under 150 words".
- **Microcopy:** plain English, with no hype, emoji or exclamation marks. Every widget has a visible label, and real headings are used.

## Cross-Story Dependencies

- Story 1.1 creates the skeleton, `test_data/` and `tests/`. Every later story depends on it.
- Story 1.2 creates `errors.py`, `ingest.py`, `ERROR_UI` and the Generate/`is_running` mechanism. At this stage a successful Generate shows a temporary "Read N words" result, which Story 1.3 replaces.
- Story 1.3 adds `models.py`, `config.py`, `helpers.py`, `llm.py`, `prompts/` and `PROMPTS.md`. Gemini failures fall back to the generic `ERROR_UI` row until Story 1.4 maps them.
- Story 1.4 fills in the Gemini error mapping. The missing-key text gets its Demo mode hint later, in Story 3.1 (an `ERROR_UI` change only).
- **Other epics:**
  - Epic 2 renders the Quiz from the `StudyPack` that Epic 1 already returns, and uses `input_fingerprint` for the stale-results note.
  - Epic 3 adds the Demo mode toggle, `demo.py`, deployment and the README section "Get a free Gemini API key", which the missing-key message points to.
