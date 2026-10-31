"""Simple UI strength estimate for randomly generated passwords.

This estimate is informational, not a security certification or breach check.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.core.password_generator import PasswordOptions, selected_character_sets


@dataclass(frozen=True)
class StrengthResult:
    label: str
    entropy_bits: float
    progress: float


def estimate_strength(options: PasswordOptions) -> StrengthResult:
    sets = selected_character_sets(options)
    alphabet_size = len(set("".join(sets.values())))
    # Upper bound: category constraints reduce the number of valid strings.
    bits = options.length * math.log2(alphabet_size)
    if bits < 55:
        label = "Weak"
    elif bits < 90:
        label = "Medium"
    else:
        label = "Strong"
    return StrengthResult(label=label, entropy_bits=bits, progress=min(bits / 128, 1))
