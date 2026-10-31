from app.core.password_generator import PasswordOptions
from app.core.strength import estimate_strength


def test_strength_increases_with_length():
    low = estimate_strength(PasswordOptions(length=8))
    high = estimate_strength(PasswordOptions(length=32))
    assert low.entropy_bits < high.entropy_bits
    assert low.progress <= high.progress


def test_strength_labels():
    short = estimate_strength(PasswordOptions(length=8, uppercase=False, symbols=False))
    long = estimate_strength(PasswordOptions(length=64))
    assert short.label == "Weak"
    assert long.label == "Strong"


def test_progress_bounded():
    assert 0 <= estimate_strength(PasswordOptions(length=64)).progress <= 1
