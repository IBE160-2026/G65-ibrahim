---
name: AI Study Buddy
description: Single-user Streamlit web app that turns a lecture PDF or pasted text into a summary and a self-test quiz. Streamlit's built-in theme is the visual system; this DESIGN.md records the inherited values and the few product-specific rules on top.
status: final
updated: 2026-11-15
sources:
  - _bmad-output/planning-artifacts/briefs/brief-G65-ibrahim-2026-09-11/brief.md
  - _bmad-output/planning-artifacts/prds/prd-G65-ibrahim-2026-10-18/prd.md
colors:
  # [ASSUMPTION] Streamlit default theme, inherited unchanged. Values listed so
  # they can be referenced; they are NOT overrides. No .streamlit/config.toml
  # [theme] section is needed.
  primary: '#FF4B4B'
  background: '#FFFFFF'
  surface: '#F0F2F6'
  text: '#31333F'
  background-dark: '#0E1117'
  surface-dark: '#262730'
  text-dark: '#FAFAFA'
  # Result semantics use Streamlit's own st.success / st.error / st.warning /
  # st.info element colours. Not restated here.
typography:
  # Inherited from Streamlit (Source Sans, sans-serif). Roles map to Streamlit calls.
  title:
    note: 'st.title — app name only, once per page'
  section:
    note: 'st.subheader — "Your material", "Results"'
  summary-heading:
    note: 'Markdown ### inside the summary, from the structured model output'
  body:
    note: 'st.markdown default body size'
  caption:
    note: 'st.caption — helper text, privacy note, word count'
rounded:
  # Inherited from Streamlit widgets. No overrides.
  DEFAULT: 'Streamlit default'
spacing:
  # Inherited from Streamlit's vertical block gap. Use st.divider between
  # the input block and the results block; no custom CSS spacing.
  section-break: 'st.divider'
components:
  generate-button:
    note: 'st.button(type="primary", use_container_width=True)'
    background: '{colors.primary}'
  input-tabs:
    note: 'st.tabs(["Upload PDF", "Paste text"])'
  results-tabs:
    note: 'st.tabs(["Summary", "Quiz"])'
  quiz-result-correct:
    note: 'st.success with ✅ icon and text "Correct"'
  quiz-result-incorrect:
    note: 'st.error with ❌ icon and text "Incorrect — correct answer: …"'
  error-message:
    note: 'st.error, one per problem, placed directly above the Generate button'
  demo-toggle:
    note: 'st.toggle under the options row, off by default'
  demo-banner:
    note: 'st.warning at the top of the results block while Demo mode output is shown'
---

## Brand & Style

AI Study Buddy is a study tool built by one beginner Python developer for a course project. Its look should be plain, calm and readable. The value is the summary and the quiz, not the interface around them. The visual posture is **"stock Streamlit, used with discipline"**: no custom CSS, no injected HTML, no theme overrides. Graders and future users should see a clean, familiar Streamlit app, and the builder should never have to debug styling. `[ASSUMPTION]`

The only product-specific visual work is **hierarchy**: one title, one input block, one results block, and a summary that reads like a well-structured study note.

## Colors

The palette is Streamlit's default theme, inherited as-is. Streamlit follows the viewer's system light/dark setting, so the `-dark` tokens apply automatically.

- **Primary (`{colors.primary}`)** appears only on the Generate button and on Streamlit's own focus and selection states. Never used for text or decoration.
- **Surface (`{colors.surface}`)** is Streamlit's secondary background (tabs, inputs). Not used for custom panels.
- **Result semantics** come from `st.success` (correct answer), `st.error` (incorrect answer, blocking problem), `st.warning` (stale results, rate limit) and `st.info` (neutral hints). Colour is never the only signal: every result also has an icon and words. See EXPERIENCE.md Accessibility Floor.

Avoid: a custom theme in `config.toml`, coloured text via HTML, emoji used as decoration outside quiz results.

## Typography

Streamlit's default sans-serif ramp, inherited.

- `{typography.title}`: "AI Study Buddy", used once.
- `{typography.section}`: block headings ("Your material", "Results").
- `{typography.summary-heading}`: topic headings inside the summary, produced from the structured response (e.g. one `###` per main topic, bullet points underneath). This is what makes the summary scannable.
- `{typography.caption}`: helper text, the privacy note, and the word count under the summary ("312 words · medium · English").

## Layout & Spacing

Streamlit `layout="centered"` (one readable column, no sidebar). `[ASSUMPTION]` Vertical order, top to bottom:

1. Title and a one-line caption explaining what the app does
2. **Your material**: input tabs, then the privacy caption
3. **Options**: length and language as two horizontal radios side by side (`st.columns(2)`), with the Demo mode toggle below them
4. Error area (only when there is an error)
5. Generate button (full column width)
6. `{spacing.section-break}`
7. **Results**: results tabs (only after a successful generation)

Spacing is Streamlit's default block gap. No custom margins.

## Elevation & Depth

None. Streamlit's flat surfaces are the rule. No cards, shadows or containers with borders other than the `st.form` wrapping the quiz.

## Shapes

Inherited Streamlit widget corners. No overrides.

## Components

All components are standard Streamlit widgets:

- **Generate button** (`{components.generate-button}`): the only primary button on the page. Disabled while generating.
- **Input tabs** (`{components.input-tabs}`): "Upload PDF" holds `st.file_uploader(type=["pdf"])`; "Paste text" holds `st.text_area`.
- **Length / language selectors**: `st.radio(horizontal=True)`. Length options: Short · Medium · Long, each with a caption giving the word range. Language options: English · Norsk.
- **Results tabs** (`{components.results-tabs}`): Summary tab shows the rendered markdown summary and a word-count caption. Quiz tab shows the quiz form.
- **Quiz question**: `st.radio` with 4 options and no pre-selected answer (`index=None`), numbered "1.", "2." and so on.
- **Quiz result rows**: `{components.quiz-result-correct}` / `{components.quiz-result-incorrect}`, one per question, under that question. The score line ("You got 3 of 5 right") is an `st.info` above the questions.
- **Error message** (`{components.error-message}`): `st.error` with a short cause and a next step.
- **Demo mode** (`{components.demo-toggle}`, `{components.demo-banner}`): the toggle is a plain switch, never primary-styled. The banner stays visible on both result tabs whenever the shown output is the saved example, so demo output can never be mistaken for a real summary.

## Do's and Don'ts

| Do | Don't |
|---|---|
| Use Streamlit widgets and theme as shipped | Inject CSS or HTML via `unsafe_allow_html` |
| Keep one primary button (Generate) on the page | Add primary styling to the quiz submit or Try again buttons |
| Pair every success/error colour with an icon and words | Mark answers correct/incorrect by colour alone |
| Render the summary as real markdown headings and bullets | Show the raw model response or JSON |
| Keep the layout in one centered column | Put inputs in the sidebar (it collapses and hides them) |
