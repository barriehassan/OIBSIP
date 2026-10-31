"""Clipboard integration with graceful fallback for GUI environments."""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class ClipboardResult:
    success: bool
    message: str


def copy_to_clipboard(value: str, root=None) -> ClipboardResult:
    """Try pyperclip, then the Tk clipboard when an active window is supplied."""
    try:
        import pyperclip
        pyperclip.copy(value)
        return ClipboardResult(True, "Copied to clipboard")
    except Exception:
        pass
    if root is not None:
        try:
            root.clipboard_clear()
            root.clipboard_append(value)
            root.update_idletasks()
            return ClipboardResult(True, "Copied to clipboard")
        except Exception:
            pass
    return ClipboardResult(False, "Clipboard unavailable; select and copy the password manually")
