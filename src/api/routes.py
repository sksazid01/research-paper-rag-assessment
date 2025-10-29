from fastapi import APIRouter, UploadFile
from services import pdf_processor

router = APIRouter(prefix="/api")

@router.post("/papers/upload")
async def upload_paper(file: UploadFile):
    file_path = f"temp/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    text = pdf_processor.process_pdf(file_path)
    return {"message": f"{file.filename} processed successfully"}