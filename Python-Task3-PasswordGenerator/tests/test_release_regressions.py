"""Release checks for failure paths and security-sensitive edge cases."""
from unittest.mock import Mock
import pytest
from PIL import Image

from app.core.password_generator import PasswordOptions, generate_password
from app.core.validator import PasswordValidationError
from app.services.clipboard import copy_to_clipboard
from app.ui.controller import PasswordController
from app.ui import background


@pytest.mark.parametrize('length', [None,False,float('nan'),float('inf'),7.99,64.01])
def test_non_integral_lengths_are_rejected(length):
    with pytest.raises(PasswordValidationError):
        generate_password(PasswordOptions(length=length))


def test_generator_rejects_candidate_missing_required_categories(monkeypatch):
    import app.core.password_generator as generator
    choices=iter('AAAAAAAA'+'Aa2!Bb3?')
    choose=Mock(side_effect=lambda alphabet:next(choices))
    monkeypatch.setattr(generator.secrets,'choice',choose)
    assert generate_password(PasswordOptions(length=8)) == 'Aa2!Bb3?'
    assert choose.call_count == 16


def test_both_clipboard_adapters_can_fail_without_exposing_input(monkeypatch,capsys,caplog):
    import pyperclip
    sentinel='DISPOSABLE-CLIPBOARD-TEST'
    def fail(*args):raise RuntimeError(sentinel)
    monkeypatch.setattr(pyperclip,'copy',fail)
    class BrokenRoot:
        clipboard_clear=staticmethod(fail)
    result=copy_to_clipboard(sentinel,BrokenRoot())
    assert not result.success
    assert sentinel not in result.message
    captured=capsys.readouterr()
    assert captured.out == captured.err == ''
    assert not caplog.records


def test_successful_clipboard_copy_uses_complete_value(monkeypatch):
    import pyperclip
    copied=[]
    monkeypatch.setattr(pyperclip,'copy',copied.append)
    value='DisposableTestValue'*4
    assert copy_to_clipboard(value).success
    assert copied == [value]


def test_history_is_per_session_and_clear_keeps_current_output():
    first,second=PasswordController(),PasswordController()
    current,_=first.generate(PasswordOptions())
    assert not second.history and not second.current_password
    first.clear_history()
    assert first.current_password == current
    assert not first.history
    first.close()
    assert first.current_password == ''


def test_corrupt_custom_artwork_falls_back(monkeypatch,tmp_path):
    monkeypatch.setattr(background,'BACKGROUND_FOLDER',tmp_path)
    (tmp_path/'mountain.png').write_bytes(b'not an image')
    image=background.build_background(200,120)
    assert image.size == (200,120)
    assert image.getpixel((0,0)) != image.getpixel((100,119))


def test_valid_custom_artwork_is_used_and_fitted(monkeypatch,tmp_path):
    monkeypatch.setattr(background,'BACKGROUND_FOLDER',tmp_path)
    Image.new('RGB',(400,80),(120,30,200)).save(tmp_path/'mountain.png')
    image=background.build_background(200,120)
    assert image.size == (200,120)
    assert image.getpixel((100,60)) == (120,30,200)
