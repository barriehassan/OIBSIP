# Task 04 — Password Lab implementation report

## Architecture inspected

The current mountain-glass version uses standard Tk and Pillow, rather than CustomTkinter. `app/ui/window.py` owns navigation and the canvas shell; `glass.py` composites the mountain panels. `PasswordController` owns generator output and five-entry history. `password_generator.py` uses `secrets` with rejection sampling. Existing `strength.py` estimates randomly generated strings from length/alphabet size; that calculation is intentionally unchanged and is not used to grade manual input.

## Implementation

A separate `PasswordLabView` owns transient input, visibility, debounced analysis, feedback, and cleanup. `app/core/password_lab.py` provides an independent assessment service and secure replacement function. The new page reuses the existing background, cards, drawing helpers, fonts, and accent colors. Findings are displayed in a word-wrapped, keyboard/mouse-scrollable text region.

Input is masked by default. A 180 ms debounce avoids analyzing every keystroke, cancels previous work, and reads only current input. Clear, navigation to another item, About, and application close cancel pending analysis and clear the field. Escape masks it. Lab does not alter the generator output, selected settings, five-entry history, or clipboard. Generator automatic-copy controls are hidden while in Lab. Ctrl+G generates an independent Lab replacement, never a suffix transformation.

## Methodology and limitations

- Local zxcvbn-python 4.5.0 (one added dependency, bounded `>=4.4,<5`) estimates guessability using dictionary/password, repeat, sequence, keyboard, date and other patterns. Scores 0–4 map to Very weak, Weak, Fair, Good, Strong. The five-step visual indicator represents that score; it is not a probability of safety.
- Only fixed issue descriptions leave the estimator adapter. Raw results include passwords and matched tokens, so they are discarded rather than retained or displayed. Estimator feedback/error messages are not forwarded. Exceptions produce an Unavailable state with no score; they are not printed or logged.
- Composition is descriptive. Reusing `validate_settings` reports generator compatibility (8–64 characters and at least two categories) separately. Passing these rules does not imply strength. A long lowercase password can estimate well yet fail the generator policy.
- Length is counted as Python Unicode code points, with no stripping or normalization. Analysis is limited to 72 code points as recommended by the estimator to bound work. Larger inputs are not truncated or assigned a partial score. The UI buffer accepts at most 4096 characters.
- Short length (under 16), repeated runs and estimator pattern classes receive specific fixed suggestions. No unsupported crack-time claims are shown. Recommendations encourage longer unique passwords, avoiding familiar patterns, using a password manager, and MFA.
- The dictionary/model is incomplete and language dependent. Unrecognized words, cultural references, or personal information may be rated too highly. A strong estimate is not proof of randomness or safety. No breach database is consulted and no claim of never having been compromised is made.
- Fresh replacements use existing `generate_password(PasswordOptions())`, with OS-backed randomness and the existing default length of 18. They are not derived from input. Optional memorable-passphrase generation was left out to avoid adding a word-list dependency or a weak custom vocabulary.

## Privacy boundary

Manual input is not logged, written to disk, sent to a service, or added to history. Lab does not automatically copy it. Selection export is disabled to avoid X11 primary-selection exposure. Python/Tk and the estimator temporarily hold strings in memory; clearing drops application references but cannot promise secure memory zeroization. Explicit OS clipboard use, screenshots, OS-level monitoring, swap, or external debugging are outside this application's memory-cleanup guarantees.

## Validation

Before changes: **46 passed, 1 desktop test skipped, 77 subchecks passed**.

After changes, with desktop tests enabled under Linux virtual display and Tk 9.0.4: **73 passed, 77 subchecks passed**.

Tests cover common/leet passwords, keyboard/sequential and repeated patterns, Unicode/whitespace, empty/oversized input, the full 72-character boundary, descriptive composition, policy/strength separation, safe failures and missing dependencies, no raw password/token output, no network connection, secure replacement constraints, actual debounce, show/hide, navigation/About/close cleanup, history isolation, no auto-copy, and window resize. The existing generator suite still passes. Secure generator, controller, validation, strength and clipboard source files are byte-for-byte unchanged from the pre-task baseline.

Visual inspection used disposable sample data at 1440×900 and 1000×680.

Commands from the project folder:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Real-window tests are opt-in. On Windows PowerShell:

```powershell
$env:RUN_DESKTOP_TESTS = "1"
python -m pytest -q
```

On Linux/macOS with a graphical session:

```bash
RUN_DESKTOP_TESTS=1 python -m pytest -q
```

## Remaining manual checks

Check Windows/macOS fonts, high-DPI scaling, keyboard navigation, paste and field selection, scrolling of long recommendations, Show/Hide/Clear, and switching views during typing on the target device. Confirm the generator's normal clipboard behavior still works on that OS. Windows/macOS have not been tested in this cloud environment.

## Changed files

New:

- `app/core/password_lab.py` — assessment, safe feedback and independent replacements.
- `app/ui/password_lab.py` — transient Lab view and cleanup.
- `tests/test_password_lab.py` — estimator and privacy tests.
- `docs/PASSWORD_LAB.md` — this report.

Updated:

- `app/ui/window.py` — sidebar, view routing, keyboard handling and lifecycle hooks.
- `requirements.txt` — local estimator dependency.
- `tests/test_desktop.py` — Lab lifecycle and generator-isolation regression test.
- `README.md` — setup and usage.
- `docs/VALIDATION.md` — Task 04 validation record.

Task 04 was implemented and tested before publication. Committing and pushing this work requires explicit user approval, which was subsequently provided.

## Estimator source

[zxcvbn-python project and API guidance](https://github.com/dwolfhub/zxcvbn-python). Its documented 72-character default is preserved; bundled dictionaries run locally.
