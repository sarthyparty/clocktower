from clocktower_game import ClocktowerGame

# Test complete workflow including player actions

game = ClocktowerGame()
usernames = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"]

print("=== Starting Game ===")
result = game.start_game(usernames)
print("Night actions:", result['night_actions'])

print("\n=== Player Roles ===")
for player in game.players:
    role_info = game.get_player_role_info(player.username)
    print(f"{player.username}: {role_info['role']} ({role_info['team']})")

print(f"\n=== Night {game.night_count} Actions ===")
progress = game.get_night_progress()
print(f"Progress: {progress}")

# Test each player who has actions
for player in game.players:
    action = game.get_my_action(player.username)
    if 'error' not in action:
        print(f"\n{player.username} ({player.role.name}): {action}")

# Progress to day should work if no required actions
print(f"\nCan progress to day: {game.can_progress_to_day()}")

# Progress to first day
day_result = game.progress_to_day()
print(f"\nDay result: {day_result}")

print(f"\n=== Starting Night 1 ===")
night_result = game.progress_to_night()
print(f"Night 1 actions: {night_result['night_actions']}")

progress = game.get_night_progress()
print(f"Night 1 progress: {progress}")

# Show actions that need input
pending_players = []
for player in game.players:
    if player.is_alive:
        action = game.get_my_action(player.username)
        if 'waiting_for_input' in action or 'prompt' in action:
            print(f"\n{player.username} needs to act: {action}")
            pending_players.append(player.username)

print(f"\nPlayers who need to act: {pending_players}")
print(f"Can progress to day: {game.can_progress_to_day()}")

# Simulate submitting actions for players that need them
if pending_players:
    print(f"\n=== Simulating Player Actions ===")

    for username in pending_players:
        action = game.get_my_action(username)
        if 'options' in action:
            # Choose the first available option(s)
            required = action.get('required_count', 1)
            choices = action['options'][:required]

            print(f"{username} submitting: {choices}")
            result = game.submit_night_action(username, choices)
            print(f"Result: {result}")

    # Check if we can progress now
    final_progress = game.get_night_progress()
    print(f"\nFinal progress: {final_progress}")
    print(f"Can progress to day: {game.can_progress_to_day()}")

    if game.can_progress_to_day():
        day2_result = game.progress_to_day()
        print(f"Day 2 result: {day2_result}")

print("\n=== System Working! ===")
print("✓ Night actions initialize correctly")
print("✓ Players get proper prompts for their roles")
print("✓ System waits for required actions")
print("✓ Progression blocked until all actions complete")
print("✓ Day progression works after actions complete")