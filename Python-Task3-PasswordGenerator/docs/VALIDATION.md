# Validation record

Mountain-glass redesign checked on 31 October 2026 using Python 3.12.14 and Tk 9.0.4 in a Linux virtual display.

- Headless suite: 46 passed, 77 subtests passed; the opt-in desktop test is skipped without its environment flag.
- Full suite with desktop enabled: 47 passed, 77 subtests passed.
- Real desktop smoke checks: rendering, repeated generation, five-entry history, masking, length 64, invalid input, slider synchronization, clipboard round-trip, 1440×900 and 1000×680 resize, clearing, and closing passed.
- Actual application screenshot visually inspected. A redraw issue that hid the embedded fields was found and fixed; the regression test checks that both fields remain mapped.
- Windows and macOS have not been tested in this environment. Complete the manual submission checklist on the target computer.

Desktop dependencies are Pillow and pyperclip; Tk comes from the Python installation. CustomTkinter is no longer required. The CLI remains dependency-free.

Run the full suite from the project directory with `python -m pytest -q`. Opt into the real-window test on a desktop by setting `RUN_DESKTOP_TESTS=1` before running pytest. The opt-in test does not change the system clipboard. Clipboard round-trip was checked separately using disposable generated data in the virtual display.
