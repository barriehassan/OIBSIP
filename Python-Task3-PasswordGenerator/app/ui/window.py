"""CustomTkinter user interface for Password Forge.

Password generation lives in independent core modules. The GUI never writes
passwords to a file or network service.
"""
from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from app.core.password_generator import PasswordOptions
from app.core.validator import DEFAULT_LENGTH, MAX_LENGTH, MIN_LENGTH, PasswordValidationError
from app.services.clipboard import copy_to_clipboard
from app.ui.background import build_background
from app.ui.controller import PasswordController

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

INK = "#273659"
MUTED = "#63718F"
PURPLE = "#6555CB"
PURPLE_HOVER = "#5140AD"
BLUE = "#467ACB"
PANEL = "#FFFFFF"
BACKDROP = "#F3F2FB"
LINE = "#E4E5F2"
GREEN = "#309D7E"


class PasswordForgeApp(ctk.CTk):
    """Desktop view with accessible controls and ephemeral password history."""

    def __init__(self) -> None:
        super().__init__()
        self.title("NOMOLI FORGE | Password Forge")
        self.geometry("1080x800")
        self.minsize(820, 620)
        self.configure(fg_color=BACKDROP)

        self.controller = PasswordController(max_history=5)
        self.length_var = tk.IntVar(value=DEFAULT_LENGTH)
        self.numeric_length_var = tk.StringVar(value=str(DEFAULT_LENGTH))
        self.uppercase_var = tk.BooleanVar(value=True)
        self.lowercase_var = tk.BooleanVar(value=True)
        self.digits_var = tk.BooleanVar(value=True)
        self.symbols_var = tk.BooleanVar(value=True)
        self.exclude_var = tk.BooleanVar(value=True)
        self.auto_copy_var = tk.BooleanVar(value=False)
        self.show_password_var = tk.BooleanVar(value=False)
        self.show_history_var = tk.BooleanVar(value=False)
        self.password_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Choose your settings and select Generate Password.")
        self.strength_var = tk.StringVar(value="Not generated")

        self._build()
        self._update_length_caption()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Configure>", self._on_window_resize)

    def _card(self, parent, **kwargs):
        return ctk.CTkFrame(
            parent, fg_color=PANEL, corner_radius=20, border_width=1,
            border_color=LINE, **kwargs
        )

    def _build(self) -> None:
        container = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0,
            scrollbar_button_color="#CFCEE8",
        )
        container.pack(fill="both", expand=True, padx=16, pady=10)
        container.grid_columnconfigure(0, weight=1)

        self._build_header(container)
        body = ctk.CTkFrame(container, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=14, pady=(16, 4))
        body.grid_columnconfigure(0, weight=2, uniform="body")
        body.grid_columnconfigure(1, weight=3, uniform="body")
        self._build_settings(body)
        right = ctk.CTkFrame(body, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        right.grid_columnconfigure(0, weight=1)
        self._build_output(right)
        self._build_history(right)

        ctk.CTkLabel(
            container, text="NOMOLI FORGE  •  Creative tools, thoughtfully engineered",
            text_color=MUTED, font=ctk.CTkFont(size=12)
        ).grid(row=2, column=0, pady=(13, 10))

    def _build_header(self, container) -> None:
        from customtkinter import CTkImage

        header = self._card(container)
        header.grid(row=0, column=0, sticky="ew", padx=14, pady=(9, 0))
        header.grid_columnconfigure(0, weight=1)
        self._header_width = 880
        self._header_image = CTkImage(
            light_image=build_background(1120, 210),
            dark_image=build_background(1120, 210),
            size=(self._header_width, 190),
        )
        self._header_label = ctk.CTkLabel(header, image=self._header_image, text="", height=190)
        self._header_label.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        title_group = ctk.CTkFrame(header, fg_color="#F8F7FC", corner_radius=15)
        title_group.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 16))
        ctk.CTkLabel(
            title_group, text="NOMOLI FORGE  /  SECURITY TOOLS",
            text_color=PURPLE, font=ctk.CTkFont(size=12, weight="bold")
        ).pack(pady=(11, 2))
        ctk.CTkLabel(
            title_group, text="Password Forge",
            text_color=INK, font=ctk.CTkFont(size=30, weight="bold")
        ).pack(pady=(0, 1))
        ctk.CTkLabel(
            title_group, text="Every Password, Uniquely Forged.",
            text_color=MUTED, font=ctk.CTkFont(size=14)
        ).pack(pady=(0, 12))

    def _section_heading(self, parent, title: str, subtitle: str) -> None:
        ctk.CTkLabel(
            parent, text=title, anchor="w", text_color=INK,
            font=ctk.CTkFont(size=21, weight="bold")
        ).pack(fill="x", padx=22, pady=(20, 1))
        ctk.CTkLabel(
            parent, text=subtitle, anchor="w", text_color=MUTED,
            wraplength=300, justify="left", font=ctk.CTkFont(size=12)
        ).pack(fill="x", padx=22, pady=(0, 16))

    def _build_settings(self, parent) -> None:
        card = self._card(parent)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self._section_heading(card, "Forge settings", "Control the length and character types.")

        ctk.CTkLabel(
            card, text="PASSWORD LENGTH", anchor="w",
            text_color=INK, font=ctk.CTkFont(size=12, weight="bold")
        ).pack(fill="x", padx=22)
        length_row = ctk.CTkFrame(card, fg_color="transparent")
        length_row.pack(fill="x", padx=20, pady=(8, 9))
        length_row.grid_columnconfigure(0, weight=1)
        self.length_slider = ctk.CTkSlider(
            length_row, from_=MIN_LENGTH, to=MAX_LENGTH,
            number_of_steps=MAX_LENGTH - MIN_LENGTH, progress_color=PURPLE,
            button_color=PURPLE, button_hover_color=PURPLE_HOVER,
            command=self._on_slider, height=20
        )
        self.length_slider.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.length_slider.set(DEFAULT_LENGTH)
        self.length_entry = ctk.CTkEntry(
            length_row, textvariable=self.numeric_length_var,
            width=58, height=36, corner_radius=10, justify="center",
            fg_color="#F7F7FD", text_color=INK, border_color=LINE
        )
        self.length_entry.grid(row=0, column=1)
        self.length_entry.bind("<Return>", self._on_length_entry)
        self.length_entry.bind("<FocusOut>", self._on_length_entry)
        self.length_hint = ctk.CTkLabel(
            card, text="", anchor="w", text_color=MUTED,
            font=ctk.CTkFont(size=12)
        )
        self.length_hint.pack(fill="x", padx=22, pady=(0, 18))

        ctk.CTkLabel(
            card, text="INCLUDE CHARACTERS", anchor="w", text_color=INK,
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(fill="x", padx=22, pady=(0, 8))
        for label, var, example in (
            ("Uppercase letters", self.uppercase_var, "A–Z"),
            ("Lowercase letters", self.lowercase_var, "a–z"),
            ("Numbers", self.digits_var, "0–9"),
            ("Symbols", self.symbols_var, "! @ # $"),
        ):
            line = ctk.CTkFrame(card, fg_color="transparent")
            line.pack(fill="x", padx=22, pady=5)
            ctk.CTkCheckBox(
                line, text=label, variable=var, width=190,
                text_color=INK, fg_color=PURPLE, hover_color=PURPLE_HOVER,
                checkmark_color="white", font=ctk.CTkFont(size=13)
            ).pack(side="left")
            ctk.CTkLabel(
                line, text=example, text_color=MUTED,
                font=ctk.CTkFont(size=12)
            ).pack(side="right")

        ctk.CTkFrame(card, height=1, fg_color=LINE).pack(fill="x", padx=22, pady=(14, 10))
        self._toggle_row(card, "Exclude lookalike characters", self.exclude_var, "0, O, o, 1, l, I")
        self._toggle_row(card, "Automatically copy generated password", self.auto_copy_var, "Can be turned off for privacy")
        ctk.CTkLabel(
            card, text="At least two character categories are required.",
            text_color=MUTED, font=ctk.CTkFont(size=11)
        ).pack(anchor="w", padx=22, pady=(15, 24))

    def _toggle_row(self, parent, title, variable, subtitle):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=22, pady=(5, 8))
        row.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            row, text=title, anchor="w", text_color=INK,
            wraplength=230, justify="left", font=ctk.CTkFont(size=12)
        ).grid(row=0, column=0, sticky="ew")
        ctk.CTkSwitch(
            row, text="", variable=variable, width=38,
            progress_color=PURPLE, button_color="white"
        ).grid(row=0, column=1, rowspan=2, sticky="e")
        ctk.CTkLabel(
            row, text=subtitle, text_color=MUTED,
            anchor="w", font=ctk.CTkFont(size=10)
        ).grid(row=1, column=0, sticky="ew")

    def _build_output(self, parent) -> None:
        card = self._card(parent)
        card.grid(row=0, column=0, sticky="ew")
        self._section_heading(card, "Your password", "Create something unique and hard to guess.")
        output = ctk.CTkFrame(card, fg_color="#F7F6FD", corner_radius=15)
        output.pack(fill="x", padx=22, pady=(2, 10))
        output.grid_columnconfigure(0, weight=1)
        self.password_entry = ctk.CTkEntry(
            output, textvariable=self.password_var,
            show="•", border_width=0, fg_color="transparent",
            text_color=INK, font=ctk.CTkFont(size=18, family="Consolas"),
            height=58, corner_radius=0
        )
        self.password_entry.grid(row=0, column=0, sticky="ew", padx=(13, 3), pady=5)
        self.password_entry.configure(state="readonly")
        self.toggle_button = ctk.CTkButton(
            output, text="Show", width=63, height=34, corner_radius=10,
            fg_color="#E8E6FA", hover_color="#DCD8F8", text_color=PURPLE,
            command=self._toggle_visibility
        )
        self.toggle_button.grid(row=0, column=1, padx=(2, 12))

        strength_box = ctk.CTkFrame(card, fg_color="transparent")
        strength_box.pack(fill="x", padx=22, pady=(6, 8))
        ctk.CTkLabel(
            strength_box, text="Estimated strength", text_color=INK,
            font=ctk.CTkFont(size=12)
        ).pack(side="left")
        self.strength_label = ctk.CTkLabel(
            strength_box, textvariable=self.strength_var,
            text_color=MUTED, font=ctk.CTkFont(size=12, weight="bold")
        )
        self.strength_label.pack(side="right")
        self.strength_bar = ctk.CTkProgressBar(
            card, progress_color=PURPLE, fg_color="#E8E6F3", height=9
        )
        self.strength_bar.pack(fill="x", padx=22, pady=(0, 18))
        self.strength_bar.set(0)

        buttons = ctk.CTkFrame(card, fg_color="transparent")
        buttons.pack(fill="x", padx=22, pady=(0, 12))
        buttons.grid_columnconfigure(0, weight=1)
        buttons.grid_columnconfigure(1, weight=1)
        ctk.CTkButton(
            buttons, text="Generate Password", height=45, corner_radius=13,
            fg_color=PURPLE, hover_color=PURPLE_HOVER,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._generate
        ).grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ctk.CTkButton(
            buttons, text="Copy Password", height=45, corner_radius=13,
            fg_color=BLUE, hover_color="#3266AD",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._copy
        ).grid(row=0, column=1, sticky="ew", padx=(5, 0))
        ctk.CTkLabel(
            card, textvariable=self.status_var, anchor="w", wraplength=460,
            justify="left", text_color=MUTED, font=ctk.CTkFont(size=12)
        ).pack(fill="x", padx=22, pady=(0, 22))

    def _build_history(self, parent) -> None:
        card = self._card(parent)
        card.grid(row=1, column=0, sticky="ew", pady=(15, 0))
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=22, pady=(16, 4))
        top.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            top, text="Recent creations", text_color=INK,
            font=ctk.CTkFont(size=19, weight="bold")
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(
            top, text="Clear history", width=110, height=30,
            corner_radius=9, fg_color="#F1F0FB", hover_color="#E4E0F8",
            text_color=PURPLE, command=self._clear_history
        ).grid(row=0, column=1, sticky="e")
        ctk.CTkLabel(
            card, text="Last five passwords; stored only until this app closes.",
            anchor="w", text_color=MUTED, font=ctk.CTkFont(size=12)
        ).pack(fill="x", padx=22, pady=(0, 8))
        reveal_line = ctk.CTkFrame(card, fg_color="transparent")
        reveal_line.pack(fill="x", padx=22)
        ctk.CTkSwitch(
            reveal_line, text="Reveal history", variable=self.show_history_var,
            command=self._render_history, progress_color=PURPLE,
            text_color=INK, font=ctk.CTkFont(size=12)
        ).pack(side="right")
        self.history_frame = ctk.CTkFrame(card, fg_color="transparent")
        self.history_frame.pack(fill="x", padx=22, pady=(8, 15))
        self._render_history()

    def _on_window_resize(self, event) -> None:
        if event.widget is not self:
            return
        width = max(670, min(1020, event.width - 115))
        if abs(width - self._header_width) >= 8:
            self._header_width = width
            self._header_image.configure(size=(width, 190))

    def _on_slider(self, value) -> None:
        value = int(round(float(value)))
        self.length_var.set(value)
        self.numeric_length_var.set(str(value))
        self._update_length_caption()

    def _update_length_caption(self) -> None:
        self.length_hint.configure(text=f"{self.length_var.get()} characters  •  Range: 8–64")

    def _on_length_entry(self, _event=None) -> None:
        try:
            number = int(self.numeric_length_var.get().strip())
            if not MIN_LENGTH <= number <= MAX_LENGTH:
                raise ValueError
        except ValueError:
            self.numeric_length_var.set(str(self.length_var.get()))
            self._status("Choose a whole number between 8 and 64.", error=True)
            return
        self.length_var.set(number)
        self.length_slider.set(number)
        self._update_length_caption()

    def _read_options(self) -> PasswordOptions:
        # Commit the numeric edit before reading the options.
        try:
            length = int(self.numeric_length_var.get().strip())
        except ValueError as exc:
            raise PasswordValidationError("Enter a valid whole-number length.") from exc
        return PasswordOptions(
            length=length,
            uppercase=self.uppercase_var.get(),
            lowercase=self.lowercase_var.get(),
            digits=self.digits_var.get(),
            symbols=self.symbols_var.get(),
            exclude_ambiguous=self.exclude_var.get(),
        )

    def _generate(self) -> None:
        try:
            options = self._read_options()
            password, strength = self.controller.generate(options)
        except (PasswordValidationError, ValueError) as exc:
            self._status(str(exc), error=True)
            return
        self.length_var.set(options.length)
        self.length_slider.set(options.length)
        self._update_length_caption()
        self.password_entry.configure(state="normal")
        self.password_var.set(password)
        self.password_entry.configure(state="readonly")
        self.strength_var.set(strength.label)
        self.strength_label.configure(text_color={"Weak":"#BE7049", "Medium":"#B08B29", "Strong":GREEN}[strength.label])
        self.strength_bar.set(strength.progress)
        self.strength_bar.configure(progress_color={"Weak":"#D88D70", "Medium":"#DBB75B", "Strong":GREEN}[strength.label])
        self._render_history()
        if self.auto_copy_var.get():
            self._copy()
        else:
            self._status("Password created. Keep it private and store it safely.")

    def _toggle_visibility(self) -> None:
        visible = not self.show_password_var.get()
        self.show_password_var.set(visible)
        self.password_entry.configure(show="" if visible else "•")
        self.toggle_button.configure(text="Hide" if visible else "Show")

    def _copy(self) -> None:
        password = self.controller.current_password
        if not password:
            self._status("Generate a password before copying.", error=True)
            return
        result = copy_to_clipboard(password, self)
        self._status(result.message, error=not result.success)

    def _status(self, message: str, *, error: bool = False) -> None:
        self.status_var.set(message)
        # The label is kept in muted text to reduce alarm for input errors.

    def _render_history(self) -> None:
        for child in self.history_frame.winfo_children():
            child.destroy()
        if not self.controller.history:
            ctk.CTkLabel(
                self.history_frame, text="No passwords generated yet.",
                anchor="w", text_color=MUTED
            ).pack(fill="x", pady=7)
            return
        reveal = self.show_history_var.get()
        for index, password in enumerate(self.controller.history, start=1):
            item = ctk.CTkFrame(self.history_frame, fg_color="#F8F7FD", corner_radius=10)
            item.pack(fill="x", pady=3)
            item.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(
                item, text=f"{index:02}", text_color=PURPLE,
                font=ctk.CTkFont(size=12, weight="bold"), width=30
            ).grid(row=0, column=0, padx=(9, 2), pady=9)
            value = password if reveal else ("•" * min(len(password), 24))
            ctk.CTkLabel(
                item, text=value, text_color=INK, anchor="w",
                font=ctk.CTkFont(size=12, family="Consolas")
            ).grid(row=0, column=1, sticky="w", padx=3)
            ctk.CTkButton(
                item, text="Copy", width=52, height=28, corner_radius=8,
                fg_color="#ECE9FC", hover_color="#DCD8F8", text_color=PURPLE,
                command=lambda p=password: self._copy_history_item(p)
            ).grid(row=0, column=2, padx=(4, 9))

    def _copy_history_item(self, password: str) -> None:
        result = copy_to_clipboard(password, self)
        self._status(result.message, error=not result.success)

    def _clear_history(self) -> None:
        self.controller.clear_history()
        self._render_history()
        self._status("Recent creations cleared from the app's memory.")

    def _on_close(self) -> None:
        self.password_var.set("")
        self.controller.close()
        self.destroy()
