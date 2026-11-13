class CatalogError(Exception):
    """Base error of catalog"""


class InvalidEntityError(CatalogError):
    def __init__(self, message: str) -> None:
        """Book is not valid"""
        self.message = message
        super().__init__(message)


class DuplicateIdError(CatalogError):
    def __init__(self, item_id: str) -> None:
        """Id already in catalog"""
        self.item_id = item_id
        super().__init__(f"duplicate id: {item_id}")


class ItemNotFoundError(CatalogError):
    def __init__(self, item_id: str) -> None:
        """No book with this id"""
        self.item_id = item_id
        super().__init__(f"item not found: {item_id}")


class UnsupportedVersionError(CatalogError):
    def __init__(self, version: object) -> None:
        """Unknown format version"""
        self.version = version
        super().__init__(f"unsupported format version: {version!r}")


class CorruptedFileError(CatalogError):
    def __init__(self, reason: str) -> None:
        """Wrong json file"""
        self.reason = reason
        super().__init__(f"corrupted file: {reason}")


class NothingToUndoError(CatalogError):
    def __init__(self) -> None:
        """No operations to undo"""
        super().__init__("nothing to undo")


class TransactionError(CatalogError):
    def __init__(self, reason: str) -> None:
        """Not allowed in transaction"""
        super().__init__(f"transaction error: {reason}")
