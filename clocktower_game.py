import random
from enum import Enum
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from night_actions import NightActionManager

class GamePhase(Enum):
    SETUP = "setup"
    DAY = "day"
    NIGHT = "night"
    ENDED = "ended"

class Team(Enum):
    GOOD = "good"
    EVIL = "evil"

class RoleType(Enum):
    TOWNSFOLK = "townsfolk"
    OUTSIDER = "outsider"
    MINION = "minion"
    DEMON = "demon"

@dataclass
class Role:
    name: str
    role_type: RoleType
    team: Team
    description: str
    night_order: Optional[int] = None
    first_night_order: Optional[int] = None

@dataclass
class Player:
    username: str
    role: Optional[Role] = None
    is_alive: bool = True
    is_poisoned: bool = False
    votes: int = 0
    nominated: bool = False
    ghost_vote_used: bool = False

class ClocktowerGame:
    def __init__(self):
        self.players: List[Player] = []
        self.phase: GamePhase = GamePhase.SETUP
        self.day_count: int = 0
        self.night_count: int = 0
        self.demon_kills: List[str] = []
        self.nominations: List[Dict] = []
        self.storyteller_notes: List[str] = []
        self.roles = self._initialize_roles()
        self.night_action_manager = NightActionManager(self)
        self.protected_tonight: Optional[str] = None
        self._random = random

    def _initialize_roles(self) -> Dict[str, Role]:
        return {
            # Townsfolk
            "washerwoman": Role("Washerwoman", RoleType.TOWNSFOLK, Team.GOOD,
                               "You start knowing that 1 of 2 players is a particular Townsfolk.",
                               first_night_order=1),
            "librarian": Role("Librarian", RoleType.TOWNSFOLK, Team.GOOD,
                             "You start knowing that 1 of 2 players is a particular Outsider.",
                             first_night_order=2),
            "investigator": Role("Investigator", RoleType.TOWNSFOLK, Team.GOOD,
                                "You start knowing that 1 of 2 players is a particular Minion.",
                                first_night_order=3),
            "chef": Role("Chef", RoleType.TOWNSFOLK, Team.GOOD,
                        "You start knowing how many pairs of evil players there are.",
                        first_night_order=4),
            "empath": Role("Empath", RoleType.TOWNSFOLK, Team.GOOD,
                          "Each night, you learn how many of your 2 alive neighbors are evil.",
                          night_order=1),
            "fortune_teller": Role("Fortune Teller", RoleType.TOWNSFOLK, Team.GOOD,
                                  "Each night, choose 2 players: you learn if either is a Demon.",
                                  night_order=2),
            "undertaker": Role("Undertaker", RoleType.TOWNSFOLK, Team.GOOD,
                              "Each night*, you learn which character died by execution today.",
                              night_order=3),
            "monk": Role("Monk", RoleType.TOWNSFOLK, Team.GOOD,
                        "Each night*, choose a player (not yourself): they are safe from the Demon tonight.",
                        night_order=4),
            "ravenkeeper": Role("Ravenkeeper", RoleType.TOWNSFOLK, Team.GOOD,
                               "If you die at night, you are woken to choose a player: you learn their character."),
            "virgin": Role("Virgin", RoleType.TOWNSFOLK, Team.GOOD,
                          "The 1st time you are nominated, if the nominator is a Townsfolk, they are executed immediately."),
            "slayer": Role("Slayer", RoleType.TOWNSFOLK, Team.GOOD,
                          "Once per game, during the day, publicly choose a player: if they are the Demon, they die."),
            "soldier": Role("Soldier", RoleType.TOWNSFOLK, Team.GOOD,
                           "You are safe from the Demon."),
            "mayor": Role("Mayor", RoleType.TOWNSFOLK, Team.GOOD,
                         "If only 3 players live & no execution occurs, your team wins."),

            # Outsiders
            "recluse": Role("Recluse", RoleType.OUTSIDER, Team.GOOD,
                           "You might register as evil & as a Minion or Demon, even when dead."),
            "saint": Role("Saint", RoleType.OUTSIDER, Team.GOOD,
                         "If you die by execution, your team loses."),
            "drunk": Role("Drunk", RoleType.OUTSIDER, Team.GOOD,
                         "You do not know you are the Drunk. You think you are a Townsfolk character, but you are not."),
            "poisoner": Role("Poisoner", RoleType.MINION, Team.EVIL,
                            "Each night, choose a player: they are poisoned tonight and tomorrow day.",
                            night_order=5),
            "spy": Role("Spy", RoleType.MINION, Team.EVIL,
                       "Each night, you see the Grimoire. You might register as good & as a Townsfolk or Outsider, even when dead.",
                       night_order=6),
            "scarlet_woman": Role("Scarlet Woman", RoleType.MINION, Team.EVIL,
                                 "If there are 5 or more players alive & the Demon dies, you become the Demon."),
            "baron": Role("Baron", RoleType.MINION, Team.EVIL,
                         "There are extra Outsiders in play."),

            # Demons
            "imp": Role("Imp", RoleType.DEMON, Team.EVIL,
                       "Each night*, choose a player: they die. If you kill yourself this way, a Minion becomes the Imp.",
                       night_order=7),
        }

    def start_game(self, usernames: List[str]) -> Dict:
        if len(usernames) < 5 or len(usernames) > 15:
            return {"error": "Game requires 5-15 players"}

        self.players = [Player(username) for username in usernames]
        player_count = len(usernames)

        role_distribution = self._get_role_distribution(player_count)
        selected_roles = self._select_roles(role_distribution)
        self._assign_roles(selected_roles)

        self.phase = GamePhase.NIGHT
        self.night_count = 0

        # Initialize first night actions
        night_result = self.night_action_manager.start_night_phase()

        return {
            "message": f"Game started with {player_count} players",
            "phase": self.phase.value,
            "players": [{"username": p.username, "alive": p.is_alive} for p in self.players],
            "role_distribution": role_distribution,
            "night_actions": night_result
        }

    def _get_role_distribution(self, player_count: int) -> Dict[RoleType, int]:
        if player_count == 5:
            return {RoleType.TOWNSFOLK: 3, RoleType.OUTSIDER: 0, RoleType.MINION: 1, RoleType.DEMON: 1}
        elif player_count == 6:
            return {RoleType.TOWNSFOLK: 3, RoleType.OUTSIDER: 1, RoleType.MINION: 1, RoleType.DEMON: 1}
        elif player_count == 7:
            return {RoleType.TOWNSFOLK: 5, RoleType.OUTSIDER: 0, RoleType.MINION: 1, RoleType.DEMON: 1}
        elif player_count == 8:
            return {RoleType.TOWNSFOLK: 5, RoleType.OUTSIDER: 1, RoleType.MINION: 1, RoleType.DEMON: 1}
        elif player_count == 9:
            return {RoleType.TOWNSFOLK: 5, RoleType.OUTSIDER: 2, RoleType.MINION: 1, RoleType.DEMON: 1}
        elif player_count == 10:
            return {RoleType.TOWNSFOLK: 7, RoleType.OUTSIDER: 0, RoleType.MINION: 2, RoleType.DEMON: 1}
        else:
            townsfolk = max(3, player_count - 4)
            outsiders = max(0, (player_count - 7) // 2)
            minions = min(3, player_count // 4)
            return {RoleType.TOWNSFOLK: townsfolk, RoleType.OUTSIDER: outsiders,
                   RoleType.MINION: minions, RoleType.DEMON: 1}

    def _select_roles(self, distribution: Dict[RoleType, int]) -> List[Role]:
        selected = []

        townsfolk_roles = [r for r in self.roles.values() if r.role_type == RoleType.TOWNSFOLK]
        outsider_roles = [r for r in self.roles.values() if r.role_type == RoleType.OUTSIDER]
        minion_roles = [r for r in self.roles.values() if r.role_type == RoleType.MINION]
        demon_roles = [r for r in self.roles.values() if r.role_type == RoleType.DEMON]

        selected.extend(random.sample(townsfolk_roles, distribution[RoleType.TOWNSFOLK]))
        if distribution[RoleType.OUTSIDER] > 0:
            selected.extend(random.sample(outsider_roles, min(distribution[RoleType.OUTSIDER], len(outsider_roles))))
        selected.extend(random.sample(minion_roles, min(distribution[RoleType.MINION], len(minion_roles))))
        selected.extend(random.sample(demon_roles, 1))

        return selected

    def _assign_roles(self, roles: List[Role]):
        random.shuffle(self.players)
        for i, player in enumerate(self.players):
            if i < len(roles):
                player.role = roles[i]

    def progress_to_day(self) -> Dict:
        if self.phase != GamePhase.NIGHT:
            return {"error": "Can only progress to day from night"}

        if not self.night_action_manager.can_progress_to_day():
            return {"error": "Cannot progress to day - pending night actions",
                   "pending": self.night_action_manager.get_night_progress()}

        # Process end of night effects
        night_end_result = self.night_action_manager.process_end_of_night()

        self.day_count += 1
        self.phase = GamePhase.DAY
        self.nominations = []

        alive_players = [p for p in self.players if p.is_alive]

        return {
            "message": f"Day {self.day_count} begins",
            "phase": self.phase.value,
            "day_count": self.day_count,
            "alive_players": len(alive_players),
            "players": [{"username": p.username, "alive": p.is_alive} for p in self.players],
            "night_results": night_end_result
        }

    def progress_to_night(self) -> Dict:
        if self.phase != GamePhase.DAY:
            return {"error": "Can only progress to night from day"}

        self.night_count += 1
        self.phase = GamePhase.NIGHT

        for player in self.players:
            player.nominated = False
            player.votes = 0

        # Initialize night actions
        night_result = self.night_action_manager.start_night_phase()

        return {
            "message": f"Night {self.night_count} begins",
            "phase": self.phase.value,
            "night_count": self.night_count,
            "alive_players": len([p for p in self.players if p.is_alive]),
            "night_actions": night_result
        }

    def get_game_state(self) -> Dict:
        return {
            "phase": self.phase.value,
            "day_count": self.day_count,
            "night_count": self.night_count,
            "players": [
                {
                    "username": p.username,
                    "alive": p.is_alive,
                    "poisoned": p.is_poisoned,
                    "votes": p.votes,
                    "nominated": p.nominated,
                    "ghost_vote_used": p.ghost_vote_used,
                    "role": p.role.name if p.role else None
                } for p in self.players
            ],
            "alive_count": len([p for p in self.players if p.is_alive]),
            "nominations": self.nominations
        }

    def nominate_player(self, nominator: str, nominated: str) -> Dict:
        if self.phase != GamePhase.DAY:
            return {"error": "Nominations only allowed during day phase"}

        nominator_player = next((p for p in self.players if p.username == nominator), None)
        nominated_player = next((p for p in self.players if p.username == nominated), None)

        if not nominator_player or not nominated_player:
            return {"error": "Player not found"}

        if not nominator_player.is_alive and nominator_player.ghost_vote_used:
            return {"error": "Dead players can only nominate once per game"}

        if not nominated_player.is_alive:
            return {"error": "Cannot nominate dead players"}

        if nominated_player.nominated:
            return {"error": "Player already nominated today"}

        nominated_player.nominated = True
        self.nominations.append({
            "nominator": nominator,
            "nominated": nominated,
            "votes": 0,
            "voters": []
        })

        if not nominator_player.is_alive:
            nominator_player.ghost_vote_used = True

        return {"message": f"{nominator} nominated {nominated}"}

    def kill_player(self, username: str, cause: str = "demon") -> Dict:
        player = next((p for p in self.players if p.username == username), None)
        if not player:
            return {"error": "Player not found"}

        if not player.is_alive:
            return {"error": "Player already dead"}

        player.is_alive = False

        if cause == "demon":
            self.demon_kills.append(username)

        return {"message": f"{username} has died ({cause})"}

    def check_win_condition(self) -> Optional[Dict]:
        alive_players = [p for p in self.players if p.is_alive]
        alive_good = [p for p in alive_players if p.role and p.role.team == Team.GOOD]
        alive_evil = [p for p in alive_players if p.role and p.role.team == Team.EVIL]

        demons_alive = [p for p in alive_players if p.role and p.role.role_type == RoleType.DEMON]

        if not demons_alive:
            return {"winner": "good", "reason": "All demons eliminated"}

        if len(alive_evil) >= len(alive_good):
            return {"winner": "evil", "reason": "Evil players equal or outnumber good players"}

        return None

    # Player callable functions for night actions
    def get_my_action(self, username: str) -> Dict:
        if self.phase != GamePhase.NIGHT:
            return {"error": "Night actions only available during night phase"}

        return self.night_action_manager.get_player_action_prompt(username)

    def submit_night_action(self, username: str, choices: List[str]) -> Dict:
        if self.phase != GamePhase.NIGHT:
            return {"error": "Night actions only available during night phase"}

        return self.night_action_manager.submit_player_action(username, choices)

    def get_night_progress(self) -> Dict:
        if self.phase != GamePhase.NIGHT:
            return {"error": "Not currently night phase"}

        return self.night_action_manager.get_night_progress()

    def can_progress_to_day(self) -> bool:
        if self.phase != GamePhase.NIGHT:
            return False

        return self.night_action_manager.can_progress_to_day()

    def get_player_role_info(self, username: str) -> Dict:
        player = next((p for p in self.players if p.username == username), None)
        if not player or not player.role:
            return {"error": "Player not found or has no role"}

        return {
            "username": username,
            "role": player.role.name,
            "description": player.role.description,
            "team": player.role.team.value,
            "alive": player.is_alive,
            "poisoned": player.is_poisoned
        }