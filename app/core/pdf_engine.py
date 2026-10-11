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

    @classmethod
    def rotate_page(cls,file_path: Path, rotation_degree: int, pages: Optional[List[int]]=None, output_path:Optional[Path]=None) -> None:
        """Rotate specific pages  or all  pages by 90,180 or 270 degrees clockwise"""
        if rotation_degree not in [90,180,270]:
            logger.error(f"Invalid rotaion angle requested: {rotation_degree}")
            raise PDFOperationError(f"Rotation angle must be either 90, 180, or 270")

        doc = cls._open_pdf(file_path)
        try:
            total_pages=len(doc)
            target_pages=([p - 1 for p in pages ]if pages else list(range(total_pages)))
            for p in target_pages:
                if p<0 or p>=total_pages:
                    logger.error(f"Page index{p+1} invalid for rotation ")
                    raise InvalidPDFRangeError(f"Page {p} is out of bonds. Documnet contains {total_pages} pages")
                current_rotation=doc[p].rotation
                doc[p].set_rotation((current_rotation + rotation_degree) % 360)

            save_dest=Path(output_path) if output_path else Path(file_path)
            save_dest.parent.mkdir(parents=True, exist_ok=True)

            if save_dest.resolve() == Path(file_path).resolve():
                doc.save(save_dest, incremental = True, encryption=fitz.PDF_ENCRYPT_KEEP)
            else:
                doc.save(save_dest)
            logger.info(f"succesfully rotated{len(target_pages)}by {rotation_degree} in {save_dest}")
        except (
            InvalidPDFRangeError,
            PDFCorruptedError,
            PDFPasswordProtectedError,
            PDFLoadError,
            PDFOperationError,
        ):
            raise
        except Exception as e:
            logger.error(f"Rotation failed: {e}")
            raise PDFOperationError(f"Failed to rotate pages: {str(e)}")
        finally:
            doc.close() 
