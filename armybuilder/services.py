import math
from functools import lru_cache
from pathlib import Path
from typing import Any

from armybuilder.config import GAME_CONFIG
from repositories import CommonRulesRepository, JsonFactionRepository


FactionData = dict[str, Any]
FactionsByGame = dict[str, dict[str, FactionData]]


class FactionCatalogService:
    """Access layer for faction and common rules data."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir)
        self.faction_repository = JsonFactionRepository(self.base_dir)
        self.common_rules_repository = CommonRulesRepository(self.base_dir)

    @lru_cache(maxsize=1)
    def load_factions(self) -> tuple[FactionsByGame, list[str]]:
        factions, games = self.faction_repository.load_catalog()
        return factions, games or list(GAME_CONFIG.keys())

    @lru_cache(maxsize=1)
    def load_generic_rules(self) -> dict[str, str]:
        result: dict[str, str] = {}
        for rule in self.common_rules_repository.load_rules():
            description = rule.get("description", "")
            title = rule.get("title")
            if title:
                result[title] = description
        return result


class ArmyRuleValidator:
    """Pure domain validation for game list-building rules."""

    def __init__(self, game_config_map: dict[str, dict[str, Any]] | None = None) -> None:
        self.game_config_map = game_config_map or GAME_CONFIG

    def validate_army(
        self, army_list: list[dict[str, Any]], army_points: int, game: str
    ) -> list[str]:
        game_config = self.game_config_map.get(game)
        if game_config is None:
            return []

        errors: list[str] = []
        hero_error = self.check_hero_limit(army_list, army_points, game_config)
        if hero_error:
            errors.append(hero_error)

        cost_error = self.check_unit_max_cost(army_list, army_points, game_config)
        if cost_error:
            errors.append(cost_error)

        copy_error = self.check_unit_copy_rule(army_list, army_points, game_config)
        if copy_error:
            errors.append(copy_error)

        return errors

    def check_hero_limit(
        self, army_list: list[dict[str, Any]], army_points: int, game_config: dict[str, Any]
    ) -> str | None:
        max_heroes = math.floor(army_points / game_config["hero_limit"])
        hero_count = sum(1 for unit in army_list if unit.get("type") == "hero")
        if hero_count > max_heroes:
            return (
                f"Limite de héros dépassée! Max: {max_heroes} "
                f"(1 héros/{game_config['hero_limit']} pts)"
            )
        return None

    def check_unit_max_cost(
        self,
        army_list: list[dict[str, Any]],
        army_points: int,
        game_config: dict[str, Any],
        new_unit_cost: int | None = None,
    ) -> str | None:
        max_cost = army_points * game_config["unit_max_cost_ratio"]
        for unit in army_list:
            if unit["cost"] > max_cost:
                return f"Unité {unit['name']} dépasse {int(max_cost)} pts (35% du total)"
        if new_unit_cost and new_unit_cost > max_cost:
            return f"Cette unité dépasse {int(max_cost)} pts (35% du total)"
        return None

    def check_unit_copy_rule(
        self, army_list: list[dict[str, Any]], army_points: int, game_config: dict[str, Any]
    ) -> str | None:
        max_copies = 1 + math.floor(army_points / game_config["unit_copy_rule"])
        unit_counts: dict[str, int] = {}
        for unit in army_list:
            name = unit["name"]
            unit_counts[name] = unit_counts.get(name, 0) + 1
        for unit_name, count in unit_counts.items():
            if count > max_copies:
                return f"Trop de copies de {unit_name}! Max: {max_copies}"
        return None

    def summarize_army(
        self, army_list: list[dict[str, Any]], army_points: int, game: str
    ) -> dict[str, int]:
        game_config = self.game_config_map.get(game)
        if game_config is None:
            return {
                "unit_cap": 0,
                "units_now": 0,
                "hero_cap": 0,
                "heroes_now": 0,
                "copy_cap": 0,
            }
        return {
            "unit_cap": math.floor(army_points / game_config["unit_per_points"]),
            "units_now": len([u for u in army_list if u.get("type") != "hero"]),
            "hero_cap": math.floor(army_points / game_config["hero_limit"]),
            "heroes_now": len([u for u in army_list if u.get("type") == "hero"]),
            "copy_cap": 1 + math.floor(army_points / game_config["unit_copy_rule"]),
        }
