# NOMOLI FORGE — Password Forge

**Every Password, Uniquely Forged.**

An advanced password-generator project for the Oasis Infobyte Python Programming internship. Python powers an offline command-line tool and a mountain-glass desktop application built with standard Tk and Pillow. This is the first project added to the repository; the folder retains the working task number, Task 3.

## Features

- OS-backed secure randomness through Python `secrets`
- Length from **8 to 64**; synchronized slider and numeric input in the GUI
- Uppercase, lowercase, digits and symbols; at least **two categories** required
- Every enabled category appears at least once
- Optional exclusion of lookalikes: `0 O o 1 l I`
- Informational strength indicator; password masking and explicit copy feedback
- Optional automatic copy, off by default
- Last five passwords in memory, hidden by default, with copy and clear controls
- Your supplied mountain landscape bundled locally, with a procedural fallback
- Dependency-free command-line mode

## Quick start: no installation needed

Install Python **3.10+**, clone or download the repository, and open a terminal in the project folder:

```bash
cd OIBSIP/Python-Task3-PasswordGenerator
python -m app.cli --length 20
python -m app.cli --length 24 --no-symbols
python -m app.cli --help
```

On Windows, use `py -3` if `python` is unavailable. CLI output contains the actual password, so it can remain in terminal scrollback or redirected output. Avoid using real credentials in recordings.

## Desktop setup

A graphical desktop and Tk are required. Create a virtual environment **inside this project folder**.

Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

macOS / Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

Installation needs internet once; generation works offline. Commands below assume the virtual environment is active (`.venv\Scripts\Activate.ps1` on Windows or `source .venv/bin/activate` on macOS/Linux). You may instead use the explicit interpreter paths above.

`run_windows.bat` is an optional launch shortcut after installation. It uses the local virtual environment when present and never installs packages automatically. If Windows blocks the shortcut, use the PowerShell commands above.

### Use the application

1. Set a length and enable at least two character types.
2. Select **Generate Password**. The password starts masked.
3. Select **Show** to inspect it, or **Copy Password** to use it.
4. Enable automatic copy only if wanted. Clipboard failures appear as status messages.
5. Reveal, copy or clear recent creations; history is limited to five entries.

### Optional custom artwork

The supplied mountain landscape is included at `assets/backgrounds/mountain.png` and fills the entire window. Frosted blue panels blur and tint the scenery beneath them. To replace it, add an image you have permission to publish at `assets/backgrounds/mountain.png` (also accepts `.jpg`, `.jpeg`, `.webp`). A missing or unreadable image falls back to the illustration.

## Structure

| Path | Responsibility |
| --- | --- |
| `main.py` | Desktop entry point |
| `app/cli.py` | Dependency-free CLI and argument validation |
| `app/core/` | Options, validation, secure generation, strength estimate |
| `app/ui/` | Desktop view, history controller, procedural artwork |
| `app/services/clipboard.py` | Clipboard adapter with Tk fallback |
| `assets/backgrounds/` | Optional user-supplied artwork |
| `tests/` | Generator, CLI, controller, strength, artwork and clipboard checks |
| `requirements.txt` | Desktop dependencies |
| `requirements-dev.txt` | Desktop dependencies plus pytest |
| `docs/` | Design explanation and submission checklist |

## Validation

Dependency-free checks (CLI and core/controller):

```bash
python -m unittest discover -s tests -p 'test_portable.py' -v
```

Full automated suite, after installing test dependencies:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

See [validation notes](docs/VALIDATION.md) for what has actually been run. Automated tests do not establish Windows/macOS GUI compatibility. Follow the [manual submission checklist](docs/SUBMISSION.md) on your computer.

## Design and security

The generator uses rejection sampling: draw a full candidate with `secrets.choice`, then accept it only when every selected category is present. This samples uniformly among valid strings. Validation runs before generation. The UI calls a separate controller so generation and history can be tested without a window. See [design notes](docs/DESIGN.md).

The strength display uses `length × log2(alphabet size)`, an approximate upper bound; category constraints reduce the valid search space. It is not a breach check or security certification. Passwords are not logged, transmitted, or saved by the app. History is held in process memory and references are cleared on close; Python cannot guarantee secure memory erasure. The system clipboard may be readable by other applications and may retain copied text after this app exits.

## Troubleshooting

- **Missing package:** install `requirements.txt` with the same interpreter used to launch the app.
- **Pillow download fails:** retry installation when connected; use CLI mode in the meantime.
- **No Tk / no display:** use a Python installation with Tk and a local desktop. On Debian/Ubuntu, Tk is commonly provided by `python3-tk`; a headless server can run CLI mode.
- **Clipboard unavailable:** reveal the password and copy it manually; Linux clipboard support depends on the desktop session.
- **Long passwords:** the output field scrolls horizontally; select it and use the arrow keys to inspect.

## Credits and originality

Prepared for Hassan Barrie under NOMOLI FORGE, with AI assistance. This project continues the independently developed Password Forge source, rather than copying a public tutorial solution. The background image was supplied by the author; procedural artwork remains available as a fallback. Third-party dependencies: [Pillow](https://github.com/python-pillow/Pillow), [pyperclip](https://github.com/asweigart/pyperclip), and [pytest](https://github.com/pytest-dev/pytest). NOMOLI FORGE uses a text wordmark and a simple mountain motif matching the supplied UI reference. The separately selected company brand identity remains a separate deliverable.

## Mountain-glass interface update

The desktop now follows the supplied reference: full-window landscape, frosted navy panels, a sidebar, an estimated-strength ring, readable settings, and five compact history rows. Panel backgrounds are composited with Pillow; widgets use standard Tk, avoiding CustomTkinter font compatibility issues.

Keyboard: **Ctrl+G** generates, **Esc** masks output and history, and **Tab** moves through canvas actions and input fields. **Enter/Space** activates focused actions. History remains masked until revealed. Each generation masks the new password again. Long history previews are shortened visually; copy always uses the complete value.
