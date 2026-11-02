import customtkinter as ctk
import tkinter.font as tkfont
from functools import lru_cache

OUTER = "#292929"
BG = "#111015"
PANEL = "#1c1c1f"
MAP = "#19191b"
SELECTED = "#bdd7ec"
TEXT = "#f5f5f7"
MUTED = "#aeacb8"
INK = "#14151b"
BLUE = "#92c6ee"
LAVENDER = "#c6b6ea"
ERROR = "#ffb4ab"


@lru_cache(maxsize=1)
def font_family():
    available = set(tkfont.families())
    return next(
        (name for name in ("Segoe UI", "DejaVu Sans", "Arial") if name in available),
        "TkDefaultFont",
    )


def font(size=14, bold=False):
    return ctk.CTkFont(
        family=font_family(), size=size, weight="bold" if bold else "normal"
    )


def label(parent, text="", size=14, color=TEXT, bold=False, **kwargs):
    return ctk.CTkLabel(
        parent,
        text=text,
        font=font(size, bold),
        text_color=color,
        height=kwargs.pop("height", 22),
        **kwargs
    )


class ActionButton(ctk.CTkButton):
    """Keyboard-operable CTk button with a visible focus ring."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._canvas.configure(takefocus=1)
        self.bind("<Return>", lambda event: self.invoke())
        self.bind("<space>", lambda event: self.invoke())
        self._canvas.bind(
            "<FocusIn>", lambda event: self.configure(border_width=2, border_color=BLUE)
        )
        self._canvas.bind("<FocusOut>", lambda event: self.configure(border_width=0))

    def focus_set(self):
        self._canvas.focus_set()


def button(parent, text, command, **kwargs):
    return ActionButton(
        parent,
        text=text,
        command=command,
        font=font(13),
        fg_color=kwargs.pop("fg_color", PANEL),
        hover_color=kwargs.pop("hover_color", "#34343b"),
        text_color=kwargs.pop("text_color", TEXT),
        corner_radius=18,
        height=34,
        **kwargs
    )
