# Manual Windows verification — pending

Status: **not performed**. Linux screenshots and simulated Windows path tests do not substitute for these checks. Use a temporary profile and database; never delete or overwrite personal history to test the app.

## Setup without activating PowerShell scripts

Open PowerShell in `OIBSIP\Python-Task2-BMICalculator`. Use Python 3.12 with Tcl/Tk installed.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m tkinter
```

Close the Tk demonstration window. Skip venv creation if it already exists. Do not disable Smart App Control or antivirus; launch Python directly if the batch file is blocked.

Use a new isolated folder for this PowerShell session:

```powershell
$env:BMI_INSIGHT_DATA_DIR = Join-Path $env:TEMP ("BMI_Insight_QA_" + [guid]::NewGuid().ToString())
.\.venv\Scripts\python.exe main.py
```

Keep this shell open so relaunches use the same temporary database. Record the directory if you want to inspect/remove the synthetic QA data later. Do not remove any real application-data directory.

## Checklist

- [ ] Record Windows version, Python version, Tk version, screen resolution and display scale.
- [ ] Launch using the direct Python command; check there is no startup traceback.
- [ ] Verify all six navigation items and the active highlight.
- [ ] Create `Windows QA Alpha`; calculate 70 kg / 175 cm. Expect 22.86, Normal. Save once; repeated save is disabled.
- [ ] Check blank, alphabetic, zero, negative and NaN inputs show helpful errors and do not save.
- [ ] Add 75 kg and 73 kg at the same height. History should show three records; latest-versus-previous weight change should be -2 kg.
- [ ] Open Trends and Dashboard. Verify current profile, counts, values, UTC labels, period filters and reference toggle.
- [ ] Create/select an empty `Windows QA Beta`. Confirm Alpha's values disappear from Calculator preview, History, Trends, Dashboard and Reports.
- [ ] Rename Beta; check its ID is preserved and menus reflect the new name.
- [ ] Return to Alpha; open Reports. Test cancellation of the save dialog, invalid custom dates and a valid date range.
- [ ] Generate a PDF into a temporary, writable local folder. Navigate during export. Confirm success appears only after completion.
- [ ] Open the PDF: verify profile, BMI/category, selected dates, table headers, readable charts, footer/page numbers and disclaimer.
- [ ] Choose the same filename. Decline replacement and verify the file remains unchanged; repeat and approve replacement to verify the native prompt.
- [ ] Try a non-writable destination and verify controlled feedback, not false success. Keep any existing personal document untouched.
- [ ] While a sufficiently long report exports, attempt normal window closure; the app should ask you to wait, remain usable and close after completion.
- [ ] Cancel a record deletion; verify nothing changed. Confirm deletion of one synthetic record; check every chart/summary refreshes.
- [ ] Delete Beta with confirmation; ensure Alpha's records remain.
- [ ] Close/reopen from the same shell and verify Alpha's remaining records persist.
- [ ] Test long names and default/minimum window sizes; scroll to all actions.
- [ ] Check 100%, 125% and 150% Windows scaling where the screen has sufficient physical space. Verify fonts, gauge labels, chart axes, dropdowns, dialog positioning and keyboard focus.
- [ ] Run tests: `.\.venv\Scripts\python.exe -m pytest -q`. Record exact counts, skips and warnings.
- [ ] Capture screenshots without personal measurements. Label them with the verified platform.

After testing, close the app and remove only the session override:

```powershell
Remove-Item Env:BMI_INSIGHT_DATA_DIR
```

The next launch uses the normal application-data location. This command does not delete any database. Cleanup of the clearly identified synthetic QA folder is optional and manual.

## Record the result

Tester/date: pending. Windows/Python/Tk versions: pending. Screen/scaling: pending. Test counts: pending. Workflow result: pending. Native overwrite confirmation: pending. PDF worker: pending. Outstanding defects and screenshots: pending.

Do not mark this checklist passed until each action has actually been performed. Report exact errors/screenshots for any failure before approving release.
