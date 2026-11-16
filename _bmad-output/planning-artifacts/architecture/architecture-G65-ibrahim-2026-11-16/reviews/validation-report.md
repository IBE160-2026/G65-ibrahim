# Validation report — AI Study Buddy architecture spine

Date: 2026-11-16 · Spine: `ARCHITECTURE-SPINE.md` (final, `b9a5d76`) · Spine not changed by this review.

**Verdict:** The paradigm, module boundaries, the single Gemini request and the pinned stack hold up. Every pin is current and installs together on Python 3.13. The holes are all on the `app.py` side: session state, the fingerprint, the `st.secrets` hand-off, and Gemini timeouts/network errors under google-genai 3.x. Stories built separately against the spine as it stands would crash at startup in one case and disagree silently in several others. Fix these before Story 1.1.

Lint: clean. Lenses (run one at a time): rubric walker, version currency, adversarial divergence. Raw reviews: `review-rubric-walker.md`, `review-version-currency.md`, `review-adversarial.md`.

## Critical

**C1 — App crashes at startup without `secrets.toml`** *(adversarial H1)*
- **Problem:** AD-9 has `app.py` pass `st.secrets` into `config.load_settings`. When there is no `.streamlit/secrets.toml` (a grader using only `.env`), reading it raises a Streamlit error. `config.py` can't catch that error without importing Streamlit, which AD-1 forbids.
- **Fix (tighten AD-9):** `app.py` converts `st.secrets` to a plain `dict` inside `try/except`, falling back to `{}`, and passes the dict.

## High

**H1 — Quiz count: "at least 5" vs "exactly 5"** *(rubric F1, adversarial H9)*
- **Problem:** AD-3 allows 5 or more questions, but the UX and stories hard-code 5 ("You got X of 5 right", "Missing: 2, 4", questions 1–5).
- **Fix (tighten AD-3):** the quiz has exactly 5 questions. That still meets the PRD's "at least 5".

**H2 — Session-state contract is incomplete** *(rubric F2, adversarial H3, H4, H5, H8, H10)*
- **Missing keys:** AD-7's "exactly these keys" leaves out widget keys (input tabs, quiz radios, demo toggle), a running flag for the disabled Generate button, and the Length/Language used for a result. Without that last one, the caption contradicts stale and demo results.
- **Radio state:** the quiz radios keep their own widget state, so clearing `quiz_answers` doesn't clear them. `st.radio` also returns option text, not an index.
- **Value types:** `study_pack` could end up stored as a `StudyPack` or as a `dict`.
- **Failure timing:** it isn't said whether Generate clears the quiz on click or only on success. Story 1.4 needs results to survive a failure.
- **Fix (rewrite AD-7):**
  - Separate app keys from widget keys, and list both.
  - Add `generated_with` (Length, Language, demo) and `generation_id` (a counter).
  - Quiz radio keys include `generation_id` and a `quiz_round` counter, and the options are indices 0–3.
  - `study_pack` is always a `StudyPack` instance.
  - State changes only after a successful generation.

**H3 — The fingerprint is underspecified** *(rubric F3, adversarial H2)*
- **Problem:** It isn't said whether the fingerprint hashes raw input or extracted text, whether the active tab counts, which hash function to use, or what to hash in demo mode. The per-rerun check can't call `ingest()`. As a result, the stale-results note ends up always on or never on.
- **Fix (new AD-12):** a core function `input_fingerprint(active_tab, raw_value, length, language, demo)` hashes the raw widget value of the active tab (file bytes or pasted text), with SHA-256. It is used both at Generate and on every rerun.

**H4 — Timeouts and network errors under google-genai 3.x** *(version VC-1, VC-2; rubric F5)*
- **Problem:** Since google-genai 3.0, the default request timeout is `None`, and network/timeout failures come from `httpx2` (`TimeoutException`, `ConnectError`), not from `errors.APIError`. Without a timeout and a mapping for these types, the "Couldn't reach Gemini" path can't happen, and the ~30 s target can't be checked.
- **Fix (tighten AD-4, AD-5):** `llm.py` sets `HttpOptions(timeout=60_000)` (milliseconds), and maps the `httpx2` timeout and connection errors to `GeminiUnavailable`. `llm.py` is allowed to import `httpx2` for this.

## Medium

- **M1 — Uncovered failures** *(rubric F4, version VC-9)*
  - **Missing:** encrypted/password-protected PDFs (`FileNotDecryptedError`), corrupt PDFs (`PdfStreamError`), a Gemini 400 for oversized input, a safety block or empty reply, and an invalid demo JSON file.
  - **Fix:** map each to an existing error type, or add one (e.g. `UnreadablePdf`).
- **M2 — Helpers that must be tested sit in `app.py`** *(rubric F6)*
  - **Problem:** word count and the fingerprint are required to have tests, but `app.py` isn't tested.
  - **Fix:** move them into a core module (`models.py` or a new `helpers.py`).
- **M3 — Error messages are split across stories** *(adversarial H10)*
  - **Problem:** Story 1.2 builds a type-to-text map shown with `st.error`; Story 1.4 needs `st.warning` for the rate limit; Story 3.1 rewrites the missing-key text.
  - **Fix:** one `ERROR_UI` table in `app.py` holding text and style (error/warning). Later stories edit only that table.
- **M4 — Enum ↔ UI label ↔ prompt wording** *(adversarial H6)*
  - **Problem:** three places each map `en`/`no` to labels and prompt wording, and the prompt placeholder names aren't fixed.
  - **Fix:** one mapping in `models.py`, and fixed placeholder names (`{word_range}`, `{language_name}`, `{material}`).
- **M5 — `ingest()` signature** *(adversarial H7)*
  - **Problem:** builders will disagree on `UploadedFile` vs bytes, on how `NotPdf` is detected, and on who owns the "no input" error.
  - **Fix:** `ingest.from_pdf(name: str, data: bytes) -> str` and `ingest.from_text(text: str) -> str`. `NotPdf` = the `.pdf` extension is missing or the bytes don't start with `%PDF`. `EmptyInput` is raised by `ingest` only.
- **M6 — LLM validation and test seam** *(rubric F7)*
  - **Problem:** neither how the reply is validated nor the function tests should replace is named.
  - **Fix:** validate with `StudyPack.model_validate_json(response.text)`; tests monkeypatch `llm._call_gemini(prompt, settings) -> str`.
- **M7 — Unpinned transitive dependencies** *(version VC-6)*
  - **Problem:** Community Cloud picks fresh starlette/uvicorn versions on every deploy, and one already broke deploys in Aug 2026.
  - **Fix:** freeze the full set (`pip freeze` into `requirements.txt`) before Story 3.2.
- **M8 — Operational envelope only in the memlog** *(rubric F8)*
  - **Missing from the spine:** the privacy disclosure (free tier → Google uses input), the model-deprecation plan (`GEMINI_MODEL` override, check Google's models page), the manual Python 3.13 choice on Cloud, and throttling (= none, the user retries).
  - **Fix:** add these to the Deployment section and to Deferred.
- **M9 — Structured output on API v1 not smoke-tested** *(version VC-3)*
  - **Problem:** google-genai 3.x defaults to API `v1`.
  - **Fix:** add one real smoke call to Story 1.3's manual checks.

## Low

- **L1:** `use_container_width` is deprecated in Streamlit 1.67; use `width="stretch"` (also affects UX `DESIGN.md` and Story 1.2). *(version VC-5)*
- **L2:** Some diagram edges don't match the text (e.g. `app → config` vs the AD-9 hand-off). *(rubric)*
- **L3:** Interim results in Story 1.2 temporarily skip AD-7's state keys. Acceptable, but worth a note in the story. *(rubric)*
- Plus 3 more low findings in `review-version-currency.md`.

## Verified OK

- **Pins:** all are the latest on PyPI, support Python 3.13 and install together. pydantic 2.14.3 meets google-genai's `>=2.12.5`.
- **Model:** `gemini-3.5-flash-lite` is stable, on the free tier, with no deprecation date.
- **SDK retries:** google-genai doesn't retry by default, which matches AD-2.
- **Streamlit:** `st.tabs(key=, on_change="rerun")` exposes the active tab label, which confirms the open item for Story 1.2.

## Totals

| Severity | Count (after merging duplicates) |
| --- | --- |
| Critical | 1 |
| High | 4 |
| Medium | 9 |
| Low | 3 (+3 in the version review) |

**Suggested next step:** an Update run that fixes C1 and H1–H4 (AD-3, AD-4, AD-5, AD-7, AD-9 tightened; new AD-12), and folds in M1–M8 as small rule and convention changes. Epics 1.2, 1.3, 1.4, 2.1, 2.2 and 3.1 then need matching acceptance-criteria edits.
