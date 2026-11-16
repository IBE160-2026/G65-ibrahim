---
lens: version-currency (round 2)
target: ARCHITECTURE-SPINE.md (architecture-G65-ibrahim-2026-11-16), updated 2026-11-16
reviewed: 2026-11-16
method: PyPI JSON API (latest versions re-checked today); a throwaway uv venv (CPython 3.13.15) outside the repo with the six pins installed; live probes against the SDK (unroutable host, refused port, real endpoint with a dummy key); pypdf fuzzing (about 4,250 truncated or byte-flipped PDFs); Streamlit `AppTest`; reading installed source (`google/genai/_api_client.py`, `types.py`, `streamlit/runtime/secrets.py`); a Linux (manylinux_2_28, py3.13, binary-only) dry-run install of the frozen set
---

# Review: version currency and reality check (round 2)

**Verdict:** All the new API claims hold up when probed: the names, the fields, the units and the exception types. The error *mapping* built on them has three gaps. A wrong API key comes back as HTTP 400, so it shows up as `MaterialRejected`. Some malformed PDFs raise non-pypdf exceptions. Owner-password-only PDFs are rejected even though their text can be read.

## Findings

### VC2-1: An invalid API key is HTTP 400 and maps to `MaterialRejected` (high)
- **Location:** AD-5 table (`MaterialRejected`: `errors.APIError` with code 400).
- **Claimed:** Code 400 means the material was rejected (for example, input too large).
- **Found:** A live call to `generativelanguage.googleapis.com` with `api_key="x"` raised `google.genai.errors.ClientError`, `code=400`, `status='INVALID_ARGUMENT'`, `message='API key not valid. Please pass a valid API key.'`, `details[...].reason='API_KEY_INVALID'`. A grader with a mistyped key, or a revoked or expired key in Cloud Secrets, would be told their *material* was rejected. That message points them the wrong way. This is the most likely live failure for a grader who clones the repo.
- **Fix:** In AD-5, check the key case first: `code == 400` and (`'API_KEY_INVALID'` in `str(e.details)` or `'API key' in e.message`) → a new `InvalidApiKey` (or reuse the `MissingApiKey` message, "check your key"). Only the remaining 400s → `MaterialRejected`. Also consider `403 PERMISSION_DENIED` → the key message. Add a pytest case that builds `errors.ClientError(400, {...API_KEY_INVALID...})`.

### VC2-2: Other `httpx2` transport errors are not covered (medium)
- **Location:** AD-5 (`GeminiUnavailable`: `httpx2.TimeoutException`, `httpx2.ConnectError`).
- **Claimed:** These two plus other `APIError`s cover network failure.
- **Found:** Both classes exist in httpx2 2.16.2, and the SDK raises them raw, not wrapped in `APIError`. Probes: an unroutable host with `timeout=500` gave `httpx2.ConnectTimeout` (a `TimeoutException`) after 0.62 s, and a refused port gave `httpx2.ConnectError`. Neither is an `errors.APIError`. They are siblings under `httpx2.TransportError`, which also includes `ReadError`, `WriteError`, `RemoteProtocolError` (server drops the connection mid-reply) and `ProxyError`. None of those is caught, so they would reach the user raw, which AD-5 forbids.
- **Fix:** Catch `httpx2.TransportError` (it covers both named types). Tests can still raise `httpx2.ConnectTimeout`/`ConnectError`.

### VC2-3: Malformed PDFs can raise non-`PyPdfError` exceptions (medium)
- **Location:** AD-5/AD-6 (`UnreadablePdf`: "any `pypdf.errors.PyPdfError`").
- **Claimed:** `PyPdfError` is the base of every read error.
- **Found:** It is the base of pypdf's own errors. Fuzzing 4,250 corrupted variants of a valid text PDF through `PdfReader` → `is_encrypted` → `extract_text()` on every page gave 1,830 `PyPdfError` subclasses (`PdfReadError`, `PdfStreamError`, `EmptyFileError`, `LimitReachedError`). It also leaked **11 `AttributeError`** (`'NoneType' object has no attribute 'get_object'`) and **5 `TypeError`** (`can only concatenate str (not "int") to str`).
- **Fix:** In `ingest.py`, wrap the pypdf block in `except PyPdfError` and then a second `except Exception` → `UnreadablePdf`. Print the original first, as AD-5 already requires. Keep `EmptyFile`/`NotPdf` checks before it.

### VC2-4: "Encrypted PDF → UnreadablePdf" rejects readable PDFs (medium)
- **Location:** AD-5/AD-6 (`UnreadablePdf`: "Encrypted PDF").
- **Found:** A PDF encrypted with an owner password only (empty user password, which is common for print- or copy-restricted lecture slides) has `reader.is_encrypted == True`, yet `pages[0].extract_text()` returns the text (`'Hello Study Buddy'`), because pypdf decrypts with the empty password automatically. A PDF with a real user password also has `is_encrypted == True`, and extraction raises `FileNotDecryptedError` (a `PyPdfError`).
- **Fix:** Don't reject on `is_encrypted` alone. Either try extraction and let `FileNotDecryptedError` → `UnreadablePdf`, or call `reader.decrypt("")` and reject only when it returns `PasswordType.NOT_DECRYPTED`.

### VC2-5: A blocked reply gives `response.text is None`, but `_call_gemini` is typed `-> str` (low)
- **Location:** AD-4 (`_call_gemini(prompt, settings) -> str`), AD-5 `BadModelResponse`.
- **Found:** With `GenerateContentResponse` built in 3.3.0, a prompt blocked through `prompt_feedback.block_reason=SAFETY` gives `.text` **`None`**. A candidate with `finish_reason=SAFETY` and no content gives `None`, and with empty `parts` it also gives `None`. A `MAX_TOKENS` cut-off returns truncated text (`'{"summary":'`), which fails JSON validation. `StudyPack.model_validate_json(None)` and `model_validate_json("")` both raise `pydantic.ValidationError`, so the outcome is still `BadModelResponse`, just by accident.
- **Fix:** Type it as `-> str | None` (or return `response.text or ""`) and check for empty before validating. Tests should cover `None`, `""` and truncated JSON.

### VC2-6: `st.session_state["source_tab"]` holds the tab *label*, not a `Source` value (low)
- **Location:** AD-6 ("`source` is the active tab (`Source.PDF` or `Source.TEXT`); `app.py` passes the raw widget values"), AD-7 widget key `source_tab`.
- **Found:** With `AppTest` on 1.67.0, `st.tabs(["PDF","Text"], key="source_tab", on_change="rerun")` gives `session_state["source_tab"] == 'PDF'`, the display label. Nothing in the spine says how the label maps to `Source`. If the UX labels change, or are localized, a direct `Source(label)` breaks.
- **Fix:** Add a `SOURCE_TAB_LABELS: dict[Source, str]` in `models.py` (next to the other label tables). `app.py` passes those labels to `st.tabs` and maps the session value back.

### VC2-7: Secrets values are not always `str` (low)
- **Location:** AD-9 (`load_settings(secrets: Mapping[str, str])`, "`MOCK_MODE` is `true` or `1`, case-insensitive").
- **Found:** `dict(st.secrets)` returns parsed TOML values. `MOCK_MODE = true` in `secrets.toml` (natural TOML) becomes Python `bool`, so `.lower()` raises `AttributeError`. A nested table becomes a dict-like `AttrDict`.
- **Fix:** Type it as `Mapping[str, object]` and normalise with `str(value).strip().lower() in {"true", "1"}`.

### VC2-8: The freeze step needs a clean venv and the right command (low)
- **Location:** Stack ("frozen into `requirements.txt` with `pip freeze`").
- **Found:** Freezing the pinned set on Windows gives 58 packages. Of those, `colorama` (through pytest, `sys_platform=="win32"`) and `tzdata` (through pandas, win32/emscripten) are Windows-only by marker. Both are pure-Python wheels, and a dry-run install of the whole frozen file for `x86_64-manylinux_2_28` / py3.13 / `--only-binary :all:` resolved all 58. **So nothing in this set breaks a Linux install.** No `pywin32` or similar appears. Three risks remain. Freezing a global or non-clean environment would pull in `pywin32`/`pywin32-ctypes` and break Cloud. A uv-created venv has no `pip`, so the command is `uv pip freeze`. The dev-only `pytest`, `pluggy`, `iniconfig` and `colorama` end up in the Cloud install. That is harmless, but they are not runtime dependencies.
- **Fix:** Say "freeze from the project's clean venv (`uv pip freeze` or `pip freeze`), and drop the dev packages or keep them in `requirements-dev.txt`". `httpx2` is imported directly by `llm.py` but is only a transitive pin of google-genai (`httpx2<3.0.0,>=2.0.0`). The freeze pins it, which is the right outcome. List it among the direct deps for clarity.

### VC2-9: `%PDF` must be at byte 0 under a strict NotPdf check (low)
- **Location:** AD-5/AD-6 ("bytes don't start with `%PDF`").
- **Found:** The PDF spec and readers, pypdf included, accept a header within the first 1,024 bytes. Some generators and mail gateways prepend a BOM or whitespace. A strict `startswith(b"%PDF")` rejects these valid files as `NotPdf`. This one is not probed against real samples, so it is a known edge only.
- **Fix:** Use `b"%PDF" in pdf_bytes[:1024]`.

## Verified OK

- **PyPI, re-checked 2026-11-16:** google-genai 3.3.0, streamlit 1.67.0, pypdf 7.1.0, pydantic 2.14.3 and httpx2 2.16.2 are still the latest. All six pins install together on CPython 3.13.15.
- **google-genai 3.3.0 → httpx2:** `requires_dist` has `httpx2<3.0.0,>=2.0.0`, and `httpx` is now only an optional extra (`httpx` is not installed). `_HTTPX_TRANSIENT_EXC` in `_api_client.py` lists `httpx2.TimeoutException` and `httpx2.ConnectError`.
- **`types.HttpOptions(timeout=60_000)`:** the field is `timeout: int | None`, described as "Timeout for the request in milliseconds". `get_timeout_in_seconds` divides by 1000. A probe with `timeout=500` timed out at 0.62 s, which confirms the unit is ms. `genai.Client(*, api_key=..., http_options=HttpOptions | dict)` matches the signature.
- **Timeouts are not wrapped in `errors.APIError`:** the raw `httpx2.ConnectTimeout`/`ConnectError` propagate (probed). `errors.APIError` subclasses `Exception` directly, not anything in httpx2.
- **`errors.APIError.code`:** 400 gives `ClientError.code == 400` (live), and 429 gives `ClientError.code == 429`, `status 'RESOURCE_EXHAUSTED'` (constructed). `.status`, `.message` and `.details` are also available.
- **`StudyPack.model_validate_json`:** this is the correct pydantic 2.14.3 API. Invalid, empty or `None` input raises `pydantic.ValidationError`.
- **pypdf 7.1.0:** `PdfReader(...).is_encrypted` exists. `pypdf.errors.PyPdfError` is the base of `PdfReadError`, `PdfStreamError`, `EmptyFileError`, `FileNotDecryptedError` and `LimitReachedError`, with the caveats in VC2-3 and VC2-4.
- **Streamlit 1.67.0 (`AppTest`, no exception):** `st.button(type="primary", width="stretch")` works. `st.radio(options=[0,1,2,3], format_func=..., index=None, key=...)` starts at `None`, and after selection both the return value and `session_state[key]` are the int `2`. `st.tabs(..., key=, on_change="rerun")` works (see VC2-6).
- **`dict(st.secrets)` with no `secrets.toml`:** this raises `StreamlitSecretNotFoundError`, a subclass of `FileNotFoundError`. It does not draw `st.error` (the 1.67 `_parse` only raises). A malformed TOML raises the same type. `try: dict(st.secrets) except Exception: {}` is enough. When secrets are found, Streamlit also copies top-level string values into `os.environ`, which is harmless here.
- **`string.Template.safe_substitute`:** `$word_range`, `$language_name` and `$material` are valid identifiers. Substitution happens in one pass, so `$x`/`${word_range}` inside the material are left as they are, and stray `$5` is left alone.
- **SyntaxWarnings:** importing google-genai 3.3.0 on 3.13 still prints the two `SyntaxWarning: invalid escape sequence '\/'` lines (`types.py:18308`, `:18346`), as the spine says.
