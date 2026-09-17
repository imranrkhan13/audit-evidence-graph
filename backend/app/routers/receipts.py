import hashlib
import hmac
from io import BytesIO
import os
import threading
import time

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader

from app.deps import get_current_user
from app.extraction.receipts import ExtractionError, extract_receipt

router = APIRouter(prefix="/receipts", tags=["receipt uploads"])
MAX_BYTES = 3 * 1024 * 1024
MAX_PAGES = 3
Image.MAX_IMAGE_PIXELS = 20_000_000
_attempts: dict[str, list[float]] = {}
_lock = threading.Lock()


def reader_enabled():
    return os.getenv("INTERFAZE_ENABLED") == "true" and bool(os.getenv("INTERFAZE_API_KEY"))


@router.get("/status")
def status(response: Response, _user=Depends(get_current_user)):
    response.headers["Cache-Control"] = "no-store"
    return {"enabled": reader_enabled(), "max_bytes": MAX_BYTES, "max_pages": MAX_PAGES}


def limit_requests(request: Request):
    # Best-effort per-instance protection, not a billing cap. Provider-side billing
    # must remain disabled or capped because serverless instances do not share RAM.
    ip = request.headers.get("x-vercel-forwarded-for") if os.getenv("VERCEL") else None
    ip = ip or (request.client.host if request.client else "unknown")
    digest = hmac.new(os.environ.get("SECRET_KEY", "local-demo").encode(), ip.encode(), hashlib.sha256).hexdigest()
    now = time.monotonic()
    with _lock:
        for key in list(_attempts):
            _attempts[key] = [stamp for stamp in _attempts[key] if now - stamp < 3600]
            if not _attempts[key]:
                del _attempts[key]
        recent = _attempts.get(digest, [])
        if len(recent) >= 10 or sum(len(v) for v in _attempts.values()) >= 100:
            raise HTTPException(429, "The receipt reader is busy or your hourly limit was reached. Try again later.")
        _attempts.setdefault(digest, []).append(now)


def validate_file(data: bytes, mime: str):
    if mime == "application/pdf":
        if not data.startswith(b"%PDF-"):
            raise HTTPException(400, "This file is not a readable PDF.")
        try:
            pdf = PdfReader(BytesIO(data))
            if pdf.is_encrypted:
                raise HTTPException(400, "Please upload a PDF without password protection.")
            if not 1 <= len(pdf.pages) <= MAX_PAGES:
                raise HTTPException(400, "Upload one receipt in a PDF with 1–3 pages.")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(400, "This PDF could not be read. Try a photo instead.") from None
    else:
        try:
            with Image.open(BytesIO(data)) as img:
                if Image.MIME.get(img.format) != mime or img.width * img.height > 20_000_000:
                    raise ValueError("unsupported image")
                img.verify()
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
            raise HTTPException(400, "Upload a valid JPG, PNG or WebP image under 20 megapixels.") from None


@router.post("/extract")
async def extract(request: Request, response: Response, _user=Depends(get_current_user)):
    response.headers["Cache-Control"] = "no-store"
    if not reader_enabled():
        raise HTTPException(503, "Receipt extraction is not enabled yet. The site owner needs to confirm the provider credits.")
    if request.headers.get("x-receipt-consent") != "true":
        raise HTTPException(400, "Please confirm you can send this receipt to Interfaze for extraction.")
    mime = request.headers.get("content-type", "").split(";")[0].lower()
    if mime not in {"image/jpeg", "image/png", "image/webp", "application/pdf"}:
        raise HTTPException(415, "Choose a JPG, PNG, WebP or PDF file.")
    data = bytearray()
    async for chunk in request.stream():
        data.extend(chunk)
        if len(data) > MAX_BYTES:
            raise HTTPException(413, "The file is too large. Choose a file under 3 MB.")
    if not data:
        raise HTTPException(400, "The file is empty. Choose another file.")
    raw = bytes(data)
    validate_file(raw, mime)
    limit_requests(request)
    try:
        receipt = await extract_receipt(raw, mime, os.environ["INTERFAZE_API_KEY"])
    except ExtractionError as error:
        raise HTTPException(error.status, str(error)) from None
    return {"receipt": receipt.model_dump(mode="json"), "file_sha256": hashlib.sha256(raw).hexdigest(),
            "provider": "Interfaze", "stored_on_server": False}
