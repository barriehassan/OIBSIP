"""Cryptographically secure password generation; no persistence or telemetry."""

from __future__ import annotations

from dataclasses import dataclass
import secrets
import string

from app.core.validator import DEFAULT_LENGTH, PasswordValidationError, validate_settings

CHARACTER_SETS = {
    "uppercase": string.ascii_uppercase,
    "lowercase": string.ascii_lowercase,
    "digits": string.digits,
    "symbols": "!@#$%^&*()-_=+[]{};:,.?",
}
AMBIGUOUS_CHARACTERS = frozenset("0Oo1lI")


@dataclass(frozen=True)
class PasswordOptions:
    length: int = DEFAULT_LENGTH
    uppercase: bool = True
    lowercase: bool = True
    digits: bool = True
    symbols: bool = True
    exclude_ambiguous: bool = True

    @property
    def categories(self) -> dict[str, bool]:
        return {
            "uppercase": self.uppercase,
            "lowercase": self.lowercase,
            "digits": self.digits,
            "symbols": self.symbols,
        }


def selected_character_sets(options: PasswordOptions) -> dict[str, str]:
    """Return each enabled, non-empty set after exclusions."""
    validate_settings(options.length, options.categories)
    chosen = {}
    for name, enabled in options.categories.items():
        if not enabled:
            continue
        alphabet = CHARACTER_SETS[name]
        if options.exclude_ambiguous:
            alphabet = "".join(c for c in alphabet if c not in AMBIGUOUS_CHARACTERS)
        if not alphabet:
            raise PasswordValidationError(f"No usable characters remain in {name}.")
        chosen[name] = alphabet
    return chosen


def generate_password(options: PasswordOptions | None = None) -> str:
    """Sample uniformly from allowed strings that contain every selected category.

    Rejection sampling retains OS-backed randomness without biasing particular
    positions or category counts. With 8–64 characters and 2–4 enabled sets,
    valid candidates are inexpensive to obtain. No password is logged or saved.
    """
    if options is None:
        options = PasswordOptions()
    sets = selected_character_sets(options)
    all_characters = "".join(sets.values())
    while True:
        candidate = "".join(secrets.choice(all_characters) for _ in range(options.length))
        if all(any(char in alphabet for char in candidate) for alphabet in sets.values()):
            return candidate
