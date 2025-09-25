from typing import Dict, List, Optional
from roles import Player

class ActionCollector:
    def __init__(self, completion_callback=None):
        self.expected_players: Dict[str, str] = {}
        self.collected_actions: Dict[str, List[str]] = {}
        self.is_complete = False
        self.completion_callback = completion_callback

    def initialize_collection(self, players_needing_actions: Dict[str, str]):
        self.expected_players = players_needing_actions.copy()
        self.collected_actions = {}
        self.is_complete = False

    def submit_action(self, username: str, choices: List[str]) -> Dict:
        if username not in self.expected_players:
            return {"error": f"Player {username} is not expected to submit an action"}

        if username in self.collected_actions:
            return {"error": f"Player {username} has already submitted their action"}

        self.collected_actions[username] = choices

        if len(self.collected_actions) == len(self.expected_players):
            self.is_complete = True
            if self.completion_callback:
                self.completion_callback()

        return {
            "success": True,
            "message": f"Action submitted for {username}",
            "collection_complete": self.is_complete
        }

    def get_collection_status(self) -> Dict:
        pending_players = [username for username in self.expected_players.keys()
                          if username not in self.collected_actions]

        return {
            "total_expected": len(self.expected_players),
            "collected": len(self.collected_actions),
            "pending_players": pending_players,
            "is_complete": self.is_complete
        }

    def get_collected_actions(self) -> Dict[str, Dict]:
        if not self.is_complete:
            return {"error": "Collection not yet complete"}

        result = {}
        for username, choices in self.collected_actions.items():
            result[username] = {
                "role": self.expected_players[username],
                "choices": choices
            }

        return result

    def set_completion_callback(self, callback):
        self.completion_callback = callback

    def reset(self):
        self.expected_players = {}
        self.collected_actions = {}
        self.is_complete = False