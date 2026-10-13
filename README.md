# PDF Toolkit Pro

A desktop tool to process and edit PDF files locally. Built with Python 3.11, PyMuPDF, and CustomTkinter.

---

## Features

- **Merge PDFs:** Combines two or more PDF files into a single file.
- **Extract Pages:** Saves specific pages (1-based index) into a new PDF.
- **Delete Pages:** Removes selected pages and saves the remaining pages to a new file.
- **Rotate Pages:** Rotates selected pages or the entire document by 90°, 180°, or 270°.
- **Extract Text:** Pulls selectable text out of pages and displays or saves it.
- **Images to PDF:** Converts JPG, PNG, and WEBP images into a multi-page PDF.
- **Add Watermark:** Adds a diagonal text watermark across document pages.
- **File Validation:** Checks for empty, non-PDF, and password-protected files before processing.

---

## Technical Details

- **File Cleanup:** Uses Python context managers (`with` blocks) so files close properly even if an error occurs.
- **Safe Overwrites:** When rotating a file in-place, writes to a temporary file first and swaps it using `os.replace` to prevent file corruption.
- **Page Indexing:** Accepts standard 1-based page numbers from the UI and converts them to 0-based indices internally.
- **File Size:** Saves files with `garbage=3` and `deflate=True` to remove unused objects and compress streams.

---

## Project Structure

```text
Desktop-pdf-suite/
├── app/
│   ├── core/
│   │   ├── exceptions.py       # Custom exception classes
│   │   └── pdf_engine.py       # PyMuPDF processing methods
│   ├── gui/
│   │   └── main_window.py      # CustomTkinter interface
│   ├── utils/
│   │   └── logger.py           # Logging setup
│   └── main.py                 # App launch script
├── requirements.txt
└── README.md