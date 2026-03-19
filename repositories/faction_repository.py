import json
from pathlib import Path
from typing import Any
from repositories.common_rules_repository import CommonRulesRepository


FactionData = dict[str, Any]
FactionsByGame = dict[str, dict[str, FactionData]]


class JsonFactionRepository:
    """Repository responsible for reading faction data from JSON files."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / "repositories" / "data"
        self.common_rules_repository = CommonRulesRepository(self.base_dir)
        self._common_rules_by_title = self.common_rules_repository.load_rules_by_title()

    def load_catalog(self) -> tuple[FactionsByGame, list[str]]:
        factions: FactionsByGame = {}
        games: set[str] = set()

        for file_path in self._iter_faction_files():
            data = self._load_file(file_path)
            game = data.get("game")
            faction = data.get("faction")
            if not game or not faction:
                continue

            if game not in factions:
                factions[game] = {}

            factions[game][faction] = self._normalize_faction(data)
            games.add(game)

        return factions, sorted(games)

    def list_games(self) -> list[str]:
        _, games = self.load_catalog()
        return games

    def list_factions(self, game: str) -> dict[str, FactionData]:
        factions_by_game, _ = self.load_catalog()
        return factions_by_game.get(game, {})

    def get_faction(self, game: str, faction: str) -> FactionData | None:
        return self.list_factions(game).get(faction)

    def _iter_faction_files(self) -> list[Path]:
        factions_dir = self._resolve_factions_dir()
        return sorted(factions_dir.glob("*.json"))

    def _resolve_factions_dir(self) -> Path:
        factions_dir = self.data_dir / "factions"
        if factions_dir.exists():
            return factions_dir

        raise FileNotFoundError(
            "Aucun dossier de factions trouve dans repositories/data/factions."
        )

    def _load_file(self, file_path: Path) -> FactionData:
        with file_path.open(encoding="utf-8") as file:
            return json.load(file)

    def _normalize_faction(self, data: FactionData) -> FactionData:
        normalized = dict(data)
        normalized["faction_special_rules"] = self._hydrate_faction_special_rules(
            normalized.get("faction_special_rules", [])
        )
        normalized.setdefault("spells", {})
        normalized.setdefault("units", [])
        return normalized

    def _hydrate_faction_special_rules(self, rules: list[Any]) -> list[dict[str, str]]:
        hydrated_rules: list[dict[str, str]] = []

        for rule in rules:
            if isinstance(rule, dict):
                name = rule.get("name")
                if not name:
                    continue
                hydrated_rules.append(
                    {
                        "name": name,
                        "description": rule.get(
                            "description", self._common_rules_by_title.get(name, "")
                        ),
                    }
                )
                continue

            if isinstance(rule, str) and rule:
                hydrated_rules.append(
                    {
                        "name": rule,
                        "description": self._common_rules_by_title.get(rule, ""),
                    }
                )

        return hydrated_rules
