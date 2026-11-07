import unittest

from xlsl import XLSLFormatError, MigrationRegistry


class XLSLMigrationTests(unittest.TestCase):
    def workbook(self):
        return {"schema_version": 1, "sheets": {
            "Items": {"columns": ["id"], "rows": [["A"], ["B"]]}
        }}

    def test_register_and_plan_explicit_steps(self):
        registry = MigrationRegistry()
        registry.register(1, 2, lambda book: book)
        registry.register(2, 3, lambda book: book)
        self.assertEqual(registry.plan(1, 3), ((1, 2), (2, 3)))

    def test_migration_is_copy_on_write_and_dry_run_by_default(self):
        registry = MigrationRegistry()
        registry.register(1, 2, lambda book: book)
        original = self.workbook()
        result = registry.migrate(original, 2)
        self.assertEqual(result.workbook["schema_version"], 2)
        self.assertTrue(result.dry_run)
        self.assertEqual(original["schema_version"], 1)
        self.assertEqual(result.applied, ((1, 2),))

    def test_no_implicit_migration_is_invented(self):
        with self.assertRaises(XLSLFormatError):
            MigrationRegistry().migrate(self.workbook(), 2)

    def test_rejects_duplicate_registration(self):
        registry = MigrationRegistry()
        registry.register(1, 2, lambda book: book)
        with self.assertRaises(ValueError):
            registry.register(1, 2, lambda book: book)

    def test_rejects_invalid_migration_output(self):
        registry = MigrationRegistry()
        registry.register(1, 2, lambda book: {"schema_version": 2, "sheets": {}})
        with self.assertRaises(XLSLFormatError):
            registry.migrate(self.workbook(), 2)


if __name__ == "__main__":
    unittest.main()
