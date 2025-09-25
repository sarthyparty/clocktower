import random
from typing import Dict, List, Optional, Set
from role_actions import *

class NightActionManager:
    def __init__(self, game_instance):
        self.game = game_instance
        self.current_night_actions: Dict[str, RoleAction] = {}
        self.action_handlers = self._initialize_handlers()
        self.completed_actions: Set[str] = set()
        self.pending_actions: Set[str] = set()

    def _initialize_handlers(self):
        return {
            "Washerwoman": WasherwomanAction(self.game),
            "Librarian": WasherwomanAction(self.game),  # Similar to washerwoman
            "Investigator": WasherwomanAction(self.game),  # Similar to washerwoman
            "Chef": WasherwomanAction(self.game),  # Similar to washerwoman
            "Empath": EmphathAction(self.game),
            "Fortune Teller": FortuneTellerAction(self.game),
            "Monk": MonkAction(self.game),
            "Undertaker": PassiveRoleAction(self.game, ["Undertaker"]),
            "Poisoner": PoisonerAction(self.game),
            "Spy": PassiveRoleAction(self.game, ["Spy"]),
            "Imp": ImpAction(self.game),
            "Ravenkeeper": RavenkeeperAction(self.game),
            # Passive roles
            "passive": PassiveRoleAction(self.game, [
                "Virgin", "Slayer", "Soldier", "Mayor", "Recluse",
                "Saint", "Drunk", "Scarlet Woman", "Baron"
            ])
        }

    def start_night_phase(self) -> Dict:
        self.current_night_actions = {}
        self.completed_actions = set()
        self.pending_actions = set()

        # Reset night-specific states
        self.game.protected_tonight = None
        for player in self.game.players:
            if hasattr(player, 'died_at_night'):
                delattr(player, 'died_at_night')

        # Initialize actions for each player
        for player in self.game.players:
            if player.role:
                handler_key = player.role.name
                if handler_key not in self.action_handlers:
                    handler_key = "passive"

                handler = self.action_handlers[handler_key]
                if handler.can_act(player):
                    action = RoleAction(player.role.name, handler.get_action_type())
                    self.current_night_actions[player.username] = action

                    if action.action_type != ActionType.NO_ACTION:
                        self.pending_actions.add(player.username)
                    else:
                        # Auto-complete passive actions
                        action.status = ActionStatus.COMPLETED
                        self.completed_actions.add(player.username)

        return {
            "message": f"Night {self.game.night_count} actions initialized",
            "pending_actions": len(self.pending_actions),
            "players_with_actions": list(self.current_night_actions.keys())
        }

    def get_player_action_prompt(self, username: str) -> Dict:
        if username not in self.current_night_actions:
            return {"error": "No action available for this player"}

        action = self.current_night_actions[username]
        if action.status == ActionStatus.COMPLETED:
            return {"message": "Action already completed"}

        player = next((p for p in self.game.players if p.username == username), None)
        if not player:
            return {"error": "Player not found"}

        handler_key = player.role.name
        if handler_key not in self.action_handlers:
            handler_key = "passive"

        handler = self.action_handlers[handler_key]

        # Perform action to get prompt
        result = handler.perform_action(player)

        if "waiting_for_input" in result:
            action.status = ActionStatus.WAITING_INPUT
            return {
                "username": username,
                "role": player.role.name,
                "prompt": result["prompt"],
                "options": result.get("options", []),
                "required_count": result.get("required_count", 1),
                "action_type": action.action_type.value
            }
        elif "complete" in result and result["complete"]:
            action.status = ActionStatus.COMPLETED
            action.result = result
            self.completed_actions.add(username)
            if username in self.pending_actions:
                self.pending_actions.remove(username)
            return {
                "username": username,
                "role": player.role.name,
                "info": result.get("info", "Action completed"),
                "completed": True
            }
        else:
            return result

    def submit_player_action(self, username: str, choices: List[str]) -> Dict:
        if username not in self.current_night_actions:
            return {"error": "No action available for this player"}

        action = self.current_night_actions[username]
        if action.status == ActionStatus.COMPLETED:
            return {"error": "Action already completed"}

        player = next((p for p in self.game.players if p.username == username), None)
        if not player:
            return {"error": "Player not found"}

        handler_key = player.role.name
        if handler_key not in self.action_handlers:
            handler_key = "passive"

        handler = self.action_handlers[handler_key]
        result = handler.perform_action(player, choices)

        if "complete" in result and result["complete"]:
            action.status = ActionStatus.COMPLETED
            action.result = result
            action.choices = choices
            self.completed_actions.add(username)
            if username in self.pending_actions:
                self.pending_actions.remove(username)

            # Handle special actions
            if "kill_target" in result:
                target_player = next((p for p in self.game.players if p.username == result["kill_target"]), None)
                if target_player and self.game.protected_tonight != result["kill_target"]:
                    target_player.is_alive = False
                    target_player.died_at_night = True

            if "special_action" in result and result["special_action"] == "imp_suicide":
                player.is_alive = False
                # Convert a minion to imp (simplified)
                minions = [p for p in self.game.players if p.role.role_type.value == "minion" and p.is_alive]
                if minions:
                    new_imp = random.choice(minions)
                    new_imp.role = self.game.roles["imp"]

        return {
            "username": username,
            "result": result.get("info", "Action processed"),
            "completed": "complete" in result and result["complete"]
        }

    def can_progress_to_day(self) -> bool:
        return len(self.pending_actions) == 0

    def get_night_progress(self) -> Dict:
        total_actions = len(self.current_night_actions)
        completed_count = len(self.completed_actions)

        return {
            "total_actions": total_actions,
            "completed_actions": completed_count,
            "pending_actions": len(self.pending_actions),
            "can_progress": self.can_progress_to_day(),
            "pending_players": list(self.pending_actions)
        }

    def process_end_of_night(self) -> Dict:
        # Clear poison from previous night
        for player in self.game.players:
            player.is_poisoned = False

        # Apply new poison from Poisoner actions
        for username, action in self.current_night_actions.items():
            if action.result and action.choices:
                player = next((p for p in self.game.players if p.username == username), None)
                if player and player.role and player.role.name == "poisoner":
                    poisoned_target = action.choices[0]
                    poisoned = next((p for p in self.game.players if p.username == poisoned_target), None)
                    if poisoned:
                        poisoned.is_poisoned = True

        deaths = [p.username for p in self.game.players if hasattr(p, 'died_at_night') and p.died_at_night and not p.is_alive]

        return {
            "message": "Night phase completed",
            "deaths": deaths,
            "actions_completed": len(self.completed_actions)
        }