"""Explicit storage initialization only; no GUI is implemented yet."""
from app.database.connection import Database
from app.database.errors import DatabaseError

def main() -> int:
    try:
        Database()
    except DatabaseError as error:
        print(str(error))
        return 1
    print("BMI Insight storage initialized. Desktop interface is planned.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
