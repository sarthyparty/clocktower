from clocktower_game import ClocktowerGame

# Example usage of the Clocktower game system

# Initialize and start a game
game = ClocktowerGame()
usernames = ["Alice", "Bob", "Charlie", "Diana", "Eve"]

# Start the game
start_result = game.start_game(usernames)
print("Game started:", start_result)

# Check game state
print("\nGame state:", game.get_game_state())

# Example: Player getting their night action
alice_action = game.get_my_action("Alice")
print("\nAlice's action:", alice_action)

# Example: If Alice is Fortune Teller and needs to choose 2 players
if alice_action.get("waiting_for_input"):
    # Alice submits her choices
    alice_result = game.submit_night_action("Alice", ["Bob", "Charlie"])
    print("Alice's result:", alice_result)

# Check night progress
progress = game.get_night_progress()
print("\nNight progress:", progress)

# Try to progress to day (will fail if actions pending)
try_day = game.progress_to_day()
print("\nTry progress to day:", try_day)

# Player functions available:
# - game.get_my_action(username) - Get what action you need to perform
# - game.submit_night_action(username, choices) - Submit your choices
# - game.get_player_role_info(username) - Get your role info
# - game.get_night_progress() - Check if night can end
# - game.progress_to_day() - Manually progress (storyteller only)
# - game.progress_to_night() - Manually progress (storyteller only)

print("\n=== PLAYER WORKFLOW ===")
print("1. Night starts automatically when game.progress_to_night() is called")
print("2. Players call game.get_my_action('username') to see what they need to do")
print("3. If action needed, players call game.submit_night_action('username', ['choice1', 'choice2'])")
print("4. When all actions complete, game.progress_to_day() works")
print("5. Day phase is manual - use existing nomination/voting functions")
print("6. Call game.progress_to_night() to start next night")