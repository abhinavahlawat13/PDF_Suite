import fitz  # PyMuPDF
from pathlib import Path
from typing import Optional,List
from app.core.exceptions import(PDFSuiteException, PDFLoadError, PDFProcessingError, PDFPasswordProtectedError, PDFCorruptedError, InvalidPDFRangeError, PDFOperationError)
from app.utils.logger import logger

class PDFEngine:
    @staticmethod
    def _open_pdf(file_path: Path)-> fitz.Document:
        path = Path(file_path)
        if not path.is_file():
            logger.error(f"file not found: {path}")
            raise PDFLoadError(f"File not found: {path}")
        try:
            doc = fitz.open(path)
        except Exception as e:
            logger.error(f"failed to open PDF: {path}, error: {e}")
            raise PDFCorruptedError(f"Cannot open PDF file: {path} file may be corrupted ")

        if doc.is_encrypted:
            doc.close()
            logger.warning(f"Encrypted PDF detected: {path} ")
            raise PDFPasswordProtectedError(f"PDF file is password protected: {path}")

        return doc