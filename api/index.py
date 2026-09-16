"""Vercel entrypoint for the disposable, synthetic-data demo only."""
import fcntl
import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

if not os.environ.get("SECRET_KEY"):
    raise RuntimeError("Set SECRET_KEY in the hosting environment before deploying.")

# This entrypoint deliberately never connects to the local or a real database.
demo_dir = Path(tempfile.gettempdir()) / "audit-evidence-hosted-v1"
demo_dir.mkdir(exist_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{demo_dir / 'demo.db'}"

# Multiple processes sharing one temporary directory must not seed over each other.
with (demo_dir / "seed.lock").open("w") as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    from app.main import app as backend_app
    from app.database import SessionLocal
    from app.models import Engagement, stable_demo_ids
    from app.seed import run_seed

    with SessionLocal() as db:
        initialized = db.query(Engagement).first() is not None
    if not initialized:
        with stable_demo_ids():
            run_seed()

from fastapi import FastAPI

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/api", backend_app)
