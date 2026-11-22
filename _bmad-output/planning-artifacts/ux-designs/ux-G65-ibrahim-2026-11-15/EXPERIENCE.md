---
name: AI Study Buddy
status: final
updated: 2026-11-22
sources:
  - _bmad-output/planning-artifacts/briefs/brief-G65-ibrahim-2026-09-11/brief.md
  - _bmad-output/planning-artifacts/prds/prd-G65-ibrahim-2026-10-18/prd.md
---

# AI Study Buddy — Experience Spine

Glossary terms (Course Material, Summary, Length, Output Language, Quiz, Answer Key) are used as defined in PRD §3. FR numbers refer to the PRD.

## Foundation

Single-surface web app, used on a laptop or desktop browser. Built with **Streamlit** and its built-in widgets; `DESIGN.md` is the visual identity reference. Single user, no login, no persistence between sessions (PRD §5). Runs locally or on Streamlit Community Cloud.

Streamlit reruns the whole script on every interaction. This spine therefore requires all generated results to live in `st.session_state`, so that answering or submitting the quiz never triggers a new Gemini call. `[ASSUMPTION]`

## Information Architecture

One page with two blocks. No navigation, no sidebar.

| Surface | Reached from | Purpose | FRs |
|---|---|---|---|
| Input block | App open | Provide Course Material (PDF or pasted text), choose Length and Output Language, press Generate, optionally turn on Demo mode | FR-1, FR-2, FR-5, FR-6, FR-12 |
| Results block: Summary tab | Appears after a successful Generate | Read the structured Summary | FR-7, FR-10, FR-13 |
| Results block: Quiz tab | Same results block, second tab | Answer 5 multiple-choice questions, submit, see per-question results | FR-8, FR-9, FR-10 |

Both tabs are always reachable from the same view, which satisfies FR-10 ("without additional navigation"). Layout order is defined in `DESIGN.md` Layout & Spacing.

## Voice and Tone

UI chrome is in **English**; only the generated content follows Output Language. Short, plain, student-to-student. No hype, no exclamation marks, no "AI magic".

| Do | Don't |
|---|---|
| "Upload a lecture PDF or paste your notes." | "Let AI supercharge your studying! 🚀" |
| "Reading your material and writing the summary and quiz…" | "Processing request…" |
| "This PDF has no readable text. It's probably scanned. Try a text-based version, or paste the text instead." | "Error: extraction failed (empty string)." |
| "You got 3 of 5 right." | "Score: 60%. Keep it up!!" |
| "Incorrect — correct answer: B. Normalisation reduces redundancy." | "Wrong!" |
| "Your material is sent to Google Gemini for processing. Nothing is saved." | (no disclosure) |

## Component Patterns

Behavioral. Visual specs live in `DESIGN.md` Components.

| Component | Behavioral rules |
|---|---|
| Input tabs | Exactly one source is used per Generate: the active tab's content. Switching tabs does not clear the other tab's content. |
| File uploader | Accepts `.pdf` only (`type=["pdf"]`). One file at a time. Validation (empty file, no extractable text) runs when Generate is pressed, not on upload, so errors show in one place. |
| Paste text area | Free text, no length limit in the UI. Whitespace-only counts as empty. |
| Length radio | Short / Medium / Long; default **Medium** `[ASSUMPTION]`. Each option's caption shows its word range (<150, 150–400, 400–800) so the choice is concrete. |
| Language radio | English / Norsk; default **English** `[ASSUMPTION]`. Applies to Summary and Quiz. |
| Demo mode toggle | `st.toggle("Demo mode (example output, no API key needed)")` under the options, off by default (on at start when `MOCK_MODE=true`). When on, Generate skips validation and the API and returns a saved example Summary and Quiz from the repo. Works without a Gemini key. (FR-12) |
| Generate button | Runs validation first (FR-4, FR-3), then one Gemini request for Summary and Quiz together (PRD §9 assumption). Disabled, with a spinner, while the request runs. A second click during a run is impossible. |
| Results tabs | Shown only after a successful generation. Opens on the Summary tab. |
| Summary | Rendered markdown: topic headings plus bullets. Caption below: "{N} words · {length} · {language}". If the word count is outside the Length's range ±10 %, the Summary is still shown, with the word-range note under the caption (FR-5, FR-13). |
| Quiz form | 5 questions (FR-8: exactly 5) in one `st.form`, each a 4-option radio with no default answer. One "Check answers" button, which checks only when all 5 are answered. (FR-8, FR-9) |
| Quiz results | After Check answers: score line at the top, and under each question a correct/incorrect row with the right answer shown if wrong. Radios stay visible with the user's choices. A "Try again" button clears answers and results (same questions, no new API call). |

## State Patterns

| State | Where | Treatment |
|---|---|---|
| First load | Whole page | Input block only. Results block hidden. Caption under title explains the app in one sentence. |
| Generating | Generate button area | `st.spinner("Reading your material and writing the summary and quiz…")`. Button disabled. Typical wait under ~30 s (PRD §7). |
| Success | Results block | Results tabs appear, Summary tab active. |
| Summary outside word range | Summary tab, under the caption | Summary is shown as normal. `st.info`: "This summary has {N} words. {Length} aims for {range} words." (e.g. "Medium aims for 150–400 words."; Short reads "under 150 words"). Shown only when the count is outside the range ±10 % (Short 0–165, Medium 135–440, Long 360–880). Uses the Length the summary was generated with, not the live radio. Not an error: the error area stays empty. (FR-13) |
| No input | Error area | "Upload a PDF or paste some text first." No API call. |
| Wrong file type | Error area | Normally blocked by the uploader. Fallback: "Only PDF files are supported." (FR-4) |
| Empty file (0 bytes) | Error area | "This file is empty. Choose another PDF." No API call. (FR-4) |
| Scanned / image PDF | Error area | "This PDF has no readable text. It's probably scanned. Try a text-based version, or paste the text instead." No API call. (FR-3) |
| Encrypted or damaged PDF | Error area | "This PDF can't be opened. It may be password-protected or damaged. Try another file, or paste the text instead." No API call. (FR-4) |
| Missing API key | Error area, on first Generate | "No Gemini API key found. See the README section 'Get a free Gemini API key', or turn on Demo mode to see example output." |
| Demo mode results | Top of results block | Persistent `st.warning`: "Demo mode — example output, not generated from your material." Shown on both tabs. |
| Rate limit (free tier) | Error area | `st.warning`: "Gemini's free limit was reached. Wait a minute and try again." Inputs kept. |
| Timeout / network error | Error area | "Couldn't reach Gemini. Check your connection and try again." Inputs kept. |
| Invalid API key (Gemini rejects the key) | Error area | "Gemini didn't accept the API key. Check GEMINI_API_KEY (see the README)." Inputs kept. |
| Unexpected error (anything not listed here) | Error area | "Something went wrong. Try Generate again." Inputs kept; details printed to the console only. |
| Material rejected by Gemini (HTTP 400, e.g. too long) | Error area | "Gemini couldn't process this material. It may be too long. Try a shorter part." Inputs kept. |
| Unusable model response | Error area | "The answer from Gemini couldn't be read. Try Generate again." Raw response is never shown to the user. |
| Stale results | Above results block | If the input, Length or Output Language changes after a generation: `st.info`: "Settings changed. Press Generate to update." Old results stay visible until regenerated. `[ASSUMPTION]` |
| Quiz unanswered questions | Quiz form | Check answers with blanks: nothing is checked. `st.warning`: "Answer all questions first. Missing: 2, 4." Chosen answers are kept. |

Errors never crash the app and never leave a blank results area. Every error keeps what the user already entered.

## Interaction Primitives

- **Mouse first.** Click to upload, select, generate, check.
- **Keyboard:** standard browser and Streamlit behaviour: Tab between widgets, arrow keys within radios, Enter/Space to press buttons. No custom shortcuts.
- **One action per run:** Generate is the only thing that calls the API. Nothing calls it automatically.
- **Banned:** auto-generate on input change, generating a new quiz on Try again, modal dialogs, hiding inputs in the sidebar.

## Accessibility Floor

Behavioral. Visual contrast is inherited from Streamlit's default theme (see `DESIGN.md` Colors).

- Every widget has a visible text label (no `label_visibility="collapsed"`).
- Correct/incorrect is shown with icon **and** words, never colour alone.
- The summary uses real markdown headings so screen readers can jump between topics.
- Error messages state cause and next step in plain language.
- Tab order follows the visual top-to-bottom order defined in `DESIGN.md` Layout & Spacing.
- Generated content follows Output Language; the UI chrome language is unchanged.

## Privacy & Disclosure

*Invented section: the PRD (§7) requires disclosing that material leaves the machine.*

- A caption under the input tabs, always visible: "Your material is sent to Google Gemini for processing. Nothing is saved." `[ASSUMPTION: in-app in addition to the README]`
- No uploaded file or result survives a browser refresh; this matches PRD §5 and needs no extra UI.

## Inspiration & Anti-patterns

- **Rejected — chat interface:** the brief positions the product against generic chat tools. No chat box, no conversation history, no follow-up prompting.
- **Rejected — gamification:** no streaks, confetti or badges. The score line is information, not a reward.
- **Rejected — showing raw AI output:** structured rendering only; the model's JSON is an implementation detail.

## Key Flows

### Flow 1 — Night before the deadline (Abdiaziz, Norwegian lecture PDF) — PRD UJ-1

1. Abdiaziz opens the running app. Only the input block is visible.
2. On the Upload PDF tab, Abdiaziz drags in a 15-slide Norwegian lecture PDF.
3. Abdiaziz picks **Medium** and **English**, then presses **Generate**.
4. The spinner shows "Reading your material and writing the summary and quiz…" for about 20 seconds.
5. The results block appears on the Summary tab: an English summary with four topic headings and bullets, caption "318 words · medium · English".
6. Abdiaziz reads it, then switches to the Quiz tab and answers all 5 questions.
7. **Climax:** Abdiaziz presses **Check answers**. "You got 3 of 5 right." Two questions show "Incorrect — correct answer: …", so Abdiaziz knows exactly which two topics to re-read. Abdiaziz scrolls back to the matching summary headings.
8. Abdiaziz presses **Try again**, answers the two from memory, and gets 5 of 5. No new API call is made.

Failure: the PDF is a scanned copy. After Generate, the error area shows "This PDF has no readable text…", the upload is kept, and Abdiaziz switches to Paste text and pastes the notes from the course page instead.

### Flow 2 — Mixed-language notes, short Norwegian recap (Abdiaziz, between lectures)

1. Abdiaziz copies a mix of Norwegian and English notes into the Paste text tab.
2. Abdiaziz picks **Short** and **Norsk** and presses Generate.
3. **Climax:** The summary comes back fully in Norwegian, under 150 words, even though half the source was English (FR-6).
4. Abdiaziz changes Length to Long out of curiosity; the "Settings changed. Press Generate to update." note appears, and the old summary stays until Abdiaziz decides to regenerate.

Failure: Gemini's free-tier limit is hit. A warning asks Abdiaziz to wait a minute; the pasted text and settings are kept.

### Flow 3 — First run by a grader `[ASSUMPTION: protagonist not named in PRD]`

1. The IBE160 grader clones the repo and follows the README, including getting a free Gemini key.
2. The grader forgets to add the key and presses Generate with a test PDF from the test-data folder.
3. The error area says "No Gemini API key found. See the README section 'Get a free Gemini API key', or turn on Demo mode to see example output."
4. The grader turns on Demo mode and presses Generate. The example summary and quiz appear under the "Demo mode" banner, and the grader tries the quiz flow.
5. The grader then adds the key to `.env`, restarts the app, turns Demo mode off, and generates again with the test PDF.
6. **Climax:** A real summary and quiz for the test PDF appear with no further help from the builder (PRD SM-2).

## Decisions on PRD open items

These are now written into the PRD (updated 2026-11-15).

- **Quiz format (PRD OQ 3):** multiple choice, 4 options, 1 correct (FR-8).
- **Demo mode (PRD OQ 4):** included, behind a toggle, with a persistent banner (FR-12).
- **UI chrome language:** English. Output Language applies to Summary and Quiz (FR-6).
