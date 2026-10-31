"""Dependency-free command-line entry point for Password Forge."""
import argparse
from app.core.password_generator import PasswordOptions, generate_password
from app.core.validator import PasswordValidationError


def main(argv=None):
    parser = argparse.ArgumentParser(description="NOMOLI FORGE | Every Password, Uniquely Forged.")
    parser.add_argument("--length", type=int, default=18, help="Password length, 8–64 (default: 18)")
    parser.add_argument("--no-uppercase", action="store_true")
    parser.add_argument("--no-lowercase", action="store_true")
    parser.add_argument("--no-digits", action="store_true")
    parser.add_argument("--no-symbols", action="store_true")
    parser.add_argument("--allow-ambiguous", action="store_true", help="Allow 0/O/o/1/l/I")
    args = parser.parse_args(argv)
    options = PasswordOptions(
        length=args.length, uppercase=not args.no_uppercase,
        lowercase=not args.no_lowercase, digits=not args.no_digits,
        symbols=not args.no_symbols, exclude_ambiguous=not args.allow_ambiguous,
    )
    try:
        password = generate_password(options)
    except PasswordValidationError as exc:
        parser.error(str(exc))
    print(password)


if __name__ == "__main__":
    main()
