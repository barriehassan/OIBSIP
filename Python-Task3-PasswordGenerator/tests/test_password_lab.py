import dataclasses
import sys
from unittest.mock import Mock
import pytest
import app._vendor.zxcvbn as zxcvbn
from app.core.password_lab import evaluate_password, generate_replacement
from app.core.password_generator import PasswordOptions, selected_character_sets


@pytest.mark.parametrize('value', ['password','P@ssword1!','12345678','qwerty123','abcabcabcabc','aaaaaaaaaaaa'])
def test_predictable_passwords_are_not_strong(value):
    result=evaluate_password(value)
    assert result.score <= 2
    assert result.issues and result.recommendations


def test_policy_is_not_strength():
    result=evaluate_password('P@ssword1!')
    assert result.policy_compliant and result.score < 3
    result=evaluate_password('velvetcanyonorchidbasilcobalt')
    assert not result.policy_compliant and result.score >= 3


def test_composition_is_descriptive(monkeypatch):
    monkeypatch.setattr(zxcvbn,'zxcvbn',lambda value:{'score':1,'sequence':[]})
    result=evaluate_password('LongMixedPasswordWith123!')
    assert result.composition == ('uppercase','lowercase','digits','symbols')
    assert result.score == 1


@pytest.mark.parametrize('value',['',' ','éééééééé','🔐'*12,'two words with spaces'])
def test_unicode_and_whitespace(value):
    result=evaluate_password(value)
    assert result.length == len(value)
    assert result.score is None or 0<=result.score<=4


def test_no_partial_score_or_work_on_oversized_inputs(monkeypatch):
    estimator=Mock(side_effect=AssertionError('Must not be called'))
    monkeypatch.setattr(zxcvbn,'zxcvbn',estimator)
    for value in ('','x'*73,'x'*100000):
        assert evaluate_password(value).score is None
    estimator.assert_not_called()


def test_maximum_is_assessed_without_truncation(monkeypatch):
    estimator=Mock(return_value={'score':3,'sequence':[]})
    monkeypatch.setattr(zxcvbn,'zxcvbn',estimator)
    value='Z8!r'*18
    assert evaluate_password(value).score == 3
    estimator.assert_called_once_with(value)


def test_estimator_error_privacy(monkeypatch,caplog,capsys):
    secret='PRIVATE-SENTINEL-XY9!'
    def broken(value):raise RuntimeError(value)
    monkeypatch.setattr(zxcvbn,'zxcvbn',broken)
    result=evaluate_password(secret)
    assert result.score is None and secret not in repr(result)
    assert not caplog.records
    captured=capsys.readouterr()
    assert captured.out == captured.err == ''


def test_no_raw_tokens_or_feedback_in_result(monkeypatch):
    secret='PRIVATE-SENTINEL-XY9!'
    monkeypatch.setattr(zxcvbn,'zxcvbn',lambda value:{'password':value,'score':1,
        'feedback':{'warning':value},'sequence':[{'pattern':'dictionary','token':value}]})
    result=evaluate_password(secret)
    assert secret not in repr(dataclasses.asdict(result))
    assert 'Common' in ' '.join(result.issues)


def test_missing_dependency_is_unavailable_not_strong(monkeypatch):
    monkeypatch.setitem(sys.modules,'app._vendor.zxcvbn',None)
    result=evaluate_password('SampleForUnavailable98!')
    assert result.rating == 'Setup needed' and result.score is None


def test_secure_replacement_satisfies_existing_rules():
    sets=selected_character_sets(PasswordOptions())
    for _ in range(10):
        value=generate_replacement()
        assert len(value)==18
        assert set(value)<=set(''.join(sets.values()))
        assert all(set(value)&set(chars) for chars in sets.values())


@pytest.mark.parametrize('pattern,fragment',[('repeat','Repeated'),('sequence','sequence'),
    ('spatial','keyboard'),('date','Date'),('dictionary','Common')])
def test_specific_safe_findings(monkeypatch,pattern,fragment):
    monkeypatch.setattr(zxcvbn,'zxcvbn',lambda value:{'score':1,'sequence':[{'pattern':pattern,'token':value}]})
    assert fragment in ' '.join(evaluate_password('SamplePassword93!').issues)


def test_assessment_needs_no_network(monkeypatch):
    import socket
    def blocked(*args,**kwargs):
        raise AssertionError('Network must not be used')
    monkeypatch.setattr(socket.socket,'connect',blocked)
    monkeypatch.setattr(socket,'create_connection',blocked)
    result=evaluate_password('OfflineSampleForTest47!')
    assert result.score is not None


def test_estimator_works_without_site_packages():
    """Reproduce the laptop case: no separately installed zxcvbn dependency."""
    import subprocess
    from pathlib import Path
    project=Path(__file__).resolve().parents[1]
    script="""
from app.core.password_lab import evaluate_password
import importlib.util
assert importlib.util.find_spec('zxcvbn') is None
weak=evaluate_password('password')
strong=evaluate_password('V8!xQ2@kM9#rT5$pL7')
assert weak.score == 0
assert strong.score == 4
print('Offline estimator passed')
"""
    # -S disables site-packages; the application is loaded from this directory.
    result=subprocess.run([sys.executable,'-S','-c',script],cwd=project,
        capture_output=True,text=True,timeout=10)
    assert result.returncode == 0, 'Standalone estimator verification failed'
    assert result.stdout.strip() == 'Offline estimator passed'
