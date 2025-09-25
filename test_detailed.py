from clocktower_game import ClocktowerGame

# Test the system step by step

# Create game
game = ClocktowerGame()
usernames = ["Alice", "Bob", "Charlie", "Diana", "Eve"]

print("=== Starting Game ===")
result = game.start_game(usernames)
print("Start result:", result)

print("\n=== Player Roles ===")
for player in game.players:
    role_info = game.get_player_role_info(player.username)
    print(f"{player.username}: {role_info}")

print(f"\nNight count: {game.night_count}")
print("=== Testing First Night Actions ===")

# Test each player's action
for player in game.players:
    print(f"\n--- {player.username} ({player.role.name}) ---")
    action = game.get_my_action(player.username)
    print(f"Action: {action}")

print("\n=== Night Progress ===")
progress = game.get_night_progress()
print(f"Progress: {progress}")

# Try to progress to day
print("\n=== Try Progress to Day ===")
day_result = game.progress_to_day()
print(f"Day result: {day_result}")

print("\n=== Start Next Night ===")
night_result = game.progress_to_night()
print(f"Night result: {night_result}")

print(f"\nNight count: {game.night_count}")
print("=== Testing Second Night Actions ===")

# Test each player's action on second night
for player in game.players:
    if player.is_alive:
        print(f"\n--- {player.username} ({player.role.name}) ---")
        action = game.get_my_action(player.username)
        print(f"Action: {action}")

print("\n=== Night Progress (Night 2) ===")
progress = game.get_night_progress()
print(f"Progress: {progress}")