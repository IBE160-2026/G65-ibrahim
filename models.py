"""Shared types used by the app and the pipeline modules."""

from enum import Enum


class Source(str, Enum):
    """Where the course material comes from."""

    PDF = "pdf"
    TEXT = "text"


SOURCE_BY_TAB_LABEL = {"Upload PDF": Source.PDF, "Paste text": Source.TEXT}
