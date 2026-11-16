# Adversarial review — compliant-yet-incompatible units

**Reviewed:** `ARCHITECTURE-SPINE.md` (status: final, 2026-11-16) against `epics.md` (9 stories) and `EXPERIENCE.md`.
**Lens:** two units, each obeying every AD to the letter, that still do not fit together.

**Verdict:** The module boundaries and the `StudyPack` shape hold, but the shell-side contracts are left open: session-state contents, the fingerprint, `Settings`, the `ingest` call shape and enum-to-text mapping. That leaves at least one crash path and several silent mismatches that independently built stories will hit.

---

## H1 — `st.secrets` passed "as a plain mapping" crashes when no secrets file exists

- **Severity:** critical
- **Units:** `app.py` (Story 1.3, AD-9) vs `config.py` (Story 1.3 / 3.1, AD-9)
- **App builder (compliant):** `settings = config.load_settings(st.secrets)`, which is the literal wording of AD-9 and the Story 1.3 AC.
- **Config builder (compliant):** `key = secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")`, because AD-9 says "from that mapping when present, otherwise from the environment".
- **Incompatibility:** on a local clone with only `.env` and no `.streamlit/secrets.toml` (the README path for graders, SM-2), any access to `st.secrets`, including `.get`, raises a Streamlit "no secrets found" error. `config.py` cannot catch that error by type without importing Streamlit, which AD-1 forbids, and `app.py` does nothing because it only "passes `st.secrets` in". The app crashes at startup on the main grader path.
- **Fix (tighten AD-9):** "`app.py` converts secrets to a plain `dict` before calling config: `secrets = dict(st.secrets)` inside `try/except Exception: secrets = {}`. `config.load_settings(secrets: Mapping[str, Any])` only ever receives a real `dict` and never sees a Streamlit object."

## H2 — `input_fingerprint` inputs: ingested text vs raw widget value, and where it is computed

- **Severity:** high
- **Units:** Story 1.3 Generate handler (writes `input_fingerprint`) vs Story 2.2 rerun comparison vs Story 3.1 (adds the demo flag)
- **Story 1.3 / 2.2 Generate side (compliant):** AD-7 says "hash of source text + length + language". The only "source text" the handler has is the output of `ingest()`, so it hashes `ingest(...)`'s `str`.
- **Story 2.2 rerun side (compliant):** it must compare "on every rerun". Running `ingest()` on every rerun would re-parse the PDF on every quiz click and raise `EmptyInput` or `NoExtractableText` whenever the active tab is empty or the input is bad. The builder therefore hashes the raw widget value instead (`uploaded.getvalue()` or the `text_area` string).
- **Story 3.1 (compliant):** in demo mode `ingest` is never called (AD-10), so the Generate handler has no "source text" to hash. It hashes `""`, or the raw widget value, or skips the text.
- **Incompatibility:** the stored hash (from extracted text) never equals the per-rerun hash (from raw bytes or raw text), so the stale note shows right after every successful Generate. Or, if both sides are fixed differently, it never shows. The active tab is also not a fingerprint input, so switching from "Upload PDF" to "Paste text" with both filled gives no stale note even though the next Generate would use other material. Story 2.2 and 3.1 also both require a pytest test of the fingerprint, but no AD says which importable module it lives in. `app.py` cannot be imported in tests without running the page.
- **Fix (new AD-12):** "`models.input_fingerprint(active_source: Literal['pdf','text'], raw: bytes | str | None, length: Length, language: Language, is_demo: bool) -> str` (SHA-256 hex) is the only fingerprint function. Its input is the *raw active-tab widget value* (uploaded file bytes or the text-area string, `None` if empty), never the output of `ingest`. The same call is used by the Generate handler (stored on success) and by the per-rerun check. In demo mode the raw value is still hashed."

## H3 — Quiz radio widget state vs `quiz_answers`: index vs text, and clearing doesn't clear the widgets

- **Severity:** high
- **Units:** Story 2.1 (quiz form, Try again) vs Story 1.3 / 2.2 Generate handler ("clears `quiz_answers`, `quiz_checked`")
- **Quiz builder (compliant):** `st.radio(q.question, q.options, index=None, key=f"q_{i}")` inside the form. On submit it writes `quiz_answers = [q.options.index(st.session_state[f"q_{i}"]) ...]`. Try again sets `quiz_answers = [None]*n` and `quiz_checked = False`, which are the only keys AD-7 lets it write.
- **Generate builder (compliant):** on success it sets `quiz_answers = []` and `quiz_checked = False`, exactly as AD-7 says.
- **Incompatibility:** (a) The radios read their state from their own widget keys `q_0..q_4`, not from `quiz_answers`. After Try again, or after a new Generate, the radios still show the old choices: Try again doesn't show "the same questions unanswered", and a new quiz opens with answers pre-selected from the previous quiz. Fixing that means writing `q_i` keys, which AD-7 does not allow any writer to own. (b) `st.radio` returns option *text*, and `.index(text)` picks the wrong index when the model returns two identical option strings (nothing in `StudyPack` forbids this). A second builder using `options=range(4), format_func=...` would store indices directly. The two approaches are not interchangeable if `quiz.py` tests use one convention and the app uses the other.
- **Fix (tighten AD-7 + quiz convention):** "Quiz radios use `options=[0,1,2,3]` with `format_func=lambda i: q.options[i]` and `index=None`, so the widget value *is* the option index. Widget keys are `quiz_q_{generation_id}_{i}`, where `generation_id` is a counter written only by the Generate handler (AD-7 key list). A new generation therefore gets fresh, empty widgets. Try again increments a `quiz_round` key, also part of the widget key, instead of mutating widget state. `quiz_answers` is derived from those widget values on submit."

## H4 — The length and language actually used for the results are not stored anywhere

- **Severity:** high
- **Units:** Story 1.3 (Summary caption "{N} words · {length} · {language}") vs Story 2.2 / 3.1 (stale results kept visible after settings change; demo pack)
- **Story 1.3 builder (compliant):** the caption reads the current Length and Language radios, since AD-7 lists no key that holds the values used for generation and `StudyPack` has no such fields.
- **Story 2.2 builder (compliant):** after the user changes Length, the old results stay visible with the stale note.
- **Story 3.1 builder (compliant):** the demo pack was produced with fixed settings, for example Medium + English, from a `test_data/` file.
- **Incompatibility:** after a settings change, or in demo mode with Short + Norsk selected, the caption says "120 words · short · Norsk" above an English 318-word summary, right below a note saying the results don't match. The only correct source is the settings at Generate time, and AD-7's closed key list forbids storing them. The fingerprint is a one-way hash.
- **Fix (tighten AD-7):** "Add `generated_with: dict(length: Length, language: Language)` to the Generate-handler keys. For demo output its values come from `demo/study_pack.json` metadata, or from fixed constants in `demo.py`. The caption reads only `generated_with`, never the live widgets."

## H5 — AD-7's "exactly these keys" contradicts keys the stories require

- **Severity:** medium
- **Units:** Story 1.2 (`st.tabs(..., key=...)`), Story 1.3 (Generate disabled while running), Story 3.1 (toggle defaulted from `MOCK_MODE`), Story 2.1 (radio keys) vs AD-7
- **Builders (compliant):** each story adds whatever widget key it needs (`input_tab`, `is_generating`, `demo_toggle`, `q_0`...). Another builder, reading AD-7 literally, refuses to add any key and instead re-derives values, for example by not keying the tab widget.
- **Incompatibility:** Story 1.2 reads `st.session_state["input_tab"]` while Story 2.2 or 3.1 reads `st.session_state["tab"]`, or a builder reverts to unkeyed widgets "per AD-7" and breaks the other's reads. The key names also have to match the values compared: is the tab value the label "Upload PDF" or an id? Disabling Generate while running needs a flag that AD-7 doesn't allow.
- **Fix (tighten AD-7):** split the table into *data keys* (fixed writers, as now) and *widget keys*, and list the widget keys by name and value type: `input_tab: Literal["Upload PDF","Paste text"]`, `pdf_file`, `paste_text`, `length: Length`, `language: Language`, `demo_on: bool` (initial value from `Settings.mock_mode`, set only if absent), `is_generating: bool`, and the quiz widget keys from H3. "Only keys in this table may be used."

## H6 — Enum value vs UI label vs prompt text for `Length` and `Language`

- **Severity:** medium
- **Units:** `models.py` (Story 1.3) vs `llm.py` / `prompts/` (Story 1.3, later prompt versions logged in Story 3.3) vs `app.py` caption and radios
- **models builder (compliant):** `class Language(str, Enum): EN="en"; NO="no"`, and a word-range table keyed by `Length` whose values are tuples like `(0, 150)`.
- **llm/prompt builder (compliant):** the template says "Write the summary in {language} ... {word_range} words", filled with `language.value` and `f"{lo}-{hi}"`. The prompt then reads "in no", and "0-150" contradicts the FR's "<150".
- **app builder (compliant):** radios show "English / Norsk". The caption shows `language.value` ("en") or the label ("Norsk"), while EXPERIENCE's example caption is "medium · English", which mixes an enum value with a label.
- **Incompatibility:** three parts each invent their own mapping. The Story 1.3 test "prompt contains the right word range and language" passes against the llm builder's strings but not against a prompt edited later using "Norwegian" and "150–400" with an en dash.
- **Fix (tighten convention):** "`models.py` also defines `LENGTH_LABEL` (UI: Short/Medium/Long), `LANGUAGE_LABEL` (UI: English/Norsk), `LANGUAGE_PROMPT_NAME` (English/Norwegian), and `WORD_RANGE_TEXT` (`'fewer than 150'`, `'150–400'`, `'400–800'`). Prompt templates use exactly the placeholders `{language_name}`, `{word_range}` and `{source_text}` with `str.format`. The caption is `f"{n} words · {length.value} · {LANGUAGE_LABEL[language]}"`."

## H7 — `ingest()` has no signature. Who owns "no file" and how is `NotPdf` detected?

- **Severity:** medium
- **Units:** Story 1.2 `ingest.py` + tests vs Story 1.2 / 3.1 `app.py` call site
- **ingest builder (compliant):** `ingest(pdf_bytes: bytes | None = None, text: str | None = None) -> str`. It detects `NotPdf` by checking that the bytes start with `%PDF-`. Tests pass `Path(...).read_bytes()` from `test_data/`.
- **Second compliant builder:** `ingest(source: UploadedFile | str)`, checking `source.name.endswith(".pdf")` and `source.type` for `NotPdf`. This doesn't work with plain-bytes tests and puts a Streamlit type in core, which is allowed by duck typing and not explicitly banned.
- **app builder (compliant):** when the PDF tab is active and `uploaded is None`, it shows "Upload a PDF or paste some text first." itself, because the spine's sequence diagram says it sends "PDF bytes or pasted text" and there are no bytes to send. That bypasses the typed-error mapping of AD-5.
- **Incompatibility:** the call shapes don't match, and `NotPdf` can't happen in one design because `type=["pdf"]` already filters by extension, while the other relies on it. The empty-input message ends up owned by two places.
- **Fix (tighten AD-6):** "`ingest.read_pdf(data: bytes | None) -> str` and `ingest.read_text(text: str | None) -> str`. The arguments are plain `bytes` and `str` only (the app passes `uploaded.getvalue()` or `None`). `None` or whitespace raises `EmptyInput`. `b""` raises `EmptyFile`. Bytes not starting with `%PDF-` raise `NotPdf`. `app.py` never shows an input message itself."

## H8 — Type of the `study_pack` session value and of the demo return value

- **Severity:** medium
- **Units:** Story 1.3 Generate handler and Summary renderer vs Story 3.1 `demo.load_study_pack()` vs Story 2.1 quiz renderer
- **Story 1.3 (compliant):** stores the `StudyPack` instance and renders `pack.summary.sections`.
- **Story 3.1 (compliant):** AD-10 says "validates it through `StudyPack`". The builder runs `StudyPack.model_validate(data)` and returns the validated `dict`, or `model_dump()` "for session-state safety".
- **Incompatibility:** with a demo pack, `pack.summary` raises `AttributeError` in the renderer, or Story 2.1 written against dicts fails on live packs. AD-3 requires validation but doesn't fix what is passed on afterwards.
- **Fix (tighten AD-3/AD-10):** "Every producer (`llm.generate_study_pack`, `demo.load_study_pack`) returns a `StudyPack` instance. `st.session_state['study_pack']` holds that instance (or `None`). `demo/study_pack.json` is exactly `StudyPack.model_dump_json()` output with no wrapper or extra fields, except the optional `generated_with` from H4, which goes in a sibling file or as `demo.DEMO_SETTINGS`."

## H9 — Quiz size: "min 5" in the model vs "5" in the UI

- **Severity:** medium
- **Units:** `models.py` (AD-3: `quiz` min 5) vs Story 2.1 `app.py` ("numbered 1–5", "You got X of 5 right") vs `quiz.py`
- **quiz.py builder (compliant):** the score total is `len(pack.quiz)`, and `quiz_answers` has length `len(pack.quiz)`.
- **app builder (compliant with the UX text):** hard-codes "of 5", or shows only `pack.quiz[:5]` while `quiz.py` scores all questions.
- **Incompatibility:** when Gemini returns 7 questions, which the schema allows, the page shows "You got 6 of 5 right", or shows 5 radios while `quiz.py` reports 2 unanswered. "Missing: 6, 7" then refers to questions that aren't on the page.
- **Fix (tighten AD-3):** "`quiz` has exactly 5 items (`min_length=5, max_length=5`). All UI text uses `len(pack.quiz)`." Alternatively, keep min 5 and require the UI to render all questions and use `len(...)` everywhere.

## H10 — Generate failure path: what gets cleared, and who owns message text and severity

- **Severity:** medium
- **Units:** Story 1.2 / 1.3 Generate handler vs Story 1.4 ("earlier results stay as they were") vs Story 3.1 (rewrites the missing-key text)
- **Generate builder (compliant):** AD-7 says `quiz_answers` and `quiz_checked` are "cleared by Generate", so the handler clears them at the start of the click, before `ingest`/`llm`.
- **Story 1.4 builder (compliant):** on `RateLimited` it keeps `study_pack`, but the user's quiz answers and checked results are gone. That contradicts "any earlier results stay as they were".
- **Error map:** Story 1.2 builds `MESSAGES: dict[type, str]` rendered with `st.error`. Story 1.4 needs `RateLimited` rendered with `st.warning`. Story 1.4's test asserts the missing-key text from its own AC, which Story 3.1 then changes to the EXPERIENCE text. AD-5 says "exactly one message from EXPERIENCE.md", so Story 1.4's AC text is already non-compliant with the spine.
- **Fix (tighten AD-5/AD-7):** "The Generate handler writes or clears *nothing* unless the result is a `StudyPack`. On success it atomically sets `study_pack`, `is_demo`, `input_fingerprint`, `generated_with`, bumps `generation_id`, and clears `quiz_answers` and `quiz_checked`. `app.py` holds one table `ERROR_UI: dict[type[StudyBuddyError], tuple[Literal['error','warning'], str]]`, with texts copied verbatim from EXPERIENCE.md State Patterns. Tests assert against `ERROR_UI`, not string literals."

---

### Also noted, not holes on their own

- `Settings` field names and types are undefined (`api_key` vs `gemini_api_key`; `mock_mode` as a `bool` from TOML vs the string `"true"` from the environment; whether config fills the default model or leaves `None` for `llm.py`; `""` vs `None` for a missing key, where `llm` checks `is None`). Fold this into AD-9: "`Settings` is a frozen dataclass `Settings(api_key: str | None, model: str, mock_mode: bool)`; config normalises empty strings to `None`, parses `mock_mode` case-insensitively from `'true'/'1'` or a bool, and fills `model` with the default `gemini-3.5-flash-lite`."
- Word count (convention: "computed by the app") and the fingerprint both need pytest coverage but are assigned to `app.py`, which can't be imported in tests. Put both pure helpers in `models.py`.

### Severity counts

| Severity | Count |
| --- | --- |
| critical | 1 |
| high | 3 |
| medium | 6 |
| low | 0 |
