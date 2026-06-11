import json
import os
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from models import ApplicationData, BatchVerificationResponse, VerificationResult
from verifier import verify_label

app = FastAPI(title="TTB Alcohol Label Verifier", version="1.0.0")

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def parse_app_data(app_data_json: str) -> ApplicationData:
    data = json.loads(app_data_json)
    return ApplicationData(**data)


@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = STATIC_DIR / "index.html"
    return HTMLResponse(content=html_path.read_text(), status_code=200)


@app.post("/verify", response_model=VerificationResult)
async def verify_single(
    label_image: UploadFile = File(..., description="Label image file"),
    app_data: str = Form(..., description="Application data as JSON string"),
):
    """Verify a single label image against application data."""
    if label_image.content_type not in ALLOWED_TYPES:
        return JSONResponse(
            status_code=400,
            content={"error": f"Unsupported file type: {label_image.content_type}. Use JPEG, PNG, or WebP."},
        )

    image_bytes = await label_image.read()
    application = parse_app_data(app_data)

    result = verify_label(
        image_bytes=image_bytes,
        media_type=label_image.content_type,
        filename=label_image.filename or "label.jpg",
        app_data=application,
    )
    return result


@app.post("/verify/batch", response_model=BatchVerificationResponse)
async def verify_batch(
    label_images: list[UploadFile] = File(..., description="Multiple label image files"),
    app_data_list: str = Form(..., description="List of application data objects as JSON array"),
):
    """
    Verify multiple labels at once.
    app_data_list must be a JSON array with one entry per image, in the same order.
    """
    app_data_entries = json.loads(app_data_list)

    if len(label_images) != len(app_data_entries):
        return JSONResponse(
            status_code=400,
            content={
                "error": (
                    f"Mismatch: {len(label_images)} images but "
                    f"{len(app_data_entries)} application data entries."
                )
            },
        )

    results: list[VerificationResult] = []

    for img_file, app_entry in zip(label_images, app_data_entries):
        if img_file.content_type not in ALLOWED_TYPES:
            results.append(
                VerificationResult(
                    filename=img_file.filename or "unknown",
                    overall_passed=False,
                    fields=[],
                    government_warning_present=False,
                    government_warning_exact=False,
                    error=f"Unsupported file type: {img_file.content_type}",
                )
            )
            continue

        image_bytes = await img_file.read()
        application = ApplicationData(**app_entry)

        result = verify_label(
            image_bytes=image_bytes,
            media_type=img_file.content_type,
            filename=img_file.filename or "label.jpg",
            app_data=application,
        )
        results.append(result)

    passed = sum(1 for r in results if r.overall_passed)

    return BatchVerificationResponse(
        results=results,
        total=len(results),
        passed=passed,
        failed=len(results) - passed,
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
