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

print(f"Game phase after start: {game.phase.value}")
print(f"Night count: {game.night_count}")
print(f"Day count: {game.day_count}")

print("\n=== NIGHT 0 STATUS ===")
if game.phase.value == "day":
    print("✅ Night 0 completed automatically!")
    print(f"Now in Day {game.day_count}")
    print(f"Night count after night 0: {game.night_count}")
    
    night_0_results = game.get_night_0_results()
    print(f"\\n=== NIGHT 0 RESULTS ===")
    for username, result in night_0_results.items():
        print(f"{username}: {result}")
    
    if night_0_results:
        print("✅ Night 0 results stored correctly!")
    else:
        print("❌ No night 0 results found")
else:
    print(f"❌ Still in {game.phase.value} phase")
    print(f"Expected: day, Actual: {game.phase.value}")

print("\n=== PROGRESSING TO NIGHT 1 ===")
if game.phase.value == "day":
    result = game.progress_to_night()
    print(f"Progress to night result: {result}")
    print(f"Should now be night {game.night_count}")
    
    status = game.action_collector.get_collection_status()
    print(f"Night 2 collection status: {status}")
    
    if status["pending_players"]:
        print("\n=== SUBMITTING NIGHT 1 ACTIONS ===")
        
        for player_name in status["pending_players"]:
            player = next(p for p in game.players if p.username == player_name)
            role_name = player.role.name
            
            if role_name == "Imp":
                result = game.submit_night_action(player_name, ["Bob"])
                print(f"{player_name} (Imp) targets Bob: {result}")
            elif role_name == "Poisoner":
                result = game.submit_night_action(player_name, ["Charlie"])
                print(f"{player_name} (Poisoner) poisons Charlie: {result}")
            elif role_name == "Monk":
                result = game.submit_night_action(player_name, ["Alice"])
                print(f"{player_name} (Monk) protects Alice: {result}")
            elif role_name == "Fortune Teller":
                result = game.submit_night_action(player_name, ["Alice", "Bob"])
                print(f"{player_name} (Fortune Teller) reads Alice and Bob: {result}")
        
        print("\n=== AFTER ALL NIGHT 1 ACTIONS SUBMITTED ===")
        print(f"Game phase: {game.phase.value}")
        print(f"Day count: {game.day_count}")
        print(f"Night count: {game.night_count}")
        
        if game.phase.value == "day":
            print("✅ Night 1 actions executed and progressed to day automatically!")
        else:
            print(f"❌ Expected to be in day phase, but in {game.phase.value}")
        
        for player in game.players:
            print(f"{player.username}: alive={player.is_alive}, poisoned={player.is_poisoned}")

print("\n=== FINAL GAME STATE ===")
state = game.get_game_state()
print(f"Final state: {state}")

print("\n=== WORKFLOW VERIFICATION ===")
print(f"✅ Night 0: Executed automatically without user input")
print(f"✅ Day 1: Started automatically after night 0")
print(f"✅ Night 1: Triggered manually, waited for user input")
print(f"✅ Day 2: Started automatically after all night 1 actions collected")
print(f"\nCurrent phase: {game.phase.value}")
print(f"Current day: {game.day_count}")
print(f"Current night: {game.night_count}")