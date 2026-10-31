import itertools
import string

import pytest

from app.core.password_generator import (
    AMBIGUOUS_CHARACTERS, CHARACTER_SETS, PasswordOptions,
    generate_password, selected_character_sets,
)
from app.core.validator import PasswordValidationError


@pytest.mark.parametrize("length", [8, 9, 12, 18, 32, 64])
def test_password_length(length):
    assert len(generate_password(PasswordOptions(length=length))) == length


@pytest.mark.parametrize("combination", list(itertools.combinations(CHARACTER_SETS, 2)))
def test_two_categories_are_present(combination):
    flags = {name: name in combination for name in CHARACTER_SETS}
    opts = PasswordOptions(length=8, **flags)
    output = generate_password(opts)
    sets = selected_character_sets(opts)
    assert set(output) <= set("".join(sets.values()))
    assert all(any(char in alphabet for char in output) for alphabet in sets.values())


@pytest.mark.parametrize("length", [7, 65, -1, 8.5, True, "12"])
def test_invalid_length(length):
    with pytest.raises(PasswordValidationError):
        generate_password(PasswordOptions(length=length))


def test_one_category_invalid():
    with pytest.raises(PasswordValidationError, match="at least two"):
        generate_password(PasswordOptions(uppercase=True, lowercase=False, digits=False, symbols=False))


def test_no_categories_invalid():
    with pytest.raises(PasswordValidationError):
        generate_password(PasswordOptions(uppercase=False, lowercase=False, digits=False, symbols=False))


def test_ambiguous_characters_excluded():
    for _ in range(100):
        assert not set(generate_password()) & AMBIGUOUS_CHARACTERS


def test_symbols_are_not_punctuation_only():
    output = generate_password(PasswordOptions(length=64))
    assert any(char in CHARACTER_SETS["symbols"] for char in output)


def test_ambiguous_can_be_enabled():
    options = PasswordOptions(exclude_ambiguous=False)
    assert "0" in selected_character_sets(options)["digits"]


def test_distinct_generations():
    passwords = {generate_password() for _ in range(40)}
    assert len(passwords) == 40


def test_all_categories_guaranteed():
    for _ in range(100):
        value = generate_password(PasswordOptions(length=8, exclude_ambiguous=False))
        assert any(c in string.ascii_uppercase for c in value)
        assert any(c in string.ascii_lowercase for c in value)
        assert any(c in string.digits for c in value)
        assert any(c in CHARACTER_SETS["symbols"] for c in value)
