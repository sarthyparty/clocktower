from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
from enum import Enum

class ActionType(Enum):
    CHOOSE_PLAYERS = "choose_players"
    CHOOSE_PLAYER = "choose_player"
    RECEIVE_INFO = "receive_info"
    NO_ACTION = "no_action"
    OPTIONAL_ACTION = "optional_action"

class ActionStatus(Enum):
    PENDING = "pending"
    WAITING_INPUT = "waiting_input"
    COMPLETED = "completed"
    SKIPPED = "skipped"

class RoleAction:
    def __init__(self, role_name: str, action_type: ActionType, required: bool = True):
        self.role_name = role_name
        self.action_type = action_type
        self.required = required
        self.status = ActionStatus.PENDING
        self.result: Optional[Any] = None
        self.choices: Optional[List[str]] = None

class RoleActionHandler(ABC):
    def __init__(self, game_instance):
        self.game = game_instance

    @abstractmethod
    def can_act(self, player) -> bool:
        pass

    @abstractmethod
    def perform_action(self, player, choices: List[str] = None) -> Dict:
        pass

    @abstractmethod
    def get_action_type(self) -> ActionType:
        pass

class WasherwomanAction(RoleActionHandler):
    def can_act(self, player) -> bool:
        return player.role.name in ["Washerwoman", "Librarian", "Investigator", "Chef"] and self.game.night_count == 0 and player.is_alive

    def perform_action(self, player, choices: List[str] = None) -> Dict:
        if player.role.name == "Librarian":
            # Librarian sees Outsiders
            target_players = [p for p in self.game.players if p.role.role_type.value == "outsider" and p != player]
            role_type = "Outsider"
        else:
            # Washerwoman/Investigator/Chef see Townsfolk/Minions/etc
            target_players = [p for p in self.game.players if p.role.role_type.value == "townsfolk" and p != player]
            role_type = "Townsfolk"

        if len(target_players) < 1:
            # Add a bluff if no valid targets
            all_players = [p for p in self.game.players if p != player]
            if len(all_players) >= 2:
                selected = self.game._random.sample(all_players, 2)
                return {
                    "info": f"One of {selected[0].username} or {selected[1].username} is a {role_type} (but neither actually is)",
                    "complete": True
                }
            return {"info": f"Not enough players for {player.role.name} info", "complete": True}

        if len(target_players) == 1:
            # Only one target - add a random other player
            other_players = [p for p in self.game.players if p != player and p != target_players[0]]
            if other_players:
                other = self.game._random.choice(other_players)
                selected = [target_players[0], other]
                self.game._random.shuffle(selected)
            else:
                selected = [target_players[0]]
        else:
            # Multiple targets - pick one correct and one random
            correct = self.game._random.choice(target_players)
            other_players = [p for p in self.game.players if p != player and p != correct]
            if other_players:
                other = self.game._random.choice(other_players)
                selected = [correct, other]
                self.game._random.shuffle(selected)
            else:
                selected = [correct]

        if len(selected) == 2:
            correct_player = next(p for p in selected if p.role.role_type.value.lower() == role_type.lower())
            return {
                "info": f"One of {selected[0].username} or {selected[1].username} is the {correct_player.role.name}",
                "complete": True
            }
        else:
            return {
                "info": f"{selected[0].username} is the {selected[0].role.name}",
                "complete": True
            }

    def get_action_type(self) -> ActionType:
        return ActionType.RECEIVE_INFO

class EmphathAction(RoleActionHandler):
    def can_act(self, player) -> bool:
        return player.role.name == "Empath" and player.is_alive

    def perform_action(self, player, choices: List[str] = None) -> Dict:
        player_index = self.game.players.index(player)
        left_neighbor = self.game.players[(player_index - 1) % len(self.game.players)]
        right_neighbor = self.game.players[(player_index + 1) % len(self.game.players)]

        evil_count = 0
        if left_neighbor.is_alive and left_neighbor.role.team.value == "evil":
            evil_count += 1
        if right_neighbor.is_alive and right_neighbor.role.team.value == "evil":
            evil_count += 1

        return {
            "info": f"You sense {evil_count} evil neighbor(s)",
            "complete": True
        }

    def get_action_type(self) -> ActionType:
        return ActionType.RECEIVE_INFO

class FortuneTellerAction(RoleActionHandler):
    def can_act(self, player) -> bool:
        return player.role.name == "Fortune Teller" and player.is_alive

    def perform_action(self, player, choices: List[str] = None) -> Dict:
        if not choices or len(choices) != 2:
            alive_players = [p.username for p in self.game.players if p.is_alive and p != player]
            return {
                "waiting_for_input": True,
                "prompt": "Choose 2 players to read",
                "options": alive_players,
                "required_count": 2
            }

        chosen_players = [p for p in self.game.players if p.username in choices]
        has_demon = any(p.role.role_type.value == "demon" for p in chosen_players)

        return {
            "info": f"{'YES' if has_demon else 'NO'} - one of {choices[0]} or {choices[1]} is a Demon",
            "complete": True
        }

    def get_action_type(self) -> ActionType:
        return ActionType.CHOOSE_PLAYERS

class MonkAction(RoleActionHandler):
    def can_act(self, player) -> bool:
        return player.role.name == "Monk" and player.is_alive and self.game.night_count > 0

    def perform_action(self, player, choices: List[str] = None) -> Dict:
        if not choices or len(choices) != 1:
            alive_players = [p.username for p in self.game.players if p.is_alive and p != player]
            return {
                "waiting_for_input": True,
                "prompt": "Choose a player to protect tonight",
                "options": alive_players,
                "required_count": 1
            }

        protected_player = choices[0]
        self.game.protected_tonight = protected_player

        return {
            "info": f"You protect {protected_player} tonight",
            "complete": True
        }

    def get_action_type(self) -> ActionType:
        return ActionType.CHOOSE_PLAYER

class PoisonerAction(RoleActionHandler):
    def can_act(self, player) -> bool:
        return player.role.name == "Poisoner" and player.is_alive

    def perform_action(self, player, choices: List[str] = None) -> Dict:
        if not choices or len(choices) != 1:
            alive_players = [p.username for p in self.game.players if p.is_alive and p != player]
            return {
                "waiting_for_input": True,
                "prompt": "Choose a player to poison",
                "options": alive_players,
                "required_count": 1
            }

        poisoned_player = next((p for p in self.game.players if p.username == choices[0]), None)
        if poisoned_player:
            poisoned_player.is_poisoned = True

        return {
            "info": f"You poison {choices[0]}",
            "complete": True
        }

    def get_action_type(self) -> ActionType:
        return ActionType.CHOOSE_PLAYER

class ImpAction(RoleActionHandler):
    def can_act(self, player) -> bool:
        return player.role.name == "Imp" and player.is_alive and self.game.night_count > 0

    def perform_action(self, player, choices: List[str] = None) -> Dict:
        if not choices or len(choices) != 1:
            all_players = [p.username for p in self.game.players if p.is_alive]
            return {
                "waiting_for_input": True,
                "prompt": "Choose a player to kill (or yourself)",
                "options": all_players,
                "required_count": 1
            }

        target = choices[0]
        if target == player.username:
            return {
                "info": f"You kill yourself - a minion will become the Imp",
                "complete": True,
                "special_action": "imp_suicide"
            }
        else:
            return {
                "info": f"You kill {target}",
                "complete": True,
                "kill_target": target
            }

    def get_action_type(self) -> ActionType:
        return ActionType.CHOOSE_PLAYER

class RavenkeeperAction(RoleActionHandler):
    def can_act(self, player) -> bool:
        return player.role.name == "Ravenkeeper" and not player.is_alive and hasattr(player, 'died_at_night') and player.died_at_night

    def perform_action(self, player, choices: List[str] = None) -> Dict:
        if not choices or len(choices) != 1:
            alive_players = [p.username for p in self.game.players if p.is_alive]
            return {
                "waiting_for_input": True,
                "prompt": "You died at night - choose a player to learn their role",
                "options": alive_players,
                "required_count": 1
            }

        target_player = next((p for p in self.game.players if p.username == choices[0]), None)
        if target_player:
            return {
                "info": f"{target_player.username} is the {target_player.role.name}",
                "complete": True
            }

        return {"error": "Player not found"}

    def get_action_type(self) -> ActionType:
        return ActionType.CHOOSE_PLAYER

# Passive roles that don't need actions
class PassiveRoleAction(RoleActionHandler):
    def __init__(self, game_instance, role_names: List[str]):
        super().__init__(game_instance)
        self.role_names = role_names

    def can_act(self, player) -> bool:
        return player.role.name in self.role_names

    def perform_action(self, player, choices: List[str] = None) -> Dict:
        return {"complete": True, "info": "No action required"}

    def get_action_type(self) -> ActionType:
        return ActionType.NO_ACTION