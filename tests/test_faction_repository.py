import json
import tempfile
import unittest
from pathlib import Path

from repositories.faction_repository import JsonFactionRepository


class JsonFactionRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)

        self.common_rules_dir = self.base_dir / "repositories" / "data" / "common-rules"
        self.factions_dir = self.base_dir / "repositories" / "data" / "factions"
        self.common_rules_dir.mkdir(parents=True)
        self.factions_dir.mkdir(parents=True)

        common_rules = [
            {"title": "Rule A", "description": "Description A"},
            {"title": "Rule B", "description": "Description B"},
        ]
        (self.common_rules_dir / "common-rules.json").write_text(
            json.dumps(common_rules, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        faction_a = {
            "game": "Game One",
            "faction": "Faction Alpha",
            "faction_special_rules": [
                "Rule A",
                {"name": "Rule B"},
                {"name": "Rule C", "description": "Custom Description C"},
                "",
                {"description": "ignored"},
            ],
            "units": [{"name": "Unit Alpha"}],
        }
        faction_b = {
            "game": "Game Two",
            "faction": "Faction Beta",
        }
        ignored_faction = {
            "game": "Game Three",
        }

        (self.factions_dir / "a_faction.json").write_text(
            json.dumps(faction_a, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (self.factions_dir / "b_faction.json").write_text(
            json.dumps(faction_b, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (self.factions_dir / "ignored.json").write_text(
            json.dumps(ignored_faction, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_load_catalog_groups_factions_by_game(self) -> None:
        repository = JsonFactionRepository(self.base_dir)

        factions_by_game, games = repository.load_catalog()

        self.assertEqual(games, ["Game One", "Game Two"])
        self.assertIn("Faction Alpha", factions_by_game["Game One"])
        self.assertIn("Faction Beta", factions_by_game["Game Two"])
        self.assertNotIn("Game Three", factions_by_game)

    def test_list_games_returns_sorted_games(self) -> None:
        repository = JsonFactionRepository(self.base_dir)

        games = repository.list_games()

        self.assertEqual(games, ["Game One", "Game Two"])

    def test_list_factions_returns_factions_for_requested_game(self) -> None:
        repository = JsonFactionRepository(self.base_dir)

        factions = repository.list_factions("Game One")

        self.assertEqual(list(factions.keys()), ["Faction Alpha"])

    def test_get_faction_returns_none_when_missing(self) -> None:
        repository = JsonFactionRepository(self.base_dir)

        faction = repository.get_faction("Game One", "Unknown Faction")

        self.assertIsNone(faction)

    def test_normalize_faction_restores_special_rules_with_descriptions(self) -> None:
        repository = JsonFactionRepository(self.base_dir)

        faction = repository.get_faction("Game One", "Faction Alpha")

        self.assertEqual(
            faction["faction_special_rules"],
            [
                {"name": "Rule A", "description": "Description A"},
                {"name": "Rule B", "description": "Description B"},
                {"name": "Rule C", "description": "Custom Description C"},
            ],
        )

    def test_normalize_faction_applies_default_values(self) -> None:
        repository = JsonFactionRepository(self.base_dir)

        faction = repository.get_faction("Game Two", "Faction Beta")

        self.assertEqual(faction["faction_special_rules"], [])
        self.assertEqual(faction["spells"], {})
        self.assertEqual(faction["units"], [])

    def test_load_catalog_raises_when_factions_directory_is_missing(self) -> None:
        repository = JsonFactionRepository(self.base_dir)
        for file_path in self.factions_dir.glob("*.json"):
            file_path.unlink()
        self.factions_dir.rmdir()

        with self.assertRaises(FileNotFoundError):
            repository.load_catalog()


if __name__ == "__main__":
    unittest.main()
