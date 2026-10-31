"""UI-independent application controller for easier testing."""

from __future__ import annotations
from collections import deque

from app.core.password_generator import PasswordOptions, generate_password
from app.core.strength import StrengthResult, estimate_strength


class PasswordController:
    def __init__(self, max_history: int = 5) -> None:
        if max_history < 1:
            raise ValueError("History capacity must be at least 1")
        self.history: deque[str] = deque(maxlen=max_history)
        self.current_password = ""

    def generate(self, options: PasswordOptions) -> tuple[str, StrengthResult]:
        password = generate_password(options)
        strength = estimate_strength(options)
        self.current_password = password
        self.history.appendleft(password)
        return password, strength

    def clear_history(self) -> None:
        self.history.clear()

    def close(self) -> None:
        self.current_password = ""
        self.clear_history()
