"""Uploads the infographic to Cloudinary so Instagram/Facebook can fetch it from a public URL."""

from pathlib import Path

import cloudinary
import cloudinary.uploader
import requests

from ..config import settings

FOLDER = "hassan-daily"


def _configure() -> None:
    if not (settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET):
        raise ValueError("Cloudinary is not configured (CLOUDINARY_CLOUD_NAME / _API_KEY / _API_SECRET)")
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )


def upload_image(png: Path, public_id: str) -> str:
    """Uploads the PNG (overwriting the same id on a re-run) and returns its public HTTPS URL."""
    _configure()
    result = cloudinary.uploader.upload(
        str(png), folder=FOLDER, public_id=public_id, overwrite=True, resource_type="image",
    )
    url = result["secure_url"]
    # Confirm anyone can download it, exactly as Meta's servers will
    r = requests.get(url, timeout=30)
    if r.status_code != 200 or not r.headers.get("content-type", "").startswith("image/"):
        raise RuntimeError(f"Uploaded image isn't publicly reachable ({r.status_code}): {url}")
    return url


def delete_image(public_id: str) -> None:
    _configure()
    cloudinary.uploader.destroy(f"{FOLDER}/{public_id}", invalidate=True)
