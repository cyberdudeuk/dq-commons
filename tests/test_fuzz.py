"""Dynamic analysis: property-based fuzzing of the parsers that read untrusted input.

Hypothesis generates thousands of inputs, including hostile ones (control characters, huge
exponents, odd Unicode), and checks that each parser never crashes and keeps its documented
contract. CI runs this file with `python -X dev` so runtime warnings and assertions are on
(OpenSSF dynamic_analysis and dynamic_analysis_enable_assertions, added in 2.15.2).

Skipped when Hypothesis is not installed, so the main test run needs no extra dependency.
"""
import math
import pathlib
import re
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

try:
    from hypothesis import given, settings, strategies as st
except ImportError:  # pragma: no cover
    given = None

from dqkit import numbers
from dqkit.metadata import _is_public_sector, parse_uk_date

_NUMBER_TEXT = re.compile(r"[ \t\n\r\v\f]*[+-]?(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?[ \t\n\r\v\f]*")


@unittest.skipIf(given is None, "Hypothesis not installed")
class Fuzz(unittest.TestCase):
    if given is not None:

        @settings(max_examples=3000, deadline=None)
        @given(st.text())
        def test_number_parser_never_crashes_and_keeps_its_rule(self, s):
            value, whole = numbers.parse(s)
            self.assertIsInstance(value, float)
            if _NUMBER_TEXT.fullmatch(s):
                self.assertFalse(math.isnan(value), f"{s!r} is a number by the documented rule")
                self.assertEqual(value, float(s.strip(" \t\n\r\v\f")))
            elif not math.isinf(value):
                self.assertTrue(math.isnan(value), f"{s!r} is not a number by the documented rule")
                self.assertFalse(whole)

        @settings(max_examples=2000, deadline=None)
        @given(st.integers(min_value=-(10 ** 30), max_value=10 ** 30))
        def test_whole_numbers_round_trip(self, n):
            value, whole = numbers.parse(str(n))
            self.assertTrue(whole)
            self.assertEqual(value, float(n))

        @settings(max_examples=2000, deadline=None)
        @given(st.one_of(st.none(), st.text()))
        def test_date_parser_never_crashes(self, s):
            d = parse_uk_date(s)
            if d is not None:
                # Whatever was accepted is a real date that reads back the same in both formats.
                self.assertEqual(parse_uk_date(d.strftime("%d/%m/%Y")), d)
                self.assertEqual(parse_uk_date(d.isoformat()), d)

        @settings(max_examples=2000, deadline=None)
        @given(st.text(alphabet=st.characters(blacklist_categories=("Cs",)), max_size=40))
        def test_public_sector_check_cannot_be_fooled_by_a_suffix(self, label):
            # A host only counts when it IS a listed domain or ends with "." + that domain.
            host = re.sub(r"[^a-z0-9-]", "", label.lower()) or "x"
            self.assertFalse(_is_public_sector(f"https://{host}gov.uk.evil.example/"))
            self.assertFalse(_is_public_sector(f"https://{host}-gov.uk/"))
            self.assertTrue(_is_public_sector(f"https://{host}.gov.uk/"))


if __name__ == "__main__":
    unittest.main()
