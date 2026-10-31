"""Local human-password assessment. Results never retain input or matched tokens."""
from dataclasses import dataclass
import re

from app.core.validator import validate_settings, PasswordValidationError
from app.core.password_generator import PasswordOptions, generate_password

MAX_ASSESSMENT_LENGTH = 72
LABELS = ('Very weak', 'Weak', 'Fair', 'Good', 'Strong')


@dataclass(frozen=True)
class LabAssessment:
    length: int
    composition: tuple[str, ...]
    policy_compliant: bool
    policy_notes: tuple[str, ...]
    score: int | None
    rating: str
    issues: tuple[str, ...]
    recommendations: tuple[str, ...]

    @property
    def progress(self):
        return 0 if self.score is None else (self.score + 1) / 5


def evaluate_password(password: str) -> LabAssessment:
    """Assess at most 72 code points; never expose estimator dictionaries/errors.

    Generator policy is compatibility feedback, not a security recommendation.
    Character classes describe input; only zxcvbn supplies the strength score.
    """
    length = len(password)
    if not password:
        return LabAssessment(0, (), False, ('Enter a password to check the generator policy.',),
            None, 'Not evaluated', (), ('Use a unique password for each account.',))
    if length > MAX_ASSESSMENT_LENGTH:
        return LabAssessment(length, (), False, ('Outside the generator range of 8 to 64 characters.',),
            None, 'Not evaluated', ('Local analysis is limited to 72 characters; no partial score is shown.',),
            ('Use a password manager; this tool cannot assess longer inputs.',))
    categories = {
        'uppercase': any(c.isupper() for c in password),
        'lowercase': any(c.islower() for c in password),
        'digits': any(c.isdecimal() for c in password),
        'symbols': any(not c.isalnum() and not c.isspace() for c in password),
    }
    composition = tuple(name for name, present in categories.items() if present)
    if any(c.isspace() for c in password):
        composition += ('whitespace',)
    notes = []
    try:
        validate_settings(length, categories)
    except PasswordValidationError:
        if not 8 <= length <= 64:
            notes.append('Generator policy: length must be 8 to 64 characters.')
        if sum(categories.values()) < 2:
            notes.append('Generator policy: at least two character categories required.')
    issues, recommendations = [], []
    if length < 16:
        issues.append('Shorter than 16 characters.')
        recommendations.append('Prefer a longer unique password or randomly chosen passphrase.')
    if re.search(r'(.)\1{2,}', password, flags=re.DOTALL):
        issues.append('Repeated characters detected.')
    try:
        # Bundled estimator avoids interpreter/pip mismatches and works offline.
        from app._vendor.zxcvbn import zxcvbn
        raw = zxcvbn(password)
        score = int(raw['score'])
        if not 0 <= score <= 4:
            raise ValueError('Invalid estimator score')
        patterns = {match.get('pattern') for match in raw.get('sequence', ())}
        # Only fixed descriptions leave this boundary: no tokens, raw feedback,
        # passwords, guesses, or exception messages are retained in the result.
        if 'repeat' in patterns and 'Repeated characters detected.' not in issues:
            issues.append('Repeated blocks or characters detected.')
        if patterns & {'sequence', 'spatial'}:
            issues.append('Predictable sequence or keyboard pattern detected.')
        if 'dictionary' in patterns:
            issues.append('Common words, names, or password patterns detected.')
        if patterns & {'date', 'regex'}:
            issues.append('Date or year-like pattern detected.')
        del raw
    except ImportError:
        return LabAssessment(length, composition, not notes, tuple(notes), None,
            'Setup needed', tuple(issues + ['Bundled estimator files are missing or cannot load.']),
            ('Update the complete project folder with git pull, then restart Password Forge.',))
    except Exception:
        # Estimator errors can include user input. Never propagate or log them.
        return LabAssessment(length, composition, not notes, tuple(notes), None,
            'Unavailable', tuple(issues + ['Strength estimator unavailable; no score assigned.']),
            ('Clear the field and retry, or restart the app. Generation still works independently.',))
    if any('Repeated' in issue for issue in issues):
        recommendations.append('Avoid repeating characters or blocks.')
    if patterns & {'sequence', 'spatial', 'date', 'regex', 'dictionary'}:
        recommendations.append('Avoid names, dates, keyboard walks, and familiar phrases.')
    if score < 3:
        recommendations.append('Generate a fresh random replacement instead of adding predictable suffixes.')
    if not issues:
        issues.append('No listed pattern flagged; this is not proof of security.')
    recommendations.append('Keep it unique, store it in a password manager, and enable MFA.')
    return LabAssessment(length, composition, not notes, tuple(notes), score,
        LABELS[score], tuple(issues), tuple(dict.fromkeys(recommendations)))


def generate_replacement() -> str:
    """Create an independent secure password; no manual input or history access."""
    return generate_password(PasswordOptions())
