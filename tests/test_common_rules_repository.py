import json
import tempfile
import unittest
from pathlib import Path

from repositories.common_rules_repository import CommonRulesRepository


class CommonRulesRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        self.common_rules_dir = self.base_dir / "repositories" / "data" / "common-rules"
        self.common_rules_dir.mkdir(parents=True)

        self.rules_payload = [
            {"title": "Rule A", "description": "Description A"},
            {"title": "Rule B", "description": "Description B"},
            {"title": "Rule C"},
            {"description": "Ignored because title is missing"},
            "ignored",
        ]
        (self.common_rules_dir / "common-rules.json").write_text(
            json.dumps(self.rules_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_load_rules_filters_invalid_entries(self) -> None:
        repository = CommonRulesRepository(self.base_dir)

        rules = repository.load_rules()

        self.assertEqual(
            rules,
            [
                {"title": "Rule A", "description": "Description A"},
                {"title": "Rule B", "description": "Description B"},
                {"title": "Rule C", "description": ""},
            ],
        )

    def test_load_rules_by_title_returns_lookup_table(self) -> None:
        repository = CommonRulesRepository(self.base_dir)

        rules_by_title = repository.load_rules_by_title()

        self.assertEqual(
            rules_by_title,
            {
                "Rule A": "Description A",
                "Rule B": "Description B",
                "Rule C": "",
            },
        )

    def test_get_rule_returns_single_rule_when_present(self) -> None:
        repository = CommonRulesRepository(self.base_dir)

        rule = repository.get_rule("Rule B")

        self.assertEqual(
            rule,
            {"title": "Rule B", "description": "Description B"},
        )

    def test_get_rule_returns_none_when_missing(self) -> None:
        repository = CommonRulesRepository(self.base_dir)

        rule = repository.get_rule("Unknown Rule")

        self.assertIsNone(rule)

    def test_load_rules_raises_when_common_rules_file_is_missing(self) -> None:
        repository = CommonRulesRepository(self.base_dir)
        (self.common_rules_dir / "common-rules.json").unlink()

        with self.assertRaises(FileNotFoundError):
            repository.load_rules()


if __name__ == "__main__":
    unittest.main()
