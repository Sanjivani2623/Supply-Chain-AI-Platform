from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.document import Document
from app.services.rag.chunking import chunk_text
from app.services.rag.embeddings import get_embedding_provider

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_TYPES = {"pdf", "docx", "txt", "csv"}


@router.get("")
def list_documents(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Document).order_by(Document.created_at.desc()).all()


@router.post("/upload")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(get_current_user)):
    ext = (file.filename.split(".")[-1] or "").lower()
    if ext not in ALLOWED_TYPES:
        return {"error": f"Unsupported file type .{ext}. Allowed: {sorted(ALLOWED_TYPES)}"}
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        return {"error": "File exceeds 10MB limit"}

    text = content.decode("utf-8", errors="ignore") if ext in ("txt", "csv") else ""
    # NOTE: pdf/docx extraction would use the pdf/docx skills' libraries in a full deployment.

    doc = Document(name=file.filename, type=ext, source="upload", uploaded_by=user.id, status="PENDING")
    db.add(doc)
    db.commit()
    db.refresh(doc)

    if text:
        chunks = chunk_text(text)
        get_embedding_provider().embed_document(db, doc, chunks)

    return {"id": doc.id, "name": doc.name, "status": doc.status}
