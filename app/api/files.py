from fastapi import APIRouter, UploadFile, HTTPException, File
from fastapi.responses import Response
import uuid
import time
from typing import Dict, Tuple

router = APIRouter(prefix="/files", tags=["Files"])

# In-memory storage: {id: (bytes, content_type, expires_at)}
STORE: Dict[str, Tuple[bytes, str, float]] = {}

TTL_SECONDS = 15 * 60


@router.post("")
async def upload_file(file: UploadFile = File(...)):
    fid = uuid.uuid4().hex[:12]
    file_bytes = await file.read()
    content_type = file.content_type or "image/png"
    expires_at = time.time() + TTL_SECONDS
    
    STORE[fid] = (file_bytes, content_type, expires_at)
    
    _cleanup_expired()
    
    return {
        "id": fid,
        "url": f"/files/{fid}",
        "expires_in_seconds": TTL_SECONDS
    }


@router.get("/{fid}")
async def serve_file(fid: str):
    item = STORE.get(fid)
    if not item:
        raise HTTPException(status_code=404, detail="File not found")
    
    data, content_type, expires_at = item
    
    if time.time() > expires_at:
        STORE.pop(fid, None)
        raise HTTPException(status_code=410, detail="File expired")
    
    return Response(
        content=data,
        media_type=content_type,
        headers={"Cache-Control": "no-store"}
    )


def _cleanup_expired():
    now = time.time()
    expired = [fid for fid, (_, _, exp) in STORE.items() if now > exp]
    for fid in expired:
        STORE.pop(fid, None)

