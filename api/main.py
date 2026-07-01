from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import tempfile
import shutil
import uuid
import logging
import traceback
from pathlib import Path

from api.upload_handler import process_uploaded_kit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/classify")
async def classify_uploaded_kit(file: UploadFile):
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are supported")

    temp_dir = Path(tempfile.gettempdir()) / "uploads"
    temp_dir.mkdir(exist_ok=True)

    upload_id = str(uuid.uuid4())
    zip_path = temp_dir / f"{upload_id}.zip"
    extract_dir = temp_dir / upload_id

    try:
        with open(zip_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        logger.info("File saved, starting classification...")
        result = process_uploaded_kit(zip_path, extract_dir)
        logger.info("Classification result: %s", result)
        return result

    except Exception as e:
        logger.error("Classification failed:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if zip_path.exists():
            zip_path.unlink()
        if extract_dir.exists():
            shutil.rmtree(extract_dir)

@app.get("/")
def root():
    return {"message": "Phishing Kit Classifier API"}
