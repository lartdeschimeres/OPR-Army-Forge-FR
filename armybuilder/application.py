from pathlib import Path
from typing import Any

from armybuilder.config import GAME_CONFIG
from armybuilder.services import ArmyRuleValidator, FactionCatalogService
from armybuilder.session import SessionStateManager


class ArmyBuilderApplication:
    """High-level application service container."""

    def __init__(self, base_dir: Path, session_state: Any) -> None:
        self.base_dir = Path(base_dir)
        self.game_config = GAME_CONFIG
        self.session = SessionStateManager(session_state)
        self.catalog = FactionCatalogService(self.base_dir)
        self.validator = ArmyRuleValidator(self.game_config)

    def initialize(self) -> None:
        self.session.initialize_defaults()

    def load_factions(self) -> tuple[dict[str, dict[str, dict[str, Any]]], list[str]]:
        return self.catalog.load_factions()

    def load_generic_rules(self) -> dict[str, str]:
        return self.catalog.load_generic_rules()
