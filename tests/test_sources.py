"""Every data source gives exactly the same table as the CSV, so rules give the same answers."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from dqkit import sources

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "assessments" / "ndl" / "chart-data" / "people__births.csv"


class FakeResponse:
    def __init__(self, body, binary=b""):
        self._body, self.content = body, binary

    def raise_for_status(self):
        pass

    def json(self):
        return self._body


class FakeSession:
    """Stands in for a CKAN portal, so the test needs no network."""
    def __init__(self, csv_bytes):
        self.csv, self.calls = csv_bytes, []

    def get(self, url, params=None, timeout=None):
        self.calls.append(url)
        if url.endswith("/api/3/action/package_show"):
            return FakeResponse({"success": True, "result": {"resources": [
                {"name": "Metadata", "format": "PDF", "url": "https://portal.example/m.pdf"},
                {"name": "Births", "format": "CSV", "url": "https://portal.example/births.csv"}]}})
        return FakeResponse(None, self.csv)


class Sources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.d = Path(cls.tmp.name)
        cls.base = sources.read(CSV)
        cls.base.to_excel(cls.d / "b.xlsx", index=False, sheet_name="Births")
        cls.base.to_excel(cls.d / "b.ods", index=False, engine="odf")
        (cls.d / "b.json").write_text(json.dumps({"data": cls.base.where(cls.base.notna(), None).to_dict("records")}))
        (cls.d / "b.jsonl").write_text("\n".join(json.dumps(r) for r in cls.base.where(cls.base.notna(), None).to_dict("records")))
        con = sqlite3.connect(cls.d / "b.db")
        cls.base.to_sql("births", con, index=False)
        con.close()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_every_file_type_matches_csv(self):
        for src in [self.d / "b.xlsx", {"type": "xlsx", "path": str(self.d / "b.xlsx"), "sheet": "Births"}, self.d / "b.ods",
                    self.d / "b.json", self.d / "b.jsonl", {"type": "sqlite", "path": str(self.d / "b.db"), "table": "births"},
                    {"type": "sqlite", "path": str(self.d / "b.db"), "query": "SELECT * FROM births"}]:
            self.assertTrue(sources.read(src).equals(self.base), sources.describe(src))

    def test_sql_must_be_read_only(self):
        for q in ("DELETE FROM births", "select 1; drop table births", "pragma table_info(births)"):
            with self.assertRaises(sources.SourceError):
                sources.read({"type": "sqlite", "path": str(self.d / "b.db"), "query": q})
        with self.assertRaises(sources.SourceError):
            sources.read({"type": "sqlite", "path": str(self.d / "b.db"), "table": "births; drop"})

    def test_ckan_picks_the_csv_resource(self):
        s = FakeSession(CSV.read_bytes())
        df = sources.read({"type": "ckan", "url": "https://portal.example", "dataset": "births", "resource": "csv"}, session=s)
        self.assertTrue(df.equals(self.base))
        self.assertEqual(s.calls[-1], "https://portal.example/births.csv")
        with self.assertRaises(sources.SourceError):
            sources.read({"type": "ckan", "url": "http://insecure.example", "dataset": "x"}, session=s)

    def test_friendly_errors(self):
        with self.assertRaises(sources.SourceError):
            sources.read("data.unknownext")
        with self.assertRaises(sources.SourceError):
            sources.read(self.d / "missing.csv")
        with self.assertRaises(sources.SourceError):
            sources.read({"type": "nosql"})


if __name__ == "__main__":
    unittest.main()
