# Architecture validation

## 2026-11-16 kl. 17:35 — Abdiaziz

### Task
Validate the architecture spine with `/bmad-architecture` (Validate intent) without changing it, running the review lenses one at a time.

### Plan
- Lint with `lint_spine.py`, then three lenses in sequence: rubric walker, version currency, adversarial divergence.
- Merge the findings into one report (Markdown + HTML).
- Spine from: [998-2026-11-16-15-56-05-architecture-spine.md](998-2026-11-16-15-56-05-architecture-spine.md).

### Result
- Lint clean. Reviews in `_bmad-output/planning-artifacts/architecture/architecture-G65-ibrahim-2026-11-16/reviews/`: `review-rubric-walker.md`, `review-version-currency.md`, `review-adversarial.md`, and the merged `validation-report.md` / `.html`.
- After merging: 1 critical, 4 high, 9 medium, 6 low.
  - C1: crash at startup without `secrets.toml`.
  - H1: quiz count (min 5 vs exactly 5).
  - H2: session-state contract incomplete.
  - H3: fingerprint underspecified.
  - H4: google-genai 3.x has no default timeout, and network errors come from `httpx2`.
- Verified OK: all pins current and compatible on Python 3.13; model stable and free; `st.tabs` exposes the active tab (closes the Story 1.2 open item).
- Spine unchanged; memlog has a validate event. Not committed.

### Open items
- Run a spine Update for C1 and H1–H4 (AD-3, AD-4, AD-5, AD-7, AD-9; new AD-12) and the medium findings M1–M8, then align Stories 1.2, 1.3, 1.4, 2.1, 2.2 and 3.1 in `epics.md`. Do this before Sprint Planning and Story 1.1.
- `use_container_width` is deprecated in Streamlit 1.67: update `DESIGN.md` and Story 1.2 to `width="stretch"`.

## 2026-11-16 kl. 18:09 — Abdiaziz

### Task
Apply the validation fixes as a spine Update, re-run the three lenses one at a time on the updated spine, apply the round-2 fixes, then finalize and commit.

### Plan
- Round-1 fixes: tighten AD-3, AD-4, AD-5, AD-6, AD-7, AD-9; add AD-12 (`helpers.py`: fingerprint and word count); staging rule; Deployment & operations section; align UX and stories.
- Round-2 review: rubric walker, version currency (probed in a Python 3.13 venv), adversarial.
- Round-2 fixes, then finalize without a third round (user's choice).

### Result
- Spine `ARCHITECTURE-SPINE.md` is final again, lint clean. AD-1 to AD-11 keep their numbers, plus the new AD-12.
- Round 2 confirmed the round-1 fixes with no regressions, and found 0 critical, 5 high, 6 medium and 6 low. All 5 highs and all mediums are fixed:
  - Generate runs through `on_click` with `disabled=is_running`, plus a new `last_error` key.
  - New `InvalidApiKey` error (Gemini answers a bad key with 400 `API_KEY_INVALID`).
  - Fixed value types for widget keys, and a fixed fingerprint serialisation.
  - `_call_gemini` makes the raw call only; `generate_study_pack` does all translation.
  - Settings are normalised.
  - Medium fixes: `httpx2.TransportError` is caught as a whole; pypdf catch-all; `decrypt("")` for owner-password PDFs; demo caption and fingerprint; `ERROR_UI` fallback and last-resort rows; Story 3.1 tests at core level.
- UX `EXPERIENCE.md` has 4 new error states (encrypted/damaged PDF, material rejected, invalid key, unexpected error). `DESIGN.md` uses `width="stretch"`.
- `epics.md` Stories 1.2, 1.3, 1.4, 2.1, 2.2, 3.1, 3.2 and 3.3 are aligned with the spine.
- Committed as `751af2f` (spine, memlog, all review files, UX, epics) and pushed to `origin/main` together with the session log.

### Open items
- The four new error messages were written by Claude and should be reviewed by Abdiaziz.
- Accepted as deferred: the quiz count is checked only after the call; the spine is somewhat heavy (trim after build if needed).
