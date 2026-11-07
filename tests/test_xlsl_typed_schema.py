import tempfile
import unittest
from pathlib import Path

from xlsl import XLSLDocument, XLSLFormatError, read_xlsl, validate_workbook, write_xlsl


class XLSLTypedSchemaTests(unittest.TestCase):
    def valid_workbook(self):
        return {
            "schema_version": 1,
            "sheets": {
                "Measurements": {
                    "columns": [
                        {"name": "id", "type": "string", "nullable": False, "unique": True},
                        {"name": "value", "type": "number", "minimum": 0, "maximum": 10},
                        {"name": "day", "type": "date", "nullable": True},
                    ],
                    "rows": [["A-1", 2.5, "2026-11-07"], ["A-2", 10, None]],
                }
            },
        }

    def test_valid_typed_workbook(self):
        valid, report = validate_workbook(self.valid_workbook())
        self.assertTrue(valid, report["errors"])

    def test_rejects_boolean_as_integer(self):
        workbook = self.valid_workbook()
        workbook["sheets"]["Measurements"]["columns"][1]["type"] = "integer"
        workbook["sheets"]["Measurements"]["rows"][0][1] = True
        valid, report = validate_workbook(workbook)
        self.assertFalse(valid)
        self.assertTrue(any("expected integer" in error for error in report["errors"]))

    def test_rejects_null_for_non_nullable_column(self):
        workbook = self.valid_workbook()
        workbook["sheets"]["Measurements"]["rows"][0][0] = None
        valid, report = validate_workbook(workbook)
        self.assertFalse(valid)
        self.assertTrue(any("null is not allowed" in error for error in report["errors"]))

    def test_enforces_unique_values(self):
        workbook = self.valid_workbook()
        workbook["sheets"]["Measurements"]["rows"][1][0] = "A-1"
        valid, report = validate_workbook(workbook)
        self.assertFalse(valid)
        self.assertTrue(any("unique constraint" in error for error in report["errors"]))

    def test_enforces_numeric_bounds(self):
        workbook = self.valid_workbook()
        workbook["sheets"]["Measurements"]["rows"][0][1] = 11
        valid, report = validate_workbook(workbook)
        self.assertFalse(valid)
        self.assertTrue(any("above maximum" in error for error in report["errors"]))

    def test_enforces_pattern(self):
        workbook = self.valid_workbook()
        workbook["sheets"]["Measurements"]["columns"][0]["pattern"] = "[A-Z]+"
        workbook["sheets"]["Measurements"]["rows"][0][0] = "bad-id-1"
        valid, report = validate_workbook(workbook)
        self.assertFalse(valid)
        self.assertTrue(any("pattern" in error for error in report["errors"]))

    def test_rejects_unknown_column_property(self):
        workbook = self.valid_workbook()
        workbook["sheets"]["Measurements"]["columns"][0]["mystery"] = True
        valid, report = validate_workbook(workbook)
        self.assertFalse(valid)

    def test_rejects_unsupported_schema_version(self):
        workbook = self.valid_workbook()
        workbook["schema_version"] = 2
        valid, report = validate_workbook(workbook)
        self.assertFalse(valid)
        self.assertIn("schema_version", report["errors"][0])

    def test_legacy_untyped_columns_remain_compatible(self):
        workbook = {
            "sheets": {"Legacy": {"columns": ["a", "b"], "rows": [[None, 2], ["x", True]]}}
        }
        valid, report = validate_workbook(workbook)
        self.assertTrue(valid, report["errors"])

    def test_package_reader_and_writer_apply_typed_validation(self):
        workbook = self.valid_workbook()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "typed.xlsl"
            write_xlsl(XLSLDocument(workbook=workbook), path)
            loaded = read_xlsl(path)
            self.assertEqual(loaded.workbook, workbook)
            workbook["sheets"]["Measurements"]["rows"][0][1] = -1
            with self.assertRaises(XLSLFormatError):
                write_xlsl(XLSLDocument(workbook=workbook), path)


if __name__ == "__main__":
    unittest.main()
