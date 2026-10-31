"""Opt-in real-window checks: RUN_DESKTOP_TESTS=1 python -m pytest tests/test_desktop.py."""
import os
import pytest

pytestmark = pytest.mark.skipif(os.environ.get('RUN_DESKTOP_TESTS') != '1', reason='Opt-in desktop display required')


def test_window_controls_and_persistent_entries():
    from app.ui.window import PasswordForgeApp
    app = PasswordForgeApp()
    errors = []
    app.report_callback_exception = lambda *error: errors.append(error)
    try:
        app.update()
        app._draw(1280, 800)
        app.update()
        for _ in range(6):
            app._generate()
        assert len(app.controller.history) == 5
        assert len(app.controller.current_password) == 18
        assert not app.show_password_var.get()
        app._toggle_visibility()
        assert app.password_entry.cget('show') == ''
        app._hide()
        app._slider(677)
        app._generate()
        assert len(app.controller.current_password) == 64
        previous = app.controller.current_password
        app.numeric_length_var.set('7')
        app._generate()
        assert app.controller.current_password == previous
        app.numeric_length_var.set('18')
        app._on_length_entry()
        app.geometry('1000x680')
        app.update()
        app._draw(1000, 680)
        app.update()
        # Redrawing must preserve embedded native input widgets.
        assert app.password_entry.winfo_ismapped()
        assert app.length_entry.winfo_ismapped()
        assert app.password_entry.get() == previous
        app._clear_history()
        assert not app.controller.history
        assert not errors
    finally:
        app._on_close()


def test_lab_lifecycle_and_generator_isolation(monkeypatch):
    from app.ui.window import PasswordForgeApp
    import app.ui.window as window
    app=PasswordForgeApp()
    errors=[]
    app.report_callback_exception=lambda *error:errors.append(error)
    try:
        app.update()
        app._generate()
        original=app.controller.current_password
        history=list(app.controller.history)
        app.auto_copy_var.set(True)
        copied=[]
        monkeypatch.setattr(window,'copy_to_clipboard',lambda *args:copied.append(args))
        app._navigate('Password Lab')
        assert app.lab.entry.winfo_exists()
        app.lab.value.set('P@ssword1!')
        app.after(250, app.quit)
        app.mainloop()  # exercise the real debounce callback
        app.update()
        assert app.lab.assessment.score < 3
        assert app.lab.entry.winfo_ismapped()
        assert not app.password_entry.winfo_ismapped()
        app.lab.toggle()
        assert app.lab.entry.cget('show') == ''
        app._hide()
        assert app.lab.entry.cget('show') == '*'
        app.lab.replace()
        assert len(app.lab.value.get()) == 18
        assert app.controller.current_password == original
        assert list(app.controller.history) == history
        assert not copied  # Lab bypasses auto-copy entirely
        app.lab.value.set('PendingValue93!')
        app._navigate('Generate')
        app.update()
        assert app.lab.value.get() == ''
        assert app.lab.assessment.score is None
        assert app.lab.pending is None
        assert not app.lab.entry.winfo_ismapped()
        assert app.password_entry.winfo_ismapped()
        assert list(app.controller.history) == history
        app._navigate('Password Lab')
        app.lab.value.set('ClearValue93!')
        app.lab._clear_clicked()
        assert app.lab.value.get() == ''
        assert app.lab.pending is None
        # About is another navigation action and must clear Lab too.
        monkeypatch.setattr(window.messagebox,'showinfo',lambda *args,**kwargs:None)
        app.lab.value.set('AboutValue93!')
        app._navigate('About')
        assert app.lab.value.get() == ''
        app.geometry('1000x680')
        app.update()
        app._draw(1000,680)
        assert not errors
    finally:
        app._on_close()
