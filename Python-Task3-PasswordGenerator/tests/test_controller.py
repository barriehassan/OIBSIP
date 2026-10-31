from app.core.password_generator import PasswordOptions
from app.ui.controller import PasswordController


def test_history_bounded():
    app = PasswordController()
    for _ in range(12):
        app.generate(PasswordOptions())
    assert len(app.history) == 5
    assert app.history[0] == app.current_password


def test_clear_history():
    app = PasswordController()
    app.generate(PasswordOptions())
    app.clear_history()
    assert not app.history


def test_close_clears_sensitive_data():
    app = PasswordController()
    app.generate(PasswordOptions())
    app.close()
    assert not app.current_password
    assert not app.history


def test_different_history_capacity():
    app = PasswordController(max_history=2)
    for _ in range(4):
        app.generate(PasswordOptions())
    assert len(app.history) == 2


def test_invalid_history_capacity():
    try:
        PasswordController(0)
    except ValueError:
        pass
    else:
        assert False
