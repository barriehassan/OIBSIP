def test_tk9_launch_has_actionable_error(monkeypatch, capsys):
    import tkinter
    import main

    monkeypatch.setattr(tkinter, "TkVersion", 9.0)
    assert main.main() == 1
    assert "Tcl/Tk 8.6" in capsys.readouterr().err
