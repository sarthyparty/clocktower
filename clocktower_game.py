import random
from typing import List, Dict, Optional
from roles import *
from action_collector import ActionCollector
from role_executor import RoleExecutor



class ClocktowerGame:
    def __init__(self):
        self.players: List[Player] = []
        self.phase: GamePhase = GamePhase.SETUP
        self.day_count: int = 0
        self.night_count: int = 0
        self._random = random
        self.night_0_results: Dict[str, str] = {}
        self.night_action_results: Dict[str, str] = {}
        self.game_result: Optional[Dict] = None

        self.action_collector = ActionCollector(completion_callback=self._on_actions_complete)


    def start_game(self, usernames: List[str], hardcoded_roles: Dict[str, str] = None) -> Dict:
        if len(usernames) < 5 or len(usernames) > 15:
            return {"error": "Game requires 5-15 players"}

        self.players = [Player(username) for username in usernames]
        player_count = len(usernames)

        if hardcoded_roles:
            self._assign_hardcoded_roles(hardcoded_roles)
            role_distribution = {"hardcoded": len(hardcoded_roles)}
        else:
            role_distribution = self._get_role_distribution(player_count)
            selected_roles = self._select_roles(role_distribution)
            self._assign_roles(selected_roles)

        self.phase = GamePhase.NIGHT
        self.night_count = 0

        self._start_first_night()

        return {
            "message": f"Game started with {player_count} players",
            "phase": self.phase.value,
            "players": [{"username": p.username, "alive": p.is_alive} for p in self.players],
            "role_distribution": role_distribution,
            "pending_actions": len(self.action_collector.expected_players)
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

        townsfolk_roles = [r for r in roles.values() if r.role_type == RoleType.TOWNSFOLK]
        outsider_roles = [r for r in roles.values() if r.role_type == RoleType.OUTSIDER]
        minion_roles = [r for r in roles.values() if r.role_type == RoleType.MINION]
        demon_roles = [r for r in roles.values() if r.role_type == RoleType.DEMON]

        selected.extend(random.sample(townsfolk_roles, distribution[RoleType.TOWNSFOLK]))
        if distribution[RoleType.OUTSIDER] > 0:
            selected.extend(random.sample(outsider_roles, min(distribution[RoleType.OUTSIDER], len(outsider_roles))))
        selected.extend(random.sample(minion_roles, min(distribution[RoleType.MINION], len(minion_roles))))
        selected.extend(random.sample(demon_roles, 1))

        return selected

    def _assign_hardcoded_roles(self, hardcoded_roles: Dict[str, str]):
        from roles import roles
        print(f"Available roles: {list(roles.keys())}")
        for player in self.players:
            if player.username in hardcoded_roles:
                role_name = hardcoded_roles[player.username]
                print(f"Looking for role {role_name} for {player.username}")
                if role_name in roles:
                    player.role = roles[role_name]
                    print(f"Assigned {role_name} to {player.username}")
                else:
                    print(f"Role {role_name} not found in roles dict")

    def _assign_roles(self, roles: List[Role]):
        random.shuffle(roles)
        for i, player in enumerate(self.players):
            if i < len(roles):
                player.role = roles[i]

    def progress_to_day(self) -> Dict:
        if self.phase != GamePhase.NIGHT:
            return {"error": "Can only progress to day from night"}
        
        if not self.action_collector.is_complete:
            status = self.action_collector.get_collection_status()
            return {
                "error": "Cannot progress to day - pending night actions",
                "pending_players": status["pending_players"]
            }
        
        self._execute_night_actions()

        alive_players = [p for p in self.players if p.is_alive]

        return {
            "message": f"Day {self.day_count} begins",
            "phase": self.phase.value,
            "day_count": self.day_count,
            "alive_players": len(alive_players),
            "players": [{"username": p.username, "alive": p.is_alive} for p in self.players],
            "night_results": {"deaths": []}
        }

    def progress_to_night(self) -> Dict:
        if self.phase != GamePhase.DAY:
            return {"error": "Can only progress to night from day"}

        self.night_count += 1
        self.phase = GamePhase.NIGHT

        self._collect_night_actions()

        return {
            "message": f"Night {self.night_count} begins",
            "phase": self.phase.value,
            "night_count": self.night_count,
            "alive_players": len([p for p in self.players if p.is_alive]),
            "pending_actions": len(self.action_collector.expected_players)
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
                    "role": p.role.name if p.role else None
                } for p in self.players
            ],
            "alive_count": len([p for p in self.players if p.is_alive])
        }

    def check_win_condition(self) -> Optional[Dict]:
        alive_players = [p for p in self.players if p.is_alive]
        alive_good = [p for p in alive_players if p.role and p.role.team == Team.GOOD]
        alive_evil = [p for p in alive_players if p.role and p.role.team == Team.EVIL]

        if len(alive_evil) >= len(alive_good):
            return {"winner": "evil", "reason": "Evil equals or outnumbers good"}

        if not alive_evil:
            return {"winner": "good", "reason": "All evil players eliminated"}

        return None

    def _collect_night_actions(self):
        self.night_action_results = {}
        players_needing_actions = {}

        for player in self.players:
            if not player.role or not player.is_alive:
                continue

            role_name = player.role.name
            needs_input = False

            if self.night_count == 0:
                needs_input = False
            else:
                if role_name in ["Monk", "Poisoner", "Imp", "Fortune Teller"]:
                    needs_input = True

            if needs_input:
                players_needing_actions[player.username] = role_name

        self.action_collector.initialize_collection(players_needing_actions)
        
        if not players_needing_actions:
            self._execute_night_actions()

    def submit_night_action(self, username: str, choices: List[str]) -> Dict:
        if self.phase != GamePhase.NIGHT:
            return {"error": "Night actions only available during night phase"}

        return self.action_collector.submit_action(username, choices)

    def _can_progress_to_day(self) -> bool:
        return self.action_collector.is_complete

    def _execute_night_actions(self):
        """Execute night actions and progress to day"""
        self._execute()
        self._progress_to_day_automatically()
    
    def _execute(self):
        """Execute night actions without progressing to day"""
        print(f"EXECUTING NIGHT ACTIONS - All actions collected!")
        collected_actions = self.action_collector.get_collected_actions()
        
        if isinstance(collected_actions, dict) and "error" in collected_actions:
            print("No actions to execute")
            return

        if self.night_count == 0:
            night_order = ["Poisoner", "Washerwoman", "Librarian", "Investigator", "Chef", "Empath", "Fortune Teller", "Undertaker", "Butler", "Spy"]
        else:
            night_order = ["Poisoner", "Monk", "Scarlet Woman", "Imp", "Ravenkeeper", "Empath", "Fortune Teller", "Undertaker", "Butler", "Spy"]

        actions_by_role = {}
        for username, action_data in collected_actions.items():
            role = action_data['role']
            actions_by_role[role] = (username, action_data)

        from role_executor import RoleExecutor
        executor = RoleExecutor(self.players)

        print(f"\n--- Executing in Night Order ---")
        for role in night_order:
            if role in actions_by_role:
                username, action_data = actions_by_role[role]
                print(f"Executing {username} ({role}): {action_data['choices']}")
                result = executor.execute_role_action(role, username, action_data['choices'])
                print(f"  → {result}")
                
                if self._role_gets_information(role) and result:
                    self.night_action_results[username] = result
            else:
                if role in ["Spy", "Empath"]:
                    for player in self.players:
                        if player.role and player.role.name == role and player.is_alive:
                            print(f"Executing {player.username} ({role}): automatic")
                            result = executor.execute_role_action(role, player.username, [])
                            print(f"  → {result}")
                            if result:
                                self.night_action_results[player.username] = result
                            break

    def _on_actions_complete(self):
        self._execute()
        return self._progress_to_day_automatically()

    def _progress_to_day_automatically(self):
        win_condition = self.check_win_condition()
        if win_condition:
            self.phase = GamePhase.ENDED
            self.game_result = win_condition
            return win_condition
        
        self.day_count += 1
        self.phase = GamePhase.DAY
        return None
        
    def _start_first_night(self):
        """Automatically execute first night (night 0) without user input"""
        print(f"\n=== STARTING NIGHT 0 (FIRST NIGHT) ===\n")
        self.night_count = 0
        
        self._execute_night_0_actions()
    
    def _execute_night_0_actions(self):
        """Execute night 0 actions automatically and progress to day"""
        print("Executing Night 0 actions automatically...")
        
        night_0_order = ["Poisoner", "Washerwoman", "Librarian", "Investigator", "Chef", "Empath", "Fortune Teller", "Undertaker", "Butler", "Spy"]
        
        from role_executor import RoleExecutor
        executor = RoleExecutor(self.players)
        
        self.night_0_results = {}
        
        print(f"\n--- Executing Night 0 in Order ---")
        for role in night_0_order:
            for player in self.players:
                if player.role and player.role.name == role and player.is_alive:
                    print(f"Executing {player.username} ({player.role.name})")
                    result = executor.execute_role_action(role, player.username, [])
                    print(f"  → {result}")
                    
                    if result and result != f"{role} action not implemented" and result != "No target specified":
                        self.night_0_results[player.username] = result
                    break
        
        self._progress_to_day_automatically()
    
    def get_night_0_results(self) -> Dict[str, str]:
        return self.night_0_results.copy()
    
    def get_night_action_results(self) -> Dict[str, str]:
        return self.night_action_results.copy()
    
    def _role_gets_information(self, role_name: str) -> bool:
        information_roles = [
            "Fortune Teller", "Empath", "Washerwoman", "Librarian", 
            "Investigator", "Chef", "Undertaker", "Ravenkeeper", "Spy"
        ]
        return role_name in information_roles
    
