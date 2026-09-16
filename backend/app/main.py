from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import auth, engagements, assertions, documents, review, audit, export, risk, impact

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Audit Evidence Graph + Tie-Out Workbench (Candidate Demo)",
    description="SYNTHETIC DEMO — fixture data only. Not a live Modus integration.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(engagements.router)
app.include_router(assertions.router)
app.include_router(documents.router)
app.include_router(review.router)
app.include_router(audit.router)
app.include_router(export.router)
app.include_router(risk.router)
app.include_router(impact.router)


@app.get("/health")
def health():
    return {"status": "ok", "note": "synthetic demo backend"}
