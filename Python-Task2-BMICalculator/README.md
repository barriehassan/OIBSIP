# NOMOLI FORGE — BMI Insight

An advanced Python desktop BMI calculator project for the Oasis Infobyte Python Programming internship. Tasks 03–04 implement the offline calculation core, SQLite persistence and application services. Python 3.10+ is supported; no runtime packages are required.

## Completed scope

- Unrounded BMI calculations, separate two-decimal formatting, and adult classification.
- Interactive measurement parsing with controlled `ValidationError` exceptions.
- Immutable results with derived BMI and category.
- Pure metric/imperial conversion utilities and automated pytest coverage.

SQLite profile and measurement persistence is implemented. No GUI, charts, dashboard, PDF reports, or network calls are implemented. The core remains independent of storage.

## Formula and categories

BMI = weight in kilograms / (height in metres × height in metres).
Calculations use Python floating-point precision, without intentional rounding. Display formatting never changes the stored value or classification. Unrepresentable floating-point results raise ValidationError.

| Unrounded BMI | Category |
| --- | --- |
| Below 18.5 | Underweight |
| 18.5 to below 25 | Normal |
| 25 to below 30 | Overweight |
| 30 and above | Obese |

Zero, negative, non-finite and nonnumeric BMI values are rejected. These are the adult thresholds specified in the task. Category metadata provides a name, colour and neutral educational explanation, separately from classification.

## Structure

```text
Python-Task2-BMICalculator/
├── app/
│   ├── __init__.py
│   └── core/
│       ├── __init__.py
│       ├── calculator.py
│       ├── classification.py
│       ├── validator.py
│       ├── models.py
│       └── conversions.py
├── tests/
│   ├── test_calculator.py
│   ├── test_classification.py
│   └── test_validator.py
├── README.md
├── requirements.txt
├── pyproject.toml
└── .gitignore
```

Database and service packages sit alongside core under app. Visualization and UI packages remain planned. Dependencies belong in requirements.txt; pyproject.toml contains pytest configuration only.

## Installation and tests

From this project directory:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

Only installing test tooling needs access to a package source; calculations run offline. Task 03 verification: **139 passed, 0 failed, 0 skipped**. Tests include result-model and conversion tests in test_calculator.py.

## Usage and validation

```python
from app.core.calculator import calculate_bmi, create_result
from app.core.validator import ValidationError

raw_bmi = calculate_bmi(70, 1.75)  # approximately 22.857142857
try:
    result = create_result("70", "1.75")
    print(result.formatted_bmi, result.category.value)  # 22.86 Normal
except ValidationError as error:
    print(str(error))
```

The low-level calculator accepts built-in int/float values, excluding bool, and requires positive finite measurements. Interactive validators additionally accept numeric strings (including decimal and scientific notation), strip whitespace, and apply inclusive application support limits: **1–500 kg** and **0.30–2.75 metres**. These broad product limits catch likely unit mistakes and define the current supported input range. They are not medical thresholds and infer no health condition. Enter height in metres, e.g. 1.75 rather than 175. Unsupported types, blanks, NaN and infinity raise ValidationError, a ValueError subclass. Decimal and Fraction objects are deliberately unsupported; pass built-in numbers or interactive numeric text.

BMIResult is frozen and derives its BMI/category from validated measurements; callers cannot inject inconsistent derived fields. create_result is the convenient interactive entry point. The calculator itself has no UI or infrastructure dependencies.

## Conversions

International definitions: 1 pound = 0.45359237 kg; 1 inch = 0.0254 m; 1 cm = 0.01 m; 1 foot = 12 inches. Functions in conversions.py accept positive finite built-in numeric inputs, rejecting booleans and text. Feet/inches accepts whole nonnegative feet and inches from zero inclusive to 12 exclusive, requiring a positive total. Converted measurements should pass the metric validators before application use.

## Task 04: SQLite and local profiles

Profiles are local named collections, not authenticated user accounts. Names are trimmed, limited to 100 characters, reject control characters, and may repeat; integer IDs identify profiles. Listing uses ascending IDs. Renaming preserves IDs, creation times and history.

Storage uses Python sqlite3, short-lived connections, foreign keys enabled on every connection, explicit write transactions and rollback on errors. Queries use bound parameters. Schema version 1 is recorded with PRAGMA user_version; future versions are rejected until migration support is added. Initialization is idempotent; initialization does not migrate incompatible pre-existing custom tables.

| Table | Fields and constraints |
| --- | --- |
| profiles | id INTEGER PRIMARY KEY AUTOINCREMENT; name TEXT NOT NULL with trimmed length 1–100; created_at TEXT NOT NULL |
| bmi_records | id INTEGER PRIMARY KEY AUTOINCREMENT; profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE; weight_kg REAL NOT NULL within 1–500; height_m REAL NOT NULL within 0.3–2.75; bmi_value REAL NOT NULL positive and at most 6000; category TEXT NOT NULL restricted to the four categories; measured_at TEXT NOT NULL |

Index: `bmi_records(profile_id, measured_at)`. Numeric checks reject invalid types, NaN and infinities. The BMI storage ceiling of 6000 exceeds the maximum reachable from supported measurements (approximately 5555.56); it is a representability guard, not a medical threshold. Repositories check result consistency using the Task 03 API. Application-managed writes normalize timestamps; arbitrary direct SQL is not an application API.

Timestamps are canonical ISO 8601 UTC strings, including six fractional digits and +00:00. Backdated aware datetimes are supported, naive datetimes are rejected. Chronological ordering uses `(measured_at, id)`; IDs break timestamp ties. Recent-N queries select the newest N and return that subset ascending. Latest/previous refer to measurement time, not insertion time.

Deleting a profile permanently cascades to all its measurements. `deletion_preview` returns the profile and record count for a future confirmation dialog; the preview is advisory and may change. Service deletion requires `confirmed=True`. Record get/delete always require both profile ID and record ID, preventing cross-profile lookups.

### Storage paths and privacy

- Override: set `BMI_INSIGHT_DATA_DIR` to the desired writable directory.
- Windows: `%LOCALAPPDATA%/NOMOLI_FORGE/BMI_Insight/bmi_insight.sqlite3` (home AppData/Local fallback).
- macOS: `~/Library/Application Support/NOMOLI_FORGE/BMI_Insight/bmi_insight.sqlite3`.
- Linux: `$XDG_DATA_HOME/nomoli-forge/bmi-insight/bmi_insight.sqlite3` (defaults to ~/.local/share).

Missing directories are created; inaccessible locations raise a controlled error. Explicit file paths and connection factories support tests. All database tests use temporary files; no tests access the real application database. Standalone `:memory:` is rejected because connections are short-lived; use a temporary file instead. SQLite files and sidecars are ignored by Git.

Records stay on the local device with no transmission, telemetry or logging of personal values. SQLite is not encrypted: anyone with filesystem access may read it. Profile selection is organizational isolation, not a security boundary. Protect the application-data directory and backups using operating-system access controls.

### Service API and example

```python
from app.database.connection import Database
from app.database.profile_repository import ProfileRepository
from app.database.measurement_repository import MeasurementRepository
from app.services.profile_service import ProfileService
from app.services.measurement_service import MeasurementService
from app.services.history_service import HistoryService

database = Database()  # Creates local storage only when explicitly called.
records = MeasurementRepository(database)
profiles = ProfileService(ProfileRepository(database), records)
measurements = MeasurementService(records)
history = HistoryService(records)
profile = profiles.create("Local profile")
saved = measurements.save(profile.id, "70", "1.75")
print(saved.formatted_bmi, saved.category.value)
```

| Service | Public operations |
| --- | --- |
| ProfileService | create(name), list(), get(id), select(id), rename(id, name), deletion_preview(id), delete(id, confirmed=True) |
| MeasurementService | save(profile_id, weight_kg, height_m, measured_at=None) → Measurement |
| HistoryService | history(profile_id, limit=None), latest(id), previous(id), comparison(id), chart_data(id), count(id), get(profile_id, record_id), delete(profile_id, record_id) |

No service accepts caller-supplied BMI/category for raw measurement saving. BMI is recalculated by Task 03 and saved without display rounding. Frozen Profile, Measurement, MeasurementComparison and DeletionPreview models contain only values. Comparison returns signed weight and BMI differences, with no medical interpretation. Empty latest/previous/comparison returns None; invalid IDs and missing profiles produce controlled exceptions. A missing record within the selected profile raises MeasurementNotFound.

Errors: Task 03 ValidationError handles inputs; DatabaseError covers storage failures, with InitializationError, IntegrityError, ProfileNotFound and MeasurementNotFound subclasses. User-readable messages do not contain SQL details; exceptions retain causes for debugging. Future UI should show str(error), not a raw traceback. No failures are silently swallowed.

### Added structure

```text
app/database/
  __init__.py  connection.py  schema.py  errors.py  validation.py
  models.py  profile_repository.py  measurement_repository.py
app/services/
  __init__.py  profile_service.py  measurement_service.py  history_service.py
main.py
tests/
  conftest.py  test_database.py  test_profile_repository.py
  test_measurement_repository.py  test_profile_service.py
  test_measurement_service.py
```

`python main.py` initializes storage and exits; it is not a desktop interface. No runtime dependencies were added. Task 04 verification: **212 passed, 0 failed, 0 skipped**, including the unchanged 139 Task 03 cases.

## Planned work and limitations

The approved Mockup 05 — Vitality Analytics remains unchanged: horizontal navigation, dark navy, teal accents, circular BMI gauge and analytics components. CustomTkinter screens, Matplotlib chart rendering, Progress Dashboard and PDF reports remain unimplemented. Cloud sync, AI recommendations and authentication are outside current scope. No backup/restore UI or schema migrations beyond version-one initialization exist yet. Short-lived synchronous operations suit the current local scope; future UI should avoid blocking its event loop during slow storage operations. A confirmation preview is not a transactional lock.

Task 04 is ready for review. Task 05 has not started. Next, agree on Task 05 scope and connect accepted services to the approved desktop design, preserving profile-scoped history and explicit deletion confirmation.

## Educational limitations

BMI is a screening reference, not a diagnosis or a direct measurement of body fat. It does not distinguish muscle from fat or describe individual health. Adult categories are not appropriate for assessing children; pregnancy and individual circumstances also require professional interpretation. This software provides educational calculations, not medical advice.
