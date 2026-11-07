import unittest

from xlsl import validate_workbook


class XLSLRelationalSchemaTests(unittest.TestCase):
    def workbook(self):
        return {
            "schema_version": 2,
            "sheets": {
                "Customers": {
                    "primary_key": ["tenant", "customer_id"],
                    "columns": [
                        {"name": "tenant", "type": "string"},
                        {"name": "customer_id", "type": "integer"},
                        {"name": "name", "type": "string"},
                    ],
                    "rows": [["acme", 1, "Ada"], ["acme", 2, "Lin"]],
                },
                "Orders": {
                    "columns": [
                        {"name": "order_id", "type": "integer"},
                        {"name": "tenant", "type": "string", "nullable": True},
                        {"name": "customer_id", "type": "integer", "nullable": True},
                    ],
                    "foreign_keys": [{
                        "columns": ["tenant", "customer_id"],
                        "references": {"sheet": "Customers", "columns": ["tenant", "customer_id"]},
                        "on_delete": "set_null",
                    }],
                    "rows": [[10, "acme", 1], [11, None, None]],
                },
            },
        }

    def test_valid_composite_primary_and_foreign_keys(self):
        valid, report = validate_workbook(self.workbook())
        self.assertTrue(valid, report["errors"])

    def test_rejects_duplicate_composite_primary_key(self):
        book = self.workbook()
        book["sheets"]["Customers"]["rows"].append(["acme", 1, "Duplicate"])
        valid, report = validate_workbook(book)
        self.assertFalse(valid)
        self.assertTrue(any("duplicate primary key" in e for e in report["errors"]))

    def test_rejects_missing_foreign_key_target(self):
        book = self.workbook()
        book["sheets"]["Orders"]["rows"][0][2] = 999
        valid, report = validate_workbook(book)
        self.assertFalse(valid)
        self.assertTrue(any("does not exist" in e for e in report["errors"]))

    def test_rejects_partial_null_composite_foreign_key(self):
        book = self.workbook()
        book["sheets"]["Orders"]["rows"][0][1] = None
        valid, report = validate_workbook(book)
        self.assertFalse(valid)
        self.assertTrue(any("partially null" in e for e in report["errors"]))

    def test_requires_foreign_key_target_to_be_unique(self):
        book = self.workbook()
        book["sheets"]["Orders"]["foreign_keys"][0]["references"]["columns"] = ["name"]
        valid, report = validate_workbook(book)
        self.assertFalse(valid)
        self.assertTrue(any("primary key or unique column" in e for e in report["errors"]))

    def test_restricts_relations_to_schema_v2(self):
        book = self.workbook()
        book["schema_version"] = 1
        valid, report = validate_workbook(book)
        self.assertFalse(valid)
        self.assertTrue(any("require schema_version 2" in e for e in report["errors"]))

    def test_set_null_requires_nullable_local_columns(self):
        book = self.workbook()
        book["sheets"]["Orders"]["columns"][1]["nullable"] = False
        valid, report = validate_workbook(book)
        self.assertFalse(valid)
        self.assertTrue(any("set_null requires nullable" in e for e in report["errors"]))


if __name__ == "__main__":
    unittest.main()
