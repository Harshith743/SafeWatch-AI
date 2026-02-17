from importlib import import_module
from fastapi.testclient import TestClient


def main():
    m = import_module("app")
    app = getattr(m, "app", None)
    if app is None:
        raise SystemExit("ERROR: `app` object not found in module `app`.")
    client = TestClient(app)
    r = client.get("/__health")
    if r.status_code != 200:
        raise SystemExit(f"ERROR: health-check returned {r.status_code}: {r.text}")
    print("OK: FastAPI app imported and health-check passed.")


if __name__ == "__main__":
    main()
