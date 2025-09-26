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
    role: Optional[Role] = None
    is_alive: bool = True
    is_poisoned: bool = False



roles = {
            # Townsfolk
            "Washerwoman": Role("Washerwoman", RoleType.TOWNSFOLK, Team.GOOD,
                               "You start knowing that 1 of 2 players is a particular Townsfolk.",
                               first_night_order=1),
            "Librarian": Role("Librarian", RoleType.TOWNSFOLK, Team.GOOD,
                             "You start knowing that 1 of 2 players is a particular Outsider.",
                             first_night_order=2),
            "Investigator": Role("Investigator", RoleType.TOWNSFOLK, Team.GOOD,
                                "You start knowing that 1 of 2 players is a particular Minion.",
                                first_night_order=3),
            "Chef": Role("Chef", RoleType.TOWNSFOLK, Team.GOOD,
                        "You start knowing how many pairs of evil players there are.",
                        first_night_order=4),
            "Empath": Role("Empath", RoleType.TOWNSFOLK, Team.GOOD,
                          "Each night, you learn how many of your 2 alive neighbors are evil.",
                          night_order=1),
            "Fortune Teller": Role("Fortune Teller", RoleType.TOWNSFOLK, Team.GOOD,
                                  "Each night, choose 2 players: you learn if either is a Demon.",
                                  night_order=2),
            "Undertaker": Role("Undertaker", RoleType.TOWNSFOLK, Team.GOOD,
                              "Each night*, you learn which character died by execution today.",
                              night_order=3),
            "Monk": Role("Monk", RoleType.TOWNSFOLK, Team.GOOD,
                        "Each night*, choose a player (not yourself): they are safe from the Demon tonight.",
                        night_order=4),
            "Ravenkeeper": Role("Ravenkeeper", RoleType.TOWNSFOLK, Team.GOOD,
                               "If you die at night, you are woken to choose a player: you learn their character."),
            "Virgin": Role("Virgin", RoleType.TOWNSFOLK, Team.GOOD,
                          "The 1st time you are nominated, if the nominator is a Townsfolk, they are executed immediately."),
            "Slayer": Role("Slayer", RoleType.TOWNSFOLK, Team.GOOD,
                          "Once per game, during the day, publicly choose a player: if they are the Demon, they die."),
            "Soldier": Role("Soldier", RoleType.TOWNSFOLK, Team.GOOD,
                           "You are safe from the Demon."),
            "Mayor": Role("Mayor", RoleType.TOWNSFOLK, Team.GOOD,
                         "If only 3 players live & no execution occurs, your team wins."),

            # Outsiders
            "Recluse": Role("Recluse", RoleType.OUTSIDER, Team.GOOD,
                           "You might register as evil & as a Minion or Demon, even when dead."),
            "Saint": Role("Saint", RoleType.OUTSIDER, Team.GOOD,
                         "If you die by execution, your team loses."),
            "Drunk": Role("Drunk", RoleType.OUTSIDER, Team.GOOD,
                         "You do not know you are the Drunk. You think you are a Townsfolk character, but you are not."),
            "Poisoner": Role("Poisoner", RoleType.MINION, Team.EVIL,
                            "Each night, choose a player: they are poisoned tonight and tomorrow day.",
                            night_order=5),
            "Spy": Role("Spy", RoleType.MINION, Team.EVIL,
                       "Each night, you see the Grimoire. You might register as good & as a Townsfolk or Outsider, even when dead.",
                       night_order=6),
            "Scarlet Woman": Role("Scarlet Woman", RoleType.MINION, Team.EVIL,
                                 "If there are 5 or more players alive & the Demon dies, you become the Demon."),
            "Baron": Role("Baron", RoleType.MINION, Team.EVIL,
                         "There are extra Outsiders in play."),

            # Demons
            "Imp": Role("Imp", RoleType.DEMON, Team.EVIL,
                       "Each night*, choose a player: they die. If you kill yourself this way, a Minion becomes the Imp.",
                       night_order=7),
        }