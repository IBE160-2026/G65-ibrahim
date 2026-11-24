# Deferred Work

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-set-up-the-project-and-open-the-app.md`
  summary: Add pytest fixture tests that open each test_data PDF with `PdfReader(strict=True)` and assert that the English text is non-empty, the Norwegian text contains æ, ø and å, and the scanned PDF extracts as whitespace only.
  evidence: Story 1.1 has only an existence/size smoke test (its frozen intent allows one test). A broken encoding or xref would pass until Story 1.2's ingest tests run.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-set-up-the-project-and-open-the-app.md`
  summary: Add a test that regenerates the fixtures with `make_test_data.py` in memory and byte-compares them with the committed files, so the generator and the fixtures cannot drift apart.
  evidence: Nothing checks the match today. An edited slide list without a regenerate passes `pytest` (Story 1.1 code review B3/V2/E5).
- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-set-up-the-project-and-open-the-app.md`
  summary: Add a `streamlit.testing.v1.AppTest` smoke test for `app.py` (title, caption, no exception) when a story first extends `app.py`.
  evidence: No test imports `app.py`, so a broken landing page would still pass `pytest` (Story 1.1 code review V3).
