---
lens: version-currency
target: ARCHITECTURE-SPINE.md (architecture-G65-ibrahim-2026-11-16)
reviewed: 2026-11-16
method: PyPI JSON API; aistudio.google.com docs (models, pricing, api-versions); docs.streamlit.io; python-genai CHANGELOG; installed the pinned set into a throwaway Python 3.13.15 venv outside the repo and inspected signatures and source
---

# Review — version currency and reality check

**Verdict:** All pinned versions are real, current and install together on Python 3.13. The model is stable and on the free tier. The weak spots are the error and timeout behaviour of google-genai 3.x, which the spine states from older SDK assumptions without checking them.

## Findings

### VC-1 — No request timeout configured; SDK default is "wait forever" (high)
- **Location:** AD-5 (`GeminiUnavailable (timeout, …)`), AD-4, Stack; epics Story covering timeout/network.
- **Claimed:** A timeout produces `GeminiUnavailable` and the UX timeout message.
- **Found:** In google-genai 3.3.0, `HttpOptions.timeout` defaults to `None` and the client passes `timeout=None` to the HTTP client, so a request without a timeout never times out. The spinner would spin until the platform kills the request. `HttpOptions.timeout` is in **milliseconds** (`types.py`: "Timeout for the request in milliseconds"; `_api_client.get_timeout_in_seconds` divides by 1000). Source: installed `google/genai/types.py`, `_api_client.py` (3.3.0); https://googleapis.github.io/python-genai/ (does not document the default).
- **Fix:** Add to AD-4: `genai.Client(api_key=..., http_options=types.HttpOptions(timeout=<ms>))`, with the value (for example 60_000) kept in `config.py`/`Settings`. State the unit.

### VC-2 — Timeouts and network errors are not `errors.APIError` in v3 (high)
- **Location:** AD-5; memlog "translating … google.genai errors.APIError".
- **Claimed:** `GeminiUnavailable` covers "timeout, network, other `errors.APIError`", which reads as if catching `APIError` is enough.
- **Found:** google-genai 3.0.0 (2026-11-06) switched the default transport to **`httpx2`**, and `httpx` is no longer installed. Timeouts and connection failures come up as `httpx2.TimeoutException` / `httpx2.ConnectError` (see `_HTTPX_TRANSIENT_EXC` in `_api_client.py`), not as `errors.APIError`. The CHANGELOG warns: "Timeout and transport exception types must match the active client, so `except` clauses catching `httpx` exceptions may need updating." A builder who follows the training-data habit of `except httpx.TimeoutException` gets an `ImportError`, because `httpx` is no longer a dependency. Source: https://raw.githubusercontent.com/googleapis/python-genai/main/CHANGELOG.md (3.0.0 BREAKING CHANGES); installed `requires_dist` shows `httpx2<3.0.0,>=2.0.0`.
- **Fix:** In AD-5, list the library exceptions explicitly: `errors.APIError` with `.code == 429` → `RateLimited`; any other `errors.APIError` (`ClientError`/`ServerError`), `httpx2.TimeoutException`, `httpx2.TransportError` → `GeminiUnavailable`. Add `httpx2` to the "May import" column for `llm.py`. AD-11 tests should raise these same types.

### VC-3 — google-genai v3 default API version is now `v1` (medium)
- **Location:** AD-2, Stack (google-genai 3.3.0).
- **Claimed:** Nothing; the spine doesn't mention the API version.
- **Found:** Since 3.0.0, Developer-API clients default to `v1` instead of `v1beta`. Google's API-versions page says "All models are supported in both v1 and v1beta" and lists Structured Output as supported on v1, so the AD-2 pattern should still work. However, nearly all online examples and the memlog's SDK guidance assume v1beta, and this was never checked end to end. Sources: CHANGELOG 3.0.0; https://aistudio.google.com/docs/api-versions.
- **Fix:** Add a short note under Stack, "google-genai ≥3 uses API v1; structured output supported there", plus a smoke test (one real call with `response_schema=StudyPack`) in the first `llm.py` story. If it fails, set `HttpOptions(api_version="v1beta")`.

### VC-4 — `response_schema=<Pydantic>` is still supported, but Google's own docs now lead with other APIs (low)
- **Location:** AD-2, AD-8.
- **Claimed:** `GenerateContentConfig(response_mime_type="application/json", response_schema=StudyPack)`.
- **Found:** This works in 3.3.0: the field exists and construction with a Pydantic class succeeds in the venv, and the python-genai README still shows `response_schema=CountryInfo`. The SDK also has `response_json_schema`. The AI Studio structured-output guide now shows only `client.interactions.create(response_format=…)` with `Model.model_json_schema()`, so the generate_content path is no longer the one Google documents first. It is not deprecated. Sources: https://googleapis.github.io/python-genai/; https://aistudio.google.com/docs/structured-output.
- **Fix:** No change to the decision. Add a pointer to the python-genai README section as the reference, so builders don't copy the Interactions example.

### VC-5 — `use_container_width` is deprecated in Streamlit 1.67 (low)
- **Location:** UX DESIGN.md line 43 (`st.button(type="primary", use_container_width=True)`). Downstream stories inherit it.
- **Found:** It is deprecated in the 1.67.0 docstrings: "will be removed in a future release. For `use_container_width=True`, use `width="stretch"`". It still works and shows no runtime warning in `button`. Source: installed `streamlit/elements/widgets/button.py`; https://docs.streamlit.io/develop/api-reference/widgets/st.button.
- **Fix:** Use `st.button(..., type="primary", width="stretch")` (same for `form_submit_button`). Note this in the epics/UX handoff.

### VC-6 — Only direct dependencies are pinned; Community Cloud resolves the transitive set fresh (medium)
- **Location:** Stack ("Dependencies are pinned with `==` in requirements.txt"), deployment seed.
- **Found:** The six direct pins resolve together (venv install on 3.13 succeeded: starlette, uvicorn, httpx2 2.16.2, websockets 17.4 and others pulled in). Streamlit 1.6x now runs on Starlette/uvicorn with open ranges (`starlette<2,>=0.46.0`, `uvicorn<1,>=0.30.0`). In Aug 2026 a new Starlette release broke Community Cloud deploys (`GZipResponder … thread_minimum_size`) until Streamlit shipped a patch. The same kind of break could hit a future redeploy of this app during grading. Sources: https://discuss.streamlit.io/t/community-cloud-installs-incompatible-streamlit-starlette-versions-causing-gzipresponder-typeerror-on-startup/122128 ; https://discuss.streamlit.io/t/all-my-streamlit-community-cloud-apps-fail-to-deploy-after-rebuild-python-3-14-requirements-installation-error/122130
- **Fix:** Before submission, freeze the working environment's full set (`pip freeze`/`uv pip compile` → `requirements.txt`) so Cloud installs the exact versions tested locally. Or at least pin `starlette` and `uvicorn`.

### VC-7 — Community Cloud Python default and selection: docs and reality disagree (low)
- **Location:** Deployment seed; memlog "(default 3.12)".
- **Found:** The docs say only "security-maintained versions" and choose-in-Advanced-settings; the deploy page still says the default is 3.12. 2026 forum reports say new apps default to 3.13/3.14, and one reports builds on 3.14 despite selecting 3.12. Python can't be changed after deploy without deleting the app. All pins publish 3.13 classifiers, and 3.14 too, so this is low risk. Sources: https://docs.streamlit.io/deploy/streamlit-community-cloud/status ; https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app/upgrade-python
- **Fix:** In the deploy story, add "confirm Python 3.13 in the Cloud build log". Drop the "default 3.12" claim from the memlog.

### VC-8 — Fresh releases pinned (low)
- **Location:** Stack.
- **Found:** google-genai 3.3.0 was uploaded 2026-11-12 (4 days ago, on a 10-day-old major version). pypdf 7.1.0 was uploaded 2026-11-13 (3 days ago). streamlit 1.67.0 and pydantic 2.14.3 were uploaded 2026-11-05. All are the latest on PyPI and none is yanked. On Python 3.13, importing google-genai 3.3.0 emits two `SyntaxWarning: invalid escape sequence '\/'` lines from `types.py`. These are harmless but show up in the console and the Cloud log. Source: https://pypi.org/pypi/google-genai/3.3.0/json, https://pypi.org/pypi/pypdf/7.1.0/json; venv import.
- **Fix:** Acceptable for a course project. Mention the warnings in the README so graders don't read them as app errors. If problems appear, fall back to the previous minor version.

### VC-9 — pypdf error mapping is incomplete for encrypted PDFs (low)
- **Location:** AD-5, AD-6.
- **Found:** Probed in 7.1.0: 0-byte stream → `EmptyFileError`; non-PDF bytes and truncated PDFs → `PdfStreamError`. Both subclass `PdfReadError` ⊂ `PyPdfError`. A password-protected PDF opens, but `pages[0].extract_text()` raises `FileNotDecryptedError` (a `PdfReadError`). A blank or scanned page returns `''`. AD-5 has no type for encrypted files. If `ingest.py` catches only specific errors, the encrypted case leaks a raw pypdf exception, which AD-5 forbids. Source: venv probe; https://pypdf.readthedocs.io/en/stable/user/encryption-decryption.html
- **Fix:** In AD-6, state "catch `pypdf.errors.PyPdfError` → `NotPdf` (or a new `EncryptedPdf`)". Check `reader.is_encrypted` before extracting text.

## Verified OK

- PyPI (2026-11-16): streamlit 1.67.0, google-genai 3.3.0, pypdf 7.1.0, pydantic 2.14.3, python-dotenv 1.2.4 and pytest 9.2.0 are each the latest release. All list Python 3.13 classifiers and `requires_python` ≤3.11. None is yanked.
- Pin compatibility: google-genai needs `pydantic>=2.12.5,<3`, which 2.14.3 satisfies. pydantic needs `typing-extensions>=4.16.0`, compatible with streamlit (`<5`) and genai (`<5`). All six installed together cleanly under uv on CPython 3.13.15. pydantic-core 2.50.4 ships cp313 wheels.
- `genai.Client(api_key=...)` and `client.models.generate_content(model=, contents=, config=)` are unchanged in 3.3.0. `errors.APIError.code` exists, with `ClientError`/`ServerError` subclasses. Default `retry_options=None` means no retries ("stop_after_attempt(1)"), which matches AD-2's no-retry rule without extra config.
- `gemini-3.5-flash-lite`: listed as **Stable**, no deprecation date, free of charge on the Free Tier, and free-tier content "used to improve our products" (README disclosure is correct). `gemini-2.5-flash` will be rerouted to it on 2026-12-01. Sources: https://aistudio.google.com/docs/models, https://aistudio.google.com/docs/pricing
- Streamlit 1.67.0: `st.secrets` (`Secrets`) is a `collections.abc.Mapping`, so the AD-9 pass-through works. `st.tabs(..., key=, on_change="rerun")` exists, and `st.session_state[key]` holds the active tab's **label** (`.open` is also available). `st.toggle`, `st.form`, `st.spinner` and `st.radio(index=None, horizontal=True, captions=...)` are all present with these parameters. `st.button(type="primary")` is fine. Source: https://docs.streamlit.io/develop/api-reference/layout/st.tabs and installed signatures.
- pypdf 7.1.0: `PdfReader(stream)` and `.pages[i].extract_text()` are unchanged.
