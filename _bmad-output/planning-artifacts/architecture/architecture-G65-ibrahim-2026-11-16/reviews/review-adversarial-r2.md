# Adversarial review, round 2: compliant-yet-incompatible units

**Reviewed:** `ARCHITECTURE-SPINE.md` (updated 2026-11-16) against `epics.md` (9 stories) and `EXPERIENCE.md`.
**Lens:** two units, each obeying every AD to the letter, that still do not fit together. Special focus on what the update itself introduced.

**Verdict:** The update closes the first-round data-shape holes (secrets crash, `StudyPack` type, quiz count, radio keys, `ingest` signature). The remaining incompatibilities are in the newly named shell contracts. The spine names keys and helpers but not their *value domains* (what `source_tab`, `length`, `raw` actually hold) or their *call sites* (where Generate runs, where errors are translated). Independently built stories can still disagree on those, which leaves one always-on stale note, one crash path through `Settings`, and a test seam that tests can't use.

---

## Status of round-1 holes

| Hole | Status | Evidence |
| --- | --- | --- |
| H1 secrets crash | **closed** | AD-9: "`app.py` converts `st.secrets` to a plain `dict` inside `try/except` (any exception → `{}`)". |
| H2 fingerprint inputs | **partly** | AD-12 fixes module and raw input: "`helpers.py` … SHA-256 hex over the active tab's raw widget value … Both Generate and every rerun call it with the same inputs." But the hashed list ("raw widget value … plus Length, Output Language and the demo flag") leaves out `source`, even though it is a parameter and Story 2.2 tests that "changing the active tab … changes the fingerprint". The types of `source` and `raw` aren't fixed either (see A2-2). |
| H3 radio state | **closed** | AD-7: "quiz radios `q_<generation_id>_<quiz_round>_<i>` with options `[0, 1, 2, 3]` and a `format_func`". `quiz_round` and `generation_id` have writers. |
| H4 generated-with settings | **partly** | AD-7 adds "`generated_with` (`length`, `language`)" and "The summary caption reads `generated_with`". But in demo mode the values come from the widgets (only "Generate, same moment" is said), not from the demo pack's real settings (see A2-5). |
| H5 key list | **partly** | AD-7 now lists "Widget keys: `source_tab`, `pdf_upload`, `paste_text`, `length`, `language`, `demo_mode`". The value types are not given (label vs enum vs `Source`), which was half of H5 (see A2-2). |
| H6 enum/label/prompt text | **closed** | Conventions: "`LENGTH_LABELS` … `LANGUAGE_PROMPT_NAMES` … Caption format: `<N> words · <length.value> · <LANGUAGE_LABELS[language]>`"; AD-8 fixes `$word_range`, `$language_name`, `$material`. (Minor: the word-range table's value shape, tuple or string, is still open.) |
| H7 ingest signature | **closed** | AD-6: "`ingest.read_material(source, pdf_name, pdf_bytes, text) -> str` … `app.py` passes the raw widget values." |
| H8 `study_pack` type | **closed** | AD-3: "`app.py` always holds a `StudyPack` instance, never a dict." |
| H9 quiz size | **closed** | AD-3: "The quiz has **exactly 5** questions." |
| H10 failure path / message owner | **closed** | AD-7: "A failed Generate changes no app key except `is_running`." AD-5: "one `ERROR_UI` table mapping each type to a `(style, text)` pair". (What `style` is remains open; see A2-6.) |

**Counts:** closed 7 · partly 3 · open 0.

---

## New holes

### A2-1: Where the Generate handler runs: inline after `st.button`, or in an `on_click` callback

- **Severity:** high
- **Units:** Story 1.2 / 1.3 Generate handler vs Story 1.3 button rendering (UX-DR8 "disabled while running") and Story 1.2 / 1.4 error area ("directly above Generate").
- **Builder A (compliant):** `if st.button("Generate", type="primary", width="stretch", disabled=st.session_state.is_running):` then `is_running = True; try: … finally: is_running = False`. This matches AD-7 literally ("`True` before the call, `False` in `finally`"). Errors are shown with `st.error(...)` right there, which renders *below* the button. The button was drawn enabled before `is_running` became `True`, and `is_running` is `False` again before the next rerun, so the button is **never** shown disabled. The flag has no visible effect.
- **Builder B (compliant):** `st.button(..., on_click=_generate)`. The callback sets `is_running`, calls the pipeline and stores the result. Callbacks run before the script, so any `st.error`/`st.spinner` inside them renders at the **top of the page**, above the title. A third variant, an `on_click` that only sets `is_running=True` with the body doing the work `if st.session_state.is_running:`, disables the button correctly. But the work then runs at whatever point in the script that check sits.
- **Incompatibility:** the spinner placement, the disabled state and the error-area position all depend on a choice no AD fixes. Story 1.2's inline error rendering and Story 1.3's "button disabled" requirement can't both hold under builder A. Story 1.4's assumption that messages appear "in the error area" breaks under builder B.
- **Draft rule (tighten AD-7):** "Generate is a two-phase handler. `st.button(..., on_click=_start)` where `_start` only sets `is_running = True` and clears `last_error`. The script body creates an `error_slot = st.empty()` above the button, renders the button with `disabled=is_running`, then `if is_running:` runs the pipeline inside `st.spinner` and, in `finally`, sets `is_running = False` and calls `st.rerun()`. A translated error is stored as `last_error: type[StudyBuddyError] | None` (app key, written only by the Generate body, cleared by `_start`) and rendered into `error_slot` from `ERROR_UI`. No `st.*` output call is made inside a callback."

### A2-2: Widget value domains: `source_tab` label vs `Source`, radio labels vs enums, and what `raw` is

- **Severity:** high
- **Units:** Story 1.3 Generate handler (stores `input_fingerprint`) vs Story 2.2 per-rerun check, both calling `helpers.input_fingerprint(source, raw, length, language, demo)`.
- **Generate builder (compliant):** it already converts widget values for `read_material` (Story 1.2's AC calls `read_material(Source.PDF, name, bytes, None)`), so it calls `input_fingerprint(Source.PDF, uploaded.getvalue(), Length.MEDIUM, Language.EN, False)`. The radio uses `options=["Short","Medium","Long"]` from `LENGTH_LABELS` and is mapped back to `Length`.
- **Rerun builder (compliant):** AD-12 says "the active tab's raw widget value", and AD-7 lists `source_tab`, `length` and `language` as widget keys, so it passes `st.session_state["source_tab"]` (`"Upload PDF"`, since `st.tabs` with a key stores the label), `st.session_state["pdf_upload"]` (an `UploadedFile`, which is the raw widget value) and `st.session_state["length"]` (`"Medium"`).
- **Helpers builder (compliant):** `sha256(f"{source}|{raw}|{length}|{language}|{demo}".encode())`. `f"{Length.MEDIUM}"` is `"Length.MEDIUM"` for a `(str, Enum)` on Python 3.12+ and `"medium"` for `StrEnum`. `f"{uploaded}"` is an object repr that changes every rerun.
- **Incompatibility:** the stored and recomputed fingerprints never match, so the stale note is always on. Or, if the `UploadedFile` repr happens to be stable, the result depends on which enum base was chosen. The same domain gap hits `read_material` ("`app.py` passes the raw widget values" reads as passing the `UploadedFile`) and the caption (`length.value` crashes on the string `"Medium"`). The empty values are also undefined: `None` (uploader) vs `""` (text area) vs a `source_tab` key that is absent before the first tab click.
- **Draft rule (tighten AD-7 + AD-12):** "Widget value types: `source_tab: str` (tab label) is mapped to `Source` only by `app.current_source()` using `SOURCE_TAB_LABELS` in `models.py` (default `Source.PDF` when the key is absent); `length` and `language` radios use `options=list(Length)` / `list(Language)` with `format_func` from the label tables, so the widget value *is* the enum; `demo_mode: bool`. `Length`, `Language` and `Source` are `StrEnum`. `app.current_raw()` returns `pdf_upload.getvalue()` or `None` for PDF, and the text string for TEXT. `input_fingerprint(source: Source, raw: bytes | str | None, length: Length, language: Language, demo: bool)` hashes `source.value`, then raw (str encoded UTF-8; `None` and `""` both as empty), then `length.value`, `language.value` and `demo`, joined with a separator that cannot occur in the enum values. Both Generate and the rerun check call it only through `current_source()`/`current_raw()`. `read_material` gets `pdf_upload.name` and `.getvalue()`, never the `UploadedFile`."

### A2-3: `_call_gemini` boundary: error translation above or below the test seam

- **Severity:** high
- **Units:** `llm.py` (Story 1.3 / 1.4) vs Story 1.4 tests ("each failure is simulated by monkeypatching `llm._call_gemini` and maps to the right error type").
- **llm builder A (compliant):** `_call_gemini` wraps `client.models.generate_content` in `try/except` and translates there: `APIError` 429 → `RateLimited`, `httpx2.TimeoutException` → `GeminiUnavailable`, `response.text is None` (blocked) → `BadModelResponse`. That keeps all network concerns in "the only function that touches the network". `generate_study_pack` only validates JSON. The `MissingApiKey` check also sits in `_call_gemini`, right before `genai.Client(...)`.
- **llm builder B (compliant):** `_call_gemini` is a thin wrapper that returns `response.text` (possibly `None`, despite `-> str`), and `generate_study_pack` does `try: raw = _call_gemini(...) except APIError …` plus the key check.
- **Test builder (compliant with AD-11):** the fake `_call_gemini` raises `genai.errors.APIError(429, …)`, `httpx2.TimeoutException`, returns `""`, or returns `None`.
- **Incompatibility:** against builder A, monkeypatching removes the translation code, so the raw `APIError` escapes and every translation test fails. The only way to pass is a fake that raises `RateLimited` itself, which tests nothing. The `MissingApiKey` test passes or fails depending on whether the check sits above or below the seam. `None` vs `""` for a blocked reply is also undefined at the seam.
- **Draft rule (tighten AD-4):** "`_call_gemini(prompt, settings) -> str | None` does only: build the client, make one `generate_content` call, and return `response.text`. It never catches exceptions. `generate_study_pack` checks `settings.api_key` (→ `MissingApiKey`) before calling `_call_gemini`, and translates every `_call_gemini` exception and every `None`/blank/invalid reply in one `try/except` per the AD-5 table. Tests fake `_call_gemini` by raising the *library* exceptions (`genai.errors.APIError`, `httpx2.*`) or returning `None`/text."

### A2-4: `Settings` normalisation: TOML booleans, empty and placeholder keys, `MOCK_MODE` source, seeding

- **Severity:** high
- **Units:** `app.py` `dict(st.secrets)` vs `config.load_settings(secrets: Mapping[str, str])` vs `llm.py` key check vs Story 3.1 toggle seeding.
- **app builder (compliant):** `dict(st.secrets)`. A `secrets.toml` with `MOCK_MODE = true` (TOML bool, as Streamlit docs write it) gives the Python value `True`, not `"true"`.
- **config builder (compliant):** the annotation says `Mapping[str, str]`, so it does `secrets.get("MOCK_MODE", os.getenv("MOCK_MODE", "")).strip().lower() in ("true", "1")`, which raises `AttributeError: 'bool' object has no attribute 'strip'` and crashes at startup. A second config builder reads `MOCK_MODE` only from the environment (AD-9 names the mapping only for `GEMINI_API_KEY`), so Story 3.1's "`MOCK_MODE=true` in the environment *or secrets*" fails.
- **Key:** config returns `api_key=""` for `GEMINI_API_KEY = ""` (from secrets, which win over `.env`), or the `.env.example` placeholder copied unedited. llm builder checks `if settings.api_key is None`, so no `MissingApiKey`. `genai.Client(api_key="")` either raises a raw `ValueError` (not a `StudyBuddyError`, so it escapes) or Gemini answers 400 "API key not valid", which AD-5 maps to `MaterialRejected`: "It may be too long". The grader gets the wrong advice.
- **Seeding (Story 3.1):** "seeded once" is met both by `if "demo_mode" not in st.session_state: st.session_state.demo_mode = settings.mock_mode` and by `st.toggle(..., value=settings.mock_mode, key="demo_mode")`. If one unit does the first and another the second, Streamlit shows its yellow "created with a default value but also had its value set via the Session State API" warning on the page.
- **Draft rule (tighten AD-9):** "`load_settings(secrets: Mapping[str, Any]) -> Settings` (frozen dataclass). For each of `GEMINI_API_KEY`, `GEMINI_MODEL` and `MOCK_MODE`: take the mapping value if present and non-blank, else the environment; convert with `str(v).strip()`. `api_key` is `None` when blank. `mock_mode` is `str(v).strip().lower() in {'true', '1'}`, so a TOML bool works. `llm.py` treats a falsy `api_key` as missing. A 400 whose message mentions an API key maps to `MissingApiKey`, not `MaterialRejected`. The demo toggle is seeded only by `app.py` writing `st.session_state.setdefault('demo_mode', settings.mock_mode)` before the widget is drawn. No widget in the app passes `value=`/`index=` together with a pre-seeded key."

### A2-5: Demo mode writes live widget values into `generated_with` and hashes input it never used

- **Severity:** medium
- **Units:** Story 1.3 Generate handler (writes `generated_with` from the Length/Language widgets) vs Story 3.1 demo branch and `demo/study_pack.json` ("produced from one of the `test_data/` files" with fixed settings).
- **Story 1.3 builder (compliant):** `generated_with = (length, language)` from the widgets, since AD-7 only says "Generate, same moment".
- **Story 3.1 builder (compliant):** reuses the same success branch, because AD-10 says nothing about `generated_with`.
- **Incompatibility:** with Short + Norsk selected, the demo caption reads "318 words · short · Norsk" above an English Medium summary. This is the round-1 H4 symptom again, now in demo mode only. The demo fingerprint also hashes the raw widget content and Length, so typing text or changing Length in demo mode raises "Settings changed. Press Generate to update." Pressing Generate then returns the identical pack. That contradicts the purpose of the note, which is that results no longer match.
- **Draft rule (tighten AD-10 + AD-12):** "`demo.py` exposes `DEMO_SETTINGS: tuple[Length, Language]`, the settings the demo pack was produced with. In demo mode Generate writes `generated_with = DEMO_SETTINGS`. The fingerprint in demo mode is `input_fingerprint(source, None, *DEMO_SETTINGS, True)` on both sides, so only toggling Demo mode marks demo results stale."

### A2-6: `ERROR_UI` value shape and lookup are not fixed across the three stories that edit it

- **Severity:** medium
- **Units:** Story 1.2 (creates `ERROR_UI` with input errors) vs Story 1.4 (adds API errors with `warning` style) vs Story 3.1 (rewrites the `MissingApiKey` text).
- **Story 1.2 builder (compliant):** `ERROR_UI = {EmptyInput: (st.error, "…")}` and renders with `style(text)`. A "(style, text) pair" with the Streamlit function as the style.
- **Story 1.4 builder (compliant):** adds `RateLimited: ("warning", "…")` and renders with `getattr(st, style)(text)`.
- **Incompatibility:** a mixed table crashes on one entry or the other (`"warning"(text)` → `TypeError`, `getattr(st, st.error)` → `TypeError`). Lookup is also open: `ERROR_UI[type(e)]` throws `KeyError` for any subclass or unmapped type, and nothing says whether `app.py` catches `StudyBuddyError` only or `Exception` (a stray `pydantic.ValidationError` from a demo builder that forgot to wrap it then crashes the page).
- **Draft rule (tighten AD-5):** "`ERROR_UI: dict[type[StudyBuddyError], tuple[Literal['error', 'warning'], str]]`, rendered as `getattr(error_slot, style)(text)`. Lookup walks `type(e).__mro__` and falls back to the `GeminiUnavailable` entry. The Generate body catches `StudyBuddyError` only; anything else is a bug and is allowed to surface. A pytest test asserts every `StudyBuddyError` subclass in `errors.py` has an `ERROR_UI` entry. This test lives in a module importable without running the page (`ui_text.py`, Foundation layer), which `app.py` imports."

### A2-7: Staging rule allows gaps with no owner: unmapped errors between 1.3 and 1.4, and two stories defining one helper

- **Severity:** medium
- **Units:** Story 1.3 (ships `llm.py`, which already raises `MissingApiKey`, `BadModelResponse`, etc. per AD-4/AD-5) vs Story 1.4 (adds their `ERROR_UI` entries). Also Story 1.3 (stores `input_fingerprint` "from `helpers.input_fingerprint`") vs Story 2.2 (specifies and tests the same helper).
- **Story 1.3 builder (compliant):** AD-4 requires `MissingApiKey` and `model_validate_json`, so 1.3 raises those types. Its AC lists no message for them. The staging rule only says "a later, named story completes it", and 1.3 names none for these.
- **Story 1.4 builder (compliant):** adds the entries.
- **Incompatibility:** between 1.3 and 1.4 the app raises errors that have no `ERROR_UI` entry, so any real `MissingApiKey` or bad reply is a `KeyError` crash. That build state is a valid "finished story". For the fingerprint, Story 1.3 has no rerun check and can satisfy "store `input_fingerprint`" with any input set (e.g. the `ingest` output). Story 2.2 then defines the helper differently. Both claim to complete AD-12, and the staging rule can't tell which one owns the helper.
- **Draft rule (tighten staging rule):** "A story that ships part of an AD names, in its AC, the story that completes it. Each AD part has exactly one completing story. Every staged gap must have a safe default: an error type raised before its message exists maps to a generic `ERROR_UI` fallback, never a crash. The story that first writes a helper or key implements its full spine signature; later stories may only widen what callers pass (e.g. the real `demo` flag), never redefine the function."

### A2-8: The value `quiz_answers` is "cleared" to is undefined, and `quiz.py`'s length contract is open

- **Severity:** low
- **Units:** Story 1.3 / 2.2 Generate success and Story 2.1 Try again ("cleared") vs `quiz.py` ("takes a `StudyPack` and `list[int | None]`").
- **Generate builder (compliant):** clears to `[]`, which is a valid `list[int | None]`.
- **Try again builder (compliant):** clears to `[None] * 5`.
- **quiz.py builder (compliant):** `missing = [i + 1 for i, a in enumerate(answers) if a is None]` and `zip(pack.quiz, answers)`.
- **Incompatibility:** with `[]`, `missing` is empty and `zip` yields zero results, so any render path that calls `quiz.py` on cleared state shows "You got 0 of 5 right" with nothing missing. With `[None]*5` it lists 1–5 as missing. Which one you see depends on which writer cleared last.
- **Draft rule (tighten AD-7 / quiz convention):** "Cleared means `quiz_answers = [None] * len(study_pack.quiz)` and `quiz_checked = False`. `quiz.py` raises `ValueError` if `len(answers) != len(pack.quiz)`. `quiz_answers` is written only on Check-answers submit, from the five radio values."

---

## Severity counts (new holes)

| Severity | Count |
| --- | --- |
| critical | 0 |
| high | 4 |
| medium | 3 |
| low | 1 |
