"""Whitelist fixture that references items to suppress false positives."""

from tests.fixtures_exempt.dead_code import unused_function

unused_function()
