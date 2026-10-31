# Task 05 — implementation and visual review

Status: functional UI implemented and refined, ready for user review. No commit or push performed.

## Pass 1 — functionality

Reviewed Task 03–04 modules; baseline 212 tests passed, none failed or skipped. Kept core, database schema, repositories, services and original tests unchanged. Composed existing services in bootstrap.py and added a Tk-independent UIController. The controller converts centimetres, coordinates calculation/saving, invalidates stale results and prevents accidental duplicate saves.

Calculator, Profiles and History are working screens. Profile creation/selection/renaming/deletion and measurement saving/retrieval/deletion use existing services. Destructive actions ask for confirmation. Inline errors cover invalid measurements and failed saves; profile/storage errors use readable dialogs. Startup storage/display/dependency failures show controlled explanations.

## Pass 2 — visual refinement

Launched the real application on a virtual desktop. Compared screenshots with the attached 1448×1086 reference. Corrected a startup scaling-order defect, oversized gauge numerals, compact-window clipping, bitmap-looking Tk 9 fonts, icon availability and proportional-font history alignment. Used local antialiased icons and Tk 8.6 for the verified rendering. Short windows scroll to retain access to every control.

| Reference feature | Implementation / difference |
| --- | --- |
| Horizontal top navigation | Same six destinations, visible active underline; no sidebar |
| Mountain hero and headline | Exact supplied mountain region cropped and blended; original standalone high-resolution artwork unavailable |
| Left profile/measurement card | Preserved position and proportions; cm/kg input; unsupported age/gender controls replaced by adult reference note |
| Large results panel | Live numeric BMI, four-colour gauge, marker, category pill, neutral interpretation, explicit save |
| Classification text | Neutral educational wording replaces the mockup's medical-risk claims |
| Summary cards | Real latest weight, count and change versus first; no fabricated records |
| Trend card | Reserved matching container with real record count and History shortcut; no plotted line until Task 06 |
| Branding/icons | Reconstructed local line art; official separate vector mark was not provided |
| Lighting and surfaces | Navy/teal palette and rounded borders; flatter turquoise buttons, simpler card lighting, no diffuse gauge bloom |
| Typeface/window chrome | Segoe UI requested, DejaVu Sans fallback on Linux; native desktop chrome retained for usability |
| Shorter windows | Vertical content scrolling instead of clipped controls; 1240×860 minimum logical size |

## Screenshots

These are captures of the running desktop app, not generated mockups. Empty state uses an isolated new database. Populated screenshots use a temporary verification profile with two measurements (75 kg then 73 kg, at 175 cm) saved through the actual application services. These records exist only in the disposable verification database. The app ships with no prepopulated profile/history.

- [Empty calculator](screenshots/01_empty.png)
- [Calculated, not yet saved](screenshots/02_calculated.png)
- [Saved result and actual summary values](screenshots/03_saved.png)
- [Profile-scoped history](screenshots/04_history.png)
- [Profile management](screenshots/05_profiles.png)
- [Compact window scrolled to the actions](screenshots/06_compact_scrolled.png)

## Verification

Final full suite: **240 passed, 0 failed, 0 skipped**. Python 3.12.3, Tk 8.6.14, CustomTkinter 6.0.0, Xvfb virtual display. Includes all 212 original backend tests plus 28 controller/desktop tests. Real-widget tests cover calculation and save, disabled/stale save state, invalid input feedback, navigation, profile create/rename/delete and cancel, profile isolation, measurement deletion, failed-save feedback, short-window scrolling and very large supported BMI display. Tests and captures never connect to the real application database.

Also smoke-launched main.py with an isolated application-data directory: it stayed running, initialized its database and produced no stderr.

A separate managed runtime uses Tk 9 and rendered fonts poorly; it was not used for the accepted screenshots. Native Windows appearance, minimize/maximize behaviour and OS scaling remain manual verification items on the user's machine. No packaged EXE was created.

## Files

Added app/ui/{__init__,bootstrap,controller,theme,icons,gauge,window}.py, assets/mountain_reference.png and assets/README.md, tests/test_ui_controller.py, tests/test_ui_desktop.py, run_windows.bat, this review and six screenshots. Updated main.py, requirements.txt, project README.md and the parent OIBSIP README.md. Password Forge and all Task 03–04 source/tests remain unchanged. No runtime databases, caches or credentials belong in the review package.

## Local acceptance checks

Use the Windows launch commands in README.md. Create two profiles, calculate and save measurements, confirm their histories are isolated, restart and verify persistence, test rename and deletion cancellation, and review the layout at your desktop's scale. The GUI is ready for review; Task 06 has not started.
