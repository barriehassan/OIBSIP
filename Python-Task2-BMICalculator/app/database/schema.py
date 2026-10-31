"""Version-one schema; initialization is idempotent and transactional."""
SCHEMA_VERSION = 1
STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL CHECK(length(trim(name)) BETWEEN 1 AND 100),
        created_at TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS bmi_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
        weight_kg REAL NOT NULL CHECK(typeof(weight_kg) IN ('real','integer') AND weight_kg BETWEEN 1 AND 500),
        height_m REAL NOT NULL CHECK(typeof(height_m) IN ('real','integer') AND height_m BETWEEN 0.3 AND 2.75),
        bmi_value REAL NOT NULL CHECK(typeof(bmi_value) IN ('real','integer') AND bmi_value > 0 AND bmi_value <= 6000),
        category TEXT NOT NULL CHECK(category IN ('Underweight','Normal','Overweight','Obese')),
        measured_at TEXT NOT NULL)""",
    "CREATE INDEX IF NOT EXISTS idx_bmi_profile_time ON bmi_records(profile_id, measured_at)",
)
