"""Launch with: py -3 main.py. Importing this file does not launch a window."""

import sys


def main():
    try:
        import tkinter

        if tkinter.TkVersion >= 9:
            print(
                "SkyCast requires Tcl/Tk 8.6 for reliable CustomTkinter rendering. Use Python 3.12 with Tcl/Tk enabled.",
                file=sys.stderr,
            )
            return 1
        from app.ui.window import SkyCastWindow

        app = SkyCastWindow()
    except ImportError as exc:
        print(
            "SkyCast could not start. Install requirements.txt with this Python interpreter.",
            file=sys.stderr,
        )
        print(f"Missing dependency: {exc.name}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(
            "SkyCast could not initialize its desktop window. Check your display and Tk installation.",
            file=sys.stderr,
        )
        print(f"Diagnostic: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
