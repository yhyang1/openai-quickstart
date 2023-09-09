from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
import uuid
import os
from translator import PDFTranslator
from io import BytesIO
import uvicorn

# Create a temporary directory for storing files
TEMP_DIR = "temp_files"

if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

class APITranslator:
    def __init__(self, translator: PDFTranslator ,config: dict ):
        self.files = {}  # Structure: {id: {"status": "processing", "path": None}}
        self.config = config
        self.transator = translator

    def add_file(self, file_id):
        self.files[file_id] = {"status": "uploaded", "path": None}

    def set_processing(self, file_id):
        if file_id in self.files:
            self.files[file_id]['status'] = "processing"

    def set_completed(self, file_id, file_path):
        if file_id in self.files:
            self.files[file_id]['status'] = "completed"
            self.files[file_id]['path'] = file_path

    def get_status(self, file_id):
        return self.files.get(file_id, {}).get("status", "not_found")

    def get_file_path(self, file_id):
        return self.files.get(file_id, {}).get("path")

    def translate_pdf(self, file_path, file_format, save=True):
        pass

translator = None
class APIManager:
    def __init__(self, pdf_translator: PDFTranslator,config: dict):
        # self.translator = translator
        # self.config = config
        global apitranslator
        apitranslator = APITranslator(pdf_translator, config)
        self.app = FastAPI()
        self._setup_routes()

    def _setup_routes(self):
        @self.app.post("/upload/")
        async def upload_pdf(file: UploadFile = File(...)):
            if file.content_type != "application/pdf":
                return JSONResponse(status_code=400, content={"detail": "Only PDF files are supported."})

            file_id = uuid.uuid4().hex
            file_path = os.path.join(TEMP_DIR, f"{file_id}.pdf")
            with open(file_path, 'wb') as buffer:
                buffer.write(await file.read())

            apitranslator.add_file(file_id)

            return {"file_id": file_id}

        @self.app.post("/translate/{file_id}")
        async def trigger_translation(file_id: str, target_language: str, file_format: str, background_tasks: BackgroundTasks):
            if file_id not in translator.files:
                return HTTPException(status_code=404, detail="File not found")

            def process_translation():
                translator.set_processing(file_id)
                translated_file_path = translator.translate_pdf(os.path.join(TEMP_DIR, f"{file_id}.pdf"), file_format=file_format)
                translator.set_completed(file_id, translated_file_path)

            background_tasks.add_task(process_translation)

            return {"status": "Translation started"}

        @self.app.get("/status/{file_id}")
        def translation_status(file_id: str):
            status = translator.get_status(file_id)
            if status == "not_found":
                raise HTTPException(status_code=404, detail="File not found")
            return {"status": status}

        @self.app.get("/download/{file_id}")
        def download_translated_file(file_id: str):
            file_path = translator.get_file_path(file_id)
            if not file_path or not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="File not found or not yet translated")

            return FileResponse(file_path, filename=os.path.basename(file_path))

    def run(self):
        uvicorn.run(self.app, host="0.0.0.0", port=8000)
