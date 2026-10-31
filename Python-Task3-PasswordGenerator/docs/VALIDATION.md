# Validation record — Task 05 release candidate

Date: **31 October 2026**. Base repository commit: `4ee00f48c828cd47123ce9d10a356c61dc3267e5`. Task 05 was tested as an uncommitted candidate; the user subsequently approved commit and push.

## Environment and exact results

Linux cloud with Python **3.12.14**, Tk **9.0.4**, Pillow **12.3.0**, pyperclip **1.11.0**, pytest **9.2.0**, bundled zxcvbn **4.5.0**.

| Executed run | Passing tests | Failing tests | Skipped tests | Collection errors | Passing subchecks |
| --- | ---: | ---: | ---: | ---: | ---: |
| Pre-Task-05 baseline, headless | 72 | 0 | 2 | 0 | 77 |
| Final candidate, headless | 84 | 0 | 3 | 0 | 77 |
| Final candidate, desktop enabled | 87 | 0 | 0 | 0 | 77 |
| Portable unittest suite, separately executed | 7 | 0 | 0 | 0 | Not counted separately |

The 77 pytest subchecks are **additional case checks inside test items** and are not added to the test-item total. Desktop tests open real Tk windows and are opt-in. Their headless skips are deliberate.

A parent-directory test invocation initially produced nine import/collection errors. The new project pytest.ini supplies the application import path, and the final parent-directory invocation passes. No failure is being counted as a passing test.

## Reproduce on Windows

From the project folder, install the test dependencies and run the ordinary suite:

```powershell
py -3 -m pip install --user -r requirements-dev.txt
py -3 -m pytest -q
```

To include all three desktop tests:

```powershell
$env:RUN_DESKTOP_TESTS = "1"
py -3 -m pytest -q
Remove-Item Env:RUN_DESKTOP_TESTS
```

Portable checks:

```powershell
py -3 -m unittest discover -s tests -p test_portable.py -v
```

Use the virtual environment's interpreter for all commands instead if dependencies were installed there.

## What was verified

- Secure generation, every allowed category combination, lookalike filtering, boundary lengths, invalid numeric types, mandatory-category rejection and bounded state.
- Generator estimates and local zxcvbn assessments, policy/strength separation, predictable patterns, Unicode/whitespace, empty/oversized input and exact 72-character handling.
- No installed estimator needed: a subprocess with site-packages disabled evaluates weak and strong fixtures.
- Network-disabled evaluation; sanitized estimator failures; no matched tokens or input in assessment results.
- Per-session history, newest-first five-entry limit, clear/close behavior, unchanged output after invalid generation and complete clipboard values.
- Clipboard fallback and simultaneous adapter failure without crashes or input disclosure.
- Missing, corrupt and valid custom artwork; glass compositing.
- Real native Lab typing/debounce, navigation/About/close cleanup, no history/auto-copy side effects, persistent input widgets, resizing, and initial laptop-window fit.

## Entry point and visual QA

The actual `main.main()` desktop entry point was executed with a 1366×768 virtual display. Initial client size was 1280×680 and fit within the display, allowing space for title bar/taskbar. Generator, Settings/History shortcuts, Lab, masking, replacement and cleanup were exercised. Four actual screenshots were inspected at 1280×680 and 1000×680 and stored in screenshots/.

The screenshots use Linux/Tk 9 and disposable data. Generated passwords/history are masked. They are not Windows evidence. The author reported earlier manual Windows launch/use; final candidate behavior at the laptop's Windows version and DPI still needs the manual checklist.

## Security review limits

Current candidate text/source/config files were checked for recognizable credential/token/private-key patterns and reviewed for password I/O. No high-confidence credentials were found. Common-password dictionary entries and disposable test fixtures are expected. This does not certify full Git history, every secret format, dependency advisories, OS clipboard privacy or secure memory erasure.

See [release-readiness report](RELEASE_READINESS.md) for the audit/fixes, [submission checklist](SUBMISSION.md) for final laptop work and [Task 04 history](PASSWORD_LAB.md) for implementation background. The user subsequently approved source publication; no GitHub release or tag is included.
