from clocktower_game import ClocktowerGame

game = ClocktowerGame()

usernames = ["Alice", "Bob", "Charlie", "Diana", "Eve"]
hardcoded_roles = {
    "Alice": "imp",
    "Bob": "poisoner",
    "Charlie": "monk",
    "Diana": "fortune_teller",
    "Eve": "empath"
}

print("=== STARTING GAME ===")
result = game.start_game(usernames, hardcoded_roles)
print(f"Start result: {result}")

print("=== PLAYER ROLES ===")
for player in game.players:
    print(f"{player.username}: {player.role.name if player.role else 'No role'}")

game.night_count = 1
game._collect_night_actions()

print("=== COLLECTING NIGHT 1 ACTIONS ===")

status = game.action_collector.get_collection_status()
print(f"Collection status: {status}")

print("\n=== SUBMITTING ACTIONS ===")

result1 = game.submit_night_action("Alice", ["Bob"])
print(f"Alice (Imp) kills Bob: {result1}")

result2 = game.submit_night_action("Bob", ["Charlie"])
print(f"Bob (Poisoner) poisons Charlie: {result2}")

print("\n=== BEFORE FINAL ACTION ===")
print(f"Bob alive: {game.players[1].is_alive}")
print(f"Charlie poisoned: {game.players[2].is_poisoned}")
print(f"Game phase: {game.phase.value}")

result3 = game.submit_night_action("Charlie", ["Alice"])
print(f"Charlie (Monk) protects Alice: {result3}")

print("\n=== AFTER EXECUTION ===")
print(f"Bob alive: {game.players[1].is_alive}")
print(f"Charlie poisoned: {game.players[2].is_poisoned}")
print(f"Game phase: {game.phase.value}")
print(f"Day count: {game.day_count}")

print("\n=== FINAL STATUS ===")
final_status = game.action_collector.get_collection_status()
print(f"Final status: {final_status}")