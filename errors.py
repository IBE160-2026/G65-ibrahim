"""Errors raised by the core modules. app.py maps them to messages in ERROR_UI."""


class StudyBuddyError(Exception):
    """Base class for every error the core modules raise on purpose."""


class EmptyInput(StudyBuddyError):
    """No PDF was uploaded, or the pasted text is missing or only whitespace."""


class EmptyFile(StudyBuddyError):
    """The uploaded file has 0 bytes."""


class NotPdf(StudyBuddyError):
    """The file name does not end in .pdf, or the bytes do not start with %PDF."""


class UnreadablePdf(StudyBuddyError):
    """The PDF is password-protected or damaged and cannot be opened."""


class NoExtractableText(StudyBuddyError):
    """The PDF has no text layer, for example because it is scanned."""
