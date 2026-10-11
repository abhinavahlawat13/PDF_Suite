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
        """checking file existence, opening the PDF, and handling errors."""
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
        """Merge multiple PDF files into a single PDF."""
        # 1. Min 2 files check
        if len(file_paths) < 2:
            logger.error("Merge failed: Less than 2 files provided")
            raise PDFOperationError(
                "Select at least 2 files to merge."
            )

        logger.info(
            f"{len(file_paths)} Merging files"
        )
        merged_doc = fitz.open()  # Create a new empty PDF document

        try:
            # Inserting pages from each source PDF into the merged document
            for file_path in file_paths:
                src_doc = cls._open_pdf(file_path)
                try:
                    merged_doc.insert_pdf(src_doc)
                finally:
                    src_doc.close()  # Ensure the source document is closed after merging

            # Saving the merged document to the specified output path
            out_file = Path(output_path)
            out_file.parent.mkdir(parents=True, exist_ok=True)

            merged_doc.save(out_file)
            logger.info(f"Merged files successfully: {out_file.name}")

        except (
            PDFLoadError,
            PDFPasswordProtectedError,
            PDFCorruptedError,
            PDFOperationError,
        ):
            raise
        except Exception as e:
            logger.error(f"Unexpected merge error: {e}")
            raise PDFOperationError(f"Cannot merge PDFs: {str(e)}")
        finally:
            merged_doc.close()

    @classmethod
    def extract_pages(cls, file_path: Path, pages: List[int], output_path: Path) -> None:
        """Extract specific pages from a PDF and save them to a new PDF. """
        if not pages:
            logger.error("Extraction failed: no pages specified")
            raise PDFOperationError("No pages specified for extraction.")
        doc=cls._open_pdf(file_path)
        new_doc = fitz.open()  # Create a new empty PDF document
        try:
            total_pages = len(doc)
            zero_indexes_pages : List[int]=[]
            for p in pages:
                if p<1 or p>total_pages:
                    logger.error(f"page index {p} out of bounds as total pages:{total_pages}")
                    raise InvalidPDFRangeError(f"page{p} is out of bonds document contains {total_pages}")
                zero_indexes_pages.append(p-1)

            for page_num in zero_indexes_pages:
                new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

            out_file=Path(output_path)
            out_file.parent.mkdir(parents=True, exist_ok=True)

            new_doc.save(out_file)
            logger.info(f"Succesfully extracted {len(pages)} pages into: {out_file}")

        except(
            InvalidPDFRangeError,
            PDFCorruptedError,
            PDFPasswordProtectedError,
            PDFLoadError,
            PDFOperationError
        ):
            raise
        except Exception as e:
            logger.error(f"extraction failed : {e}")
            raise PDFOperationError(f"failed to extract pages")
        finally:
            doc.close()
            new_doc.close()
