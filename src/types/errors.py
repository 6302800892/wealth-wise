"""Error types shared by every layer. The API layer maps `code` to an HTTP status (spec §10.1)."""

from typing import Any


class WealthWiseError(Exception):
    """A business or validation failure with a stable, machine-readable code."""

    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


def validation_error(field: str, message: str) -> WealthWiseError:
    return WealthWiseError("VALIDATION_FAILED", message, {"field": field})


def not_found(entity: str) -> WealthWiseError:
    return WealthWiseError("NOT_FOUND", f"{entity} not found")


class MigrationIntegrityError(Exception):
    """An applied migration file was modified or deleted (NFR-05). Startup must stop."""
