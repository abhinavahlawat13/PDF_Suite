"""Core PDF operations (PyMuPDF). No UI code lives here.
 
Public API uses 1-based page numbers (what users see); internally we
convert to 0-based indexes in exactly one place (_to_indexes).
"""
 
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
 
import fitz  # PyMuPDF
 
from app.core.exceptions import (
    InvalidPDFRangeError,
    PDFCorruptedError,
    PDFLoadError,
    PDFOperationError,
    PDFPasswordProtectedError,
    PDFSuiteException,  
)
from app.utils.logger import logger
 
_SAVE_OPTS = {"garbage": 3, "deflate": True}  # drop unused objects, compress
 
 
class PDFEngine:
    #  helpers
    @staticmethod
    def _open_pdf(file_path: Path) -> fitz.Document:
        """Check the file exists, open it, and make sure it is a usable PDF."""
        path = Path(file_path)
        if not path.is_file():
            logger.error(f"File not found: {path}")
            raise PDFLoadError(f"File not found: {path}")
 
        try:
            doc = fitz.open(path)
        except Exception as e:
            logger.error(f"Failed to open PDF: {path}, error: {e}")
            raise PDFCorruptedError(
                f"Cannot open '{path.name}'. The file may be corrupted."
            ) from e
 
        # fitz also opens images, EPUB, XPS... so verify it is really a PDF.
        if not doc.is_pdf:
            doc.close()
            logger.error(f"Not a PDF: {path}")
            raise PDFCorruptedError(f"'{path.name}' is not a PDF file.")
 
        # needs_pass is True only when a password is required to open it.
        # (is_encrypted is also True for PDFs that open freely.)
        if doc.needs_pass:
            doc.close()
            logger.warning(f"Password-protected PDF: {path}")
            raise PDFPasswordProtectedError(
                f"'{path.name}' is password protected."
            )
 
        if doc.page_count == 0:
            doc.close()
            logger.error(f"PDF has no pages: {path}")
            raise PDFCorruptedError(f"'{path.name}' has no pages.")
 
        return doc
 
    @classmethod
    @contextmanager
    def _pdf(cls, file_path: Path) -> Iterator[fitz.Document]:
        """Open a PDF and always close it, even if an error is raised."""
        doc = cls._open_pdf(file_path)
        try:
            yield doc
        finally:
            if not doc.is_closed:
                doc.close()
 
    @staticmethod
    def _to_indexes(pages: list[int], total: int) -> list[int]:
        """Validate 1-based page numbers and return 0-based indexes."""
        bad = [p for p in pages if not 1 <= p <= total]
        if bad:
            logger.error(f"Pages {bad} out of range (document has {total})")
            raise InvalidPDFRangeError(
                f"Page(s) {bad} out of range. The document has {total} pages."
            )
        return [p - 1 for p in pages]
 
    @staticmethod
    def _check_output(output_path: Path, *sources: Path) -> Path:
        """Refuse to write over an input file."""
        out = Path(output_path)
        if any(out.resolve() == Path(s).resolve() for s in sources):
            raise PDFOperationError("Output file must be different from the input file.")
        return out
 
    # --------------------------------------------------------------- operations
    @classmethod
    def merge_pdfs(cls, file_paths: list[Path], output_path: Path) -> None:
        """Merge multiple PDF files into a single PDF."""
        if len(file_paths) < 2:
            logger.error("Merge failed: fewer than 2 files provided")
            raise PDFOperationError("Select at least 2 files to merge.")
 
        out = cls._check_output(output_path, *file_paths)
        logger.info(f"Merging {len(file_paths)} files")
 
        merged = fitz.open()
        try:
            for file_path in file_paths:
                with cls._pdf(file_path) as src:
                    merged.insert_pdf(src)
 
            out.parent.mkdir(parents=True, exist_ok=True)
            merged.save(out, **_SAVE_OPTS)
            logger.info(f"Merged successfully: {out.name}")
        except PDFSuiteException:
            raise
        except Exception as e:
            logger.error(f"Unexpected merge error: {e}")
            raise PDFOperationError(f"Cannot merge PDFs: {e}") from e
        finally:
            merged.close()
 
    @classmethod
    def extract_pages(cls, file_path: Path, pages: list[int], output_path: Path) -> None:
        """Copy the given pages (1-based, in the given order) into a new PDF."""
        if not pages:
            logger.error("Extraction failed: no pages specified")
            raise PDFOperationError("No pages specified for extraction.")
 
        out = cls._check_output(output_path, file_path)
 
        try:
            with cls._pdf(file_path) as doc:
                indexes = cls._to_indexes(pages, doc.page_count)
                doc.select(indexes)  # in-memory only; original file untouched
                out.parent.mkdir(parents=True, exist_ok=True)
                doc.save(out, **_SAVE_OPTS)
            logger.info(f"Extracted {len(pages)} pages into: {out}")
        except PDFSuiteException:
            raise
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            raise PDFOperationError(f"Failed to extract pages: {e}") from e
 
    @classmethod
    def rotate_page(
        cls,
        file_path: Path,
        rotation_degree: int,
        pages: list[int] | None = None,
        output_path: Path | None = None,
    ) -> None:
        """Rotate given pages (1-based) or all pages clockwise by 90/180/270.
 
        If output_path is None the original file is replaced, safely: we write
        a temp file first and only swap it in once saving succeeded.
        """
        if rotation_degree not in (90, 180, 270):
            logger.error(f"Invalid rotation angle: {rotation_degree}")
            raise PDFOperationError("Rotation angle must be 90, 180, or 270.")
        if pages is not None and not pages:
            raise PDFOperationError("No pages specified for rotation.")
 
        src = Path(file_path)
        dest = Path(output_path) if output_path else src
        in_place = dest.resolve() == src.resolve()
        tmp_path: Path | None = None
 
        try:
            with cls._pdf(src) as doc:
                if pages is None:
                    targets = list(range(doc.page_count))
                else:
                    # dict.fromkeys removes duplicates, so [2, 2] rotates once
                    targets = list(dict.fromkeys(cls._to_indexes(pages, doc.page_count)))
 
                for i in targets:
                    page = doc[i]
                    page.set_rotation((page.rotation + rotation_degree) % 360)
 
                dest.parent.mkdir(parents=True, exist_ok=True)
                save_to = dest
                if in_place:
                    fd, name = tempfile.mkstemp(suffix=".pdf", dir=dest.parent)
                    os.close(fd)
                    tmp_path = save_to = Path(name)
                doc.save(save_to, **_SAVE_OPTS)
 
            # Doc is closed now (required on Windows before replacing the file).
            if tmp_path is not None:
                os.replace(tmp_path, dest)
                tmp_path = None
            logger.info(f"Rotated {len(targets)} page(s) by {rotation_degree} in {dest}")
        except PDFSuiteException:
            raise
        except Exception as e:
            logger.error(f"Rotation failed: {e}")
            raise PDFOperationError(f"Failed to rotate pages: {e}") from e
        finally:
            if tmp_path is not None:
                tmp_path.unlink(missing_ok=True)
 
    @classmethod
    def delete_pages(cls, file_path: Path, pages: list[int], output_path: Path) -> None:
        """Save a copy of the PDF with the given pages (1-based) removed."""
        if not pages:
            logger.error("Delete failed: no pages specified")
            raise PDFOperationError("No pages specified for deletion.")
 
        out = cls._check_output(output_path, file_path)
 
        try:
            with cls._pdf(file_path) as doc:
                to_delete = set(cls._to_indexes(pages, doc.page_count))
                keep = [i for i in range(doc.page_count) if i not in to_delete]
                if not keep:
                    logger.error("Delete failed: would remove every page")
                    raise PDFOperationError("Cannot delete every page of a PDF.")
 
                doc.select(keep)  # in-memory only; original file untouched
                out.parent.mkdir(parents=True, exist_ok=True)
                doc.save(out, **_SAVE_OPTS)
            logger.info(f"Deleted {len(to_delete)} page(s), saved to: {out}")
        except PDFSuiteException:
            raise
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            raise PDFOperationError(f"Failed to delete pages: {e}") from e
 
    @classmethod
    def extract_text(
        cls,
        file_path: Path,
        pages: list[int] | None = None,
        output_path: Path | None = None,
    ) -> str:
        """Return the text of the given pages (1-based) or of all pages.
 
        If output_path is given, the text is also written there as UTF-8.
        Raises PDFOperationError if no selectable text exists (e.g. scanned PDF).
        """
        if pages is not None and not pages:
            raise PDFOperationError("No pages specified for text extraction.")
 
        out = cls._check_output(output_path, file_path) if output_path else None
 
        try:
            with cls._pdf(file_path) as doc:
                if pages is None:
                    indexes = list(range(doc.page_count))
                else:
                    indexes = list(dict.fromkeys(cls._to_indexes(pages, doc.page_count)))
 
                chunks = []
                for i in indexes:
                    text = doc[i].get_text("text").strip()
                    if text:
                        chunks.append(f"--- Page {i + 1} ---\n{text}")
 
            if not chunks:
                logger.warning(f"No selectable text found in: {file_path}")
                raise PDFOperationError(
                    "No selectable text found. The PDF may contain scanned images."
                )
 
            result = "\n\n".join(chunks)
            if out is not None:
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(result, encoding="utf-8")
                logger.info(f"Text saved to: {out}")
            return result
        except PDFSuiteException:
            raise
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            raise PDFOperationError(f"Failed to extract text: {e}") from e
    @classmethod
    def images_to_pdf(cls, image_paths: list[Path], output_path: Path) -> None:
        """Convert a list of images (PNG, JPG, JPEG) into a single unified PDF."""
        if not image_paths:
            logger.error("Image to PDF failed: no images provided")
            raise PDFOperationError("Select at least one image to convert.")

        out = cls._check_output(output_path, *image_paths)
        logger.info(f"Converting {len(image_paths)} images to PDF")

        doc = fitz.open()
        try:
            for img_path in image_paths:
                path = Path(img_path)
                if not path.is_file():
                    raise PDFOperationError(f"Image not found: {path.name}")

                try:
                    # Open image, convert to PDF stream, and insert
                    with fitz.open(path) as img_doc:
                        pdf_bytes = img_doc.convert_to_pdf()
                        with fitz.open("pdf", pdf_bytes) as img_pdf:
                            doc.insert_pdf(img_pdf)
                except Exception as img_err:
                    raise PDFOperationError(
                        f"Failed to process '{path.name}'. File may not be a supported image: {img_err}"
                    ) from img_err

            out.parent.mkdir(parents=True, exist_ok=True)
            doc.save(out, **_SAVE_OPTS)
            logger.info(f"Images converted successfully to: {out.name}")

        except PDFSuiteException:
            raise
        except Exception as e:
            logger.error(f"Image conversion failed: {e}")
            raise PDFOperationError(f"Cannot convert images to PDF: {e}") from e
        finally:
            doc.close()

    @classmethod
    def add_watermark(
        cls,
        file_path: Path,
        watermark_text: str,
        output_path: Path,
        fontsize: int = 36,
    ) -> None:
        """Add a semi-transparent diagonal text watermark across every page of the PDF."""
        if not watermark_text.strip():
            logger.error("Watermark failed: empty watermark text")
            raise PDFOperationError("Watermark text cannot be empty.")

        out = cls._check_output(output_path, file_path)

        try:
            with cls._pdf(file_path) as doc:
                for page in doc:
                    rect = page.rect
                    # Watermark ko center-left se start karne ke liye point
                    center = fitz.Point(rect.width * 0.2, rect.height * 0.6)
                    
                    # 45 degree slant ke liye 'morph' use kiya hai (rotate=45 crash karta hai)
                    page.insert_text(
                        center,
                        watermark_text,
                        fontsize=fontsize,
                        color=(0.75, 0.75, 0.75),  # Light gray
                        morph=(center, fitz.Matrix(-45)),
                    )

                out.parent.mkdir(parents=True, exist_ok=True)
                doc.save(out, **_SAVE_OPTS)

            logger.info(f"Watermark applied successfully to: {out.name}")

        except PDFSuiteException:
            raise
        except Exception as e:
            logger.error(f"Watermarking failed: {e}")
            raise PDFOperationError(f"Failed to apply watermark: {e}") from e