"""BMI Insight desktop entry point; calculations and storage remain offline."""
import sys


def main() -> int:
    try:
        from app.ui.bootstrap import create_controller
        from app.ui.window import BMIWindow
        from app.database.errors import DatabaseError
    except ImportError:
        print('Desktop dependencies are missing. Run: python -m pip install -r requirements.txt',file=sys.stderr)
        return 1
    try:
        controller = create_controller()
    except DatabaseError as error:
        # A Tk error dialog if supported, otherwise a safe console explanation.
        try:
            import tkinter as tk
            from tkinter import messagebox
            root=tk.Tk();root.withdraw()
            messagebox.showerror('BMI Insight — Storage unavailable',str(error),parent=root)
            root.destroy()
        except tk.TclError:
            print(str(error),file=sys.stderr)
        return 1
    import tkinter as tk
    try:
        application = BMIWindow(controller)
    except tk.TclError:
        print('A graphical desktop with Tk support is required to launch BMI Insight.',file=sys.stderr)
        return 1
    application.mainloop()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
