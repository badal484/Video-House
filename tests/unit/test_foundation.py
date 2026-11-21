"""
Unit tests for Part 01 Architecture Foundation.
Compatible with standard library unittest and pytest.
"""
import csv
import json
import unittest
from pathlib import Path

REQUIRED_DOCUMENTS = [
    "GLOBAL_TECHNOLOGY_RESEARCH.md",
    "TECHNOLOGY_COMPARISON_MATRIX.md",
    "TOOL_REGISTRY.md",
    "MODEL_REGISTRY.md",
    "LICENSE_REGISTRY.csv",
    "COMPATIBILITY_MATRIX.md",
    "ENVIRONMENT_REPORT.md",
    "SYSTEM_ARCHITECTURE.md",
    "MULTIMODAL_INTELLIGENCE_ARCHITECTURE.md",
    "AGENT_ARCHITECTURE.md",
    "DATA_AND_TIMELINE_ARCHITECTURE.md",
    "ARCHITECTURE_DECISIONS.md",
    "IMPLEMENTATION_ROADMAP.md",
    "DEVELOPMENT_STATUS.md"
]

class TestArchitectureFoundation(unittest.TestCase):
    def test_all_14_required_documents_exist_and_non_empty(self):
        for doc_name in REQUIRED_DOCUMENTS:
            doc_path = Path(doc_name)
            self.assertTrue(doc_path.exists(), f"Required document {doc_name} is missing.")
            self.assertGreater(doc_path.stat().st_size, 100, f"Document {doc_name} is unexpectedly small or empty.")

    def test_license_registry_csv_validity(self):
        csv_path = Path("LICENSE_REGISTRY.csv")
        self.assertTrue(csv_path.exists())
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertGreaterEqual(len(rows), 20, "License registry should have at least 20 entries.")
            required_headers = {
                "Name", "Category", "CodeLicense", "WeightsLicense",
                "CommercialUsePermitted", "RestrictionsAndAttribution",
                "SourceURL", "VerifiedDate"
            }
            self.assertTrue(required_headers.issubset(set(reader.fieldnames or [])))

    def test_all_json_schemas_valid(self):
        schemas_dir = Path("schemas")
        schema_files = list(schemas_dir.glob("*.json"))
        self.assertGreaterEqual(len(schema_files), 5, "Expected at least 5 JSON schemas.")
        for schema_file in schema_files:
            with open(schema_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.assertTrue("$schema" in data or "type" in data, f"Schema {schema_file.name} missing schema or type declaration.")

    def test_all_22_departments_exist(self):
        dept_dir = Path("departments")
        depts = [d for d in dept_dir.iterdir() if d.is_dir() and d.name[0].isdigit()]
        self.assertEqual(len(depts), 22, f"Expected exactly 22 departments, found {len(depts)}.")
        for d in depts:
            self.assertTrue((d / "__init__.py").exists(), f"Missing __init__.py in {d.name}")
            self.assertTrue((d / "interface.py").exists(), f"Missing interface.py in {d.name}")

if __name__ == "__main__":
    unittest.main()
