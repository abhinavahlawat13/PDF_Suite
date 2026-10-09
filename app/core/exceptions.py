class PDFSuiteException(Exception):
    """Base exception class for PDFSuite errors."""
    def __init__(self, message: str = "An error occurred in PDFSuite."):
        self.message = message
        super().__init__(self.message)

class PDFLoadError(PDFSuiteException):
    """Exception raised when there is an error loading a PDF file."""
    def __init__(self, message: str = "Failed to load the PDF file."):
        super().__init__(message)

class PDFProcessingError(PDFSuiteException):
    """Exception raised when there is an error processing a PDF file."""
    def __init__(self, message: str = "An error occurred while processing the PDF file."):
        super().__init__(message)

class PDFPasswordProtectedError(PDFSuiteException):
    """Exception raised when a PDF file is password protected."""
    def __init__(self, message: str = "The PDF file is password protected."):
        super().__init__(message)

class PDFCorruptedError(PDFSuiteException):
    """Exception raised when a PDF file is corrupted."""
    def __init__(self, message: str = "The PDF file is corrupted."):
        super().__init__(message)

class InvalidPDFRangeError(PDFSuiteException):
    """Exception raised when an invalid page range is specified for a PDF file."""
    def __init__(self, message: str = "The specified page range is invalid."):
        super().__init__(message)

class PDFOperationError(PDFSuiteException):
    """Exception raised when an error occurs during a PDF operation."""
    def __init__(self, message: str = "An error occurred during the PDF operation."):
        super().__init__(message)
        