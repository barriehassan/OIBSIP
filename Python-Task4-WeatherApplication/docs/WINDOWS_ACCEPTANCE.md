# SkyCast — Windows acceptance checklist

Status: **not yet executed on Windows**. Record date, Windows version, Python/Tk versions, scaling, result and any defect; do not mark a checkbox from Linux evidence.

## Setup

From the project directory in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -c "import sys, tkinter; print(sys.version); print(tkinter.TkVersion)"
.\.venv\Scripts\python.exe main.py
```

- [ ] Dependencies install without conflicts; Tk is 8.6. Use the same interpreter to install and run. Do not disable Smart App Control or other security protection.
- [ ] Main window opens without traceback, speech, or automatic IP lookup.
- [ ] Run development tests after installing `requirements-dev.txt`; record exact counts/warnings separately from the Linux report.

## Weather and design

- [ ] Search `Freetown, Sierra Leone` and a second known city; verify displayed country, coordinates and local timezone. Try an ambiguous city and explicitly choose the intended candidate.
- [ ] Try a provider-supported postal code, unknown city, empty input and invalid characters; confirm understandable results/errors. Postal coverage is not universal.
- [ ] Check current temperature, humidity, wind/units and observation timestamp against Full report.
- [ ] Today shows six actual upcoming hours; Tomorrow and Next 7 Days select proper dates and at least five available days. Missing data is unavailable, never zero-filled.
- [ ] Switch C/F repeatedly: current/daily/hourly/city/feels-like/chart labels agree; wind remains km/h. Confirm no cumulative conversion drift.
- [ ] Inspect rain probability timestamps, temperature-chart gaps, sunrise/sunset selected date and timezone.
- [ ] At 1440×900, 1366×768 and about 1024×700, check location/search alignment, scrolling, labels and essential controls. Repeat at native 100%, 125% and 150% scaling as available.
- [ ] Map renders; pins match selected places. Pan, zoom, reset, layers, locate and View wide work. City update/remove and retrieval details work.
- [ ] Ctrl+L, Ctrl+U, candidate/day arrows, Enter/Space, Escape and city Shift+F10 work. Check focus visibility and any required screen reader.

## Local data and reliability

- [ ] Save two favorites; restart; select each; remove one; repeated Save does not duplicate it. Distinct same-name places remain distinct.
- [ ] After a successful download, temporarily disconnect connectivity and select a saved favorite or Refresh. Expect cache/offline label plus original download time. A location without cached data must show an error.
- [ ] Restore connectivity and Refresh. Expect a new retrieval time and successful status. Rapid searches must not let old results replace the latest selection.
- [ ] After 20 minutes, old main/city readings are labeled stale/cached; expired forecast hours do not become future hours.
- [ ] On disposable test data only, Clear weather cache preserves favorites and the displayed snapshot. Do not erase real favorites/cache to run tests.

## Real Windows speech

- [ ] Listen reads actual selected location and current data in C then F, without overlap or a frozen GUI.
- [ ] Stop during startup and playback; repeat Listen/Stop; change location/unit while speaking. Obsolete speech ends.
- [ ] Cached summary says last retrieved and includes download time.
- [ ] Where safely reproducible, unavailable voice/audio produces a useful error and weather still works. Do not uninstall a needed system voice merely for testing.
- [ ] Close during playback; confirm no lingering SkyCast speech process or continued audio. Reopen normally.

## Optional approximate location

- [ ] Read consent, then Cancel: no lookup. Manual search remains usable.
- [ ] If you choose to permit it, Continue performs lookup; confirm/reject the approximate city before weather selection. VPN/mobile results may be wrong.
- [ ] Provider/network errors leave manual search usable. No IP is written to local data or logs.

## Sign-off

- Test date / tester:
- Windows / Python / Tk:
- Scaling / screen sizes:
- Automated test outcome:
- Manual pass/fail items:
- Defects and reproduction steps:
- Screenshots (actual Windows only):
- Final acceptance decision:

Until completed, release status remains **conditionally ready**. Publication requires separate approval.
