"""Parameterized profile persistence; duplicate names are allowed."""
from .connection import Database
from .errors import ProfileNotFound
from .models import Profile
from .validation import identifier, profile_name, utc_timestamp

class ProfileRepository:
    def __init__(self, database: Database):
        self.database = database

    def create(self, name: str) -> Profile:
        name = profile_name(name)
        timestamp = utc_timestamp()
        with self.database.connection(write=True) as c:
            cursor = c.execute("INSERT INTO profiles(name, created_at) VALUES (?, ?)", (name, timestamp))
            return Profile(cursor.lastrowid, name, timestamp)

    def list(self) -> list[Profile]:
        with self.database.connection() as c:
            return [Profile(**dict(row)) for row in c.execute("SELECT * FROM profiles ORDER BY id")]

    def get(self, profile_id: int) -> Profile:
        identifier(profile_id)
        with self.database.connection() as c:
            row = c.execute("SELECT * FROM profiles WHERE id=?", (profile_id,)).fetchone()
            if row is None:
                raise ProfileNotFound("Profile not found.")
            return Profile(**dict(row))

    def rename(self, profile_id: int, name: str) -> Profile:
        identifier(profile_id)
        name = profile_name(name)
        with self.database.connection(write=True) as c:
            if c.execute("UPDATE profiles SET name=? WHERE id=?", (name, profile_id)).rowcount != 1:
                raise ProfileNotFound("Profile not found.")
            return Profile(**dict(c.execute("SELECT * FROM profiles WHERE id=?", (profile_id,)).fetchone()))

    def delete(self, profile_id: int) -> None:
        """Explicitly delete a profile and cascade its records atomically."""
        identifier(profile_id)
        with self.database.connection(write=True) as c:
            if c.execute("DELETE FROM profiles WHERE id=?", (profile_id,)).rowcount != 1:
                raise ProfileNotFound("Profile not found.")
