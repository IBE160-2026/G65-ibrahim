---
title: AI Study Buddy
status: final
created: 2026-10-18
updated: 2026-10-18
---

# PRD: AI Study Buddy

## 0. Document Purpose

This PRD translates the product brief (`_bmad-output/planning-artifacts/briefs/brief-G65-ibrahim-2026-09-11/brief.md`, revised 2026-10-18 per lecturer feedback) into requirements a solo builder can implement directly and a grader can trace against the finished app. It is written for Abdiaziz (builder) and whoever grades IBE160's Del 1 submission. Terms are defined once in the Glossary and used verbatim throughout; features are grouped with globally numbered Functional Requirements (FR-1, FR-2, ...) nested under them; inferences the brief didn't spell out are tagged inline as `[ASSUMPTION]` and indexed in §13.

## 1. Vision

AI Study Buddy turns a lecture PDF or pasted text into two things in one pass: a structured summary at a chosen length and language, and a short self-test quiz with an answer key covering the same material. It exists so Abdiaziz can process dense Norwegian/English course material faster and check whether he actually absorbed it, instead of manually re-reading and condensing it himself.

It is deliberately small: one person, new to programming, building against a near-term deadline. The two features share one pipeline (parse material → LLM call → structured output), which is what makes doing both in v1 realistic rather than reckless. It is not solving something no AI tool can do — see §4 Non-Goals and the brief's "What Makes This Different" — it is removing the friction of doing this manually, repeatedly, across courses.

## 2. Target User

### 2.1 Jobs To Be Done

- **Functional:** Turn a PDF of lecture slides/notes (or pasted text) into an accurate summary at the level of detail I want, in the language I want, without manually condensing it myself.
- **Functional:** Check whether I actually understood the material, right after reading the summary, without writing my own quiz questions.
- **Contextual:** Work across a mix of Norwegian and English course material within the same course, without re-reading everything in the "wrong" language first.
- **Personal/builder:** Understand the Python code I write well enough to explain it — not just have working output.

### 2.2 Non-Users (v1)

Other students are explicitly not users of v1 — no accounts, no multi-tenancy, single local/Community-Cloud deployment used only by Abdiaziz. Opening this up to classmates is a post-course Vision item (§8), not a v1 concern.

### 2.3 Key User Journeys

- **UJ-1. Abdiaziz turns a lecture PDF into a summary and a self-test, the night before a deadline.**
  - **Persona + context:** Abdiaziz, solo builder and student, has a dense Norwegian-language lecture PDF he needs to study quickly.
  - **Entry state:** No login — he opens the running Streamlit app directly.
  - **Path:** He uploads the PDF, picks summary length "medium" and output language "English," and submits. The app extracts the text, sends one request to the Gemini API, and shows a loading indicator while waiting.
  - **Climax:** The app returns a structured English summary (150–400 words) and a 5-question quiz with an answer key, generated from the same material in the same pass.
  - **Resolution:** He reads the summary, answers the quiz questions in the UI, and sees which ones he got right against the answer key — telling him what to re-read before moving on.
  - **Edge case:** If the PDF turns out to be scanned/image-based with no extractable text, the app shows a clear, understandable error instead of a blank or broken result, and he knows to find a text-based version instead.

## 3. Glossary

- **Course Material** — the PDF or pasted text a user submits as input. Source for both the Summary and the Quiz in a single request.
- **Text-based PDF** — a PDF whose text can be extracted directly (no OCR required). The only PDF type supported in v1; distinct from a **Scanned/Image-based PDF**, which has no extractable text and is out of scope.
- **Summary** — the structured, LLM-generated condensation of Course Material, produced at a selected Length and Output Language.
- **Length** — one of three selectable summary sizes: short (<150 words), medium (150–400 words), long (400–800 words).
- **Output Language** — Norwegian or English; the language the Summary (and Quiz) are generated in, independent of the Course Material's source language.
- **Quiz** — a set of at least 5 questions generated from the same Course Material as the Summary, each with a stored correct answer (the **Answer Key**).
- **Answer Key** — the correct answer for each Quiz question, used to check the user's submitted answers.
- **Gemini API (free tier)** — the external LLM service (Google Gemini) used for both Summary and Quiz generation. The only external dependency in v1.

## 4. Features

### 4.1 Course Material Ingestion

**Description:** The entry point for both downstream features. A user provides Course Material either by uploading a text-based PDF or pasting text directly. The system must distinguish a usable text-based PDF from one it cannot read, and reject invalid input clearly rather than failing silently. Realizes UJ-1.

**Functional Requirements:**

#### FR-1: PDF upload and text extraction

User can upload a text-based PDF as Course Material. System extracts its text content directly (no OCR).

**Consequences (testable):**
- A text-based PDF (lecture slides/notes) produces extracted text ready for downstream generation.
- Extraction does not attempt or require OCR for any input.

#### FR-2: Pasted-text input

User can paste plain text directly as Course Material, as an alternative to PDF upload.

**Consequences (testable):**
- Pasted text is accepted and used identically to extracted PDF text by downstream features.

#### FR-3: Scanned/invalid-PDF error handling

System detects when an uploaded PDF has no extractable text (scanned/image-based) and reports a clear, understandable error instead of proceeding or returning an empty result.

**Consequences (testable):**
- A scanned PDF with no extractable text produces a specific, human-readable error message, not a blank summary/quiz or an unhandled exception.

#### FR-4: Invalid-upload rejection

System rejects invalid uploads (wrong file type, 0-byte file) with a clear error message.

**Consequences (testable):**
- An empty file or a non-PDF/non-text file upload is rejected with a specific error message before any Gemini API call is made.

**Out of Scope:**
- Complex table/figure extraction, multi-column layout reconstruction, or any image/diagram content within a PDF.

### 4.2 Summary Generation

**Description:** Produces a structured summary of the Course Material at a user-selected Length and Output Language. Realizes UJ-1.

**Functional Requirements:**

#### FR-5: Length selection

User selects summary Length (short/medium/long) before generating.

**Consequences (testable):**
- Selecting "short" produces a summary under 150 words; "medium" produces 150–400 words; "long" produces 400–800 words.

#### FR-6: Output language selection

User selects Output Language (Norwegian or English) before generating, independent of Course Material's source language.

**Consequences (testable):**
- Selecting English output returns an English summary even when the source Course Material is in Norwegian, and vice versa.

#### FR-7: Structured summary generation

System generates a Summary from Course Material via the Gemini API, respecting the selected Length and Output Language, using a deliberately engineered prompt (not a naive pass-through of the raw text).

**Consequences (testable):**
- Output is a structured, readable summary, not a raw/unformatted model response.
- A typical lecture PDF (10–20 slides) returns a Summary within ~30 seconds under normal Gemini free-tier conditions.

**Feature-specific NFRs:**
- Prompt engineering must be demonstrable and documented — see §9 AI Approach & Prompt Engineering.

### 4.3 Quiz Generation

**Description:** Generates a self-test quiz with an answer key from the same Course Material used for the Summary, in the same user-facing request. Realizes UJ-1.

**Functional Requirements:**

#### FR-8: Quiz generation with answer key

System generates a Quiz of at least 5 questions from the Course Material, each with a stored correct Answer Key entry, alongside the Summary in the same generation request. `[ASSUMPTION: questions are multiple-choice or short-answer with an exact-match expected answer, to make "correct vs. incorrect" checking unambiguous for a beginner implementation — confirm format during architecture/UX.]`

**Consequences (testable):**
- Every generated Quiz has at least 5 questions.
- Every question has a corresponding stored correct answer before the user submits anything.

#### FR-9: Quiz answer submission and results

User can submit answers to the displayed Quiz and see, per question, whether their answer matched the Answer Key.

**Consequences (testable):**
- After submission, each question's result (correct/incorrect) is shown, compared against the Answer Key.

**Out of Scope:**
- Scoring history, retakes with new questions, or any persistence of quiz attempts across sessions (see §5 Non-Goals).

### 4.4 Results Display

**Description:** Presents the Summary and Quiz in a single, simple Streamlit interface, with clear feedback while the Gemini API call is in progress. Realizes UJ-1.

**Functional Requirements:**

#### FR-10: Combined results UI

System displays the generated Summary and Quiz together in a clean, simple Streamlit UI.

**Consequences (testable):**
- Summary and Quiz are both visible/reachable from the same results view without additional navigation.

#### FR-11: Loading feedback

System shows a loading/progress indicator while waiting on the Gemini API response.

**Consequences (testable):**
- A visible loading state is shown between submission and result, so the UI never appears frozen during the ~30-second wait.

## 5. Non-Goals (Explicit)

- Not building OCR or any scanned/image-PDF support in v1.
- Not building complex table/figure extraction or layout reconstruction.
- Not building multi-user accounts, login, or encrypted storage.
- Not supporting languages other than Norwegian and English.
- Not using any paid API tier — Gemini free tier only.
- Not persisting Summaries or Quizzes between sessions in v1 — each request is processed and displayed, not saved (storage is a stretch goal — see §8).

## 6. MVP Scope

### 6.1 In Scope

- PDF upload (text-based only) and pasted-text input (§4.1)
- Summary generation: length + language selection (§4.2)
- Quiz generation with answer key: ≥5 questions, submit-and-check flow (§4.3)
- Clean, simple Streamlit UI with loading feedback (§4.4)
- Documentation explaining how the app and its AI use work
- Secrets handled via `.env` or Streamlit `secrets.toml`, both gitignored; `.env.example` committed with placeholder values
- A dedicated test-data folder with sample documents: Norwegian PDF, English PDF, mixed-language text, scanned/invalid PDF
- README covering local setup, obtaining a free Gemini API key, and running the app end-to-end
- Deployment on Streamlit Community Cloud (free tier) or local run

### 6.2 Out of Scope for MVP

- Flashcard generation — deferred, same pipeline reusable later (§8)
- Per-subject storage of past summaries/quizzes (e.g. local SQLite) — deferred (§8)
- Multi-user accounts/login — deferred, not designed against in v1 architecture decisions
- `[NOTE FOR PM]` A canned-response test mode for graders without their own Gemini key is under consideration but not committed — see Open Question in §12.

## 7. Cross-Cutting NFRs

- **Performance:** Summary + Quiz for a typical 10–20 slide PDF return within ~30 seconds under normal Gemini free-tier conditions (validates FR-7, FR-8).
- **Cost:** Gemini free tier only, for both development and any live demo/grading run. Rate-limit risk is managed via throttling and/or caching during heavy testing, not by upgrading tier.
- **Privacy:** Uploaded Course Material is sent to Google's Gemini API for processing. No accounts and no server-side storage of uploads; this must be disclosed in the README so a grader (or future user) knows material leaves the local machine.
- **Beginner-risk / maintainability:** Abdiaziz is new to Python. The stack (Streamlit + one external API) and v1 feature set are kept deliberately narrow so the whole system stays within what a beginner can build, test, and genuinely explain.

## 8. Stretch Goals & Vision (Post-v1)

- **Flashcard generation** from the same Course Material, reusing the parse → LLM call → structured output pipeline, added only if time remains after v1 is solid.
- **Per-subject storage** of past Summaries/Quizzes (e.g. local SQLite), to build a collection over the semester.
- **Beyond this course:** opening the app to other students with basic accounts, and supporting organization across multiple courses. Not committed for this project; v1 is built so it doesn't require a full rewrite to get there.

## 9. AI Approach & Prompt Engineering

*Added because the grading rubric weights "process and AI governance" at 30% — the heaviest single criterion — and both the brief and lecturer feedback explicitly call for demonstrable, non-naive prompt engineering.*

- Summary and Quiz generation must use a deliberately engineered prompt — not a direct pass-through of the raw extracted text — and must request structured output (e.g., a defined schema separating the Summary text from the Quiz questions/answers) rather than freeform chat-style text, so the app can parse results reliably.
- `[ASSUMPTION: Summary and Quiz are produced by a single Gemini request per submission, combining both outputs in one structured response, to conserve free-tier rate-limit budget — confirm during architecture.]`
- Prompt iterations (what changed and why — e.g., tightening length adherence, fixing language leakage, improving quiz-answer unambiguity) should be captured somewhere durable (e.g., a `PROMPTS.md` or commit history with descriptive messages), so a grader can trace the AI-governance process from brief → PRD → actual prompt decisions. `[NOTE FOR PM: exact location/format for this log is an implementation decision, not a PRD requirement — flag for the architecture phase.]`

## 10. Testing & Quality Assurance

*Added because the grading rubric weights "quality assurance and testing" at 15%, and the brief's success criteria are now explicitly testable — this section says how they get verified.*

- **Automated-testable behavior:** PDF text extraction (success and scanned-PDF failure paths), invalid-upload rejection, length/language selection branching, quiz answer-key correctness checking. These map directly to the "Consequences (testable)" lists in §4 and should have corresponding automated tests.
- **Manual-only verification:** Summary *quality* (is it actually accurate and useful) cannot be automated — verified against a short checklist Abdiaziz writes for "what a good summary must contain," run against his own real lecture notes.
- **Test data:** the dedicated test-data folder (§6.1) — Norwegian PDF, English PDF, mixed-language text, scanned/invalid PDF — is the fixed set used to verify FR-1 through FR-9 before submission.

## 11. Repository, Secrets & Deployment

*Added because the grading rubric weights README/runnability at 10% and repo hygiene at 5%, both specifically flagged in lecturer feedback.*

- API key stored via `.env` or Streamlit `secrets.toml`; both gitignored. `.env.example` with placeholder values is committed so the structure is visible without exposing a real key.
- README documents: local setup, how to obtain a free Gemini API key from Google AI Studio (no credit card required), and how to run the app end-to-end — sufficient for someone unfamiliar with the project (e.g., a grader) to succeed without the builder's own key or infrastructure.
- `[NOTE FOR PM]` Whether to also ship a canned-response test mode (pre-saved example output, no live API key needed) as a grading fallback is still open — see §12.

## 12. Success Metrics

**Primary**
- **SM-1:** All functional success criteria in §4 (FR-1 through FR-11 consequences) pass verification — via automated test where listed in §10, manual checklist otherwise — before submission. Validates FR-1–FR-11.
- **SM-2:** A person unfamiliar with the project can run the app locally end-to-end using only the README, without the builder's intervention. Validates §11.

**Secondary**
- **SM-3 (personal):** Abdiaziz keeps using the app on his own coursework after the semester ends.

**Counter-metrics (do not optimize)**
- **SM-C1:** Summary length compliance should not be met by padding output with filler to hit a word-count floor — the word-count ranges in FR-5 bound length, they do not set a target to maximize. Counterbalances SM-1.

## 13. Open Questions

1. Exact submission deadline and deliverable format are unconfirmed against the actual IBE160 syllabus — the brief currently marks this **Urgent** (reported as due now/overdue). Needs resolution immediately; may force further scope cuts.
2. Whether Summary and Quiz are generated via one combined Gemini request or two separate calls — affects rate-limit exposure and prompt design. Deferred to architecture.
3. Exact Quiz question format (multiple-choice vs. short-answer) — see `[ASSUMPTION]` in FR-8. Deferred to architecture/UX.
4. Whether to build a canned-response test mode for graders, or rely solely on README instructions for obtaining a free key. Deferred — decide based on remaining time before the deadline.

## 14. Assumptions Index

- §4.3 FR-8 — Quiz questions assumed to be multiple-choice or short-answer with exact-match checking, for unambiguous correct/incorrect scoring.
- §9 — Summary and Quiz assumed to be generated via a single combined Gemini request per submission, to conserve free-tier rate-limit budget.
