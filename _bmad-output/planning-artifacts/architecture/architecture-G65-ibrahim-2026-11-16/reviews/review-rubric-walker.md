# Review: rubric walker — ARCHITECTURE-SPINE.md (AI Study Buddy)

Reviewer: independent, good-spine checklist (items 1–6). Inputs: PRD (2026-11-15), EXPERIENCE.md, DESIGN.md, epics.md, .memlog.md. `technology.md` ignored as instructed.

**Verdict:** The spine is a sound, beginner-sized substrate that gets the big divergence points right (one gateway, one shared `StudyPack`, typed errors, demo bypass). Two real contradictions with the UX and epics need fixing before build: the quiz length (`min 5` vs a fixed 5) and AD-7's "exactly these keys", which Streamlit widget keys and the epics already break. Below those sit gaps in error coverage, the fingerprint definition and PRD §7 coverage.

---

## F1 — Quiz length: `min 5` in the schema, exactly 5 everywhere else

- **Severity:** high
- **Location:** AD-3 class diagram (`quiz: list~QuizQuestion~ (min 5)`); EXPERIENCE.md Component Patterns; epics Story 2.1
- **Problem:** The spine allows 5 or more questions. EXPERIENCE.md fixes 5: "Answer 5 multiple-choice questions", "checks only when all 5 are answered". Epics hard-code it too: "questions numbered 1–5", score line "You got X of 5 right", and the demo file has "5 quiz questions".
- **Why it matters:** Gemini can legally return 6–8 questions. The quiz UI story will hard-code `5` (the ACs say so), while `quiz.py` and the schema follow `len(quiz)`. The result is a wrong score denominator ("You got 6 of 5"), questions that are never shown, or a completeness check that misses questions 6+.
- **Fix:** Choose one. (a) Pin the count in AD-3: `quiz: exactly 5` (`min_length=5, max_length=5`) and tell the prompt to ask for 5. Or (b) add a convention: "UI and `quiz.py` always use `len(study_pack.quiz)`; the literal 5 never appears in code", and change the epics ACs to "X of N". Option (a) matches the UX and is simpler.

## F2 — AD-7 "exactly these keys" doesn't hold under Streamlit, and the epics already break it

- **Severity:** high
- **Location:** AD-7; epics UX-DR3 / Story 1.2 (`st.tabs(..., key=..., on_change="rerun")`), Story 3.1 (toggle default from `MOCK_MODE`), Story 2.1 (Try again)
- **Problem:** The rule says "`app.py` uses exactly these `st.session_state` keys". But every keyed widget also writes `st.session_state`: the input-tabs key that the epics require, the quiz radios inside the `st.form`, and the demo toggle, whose default has to be seeded once from `MOCK_MODE`. Three behaviours also need state the AD leaves out:
  - Disabling Generate "while the request runs" needs a running flag across reruns.
  - Try again "clears answers" can't assign to a widget-keyed value after the widget is created. It has to delete the keys or rotate the form key.
  - The AD says `quiz_answers` is "cleared by Generate", but it doesn't say whether that happens on press or only on success. Story 1.4 says on a failure "any earlier results stay as they were".
- **Why it matters:** The rule can't be met as written, so each story author will invent their own widget keys and their own reset method. Two likely clashes: the quiz story keeps the answers in radio keys while `quiz.py` expects `quiz_answers`; and a failed Generate wipes the quiz answers in one implementation and keeps them in another.
- **Fix:** Rewrite AD-7 as "app-owned keys" (the five listed) plus a "widget keys" naming rule, e.g. prefix `w_`, with the names listed for: input tabs, paste area, uploader, length, language, demo toggle, quiz radios `w_q{i}`. Add these rules:
  - The toggle default is seeded only if its key is absent.
  - Try again deletes the `w_q*` keys plus `quiz_answers` and `quiz_checked`.
  - Generate writes `study_pack`, `is_demo` and `input_fingerprint`, and clears the quiz keys, **only on success**.
  - Say how Generate is disabled (e.g. `is_generating` with a rerun), or accept that one Streamlit run blocks the UI and change the UX wording.

## F3 — `input_fingerprint` is underspecified

- **Severity:** medium
- **Location:** AD-7 ("a hash of source text + length + language + demo flag")
- **Problem:** The rule doesn't say:
  - whether "source text" means the raw input (PDF bytes or pasted string) or the extracted text from `ingest.py`;
  - whether the active input tab is part of the fingerprint;
  - which hash function to use;
  - what to hash in demo mode, where `ingest` is skipped (AD-10).

  If it means extracted text, every rerun (every quiz click) has to re-run pypdf just to compare. If the input is currently invalid, there is no fingerprint to compare at all.
- **Why it matters:** Story 2.2 (stale note) and Story 3.1 (demo flag) are built separately. Story 2.2 might hash extracted text while the rerun compare hashes raw bytes, so the note shows all the time or never. Switching tabs while both tabs hold content gives a false "not stale".
- **Fix:** Define it as `fingerprint(active_tab, raw_source, length, language, is_demo)`, where `raw_source` is the uploaded file's bytes or the pasted string (not extracted). Use `hashlib.sha256` and make it a pure function in a core module (see F6).

## F4 — Error taxonomy leaves real failure paths unmapped

- **Severity:** medium
- **Location:** AD-5, AD-6, AD-10
- **Problem:** The eight error types don't cover several cases:
  - **Corrupt or encrypted PDF:** pypdf raises `PdfReadError` or `FileNotDecryptedError`. Is that `NotPdf` or `NoExtractableText`? The AD doesn't say.
  - **How `NotPdf` is detected:** extension, `%PDF` magic bytes, or a pypdf parse failure? Undefined.
  - **Gemini 400 `INVALID_ARGUMENT`:** for example input over the token limit. Pasted text has no cap (EXPERIENCE: "no length limit in the UI"), so this is reachable. It falls into `GeminiUnavailable`, whose message "Check your connection" is wrong for this case.
  - **Safety block or empty candidate:** the API returns no text, or `response.parsed` is `None`. Not mapped.
  - **Invalid `demo/study_pack.json`:** a raw pydantic `ValidationError` from `demo.py`. This breaks "Core modules raise only subclasses of `StudyBuddyError`", and the module diagram has no `demo --> errors` edge.
- **Why it matters:** `ingest.py` and `llm.py` authors will each decide these alone, and `app.py`'s single mapping will hit an unhandled exception. That breaks "Errors never crash the app" (EXPERIENCE State Patterns) and FR-3/FR-4's "not an unhandled exception".
- **Fix:** Extend AD-5 with explicit mappings:
  - unreadable or encrypted PDF → `NotPdf`, detected via pypdf open failure;
  - empty or blocked response, or `parsed is None` → `BadModelResponse`;
  - a new `InputTooLarge` error (needs a UX message), or map 400 to `BadModelResponse`;
  - demo file invalid → `BadModelResponse`.

  Add `demo --> errors` to the diagram. Add a convention that `app.py` also catches any `StudyBuddyError` it didn't expect with one generic message.

## F5 — The "timeout" state can't be reached: no request timeout is set

- **Severity:** medium
- **Location:** AD-4, AD-5 (`GeminiUnavailable (timeout, …)`); PRD §7 Performance (~30 s); EXPERIENCE "Timeout / network error"
- **Problem:** Nothing fixes a client timeout. The spine doesn't set `http_options`/timeout, so a stalled call leaves the spinner running far longer than the ~30 s the PRD and UX promise. The "Couldn't reach Gemini" state may never fire.
- **Why it matters:** The NFR and the UX state can't be verified. Each builder or tester picks their own value, or none.
- **Fix:** In AD-4, set one timeout (e.g. 60 s via `types.HttpOptions(timeout=60_000)`) in `llm.py`. Say that the timeout exception maps to `GeminiUnavailable`.

## F6 — Testable logic is assigned to `app.py`, which AD-11 doesn't test

- **Severity:** medium
- **Location:** Conventions "Word count … computed by the app"; AD-7 fingerprint; AD-11 coverage list; epics Story 1.3 ("tests cover … word counting") and Story 2.2 ("a `pytest` test confirms … the fingerprint")
- **Problem:** Word count and the fingerprint are placed in the shell, which imports Streamlit (AD-1). AD-11's test scope is `ingest`, `quiz`, `models` and `llm` parsing, not `app.py`. Yet the epics require pytest tests for both.
- **Why it matters:** One builder writes the functions in `app.py` and has to import Streamlit in tests. Another puts them in a core module the spine doesn't name. The structural seed and the capability map then don't match the code.
- **Fix:** Put `word_count(summary)` and `fingerprint(...)` in a core module, e.g. `models.py` or a small `study.py`. Name it in the seed and the capability map, and add it to AD-11's coverage list.

## F7 — `llm.py` parse path and schema constraints are not fixed

- **Severity:** medium
- **Location:** AD-2, AD-3, AD-11 ("`llm`'s network call monkeypatched")
- **Problem:** AD-2 passes `response_schema=StudyPack`, but doesn't say how the reply is validated. `response.parsed` can be `None` without raising. `StudyPack.model_validate_json(response.text)` raises `ValidationError`. They fail differently. The spine also doesn't say whether the Pydantic constraints (exactly 4 options, `correct_index` 0–3, list lengths) are sent in the schema or only checked after the reply. Last, AD-11 doesn't name the seam to monkeypatch.
- **Why it matters:** The test author patches one thing (for example `genai.Client`) while the implementer wraps the call in another helper. The failure tests in Story 1.4 then pass or fail by accident, and "fails schema validation → `BadModelResponse`" isn't guaranteed.
- **Fix:** In AD-2/AD-4, state the following:
  - `llm.py` calls a private `_call_gemini(prompt, settings) -> str`, which is the only monkeypatch seam.
  - It validates with `StudyPack.model_validate_json(text)`.
  - Any `ValidationError`, `JSONDecodeError` or empty text becomes `BadModelResponse`.
  - Constraints are enforced after the reply; the schema sent to Gemini is guidance only.

## F8 — PRD §7 and the operational envelope are only partly covered

- **Severity:** medium
- **Location:** Capability → Architecture Map; Deployment & environments; Deferred
- **Problem:** Several required items are missing or appear only in the memlog:
  - **§7 Privacy:** the README disclosure, and the memlog's own finding that "Free-tier data is used to improve Google products -> README disclosure". Neither is in the spine.
  - **§7 Cost:** "managed via throttling and/or caching". Caching is deferred, but throttling isn't decided, deferred or raised as a question.
  - **§7 Performance:** has no row in the map.
  - **README / SM-2:** appears in the seed, but no capability row points at it.
  - **Provider strategy:** the spine is silent on free-tier quota limits, what happens if `gemini-3.5-flash-lite` is deprecated (the memlog notes 2.5-flash is being rerouted), and whether there is a fallback model. `GEMINI_MODEL` is the only lever, and the spine never presents it as the fallback strategy.
  - **Python 3.13 on Community Cloud:** must be picked by hand in Advanced settings (the default is 3.12). This is only in the memlog.
- **Why it matters:** The epics had to pull these items from the memlog and the PRD themselves. Story 3.3's privacy text and Story 3.2's Python choice aren't anchored in an AD or the seed. A different epic author could leave them out.
- **Fix:** Add map rows for §7 Privacy (README + in-app caption), §7 Performance (AD-2 + the F5 timeout) and SM-2/README. Add one "Provider strategy" line: single model, `GEMINI_MODEL` is the fallback lever, no automatic fallback, no throttling in v1 (deferred alongside caching). Copy the Python 3.13 Advanced-settings note into the deployment section.

## F9 — Epics stage deviations from ADs that the spine doesn't allow

- **Severity:** low
- **Location:** AD-5 ("maps each type to exactly one message from EXPERIENCE.md"), AD-7 (fingerprint includes the demo flag); epics Story 1.4, Story 2.2, Story 1.2
- **Problem:** The epics knowingly break three ADs for a while:
  - Story 1.4 uses a shortened missing-key message (no Demo mode hint).
  - Story 2.2 builds the fingerprint without the demo flag ("Story 3.1 adds the demo flag").
  - Story 1.2 shows a temporary "Read 1,234 words" result.

  Each is reasonable, but under the ADs as written they are violations.
- **Why it matters:** A strict reviewer of Story 1.4 or 2.2 would flag a correct story as non-compliant. Or the temporary versions survive because nothing says they must be replaced.
- **Fix:** Add one line to the spine: "Stories may ship a subset of an AD's enumerations (messages, fingerprint fields) as long as a later story completes it; the final state must match the AD." Or align Stories 1.4 and 2.2 with the ADs from the start.

## F10 — Diagrams disagree with the text

- **Severity:** low
- **Location:** Design Paradigm flowchart and layer table; Generate-flow sequence diagram
- **Problem:**
  - The module flowchart leaves out `llm --> prompts/` (AD-8), `demo --> errors` (F4), the `demo/study_pack.json` read, and `ingest`'s pypdf dependency, although the layer table lists them.
  - `app --> config` and `llm --> config` are drawn, but `demo` and `quiz` are allowed to import `config` and have no edge. That is harmless, but the table and the diagram disagree.
  - The sequence diagram shows the demo branch as `A->>A: demo.load_study_pack()`, a self-call on `app.py`, instead of a call to a `demo.py` participant. That makes it look as if the demo logic lives in the shell.
  - The capability map lists FR-10/FR-11 as "Governed by … UX spines", which is not an AD.
- **Why it matters:** These are small, but the readers are a beginner builder and a grader. The diagrams are the first thing they trust.
- **Fix:** Add the missing edges and a `D as demo.py` participant. In the layer table, narrow `config.py` imports to `app.py` and `llm.py` (or draw the edges).

## F11 — Enum values vs display and prompt labels are undecided

- **Severity:** low
- **Location:** Conventions "Length / language values … UI labels map to these"
- **Problem:** `Language` is `en`/`no`. The UI shows "English / Norsk". The summary caption's `{language}` shows "English" (EXPERIENCE Flow 1). The prompt needs a language name, not an ISO code. The spine doesn't say where these mappings live. Length has the same issue: the caption shows "medium" but the radio label is "Medium".
- **Why it matters:** `prompts/` and the summary caption may use different strings. For example, the prompt gets "no", which the model might read as the word "no".
- **Fix:** Put one label table in `models.py` per enum value: UI label, caption label, and prompt name ("Norwegian (Bokmål)" / "English").

---

## Counts

| Severity | Count |
| --- | --- |
| critical | 0 |
| high | 2 |
| medium | 6 |
| low | 3 |
| **total** | **11** |
