import random
from typing import List, Dict, Any
from roles import Player, Role, RoleType, Team, roles

class RoleExecutor:
    def __init__(self, players: List[Player]):
        self.players = players

    def get_player_by_name(self, username: str) -> Player:
        return next(p for p in self.players if p.username == username)

    def poisoner_action(self, username: str, choices: List[str]) -> str:
        if not choices:
            return "No target specified"

        target = self.get_player_by_name(choices[0])
        target.is_poisoned = True
        return f"{choices[0]} is poisoned"

    def imp_action(self, username: str, choices: List[str]) -> str:
        if not choices:
            return "No target specified"

        player = self.get_player_by_name(username)
        target_name = choices[0]

        if target_name == username:
            player.is_alive = False
            minions = [p for p in self.players if p.role and p.role.role_type == RoleType.MINION and p.is_alive]
            if minions:
                new_imp = random.choice(minions)
                new_imp.role = roles["imp"]
                return f"{username} kills themselves, {new_imp.username} becomes the new Imp"
            return f"{username} kills themselves"
        else:
            target = self.get_player_by_name(target_name)
            
            if target.role and target.role.name == "Soldier" and not target.is_poisoned:
                return f"{target_name} is safe (Soldier cannot be killed by Demon)"
            
            target.is_alive = False
            return f"{target_name} is killed"

    def monk_action(self, username: str, choices: List[str]) -> str:
        if not choices:
            return "No target specified"
        return f"{choices[0]} is protected tonight"

    def fortune_teller_action(self, username: str, choices: List[str]) -> str:
        if len(choices) < 2:
            player = self.get_player_by_name(username)
            other_players = [p for p in self.players if p != player and p.is_alive]
            if len(other_players) < 2:
                return "Not enough players to read"
            chosen_players = random.sample(other_players, 2)
            choices = [p.username for p in chosen_players]
        else:
            chosen_players = [self.get_player_by_name(name) for name in choices[:2]]

        has_demon = any(p.role and p.role.role_type == RoleType.DEMON for p in chosen_players)
        if has_demon:
            return f"YES - one of {choices[0]} or {choices[1]} is a Demon"
        else:
            return f"NO - neither {choices[0]} nor {choices[1]} is a Demon"

    def empath_action(self, username: str, choices: List[str]) -> str:
        player = self.get_player_by_name(username)
        player_index = self.players.index(player)
        left = self.players[(player_index - 1) % len(self.players)]
        right = self.players[(player_index + 1) % len(self.players)]

        evil_count = sum(1 for p in [left, right] if p.is_alive and p.role and p.role.team == Team.EVIL)
        return f"You sense {evil_count} evil neighbor(s)"

    def washerwoman_action(self, username: str, choices: List[str]) -> str:
        player = self.get_player_by_name(username)
        townsfolk = [p for p in self.players if p.role and p.role.role_type == RoleType.TOWNSFOLK and p != player]

        if not townsfolk:
            return "No townsfolk to show"

        correct = random.choice(townsfolk)
        others = [p for p in self.players if p != player and p != correct]

        if others:
            other = random.choice(others)
            pair = [correct, other]
            random.shuffle(pair)
            return f"Player [{pair[0].username}] or [{pair[1].username}] is the {correct.role.name}"
        else:
            return f"{correct.username} is the {correct.role.name}"

    def librarian_action(self, username: str, choices: List[str]) -> str:
        player = self.get_player_by_name(username)
        outsiders = [p for p in self.players if p.role and p.role.role_type == RoleType.OUTSIDER and p != player]

        if not outsiders:
            return "No outsiders to show"

        correct = random.choice(outsiders)
        others = [p for p in self.players if p != player and p != correct]

        if others:
            other = random.choice(others)
            pair = [correct, other]
            random.shuffle(pair)
            return f"Player [{pair[0].username}] or [{pair[1].username}] is the {correct.role.name}"
        else:
            return f"{correct.username} is the {correct.role.name}"

    def investigator_action(self, username: str, choices: List[str]) -> str:
        player = self.get_player_by_name(username)
        minions = [p for p in self.players if p.role and p.role.role_type == RoleType.MINION and p != player]

        if not minions:
            return "No minions to show"

        correct = random.choice(minions)
        others = [p for p in self.players if p != player and p != correct]

        if others:
            other = random.choice(others)
            pair = [correct, other]
            random.shuffle(pair)
            return f"Player [{pair[0].username}] or [{pair[1].username}] is the {correct.role.name}"
        else:
            return f"{correct.username} is the {correct.role.name}"

    def chef_action(self, username: str, choices: List[str]) -> str:
        # Chef counts pairs of evil players sitting next to each other
        adjacent_evil_pairs = 0

        for i in range(len(self.players)):
            current_player = self.players[i]
            next_player = self.players[(i + 1) % len(self.players)]  # Wrap around for circle

            # Check if both adjacent players are evil
            if (current_player.role and current_player.role.team == Team.EVIL and
                next_player.role and next_player.role.team == Team.EVIL):
                adjacent_evil_pairs += 1

        return f"Pairs of adjacent evil players: {adjacent_evil_pairs}"

    def undertaker_action(self, username: str, choices: List[str]) -> str:
        return "Undertaker sees executed players"

    def ravenkeeper_action(self, username: str, choices: List[str]) -> str:
        if not choices:
            return "No player selected"

        target = self.get_player_by_name(choices[0])
        return f"{target.username} is the {target.role.name if target.role else 'Unknown'}"

    def butler_action(self, username: str, choices: List[str]) -> str:
        return "Butler action completed"

    def spy_action(self, username: str, choices: List[str]) -> str:
        grimoire_info = []
        for player in self.players:
            if player.role:
                status = "alive" if player.is_alive else "dead"
                poison = " (poisoned)" if player.is_poisoned else ""
                grimoire_info.append(f"{player.username}: {player.role.name} ({player.role.team.value}) - {status}{poison}")
        
        return "GRIMOIRE:\n" + "\n".join(grimoire_info)

    def scarlet_woman_action(self, username: str, choices: List[str]) -> str:
        return "Scarlet Woman is ready to become Demon"
    
    def soldier_action(self, username: str, choices: List[str]) -> str:
        return "Soldier is protected"
    

    def execute_role_action(self, role_name: str, username: str, choices: List[str]) -> str:
        role_methods = {
            "Poisoner": self.poisoner_action,
            "Imp": self.imp_action,
            "Monk": self.monk_action,
            "Fortune Teller": self.fortune_teller_action,
            "Empath": self.empath_action,
            "Washerwoman": self.washerwoman_action,
            "Librarian": self.librarian_action,
            "Investigator": self.investigator_action,
            "Chef": self.chef_action,
            "Undertaker": self.undertaker_action,
            "Ravenkeeper": self.ravenkeeper_action,
            "Butler": self.butler_action,
            "Spy": self.spy_action,
            "Scarlet Woman": self.scarlet_woman_action,
            "Soldier": self.soldier_action
        }

        if role_name in role_methods:
            return role_methods[role_name](username, choices)
        else:
            return f"{role_name} action not implemented"