"""The register reader (scripts/read_dea_register.py) used by examples/register-method-field."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("read_dea_register", ROOT / "scripts" / "read_dea_register.py")
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)

PAGE = """<main><h1>Synthetic agreement</h1><dl class="govuk-summary-list">
<div><dt>Purpose</dt><dd>To deliver a helpline.</dd></div>
<div><dt>Disclosed information</dt><dd>{disclosed}</dd></div>
<div><dt>Information sharing method</dt><dd>{method}</dd></div>
<div><dt>Contact</dt><dd>someone@example.org</dd></div>
<div><dt>Start date</dt><dd>2026-09-22</dd></div><div><dt>Isa status</dt><dd>Active</dd></div></dl>
<h2>Powers</h2><ul><li>Public Service Delivery - Fuel poverty</li></ul>
<h2>Controllers</h2><ul><li>Controller A</li><li>Controller B</li></ul></main>"""


def read(method, disclosed):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "1.html"
        p.write_text(PAGE.format(method=method, disclosed=disclosed), encoding="utf-8")
        return reader.read(p, 1)


class ReadDeaRegister(unittest.TestCase):
    def test_fields_and_lists(self):
        r = read("Secure File Transfer", "Personal details.")
        self.assertEqual((r["status"], r["sharing_method"], r["start_date"], r["power"], r["controller_count"]),
                         ("Active", "Secure File Transfer", "2026-09-22", "Public Service Delivery - Fuel poverty", 2))

    def test_text_naming_an_api_with_another_method_is_flagged(self):
        r = read("Secure File Transfer", "Access to the Citizen Application Programming Interface (CAPI) will be enabled.")
        self.assertEqual((r["method_is_api"], r["text_mentions_api"]), (0, 1))

    def test_api_method_and_text_agree(self):
        self.assertEqual(read("API", "Data is shared through an API.")["method_is_api"], 1)

    def test_words_containing_api_are_not_an_api(self):
        # negative test: "rapid" and "capital" contain the letters but are not an API
        self.assertEqual(read("Secure File Transfer", "A rapid, capital-wide service.")["text_mentions_api"], 0)

    def test_contact_details_are_not_copied(self):
        self.assertNotIn("example.org", str(read("API", "x")))


if __name__ == "__main__":
    unittest.main()
