from __future__ import annotations

import sys
import unittest
from pathlib import Path


TASK_ROOT = Path(__file__).resolve().parents[1]
if str(TASK_ROOT) not in sys.path:
    sys.path.insert(0, str(TASK_ROOT))

from Coding.slugger import slugify


class SlugifyTests(unittest.TestCase):
    def test_slugifies_basic_sentence(self) -> None:
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_collapses_consecutive_whitespace_and_punctuation(self) -> None:
        self.assertEqual(slugify("Hello   ,,,   World!!!"), "hello-world")

    def test_removes_leading_and_trailing_separators(self) -> None:
        self.assertEqual(slugify("  --Hello World--  "), "hello-world")

    def test_returns_empty_string_for_empty_or_punctuation_only_input(self) -> None:
        self.assertEqual(slugify(""), "")
        self.assertEqual(slugify("...---!!!"), "")

    def test_preserves_unicode_letters_and_digits(self) -> None:
        self.assertEqual(slugify("Über Café 123"), "über-café-123")


if __name__ == "__main__":
    unittest.main()
