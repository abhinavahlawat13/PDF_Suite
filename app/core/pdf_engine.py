import fitz  # PyMuPDF
from pathlib import Path
from typing import Optional,List
from app.utils.logger import logger
from app.core.exceptions import(PDFSuiteException, PDFLoadError, PDFProcessingError, PDFPasswordProtectedError, PDFCorruptedError, InvalidPDFRangeError, PDFOperationError)
from app.utils.logger import logger
