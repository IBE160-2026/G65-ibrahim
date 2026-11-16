# Rubric walker, round 2: updated architecture spine

Date: 2026-11-16 · Spine: `ARCHITECTURE-SPINE.md` (status: draft, updated) · Inputs: PRD, EXPERIENCE.md, DESIGN.md, epics.md · Spine and other files were not changed by this review.

**Verdict:** The update fixes the critical finding and all four high findings, and nothing has regressed. One new high-severity gap remains: the `is_running` rule cannot actually disable Generate in Streamlit's run model. There are also four medium contradictions between the test seam, the demo path and AD-11, and the spine should be tightened on these before Story 1.3.

## A. Regression check (validation-report.md)

| Id | Status | Evidence |
| --- | --- | --- |
| C1 | Resolved | AD-9: "`app.py` converts `st.secrets` to a plain `dict` inside `try/except` (any exception → `{}`) and passes it to `config.load_settings(...)`". Story 1.3 AC: "the app starts without a crash when only `.env` exists". |
| H1 | Resolved | AD-3: "The quiz has **exactly 5** questions." The class diagram says "(exactly 5)". Story 1.3 test: "rejects … 4 or 6 questions". |
| H2 | Partly resolved | Fixed: app keys and widget keys are separate, `generated_with`, `generation_id`, `quiz_round` and the `q_<generation_id>_<quiz_round>_<i>` radios with options `[0, 1, 2, 3]` are added, "`app.py` always holds a `StudyPack` instance", and "A failed Generate changes no app key except `is_running`". Still open: the report said that without the recorded settings "the caption contradicts … demo results". `generated_with` is "(`length`, `language`)" taken from the widgets, so a demo pack still gets a caption with the user's widget values rather than the demo file's own length and language (see R2-4). |
| H3 | Resolved | AD-12: "`input_fingerprint(source, raw, length, language, demo) -> str`: SHA-256 hex over the active tab's raw widget value … Both Generate and every rerun call it with the same inputs." Smaller gaps remain (R2-6). |
| H4 | Resolved | AD-4: "`http_options=HttpOptions(timeout=60_000)` (milliseconds)". AD-5: "`GeminiUnavailable` … `httpx2.TimeoutException`, `httpx2.ConnectError`". The layer table allows `httpx2` in `llm.py`. |
| M1 | Resolved | New `UnreadablePdf` ("Encrypted PDF, or any `pypdf.errors.PyPdfError`") and `MaterialRejected` (400). `BadModelResponse` covers "Empty or blocked reply", and AD-10 covers invalid demo JSON. EXPERIENCE.md has the new message rows. A residual catch-all gap is R2-3. |
| M2 | Resolved | AD-12: `helpers.py` is a Foundation module and is listed in AD-11's test scope. |
| M3 | Resolved | AD-5: "`app.py` holds one `ERROR_UI` table mapping each type to a `(style, text)` pair … later stories change messages only in that table." Stories 1.4 and 3.1 refer to it. |
| M4 | Resolved | Conventions: `LENGTH_LABELS`, `LANGUAGE_LABELS`, `LANGUAGE_PROMPT_NAMES` in `models.py`. AD-8: placeholders `$word_range`, `$language_name`, `$material` with `safe_substitute`. |
| M5 | Resolved (another way) | AD-6: one `ingest.read_material(source, pdf_name, pdf_bytes, text) -> str`. `NotPdf` is defined in the AD-5 table, and `EmptyInput` is raised by `ingest`. |
| M6 | Resolved | AD-4: "`_call_gemini(prompt: str, settings: Settings) -> str` … Tests monkeypatch this function", and the reply is validated with `StudyPack.model_validate_json(...)`. Where error translation lives is still open (R2-2). |
| M7 | Resolved | Stack: "Before the first deploy, the full installed set … is frozen into `requirements.txt` with `pip freeze`." A side risk is R2-8. |
| M8 | Resolved | Deployment & operations has Python 3.13 in Cloud Advanced settings, "No throttling", the `GEMINI_MODEL` deprecation plan, and the Privacy bullet. |
| M9 | Resolved | AD-11: "The one live call is a manual smoke check in Story 1.3". Story 1.3: "the structured JSON request succeeds on google-genai 3.3.0". |
| L1 | Resolved | Conventions: "Use `width="stretch"`". DESIGN.md: `st.button(type="primary", width="stretch")`. Story 1.2 uses it too. |
| L2 | Partly resolved | `llm → prompts`, `demo → errors`, `helpers` and the demo participant were added. The flowchart still has no `app → models` or `app → errors` edge, although `app.py` holds `StudyPack`, the enums and the `ERROR_UI` keys. Nothing is forbidden; the diagram is just incomplete. |
| L3 | Resolved | Staging rule added. Story 1.2: "a temporary result that Story 1.3 replaces with the summary (staging rule)". |

**Counts:** 15 resolved · 2 partly resolved · 0 not resolved.

## B. New findings

### R2-1 — `is_running` cannot disable Generate as written (high)

- **Location:** AD-7 (`is_running` row), Generate flow diagram, Story 1.3 AC ("`is_running` is set while the call runs, so the Generate button is disabled").
- **Problem:** AD-7 says `is_running` is written by "Generate, `True` before the call, `False` in `finally`". In the usual `if st.button("Generate"):` handler, the button has already been drawn, enabled, by the time the handler sets `True`. Setting the flag inside the same run never shows a disabled button. A click on any widget during the run makes Streamlit stop the script and rerun it. The `finally` resets the flag, and a second Generate click can start a second `generate_content` call.
- **Why it matters:** EXPERIENCE.md requires "Disabled, with a spinner, while the request runs. A second click during a run is impossible." AD-2 exists to protect free-tier quota. The rule does not prevent the divergence it names. Builders will each invent a different mechanism: an `on_click` callback plus a rerun, `disabled=` read from state, or ignoring the flag.
- **Suggested fix:** State the mechanism in AD-7. The Generate button uses `on_click` to set `is_running=True` (and a `generate_requested` flag). The button is drawn with `disabled=st.session_state.is_running`. The call runs later in the same rerun, under `st.spinner`, and `is_running=False` is set in `finally` followed by `st.rerun()`. Otherwise, drop the "disabled" promise and accept the spinner alone, which is enough for FR-11.

### R2-2 — Unclear whether error translation sits inside or outside the test seam (medium)

- **Location:** AD-4, AD-5, AD-11, Story 1.4 test AC.
- **Problem:** AD-4 says `_call_gemini` "returns the raw response text" and that tests monkeypatch it. AD-11 says tests cover `llm.py` "(parsing and error translation), with `llm._call_gemini` monkeypatched". Neither says where `APIError → RateLimited` and related translation happens, or what `_call_gemini` does with a blocked reply whose `response.text` is `None`, given its signature `-> str`. If one builder translates inside `_call_gemini`, the Story 1.4 tests ("each failure is simulated by monkeypatching `llm._call_gemini`") have to raise `RateLimited` directly and test nothing. If another builder translates outside, the fakes must raise raw `genai.errors.APIError` or `httpx2` exceptions.
- **Why it matters:** The AD-5 mapping is the most-tested contract in the spine, and right now its tests can be empty without anyone noticing.
- **Suggested fix:** Add to AD-4: "`_call_gemini` contains no `try/except`. It builds the client, calls `generate_content` and returns `response.text or ""`. `generate_study_pack` translates every exception from `_call_gemini` and every empty or invalid reply into AD-5 types. Tests make the fake raise the raw library exceptions."

### R2-3 — No rule for unexpected exceptions (medium)

- **Location:** AD-5 ("Core modules raise only subclasses of `StudyBuddyError`"), EXPERIENCE.md ("Errors never crash the app").
- **Problem:** pypdf does not always wrap its failures in `PyPdfError`. Malformed files can raise `ValueError`, `KeyError`, `TypeError` or `struct.error`. Bugs in the core can raise anything as well. The spine gives `app.py` no rule for exceptions outside `StudyBuddyError`. Some builders will catch `Exception`, others only `StudyBuddyError`, and the second group shows a Streamlit traceback.
- **Why it matters:** The UX floor says errors never crash the app. It is also the scenario a grader is most likely to hit, with a random PDF from their own disk.
- **Suggested fix:** In AD-6, `read_material` wraps the whole pypdf block and maps any remaining `Exception` to `UnreadablePdf`. In AD-5, `app.py`'s Generate handler has one final `except Exception` that prints the error and shows the `BadModelResponse`-style generic message (or adds an `ERROR_UI` "Unexpected" row). Make this the only allowed broad catch.

### R2-4 — In demo mode, the caption and fingerprint describe the widgets, not the output (medium)

- **Location:** AD-7 (`generated_with`), conventions caption format, AD-10, AD-12.
- **Problem:** In demo mode Generate stores `generated_with` from the live Length and Language widgets. The demo pack, however, is fixed: one language and one length, made "from one of the `test_data/` files" (Story 3.1). With Short + Norsk selected, the caption reads e.g. "312 words · short · Norsk" under an English medium summary. The fingerprint also hashes the raw input in demo mode, so editing the pasted text shows "Settings changed. Press Generate to update." even though regenerating gives the same demo output. AD-12 also does not say what to hash when the active tab is empty (`raw` is `None`), which is a normal demo-mode case.
- **Why it matters:** These are the "captions contradicting the results" that AD-7 says it prevents (and part of the original H2), shown to the grader, who is the main user of demo mode.
- **Suggested fix:** In demo mode, store `generated_with` from fixed values in `demo.py` (or hide the length and language part of the caption when `is_demo`). Specify `input_fingerprint` for `raw=None` (hash an empty byte string), and decide whether the demo fingerprint ignores `raw`.

### R2-5 — Story 3.1's "no network call" test targets `app.py`, which AD-11 leaves untested (medium)

- **Location:** AD-11 (test scope lists `ingest`, `quiz`, `models`, `helpers`, `demo`, `llm` only) and Story 3.1 test AC: "Demo mode makes no network call (the call is monkeypatched to fail if used)".
- **Problem:** AD-10 puts the demo-vs-live branch in `app.py` ("Generate calls `demo.load_study_pack()` … `ingest.py` and `llm.py` are not called"). A pytest test of that branch has to run `app.py`, through `streamlit.testing.v1.AppTest` or similar, which the spine neither allows nor describes. Testing `demo.load_study_pack()` alone proves nothing about network calls.
- **Why it matters:** The builder will either write a meaningless test or invent an app-testing approach the spine does not cover. FR-12's "No Gemini API call is made while Demo mode is on" is also a PRD testable consequence.
- **Suggested fix:** Either add `AppTest` for this one case to AD-11, or move the branch into a core function, e.g. `pipeline.generate(...)` (or a small function in `helpers.py`), that `app.py` calls and tests can exercise. Then change Story 3.1's test AC to match.

### R2-6 — Stale-note inputs and style differ across documents (low)

- **Location:** AD-12, Story 2.2, EXPERIENCE.md State Patterns, DESIGN.md Colors.
- **Problem:**
  - AD-12 hashes "the active tab's raw widget value … plus Length, Output Language and the demo flag". It does not say the `source` itself is hashed. Story 2.2 hashes "the active tab and its raw widget value" and tests that "changing the active tab … changes the fingerprint".
  - EXPERIENCE.md's stale-results row lists only "the input, Length or Output Language". UX-DR14 and AD-12 also include Demo mode.
  - DESIGN.md says `st.warning` is for "stale results, rate limit", while EXPERIENCE.md and UX-DR14 use `st.info`.
- **Why it matters:** These are small, but they are exactly the "always on or never on" class of bug that AD-12 is meant to stop.
- **Suggested fix:** AD-12: "SHA-256 over `source.value`, the active raw value, `length.value`, `language.value` and `demo`". Then align EXPERIENCE.md (add Demo mode) and DESIGN.md (`st.info`).

### R2-7 — Small signature mismatches (low)

- **Location:** AD-6 versus Story 1.2; conventions "Quiz checking" versus Story 2.1.
- **Problem:**
  - AD-6 says "`app.py` passes the raw widget values", but Story 1.2 calls `read_material(Source.PDF, name, bytes, None)` with `text=None`.
  - The conventions say `quiz.py` "returns per-question results and the score", but Story 2.1 tests that it produces "the list of unanswered question numbers", which the convention does not mention.
- **Suggested fix:** State in AD-6 that inactive-source arguments may be anything and are ignored, or require `None`. Add "and the 1-based numbers of unanswered questions" to the quiz convention.

### R2-8 — `pip freeze` on a Windows dev machine can break the Linux Cloud build (low)

- **Location:** Stack paragraph, Story 3.2.
- **Problem:** "the full installed set … is frozen into `requirements.txt` with `pip freeze`". The builder works on Windows, where this can pin Windows-only packages and also pins dev tools such as pytest. Community Cloud builds on Linux.
- **Suggested fix:** Freeze from a clean virtual environment that has only the runtime pins. Check the result for platform-specific packages, or add environment markers to them, and confirm the Cloud build log as Story 3.2 already requires.

### R2-9 — "Exactly 5" is enforced only after the call (low)

- **Location:** AD-3, AD-8 ("The JSON schema is passed only through `response_schema`, never repeated in the prompt").
- **Problem:** If the Pydantic count constraints don't reach Gemini's schema as `minItems`/`maxItems`, or the model ignores them, a 6-question reply becomes `BadModelResponse`. With "No automatic retries", that costs a whole free-tier request. The spine doesn't say whether the prompt should state "5 questions, 4 options each" in plain words. A ban on "repeating the schema" may read as forbidding that.
- **Suggested fix:** In AD-8, allow (or require) the prompt to state the counts in natural language. In AD-11, add a test that `StudyPack.model_json_schema()` carries the 5 and 4 limits.

### R2-10 — Some pins are README or story facts, not divergence points (low)

- **Location:** AD-2 ("reference: the python-genai README, not the Interactions API"), Stack paragraph (SyntaxWarnings), Deployment (Python 3.13 "can't be changed later without redeploying"), conventions (`width="stretch"`).
- **Problem:** None of these can cause two stories to diverge. There is one primary button and one README. They make the build substrate heavier for a beginner reader. Overall the spine is still at a reasonable weight, and most of its detail (AD-5 table, AD-7 keys, AD-12) is justified.
- **Suggested fix:** Move these four items to Story 1.3, Story 3.2 and Story 3.3, which already contain them, and keep the spine to the invariants.

## Rubric summary

1. **Divergence points:** mostly fixed. The ones still missing are the Generate-disable mechanism (R2-1), where translation sits relative to the test seam (R2-2) and the broad-exception policy (R2-3).
2. **Enforceable rules:** AD-7's `is_running` row does not prevent its stated divergence (R2-1). The other rules are enforceable.
3. **Deferred:** safe. None of the deferred items lets two units diverge.
4. **PRD coverage:** FR-1 to FR-12, §9, §10 and §11 are covered. §7 Cost says "throttling and/or caching during heavy testing". The spine chooses none and relies on tests never calling the API, which is acceptable and stated.
5. **Dimensions:** the operational envelope is now in the spine. Two edge cases are not decided: unexpected exceptions (R2-3) and the empty-input fingerprint (R2-4).
6. **Consistency:** see R2-4 to R2-7 and L2. Epic messages match EXPERIENCE.md word for word, apart from staged variants that are labelled as such. No story depends on a later story.

## Totals

| Severity | Count |
| --- | --- |
| Critical | 0 |
| High | 1 |
| Medium | 4 |
| Low | 5 |
