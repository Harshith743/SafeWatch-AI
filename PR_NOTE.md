This PR adds a small shim and CI checks so Vercel can import the FastAPI ASGI
application as `app:app`.

What changed
- `app.py` (repo root) — re-exports the FastAPI `app` from `api.py` and adds
  a `/__health` route used by CI and deployments.
- `requirements.txt` — added `httpx` to support `TestClient` in CI.
- `.github/workflows/ci.yml` and `tools/check_entrypoint.py` — CI validates
  that `app:app` is importable and that `/__health` returns 200, then runs
  the test suite.

How to verify locally

1. Create and activate a virtualenv (recommended):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Run the app and test the health endpoint:

```powershell
python -m uvicorn app:app --reload --port 8000
Invoke-RestMethod http://127.0.0.1:8000/__health
```

3. Run the CI check script locally (uses TestClient):

```powershell
python tools/check_entrypoint.py
```

Notes
- This is a minimal, non-invasive shim to satisfy Vercel's import requirement.
- If you prefer a different module path for the entrypoint, update `app.py`.
