"""Validation rules for the password creation options."""

MIN_LENGTH = 8
MAX_LENGTH = 64
DEFAULT_LENGTH = 18


class PasswordValidationError(ValueError):
    """Raised when requested password settings are unsafe or impossible."""


def validate_settings(length: int, categories: dict[str, bool]) -> None:
    if isinstance(length, bool) or not isinstance(length, int):
        raise PasswordValidationError("Password length must be a whole number.")
    if not MIN_LENGTH <= length <= MAX_LENGTH:
        raise PasswordValidationError(
            f"Password length must be between {MIN_LENGTH} and {MAX_LENGTH}."
        )
    if sum(bool(selected) for selected in categories.values()) < 2:
        raise PasswordValidationError("Select at least two character categories.")
