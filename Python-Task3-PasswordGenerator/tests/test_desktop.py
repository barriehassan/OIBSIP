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
