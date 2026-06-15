import base64
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List
import datetime

from ..database import get_db
from .. import models, schemas, auth

router = APIRouter(
    prefix="/mcp/academics",
    tags=["MCP Academics"]
)

# Minimal 1-page valid PDF in base64: "Hello World"
MINIMAL_PDF_BASE64 = (
    "JVBERi0xLjQKJdOlhq1sdwogMSAwIG9iagogIDw8IC9UeXBlIC9DYXRhbG9nCiAgICAgL1BhZ2VzIDIgMCBS"
    "CiAgPj4KZW5kb2JqCjIgMCBvYmoKICA8PCAvVHlwZSAvUGFnZXMKICAgICAvS2lkcyBbIDMgMCBSIF0K"
    "ICAgICAvQ291bnQgMQogID4+CmVuZG9iagozIDAgb2JqCiAgPDwgL1R5cGUgL1BhZ2UKICAgICAvUGFy"
    "ZW50IDIgMCBSCiAgICAgL01lZGlhQm94IFsgMCAwIDU5NSA4NDIgXQogICAgIC9Db250ZW50cyA0IDAg"
    "UgogICAgIC9SZXNvdXJjZXMgPDwgPj4KICA+PgplbmRvYmoKNCAwIG9iagogIDw8IC9MZW5ndGggMjUg"
    "Pj4Kc3RyZWFtCkJUCi9GMSAxMiBUZgogNzAgNzAwIFRkCihIZWxsbyBXb3JsZCkgVGoKRVQKZW5kc3Ry"
    "ZWFtCmVuZG9iagp4cmVmCjAgNQowMDAwMDAwMDAwIDY1NTM1IGYgCjAwMDAwMDAwMTUgMDAwMDAgbiAK"
    "MDAwMDAwMDA4MCAwMDAwMCBuIAowMDAwMDAwMTQwIDAwMDAwIG4gCjAwMDAwMDAyNDQgMDAwMDAgbiAK"
    "dHJhaWxlcgogIDw8IC9TaXplIDUKICAgICAvUm9vdCAxIDAgUgogID4+CnN0YXJ0eHJlZgogMzE4CiUl"
    "RU9GCg=="
)

# Seeding list for Academics
MOCK_ACADEMIC_ENTRIES = [
    {"title": "Introduction to Computer Science", "subject": "Computer Science", "uploaded_by": "Dr. Sunita Sarawagi"},
    {"title": "Principles of Microeconomics", "subject": "Economics", "uploaded_by": "Prof. Amit Sheth"},
    {"title": "Modern Organic Chemistry", "subject": "Chemistry", "uploaded_by": "Dr. CNR Rao"},
    {"title": "Linear Algebra & Applications", "subject": "Mathematics", "uploaded_by": "Prof. Manindra Agrawal"},
    {"title": "Calculus Vol 1", "subject": "Mathematics", "uploaded_by": "Dr. Devendra Jalihal"},
    {"title": "World History 101", "subject": "History", "uploaded_by": "Prof. Romila Thapar"},
    {"title": "Introduction to Quantum Physics", "subject": "Physics", "uploaded_by": "Dr. Preeti Ranjan Panda"},
    {"title": "Cognitive Psychology", "subject": "Psychology", "uploaded_by": "Dr. Girishwar Misra"},
    {"title": "Classical Mechanics", "subject": "Physics", "uploaded_by": "Dr. Hema A. Murthy"},
    {"title": "Data Structures and Algorithms", "subject": "Computer Science", "uploaded_by": "Dr. Pushpak Bhattacharyya"}
]

def seed_academics(db: Session):
    # Check if we have entries
    count = db.query(models.AcademicPDF).count()
    if count == 0:
        for entry in MOCK_ACADEMIC_ENTRIES:
            db_pdf = models.AcademicPDF(
                title=entry["title"],
                subject=entry["subject"],
                uploaded_by=entry["uploaded_by"],
                file_data=MINIMAL_PDF_BASE64,
                upload_date=datetime.datetime.utcnow()
            )
            db.add(db_pdf)
        db.commit()

@router.get("/pdfs", response_model=List[schemas.AcademicPDFResponse])
def get_all_pdfs(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    pdfs = db.query(models.AcademicPDF).all()
    response_list = []
    for pdf in pdfs:
        response_list.append(
            schemas.AcademicPDFResponse(
                id=pdf.id,
                title=pdf.title,
                subject=pdf.subject,
                uploaded_by=pdf.uploaded_by,
                upload_date=pdf.upload_date,
                file_url=f"/mcp/academics/download/{pdf.id}"
            )
        )
    return response_list

@router.get("/search", response_model=List[schemas.AcademicPDFResponse])
def search_pdfs(q: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    query = q.lower()
    pdfs = db.query(models.AcademicPDF).filter(
        (models.AcademicPDF.title.ilike(f"%{query}%")) | 
        (models.AcademicPDF.subject.ilike(f"%{query}%"))
    ).all()
    
    response_list = []
    for pdf in pdfs:
        response_list.append(
            schemas.AcademicPDFResponse(
                id=pdf.id,
                title=pdf.title,
                subject=pdf.subject,
                uploaded_by=pdf.uploaded_by,
                upload_date=pdf.upload_date,
                file_url=f"/mcp/academics/download/{pdf.id}"
            )
        )
    return response_list

@router.post("/upload", response_model=schemas.AcademicPDFResponse, status_code=status.HTTP_201_CREATED)
async def upload_pdf(
    title: str = Form(...),
    subject: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Validation: Only PDF
    if not file.filename.lower().endswith(".pdf") and file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported."
        )
        
    # Read content to check size
    contents = await file.read()
    max_size_bytes = 20 * 1024 * 1024  # 20MB
    if len(contents) > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 20MB limit."
        )
        
    # Encode to base64
    base64_data = base64.b64encode(contents).decode("utf-8")
    
    db_pdf = models.AcademicPDF(
        title=title,
        subject=subject,
        uploaded_by=current_user.name,
        file_data=base64_data,
        upload_date=datetime.datetime.utcnow()
    )
    db.add(db_pdf)
    db.commit()
    db.refresh(db_pdf)
    
    return schemas.AcademicPDFResponse(
        id=db_pdf.id,
        title=db_pdf.title,
        subject=db_pdf.subject,
        uploaded_by=db_pdf.uploaded_by,
        upload_date=db_pdf.upload_date,
        file_url=f"/mcp/academics/download/{db_pdf.id}"
    )

@router.get("/download/{pdf_id}")
def download_pdf(pdf_id: int, db: Session = Depends(get_db)):
    pdf = db.query(models.AcademicPDF).filter(models.AcademicPDF.id == pdf_id).first()
    if not pdf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF entry not found."
        )
        
    try:
        file_bytes = base64.b64decode(pdf.file_data)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error decoding file data."
        )
        
    headers = {
        "Content-Disposition": f'attachment; filename="{pdf.title.replace(" ", "_")}.pdf"'
    }
    return Response(content=file_bytes, media_type="application/pdf", headers=headers)
