from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from pdf2docx import Converter
import tempfile
import os

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "Python PDF Converter API is running"}

@app.post("/convert/pdf-to-docx")
async def convert_pdf_to_docx(file: UploadFile = File(...)):
    # Cria arquivos temporários para processamento
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        tmp_pdf.write(await file.read())
        pdf_path = tmp_pdf.name
        
    docx_path = pdf_path.replace(".pdf", ".docx")
    
    try:
        # Converte usando pdf2docx (Alta qualidade, preserva tabelas e imagens)
        cv = Converter(pdf_path)
        cv.convert(docx_path, start=0, end=None)
        cv.close()
        
        return FileResponse(
            docx_path, 
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=file.filename.replace(".pdf", ".docx")
        )
    finally:
        # O FastAPI FileResponse cuida do envio, mas em produção 
        # você deve usar BackgroundTasks para deletar os arquivos temporários depois.
        pass
