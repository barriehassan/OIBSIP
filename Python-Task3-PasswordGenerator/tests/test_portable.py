"""Standard-library checks runnable without desktop dependencies."""
import itertools
from pathlib import Path
import subprocess
import sys
import unittest
from app.core.password_generator import AMBIGUOUS_CHARACTERS, CHARACTER_SETS, PasswordOptions, generate_password, selected_character_sets
from app.core.validator import PasswordValidationError
from app.ui.controller import PasswordController

PROJECT = Path(__file__).resolve().parents[1]


class PortableTests(unittest.TestCase):
    def test_all_combinations(self):
        for count in (2, 3, 4):
            for categories in itertools.combinations(CHARACTER_SETS, count):
                for length in (8, 18, 64):
                    for exclude in (False, True):
                        with self.subTest(categories=categories, length=length, exclude=exclude):
                            options = PasswordOptions(length=length, exclude_ambiguous=exclude,
                                **{key: key in categories for key in CHARACTER_SETS})
                            value = generate_password(options)
                            sets = selected_character_sets(options)
                            self.assertEqual(len(value), length)
                            self.assertLessEqual(set(value), set(''.join(sets.values())))
                            self.assertTrue(all(set(value) & set(chars) for chars in sets.values()))
                            if exclude:
                                self.assertFalse(set(value) & AMBIGUOUS_CHARACTERS)

    def test_bad_lengths(self):
        for length in (True, False, None, '18', 8.5, 7, 65, -1):
            with self.subTest(length=length), self.assertRaises(PasswordValidationError):
                generate_password(PasswordOptions(length=length))

    def test_failed_generation_keeps_state(self):
        controller = PasswordController()
        old, _ = controller.generate(PasswordOptions())
        with self.assertRaises(PasswordValidationError):
            controller.generate(PasswordOptions(length=0))
        self.assertEqual(controller.current_password, old)
        self.assertEqual(list(controller.history), [old])

    def test_history_order_and_cleanup(self):
        controller = PasswordController()
        generated = [controller.generate(PasswordOptions())[0] for _ in range(6)]
        self.assertEqual(list(controller.history), list(reversed(generated[-5:])))
        controller.close()
        self.assertEqual(controller.current_password, '')
        self.assertFalse(controller.history)

    def run_cli(self, *args):
        return subprocess.run([sys.executable, '-m', 'app.cli', *args],
            cwd=PROJECT, capture_output=True, text=True, timeout=10)

    def test_cli_output(self):
        result = self.run_cli('--length', '24', '--no-symbols', '--no-uppercase')
        self.assertEqual(result.returncode, 0, result.stderr)
        value = result.stdout.strip()
        self.assertEqual(len(value), 24)
        self.assertTrue(value.isalnum())
        self.assertFalse(any(c.isupper() for c in value))
        self.assertTrue(any(c.isdigit() for c in value))

    def test_cli_invalid_input(self):
        for args in (('--length', '7'), ('--length', 'bad'),
                     ('--no-uppercase', '--no-lowercase', '--no-symbols')):
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, '')
                self.assertIn('error:', result.stderr)

    def test_cli_help(self):
        result = self.run_cli('--help')
        self.assertEqual(result.returncode, 0)
        self.assertIn('NOMOLI FORGE', result.stdout)


if __name__ == '__main__':
    unittest.main()
