from collections.abc import MutableMapping
from typing import Any

from armybuilder.config import DEFAULT_SESSION_STATE


class SessionStateManager:
    """Encapsulates Streamlit session state mutations."""

    def __init__(self, session_state: MutableMapping[str, Any]) -> None:
        self.session_state = session_state

    def initialize_defaults(self) -> None:
        for key, value in DEFAULT_SESSION_STATE.items():
            if key not in self.session_state:
                self.session_state[key] = self._clone_default(value)

    def reset_army(self) -> None:
        self.session_state["army_list"] = []
        self.session_state["army_cost"] = 0
        self.session_state["unit_selections"] = {}

    def apply_faction_selection(
        self,
        game: str,
        faction: str,
        points: int,
        list_name: str,
        faction_data: dict[str, Any],
    ) -> None:
        self.session_state["game"] = game
        self.session_state["faction"] = faction
        self.session_state["points"] = points
        self.session_state["list_name"] = list_name
        self.session_state["units"] = faction_data.get("units", [])
        self.session_state["faction_special_rules"] = faction_data.get(
            "faction_special_rules", []
        )
        self.session_state["faction_spells"] = faction_data.get("spells", {})
        self.session_state["faction_data"] = faction_data

    def load_qr_army_if_pending(self) -> None:
        if self.session_state.get("_qr_army_list"):
            self.session_state["army_list"] = self.session_state.pop("_qr_army_list")
            self.session_state["army_cost"] = self.session_state.pop("_qr_army_cost", 0)
            self.session_state["unit_selections"] = {}

    def load_imported_army(self, imported_data: dict[str, Any]) -> None:
        army_list = imported_data["army_list"]
        self.session_state["list_name"] = imported_data.get(
            "list_name", self.session_state.get("list_name", "")
        )
        self.session_state["army_list"] = army_list
        self.session_state["army_cost"] = imported_data.get(
            "army_cost", sum(unit["cost"] for unit in army_list)
        )

    @staticmethod
    def _clone_default(value: Any) -> Any:
        if isinstance(value, list):
            return list(value)
        if isinstance(value, dict):
            return dict(value)
        return value
