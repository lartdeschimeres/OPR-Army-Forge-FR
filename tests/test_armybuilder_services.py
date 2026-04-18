import unittest

from armybuilder.config import DEFAULT_SESSION_STATE, GAME_CONFIG
from armybuilder.services import ArmyRuleValidator
from armybuilder.session import SessionStateManager


class ArmyRuleValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = ArmyRuleValidator()
        self.game = "Age of Fantasy"
        self.config = GAME_CONFIG[self.game]

    def test_check_hero_limit_returns_error_when_limit_exceeded(self) -> None:
        army_list = [{"type": "hero"}, {"type": "hero"}, {"type": "unit"}]

        error = self.validator.check_hero_limit(army_list, 500, self.config)

        self.assertEqual(
            error,
            "Limite de héros dépassée! Max: 1 (1 héros/500 pts)",
        )

    def test_check_unit_max_cost_returns_error_when_unit_too_expensive(self) -> None:
        army_list = [{"name": "Dragon", "cost": 1000}]

        error = self.validator.check_unit_max_cost(army_list, 2000, self.config)

        self.assertEqual(error, "Unité Dragon dépasse 800 pts (35% du total)")

    def test_check_unit_copy_rule_returns_error_when_too_many_copies(self) -> None:
        army_list = [
            {"name": "Guerriers"},
            {"name": "Guerriers"},
            {"name": "Guerriers"},
            {"name": "Guerriers"},
        ]

        error = self.validator.check_unit_copy_rule(army_list, 2000, self.config)

        self.assertEqual(error, "Trop de copies de Guerriers! Max: 3")

    def test_summarize_army_returns_caps_and_current_counts(self) -> None:
        army_list = [{"type": "hero"}, {"type": "unit"}, {"type": "unit"}]

        summary = self.validator.summarize_army(army_list, 2000, self.game)

        self.assertEqual(
            summary,
            {
                "unit_cap": 10,
                "units_now": 2,
                "hero_cap": 4,
                "heroes_now": 1,
                "copy_cap": 3,
            },
        )


class SessionStateManagerTests(unittest.TestCase):
    def test_initialize_defaults_populates_missing_values(self) -> None:
        state = {}

        SessionStateManager(state).initialize_defaults()

        self.assertEqual(state["page"], DEFAULT_SESSION_STATE["page"])
        self.assertEqual(state["army_list"], [])
        self.assertIsNot(state["army_list"], DEFAULT_SESSION_STATE["army_list"])

    def test_apply_faction_selection_updates_session(self) -> None:
        state = {}
        manager = SessionStateManager(state)
        manager.initialize_defaults()
        faction_data = {
            "units": [{"name": "Soldat"}],
            "faction_special_rules": [{"name": "Brave"}],
            "spells": {"Feu": {"description": "Boule de feu"}},
        }

        manager.apply_faction_selection(
            game="Age of Fantasy",
            faction="Humains",
            points=2000,
            list_name="Liste test",
            faction_data=faction_data,
        )

        self.assertEqual(state["game"], "Age of Fantasy")
        self.assertEqual(state["faction"], "Humains")
        self.assertEqual(state["points"], 2000)
        self.assertEqual(state["units"], faction_data["units"])
        self.assertEqual(state["faction_data"], faction_data)

    def test_reset_army_clears_army_specific_state(self) -> None:
        state = {
            "army_list": [{"name": "Unit"}],
            "army_cost": 120,
            "unit_selections": {"u1": {"group_1": "Option"}},
        }

        SessionStateManager(state).reset_army()

        self.assertEqual(state["army_list"], [])
        self.assertEqual(state["army_cost"], 0)
        self.assertEqual(state["unit_selections"], {})

    def test_load_qr_army_if_pending_moves_pending_payload(self) -> None:
        state = {
            "_qr_army_list": [{"name": "Unit"}],
            "_qr_army_cost": 250,
            "unit_selections": {"old": True},
        }

        SessionStateManager(state).load_qr_army_if_pending()

        self.assertEqual(state["army_list"], [{"name": "Unit"}])
        self.assertEqual(state["army_cost"], 250)
        self.assertEqual(state["unit_selections"], {})
        self.assertNotIn("_qr_army_list", state)

    def test_load_imported_army_uses_existing_name_as_fallback(self) -> None:
        state = {"list_name": "Avant"}
        imported_data = {"army_list": [{"cost": 50}, {"cost": 75}]}

        SessionStateManager(state).load_imported_army(imported_data)

        self.assertEqual(state["list_name"], "Avant")
        self.assertEqual(state["army_cost"], 125)
        self.assertEqual(state["army_list"], imported_data["army_list"])


if __name__ == "__main__":
    unittest.main()
