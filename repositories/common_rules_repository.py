import json
from pathlib import Path
from typing import Any


CommonRule = dict[str, str]


class CommonRulesRepository:
    """Repository responsible for reading common rules data."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / "repositories" / "data"

    def load_rules(self) -> list[CommonRule]:
        common_rules_path = self._resolve_common_rules_path()
        with common_rules_path.open(encoding="utf-8") as file:
            data = json.load(file)

        return [
            {
                "title": str(rule["title"]),
                "description": str(rule.get("description", "")),
            }
            for rule in data
            if isinstance(rule, dict) and rule.get("title")
        ]

    def load_rules_by_title(self) -> dict[str, str]:
        return {
            rule["title"]: rule["description"]
            for rule in self.load_rules()
        }

    def get_rule(self, title: str) -> CommonRule | None:
        rules_by_title = self.load_rules_by_title()
        if title not in rules_by_title:
            return None

        return {
            "title": title,
            "description": rules_by_title[title],
        }

    def _resolve_common_rules_path(self) -> Path:
        common_rules_path = self.data_dir / "common-rules" / "common-rules.json"
        if common_rules_path.exists():
            return common_rules_path

        raise FileNotFoundError(
            "Aucun fichier de regles communes trouve dans repositories/data/common-rules/common-rules.json."
        )
