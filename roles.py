from enum import Enum
from typing import Optional
from dataclasses import dataclass

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
    role: Role
    is_alive: bool = True
    is_poisoned: bool = False



roles = {
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