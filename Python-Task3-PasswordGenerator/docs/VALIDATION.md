# Validation record

Checked on 31 October 2026 in a Linux cloud environment.

| Check | Result |
| --- | --- |
| Full suite: Python 3.12.14, pytest 9.2.0 | 44 passed, 77 subtests passed |
| Standard-library suite: Python 3.12.14, no desktop packages | 7 passed |
| Desktop module import | Passed; Tk 9.0 detected |
| Window rendering / interactive GUI | Not verified: no graphical display available |
| Actual OS clipboard | Not verified; adapter failure and Tk fallback tested with substitutes |
| Windows / macOS launch | Not run in this environment |

Installed desktop versions for the automated run: CustomTkinter 5.2.2, Pillow 12.3.0, pyperclip 1.11.0. Requirements use bounded compatible ranges rather than claiming these versions were tested on every platform.

Coverage includes all 11 allowed category combinations at lengths 8, 18, and 64 with both lookalike settings (66 cases), invalid types and boundaries, mandatory categories, alphabet filtering, history order/capacity/cleanup, unchanged state after invalid generation, CLI flags/errors/help, strength labels, artwork fallback and simulated clipboard errors.

Complete the manual checklist before describing the desktop application as verified on your own OS. No screenshots, demonstration videos, internship acceptance, or platform test results are fabricated.
