# zxcvbn-python 4.5.0

Source: https://github.com/dwolfhub/zxcvbn-python
Distribution: PyPI zxcvbn==4.5.0.
License: MIT; see LICENSE.txt.

Bundled for offline analysis without a separate pip installation. Three absolute import statements in matching.py and one in feedback.py were converted to relative imports so the upstream package runs under app._vendor.zxcvbn. The unused CLI module was omitted. No scoring logic or dictionaries were changed.

When updating, preserve the license, review upstream changes, and rerun the Password Lab regression tests.
