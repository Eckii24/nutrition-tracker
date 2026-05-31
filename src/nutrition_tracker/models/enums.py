from enum import StrEnum


class Source(StrEnum):
    MANUAL = "manual"
    TEXT = "text"
    IMAGE = "image"
    IMAGE_TEXT = "image+text"
    IMPORT = "import"


class CorrectionOperation(StrEnum):
    REPLACE = "replace"
    CANCEL = "cancel"
    ANNOTATE = "annotate"
