from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pdf2docx import Converter
import tempfile
import os
import subprocess
import yt_dlp
import pikepdf

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "Python Backend API is running"}

@app.post("/convert/pdf-to-docx")
async def convert_pdf_to_docx(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        tmp_pdf.write(await file.read())
        pdf_path = tmp_pdf.name
        
    docx_path = pdf_path.replace(".pdf", ".docx")
    
    try:
        cv = Converter(pdf_path)
        cv.convert(docx_path, start=0, end=None)
        cv.close()
        
        return FileResponse(
            docx_path, 
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=file.filename.replace(".pdf", ".docx")
        )
    finally:
        pass

@app.post("/convert/docx-to-pdf")
async def convert_docx_to_pdf(file: UploadFile = File(...)):
    with tempfile.TemporaryDirectory() as temp_dir:
        docx_path = os.path.join(temp_dir, file.filename)
        with open(docx_path, "wb") as f:
            f.write(await file.read())
        
        try:
            subprocess.run([
                'libreoffice', '--headless', '--convert-to', 'pdf',
                docx_path, '--outdir', temp_dir
            ], check=True)
        except Exception as e:
            return {"error": f"LibreOffice conversion failed: {str(e)}"}
        
        pdf_filename = file.filename.rsplit('.', 1)[0] + '.pdf'
        pdf_path = os.path.join(temp_dir, pdf_filename)
        
        if os.path.exists(pdf_path):
            return FileResponse(
                pdf_path, 
                media_type="application/pdf",
                filename=pdf_filename
            )
        else:
            return {"error": "PDF file not generated"}

@app.post("/pdf/crack")
async def crack_pdf(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        tmp_pdf.write(await file.read())
        pdf_path = tmp_pdf.name

    unlocked_path = pdf_path.replace(".pdf", "_unlocked.pdf")
    
    try:
        passwords_to_try = ["", "1234", "123456", "password", "admin"] + [str(i).zfill(4) for i in range(10000)]
        
        found_password = None
        for pwd in passwords_to_try:
            try:
                with pikepdf.open(pdf_path, password=pwd) as pdf:
                    pdf.save(unlocked_path)
                    found_password = pwd
                    break
            except pikepdf.PasswordError:
                continue
            except Exception as e:
                break
                
        if found_password is not None:
            return FileResponse(
                unlocked_path,
                media_type="application/pdf",
                filename=file.filename.replace(".pdf", "_desbloqueado.pdf")
            )
        else:
            raise HTTPException(status_code=400, detail="Senha muito complexa. A quebra online suporta apenas PINs de 4 dígitos ou senhas comuns.")
    finally:
        pass

@app.get("/youtube/info")
async def youtube_info(url: str):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = []
            for f in info.get('formats', []):
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    formats.append({
                        'format_id': f.get('format_id'),
                        'ext': f.get('ext'),
                        'resolution': f.get('resolution'),
                        'filesize': f.get('filesize') or f.get('filesize_approx') or 0,
                        'format_note': f.get('format_note', '')
                    })
            
            formats = sorted(formats, key=lambda x: x['filesize'], reverse=True)
            
            unique_formats = []
            seen_res = set()
            for f in formats:
                if f['resolution'] not in seen_res and f['resolution'] != 'audio only':
                    seen_res.add(f['resolution'])
                    unique_formats.append(f)

            return {
                "title": info.get('title'),
                "thumbnail": info.get('thumbnail'),
                "duration": info.get('duration'),
                "formats": unique_formats[:5]
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/youtube/download")
async def youtube_download(url: str = Form(...), format_id: str = Form(...)):
    with tempfile.TemporaryDirectory() as temp_dir:
        ydl_opts = {
            'format': format_id,
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
            return FileResponse(
                filename,
                media_type="application/octet-stream",
                filename=os.path.basename(filename)
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
