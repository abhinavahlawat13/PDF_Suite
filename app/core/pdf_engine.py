from pathlib import Path
from typing import List, Optional
import fitz  # PyMuPDF

from app.core.exceptions import (
    InvalidPDFRangeError,
    PDFCorruptedError,
    PDFLoadError,
    PDFOperationError,
    PDFPasswordProtectedError,
    PDFProcessingError,
    PDFSuiteException,
)
from app.utils.logger import logger


class PDFEngine:

    @staticmethod
    def _open_pdf(file_path: Path) -> fitz.Document:
        """PDF ko safely check karke open karta hai."""
        path = Path(file_path)
        if not path.is_file():
            logger.error(f"File not found: {path}")
            raise PDFLoadError(f"File not found: {path}")

        try:
            doc = fitz.open(path)
        except Exception as e:
            logger.error(f"Failed to open PDF: {path}, error: {e}")
            raise PDFCorruptedError(
                f"Cannot open PDF file: {path} file may be corrupted"
            )

        if doc.is_encrypted:
            doc.close()
            logger.warning(f"Encrypted PDF detected: {path}")
            raise PDFPasswordProtectedError(
                f"PDF file is password protected: {path}"
            )

        return doc

    @classmethod
    def merge_pdfs(cls, file_paths: List[Path], output_path: Path) -> None:
        """2 ya 2 se zyada PDFs ko sequence me jod kar nayi PDF banata hai."""
        # 1. Minimum 2 files check
        if len(file_paths) < 2:
            logger.error("Merge failed: Less than 2 files provided")
            raise PDFOperationError(
                "PDFs merge karne ke liye kam se kam 2 files select karein."
            )

        logger.info(
            f"{len(file_paths)} files ko merge karna shuru kar rahe hain..."
        )
        merged_doc = fitz.open()  # Khali PDF banayi

        try:
            # 2. Har file ke pages nayi PDF me insert karo
            for file_path in file_paths:
                src_doc = cls._open_pdf(file_path)
                try:
                    merged_doc.insert_pdf(src_doc)
                finally:
                    src_doc.close()  # Memory leak aur OS file lock se bachne ke liye

            # 3. Output directory ensure karo aur save karo
            out_file = Path(output_path)
            out_file.parent.mkdir(parents=True, exist_ok=True)

            merged_doc.save(out_file)
            logger.info(f"Files successfully merge ho gayi: {out_file.name}")

        except (
            PDFLoadError,
            PDFPasswordProtectedError,
            PDFCorruptedError,
            PDFOperationError,
        ):
            raise
        except Exception as e:
            logger.error(f"Unexpected merge error: {e}")
            raise PDFOperationError(f"PDF merge nahi ho paayi: {str(e)}")
        finally:
            merged_doc.close()