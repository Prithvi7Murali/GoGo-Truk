from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from app.utils.cloudinary_client import get_signed_url

router = APIRouter(prefix="/api/docs", tags=["Document Proxy"])


@router.get("/view")
def view_document(url: str):
    """
    Proxy endpoint for Cloudinary documents.
    Frontend calls /api/docs/view?url=<cloudinary_url> instead of the raw CDN URL.
    Returns a 302 redirect to a short-lived signed Cloudinary download URL.
    """
    if not url:
        raise HTTPException(status_code=400, detail="url query parameter is required")
    try:
        signed_url = get_signed_url(url)
        return RedirectResponse(url=signed_url, status_code=302)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not generate signed URL: {e}")
