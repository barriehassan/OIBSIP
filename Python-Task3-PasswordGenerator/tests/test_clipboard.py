from app.services.clipboard import ClipboardResult, copy_to_clipboard


def test_clipboard_result_fields():
    result = ClipboardResult(True, "ok")
    assert result.success and result.message == "ok"


def test_clipboard_fails_gracefully(monkeypatch):
    import pyperclip

    def fail(value):
        raise RuntimeError("unavailable")

    monkeypatch.setattr(pyperclip, "copy", fail)
    result = copy_to_clipboard("temporary")
    assert not result.success
    assert "unavailable" in result.message.lower()


def test_fallback_to_tk_clipboard(monkeypatch):
    import pyperclip
    monkeypatch.setattr(pyperclip, "copy", lambda value: (_ for _ in ()).throw(RuntimeError("blocked")))

    class Root:
        value = None
        def clipboard_clear(self):
            self.value = None
        def clipboard_append(self, text):
            self.value = text
        def update_idletasks(self):
            pass

    root = Root()
    result = copy_to_clipboard("secret", root)
    assert result.success
    assert root.value == "secret"
