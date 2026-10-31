"""NOMOLI FORGE — Password Forge desktop application."""


def main() -> None:
    try:
        from app.ui.window import PasswordForgeApp
        from tkinter import TclError
    except ImportError as exc:
        raise SystemExit(
            "Missing desktop dependencies or Tk. Install requirements.txt with "
            "the same Python interpreter. For offline use: python -m app.cli"
        ) from exc
    try:
        app = PasswordForgeApp()
    except TclError as exc:
        raise SystemExit(
            "Could not initialize the desktop interface. Use a local graphical "
            "session and a working Python/Tk installation "
            "(Tk 8.6 or 9). CLI alternative: python -m app.cli"
        ) from exc
    app.mainloop()


if __name__ == "__main__":
    main()
