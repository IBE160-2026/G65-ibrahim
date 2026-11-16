# Re-review (round 2) — AI Study Buddy architecture spine

Date: 2026-11-16 · Spine: updated draft · Lenses run one at a time: rubric walker (`review-rubric-walker-r2.md`), version currency (`review-version-currency-r2.md`), adversarial (`review-adversarial-r2.md`).

**Verdict:** The update closed the round-1 critical and high findings without regressions (rubric: 15 resolved, 2 partly; adversarial: 7 closed, 3 partly). Every new API claim was confirmed by probing in a Python 3.13 venv. What remains is one layer finer: how Generate runs in Streamlit's rerun model, which side of the `_call_gemini` seam translates errors, what values widget keys hold, and how messy settings input is normalised. Five of these are high-impact for stories built separately.

## High

| # | Finding | Sources | Proposed fix |
| --- | --- | --- | --- |
| R1 | **Generate mechanism.** Setting `is_running` inside an inline handler can't disable a button that has already been drawn, so a second click can start a second Gemini call. Callback vs inline also moves where the spinner and errors appear. | rubric R2-1, adversarial A2-1 | AD-7: Generate uses `on_click` to set `is_running=True`. The script body runs the pipeline at the error-area position under `st.spinner`, stores the result or `last_error`, sets `is_running=False`, then `st.rerun()`. The button uses `disabled=is_running`. |
| R2 | **A wrong API key shows "material rejected".** Gemini answers a bad key with HTTP 400 `API_KEY_INVALID`, which AD-5 maps to `MaterialRejected`. | version VC2-1, adversarial A2-4 | AD-5: new `InvalidApiKey`, checked before the general 400 rule. An empty or whitespace key counts as missing. |
| R3 | **Widget values have no fixed types.** `source_tab` holds the tab label; the radios could hold labels or enums; `raw` could be `UploadedFile`, bytes, `None` or `""`. The Generate fingerprint and the rerun fingerprint never match, so the stale note is always on. | adversarial A2-2, rubric R2-4 | AD-7/AD-12: Length/Language radios use enum members as options with a label `format_func`; `models.SOURCE_BY_TAB_LABEL` maps the tab label to `Source`; `raw` is `bytes` (`getvalue()`, or `b""`) for PDF and `str` (or `""`) for text; the fingerprint is SHA-256 over a fixed serialisation that includes `source`. |
| R4 | **Which side of the test seam translates errors.** If `_call_gemini` translates, monkeypatching it skips translation. Its return value for a blocked reply (`None`) isn't fixed. | rubric R2-2, adversarial A2-3, version VC2-5 | AD-4: `_call_gemini(prompt, settings) -> str \| None` makes the raw call only and lets SDK and `httpx2` exceptions propagate. `generate_study_pack` checks the key, calls `_call_gemini`, translates every exception, maps `None`/empty to `BadModelResponse`, and validates. |
| R5 | **Settings input isn't normalised.** TOML booleans, placeholder keys, and seeding `demo_mode` two different ways (which shows a Streamlit warning). | adversarial A2-4 | AD-9: `load_settings(secrets: Mapping[str, object])` turns values into strings; the key is stripped and `""` becomes `None`; `mock_mode` accepts `True`, `"true"` or `"1"`. `demo_mode` is seeded only via `if "demo_mode" not in st.session_state`, and the widget gets no `value=`. |

## Medium

| # | Finding | Sources | Proposed fix |
| --- | --- | --- | --- |
| R6 | Only `TimeoutException`/`ConnectError` are mapped; `ReadError` and `RemoteProtocolError` escape. | version VC2-2 | AD-5: catch `httpx2.TransportError`, the base class. |
| R7 | pypdf can raise `AttributeError` and `TypeError` on corrupt files (16 of ~4,250 fuzzed). Nothing catches errors that aren't `StudyBuddyError`. | version VC2-3, rubric R2-3 | AD-6: `read_material` turns any other exception into `UnreadablePdf`. AD-5: `app.py` has one last-resort row in `ERROR_UI` for unexpected exceptions: "Something went wrong. Try Generate again." |
| R8 | Owner-password PDFs are `is_encrypted` but readable, so the current rule rejects good slides. | version VC2-4 | AD-6: if encrypted, try `decrypt("")`; only a `FileNotDecryptedError` gives `UnreadablePdf`. |
| R9 | Demo mode: the caption shows the live widgets over a fixed pack, and editing the input raises the stale note for output that can't change. | rubric R2-4 / H2 partly, adversarial A2-5 / H4 partly | AD-10/AD-12: `demo.py` exposes `DEMO_LENGTH` and `DEMO_LANGUAGE`; `generated_with` uses them in demo mode; the demo fingerprint covers only the demo flag. |
| R10 | `ERROR_UI` style could be a Streamlit function or a string; lookup and catch scope are open. The staging rule leaves unmapped errors between Stories 1.3 and 1.4. | adversarial A2-6, A2-7 | AD-5: style is the string `"error"` or `"warning"`, lookup is by exact type, and there is a fallback row for any `StudyBuddyError` not yet mapped, so Story 1.3 is already safe. |
| R11 | Story 3.1's "no network in Demo mode" test would need to test `app.py`, which AD-11 doesn't cover. | rubric R2-5 | Story 3.1: test at core level (`demo.load_study_pack` with `llm._call_gemini` patched to fail), plus a manual check in the app. |

## Low

- `quiz_answers` "cleared" should be one fixed value: `None`. *(A2-8)*
- Stale-note inputs and style should match across AD-12, Story 2.2 and EXPERIENCE.md. *(R2-6)*
- Small signature mismatches between AD-6 and Story 1.2, and between the quiz convention and Story 2.1. *(R2-7)*
- The flowchart lacks `app → models` and `app → errors` edges. *(L2 partly)*
- The 5-question count is enforced only after the call. Accepted: it's a rare wasted request. *(R2-9)*
- The spine is getting heavy. Four pins could move to stories or the README. Accepted for now; trim after build if needed. *(R2-10)*
- Confirmed harmless: `pip freeze` on Windows adds only pure-Python `colorama` and `tzdata`, and the Linux dry-run install works. `source_tab` holds the tab label.

## Counts after merging

| Severity | Count |
| --- | --- |
| Critical | 0 |
| High | 5 |
| Medium | 6 |
| Low | 6 |

New UX text that R2 and R7 would introduce: "Gemini didn't accept the API key. Check GEMINI_API_KEY (see the README)." and "Something went wrong. Try Generate again."
