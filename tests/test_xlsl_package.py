import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from src.xlsl import XLSLDocument, XLSLFormatError, read_xlsl, validate_workbook, write_xlsl


class XLSLPackageTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.path = Path(self.temporary_directory.name) / "sample.xlsl"
        self.document = XLSLDocument(
            workbook={
                "sheets": {
                    "Measurements": {
                        "columns": ["id", "value"],
                        "rows": [["a", 1.5], ["b", 2.5]],
                    }
                }
            },
            logic_modules={"logic/analysis.xsl": "task analysis\\n  return 1\\n"},
        )

    def test_round_trip_preserves_workbook_and_inert_logic(self):
        write_xlsl(self.document, self.path)
        loaded = read_xlsl(self.path)
        self.assertEqual(loaded.workbook, self.document.workbook)
        self.assertEqual(loaded.logic_modules, self.document.logic_modules)
        self.assertEqual(loaded.manifest["format_version"], "1.0.0")

    def test_writer_creates_parent_directories(self):
        nested = self.path.parent / "nested" / "file.xlsl"
        write_xlsl(self.document, nested)
        self.assertTrue(nested.is_file())

    def test_rejects_non_zip_file(self):
        self.path.write_text("not a zip", encoding="utf-8")
        with self.assertRaises(XLSLFormatError):
            read_xlsl(self.path)

    def test_rejects_missing_required_members(self):
        with zipfile.ZipFile(self.path, "w") as archive:
            archive.writestr("manifest.json", json.dumps({
                "format": "XLSL", "format_version": "1.0.0"
            }))
        with self.assertRaises(XLSLFormatError):
            read_xlsl(self.path)

    def test_rejects_unsupported_version(self):
        self.document.manifest["format_version"] = "2.0.0"
        with self.assertRaises(XLSLFormatError):
            write_xlsl(self.document, self.path)

    def test_rejects_path_traversal(self):
        with zipfile.ZipFile(self.path, "w") as archive:
            archive.writestr("../outside.txt", "bad")
        with self.assertRaises(XLSLFormatError):
            read_xlsl(self.path)

    def test_rejects_unknown_package_entries(self):
        write_xlsl(self.document, self.path)
        with zipfile.ZipFile(self.path, "a") as archive:
            archive.writestr("scripts/run.py", "print('unsafe')")
        with self.assertRaises(XLSLFormatError):
            read_xlsl(self.path)

    def test_rejects_duplicate_json_keys(self):
        with zipfile.ZipFile(self.path, "w") as archive:
            archive.writestr("manifest.json",
                '{"format":"XLSL","format":"OTHER","format_version":"1.0.0"}')
            archive.writestr("workbook.json", '{"sheets":{"S":{"columns":[],"rows":[]}}}')
        with self.assertRaises(XLSLFormatError):
            read_xlsl(self.path)

    def test_rejects_rows_with_wrong_width(self):
        invalid = XLSLDocument(workbook={
            "sheets": {"S": {"columns": ["a", "b"], "rows": [[1]]}}
        })
        with self.assertRaises(XLSLFormatError):
            write_xlsl(invalid, self.path)

    def test_structural_validator_reports_errors(self):
        valid, report = validate_workbook({
            "sheets": {"S": {"columns": ["x"], "rows": [[1]]}}
        })
        self.assertTrue(valid)
        self.assertEqual(report["errors"], [])
        valid, report = validate_workbook({
            "sheets": {"S": {"columns": ["x"], "rows": [[1, 2]]}}
        })
        self.assertFalse(valid)
        self.assertTrue(report["errors"])


if __name__ == "__main__":
    unittest.main()
