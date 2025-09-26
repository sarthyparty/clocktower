import discord
from discord.ext import commands
from clocktower_game import ClocktowerGame
from typing import Dict, List, Optional
import os
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

games: Dict[int, ClocktowerGame] = {}
player_guilds: Dict[int, int] = {}
player_usernames: Dict[int, str] = {}
test_mode_guilds: Dict[int, bool] = {}
game_channels: Dict[int, int] = {}

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command(name='test')
async def test_mode(ctx):
    if ctx.guild is None:
        await ctx.send("This command must be used in a server.")
        return
    
    guild_id = ctx.guild.id
    test_mode_guilds[guild_id] = True
    await ctx.send("🧪 **Test mode enabled!** You can now start a game with any usernames, even if they're not in the server.")

@bot.command(name='start')
async def start_game(ctx, *players):
    if ctx.guild is None:
        await ctx.send("This command must be used in a server, not DMs.")
        return

    guild_id = ctx.guild.id

    if guild_id in games:
        await ctx.send("A game is already running in this server!")
        return

    if len(players) < 5 or len(players) > 15:
        await ctx.send("Need 5-15 players to start a game!")
        return

    is_test_mode = test_mode_guilds.get(guild_id, False)
    
    if is_test_mode:
        members = [ctx.author] * len(players)
        player_members = {players[i]: ctx.author for i in range(len(players))}
        await ctx.send(f"🧪 **Test mode active** - {ctx.author.mention} will play as all characters")
    else:
        members = []
        missing_players = []

        for player_name in players:
            member = discord.utils.find(lambda m: m.name == player_name or m.display_name == player_name or str(m) == player_name, ctx.guild.members)
            if member:
                members.append(member)
            else:
                missing_players.append(player_name)

        if missing_players:
            await ctx.send(f"❌ **Cannot start game!**\nThe following players are not in this server: {', '.join(missing_players)}\n\nPlease make sure all player names match Discord usernames or display names in this server.")
            return
        
        player_members = {players[i]: members[i] for i in range(len(players))}

    # Create new game
    game = ClocktowerGame()
    games[guild_id] = game
    game_channels[guild_id] = ctx.channel.id

    # Map members to this guild and store their IDs
    if not is_test_mode:
        for i, member in enumerate(members):
            player_guilds[member.id] = guild_id
            player_usernames[member.id] = players[i]
    else:
        player_guilds[ctx.author.id] = guild_id

    # Start the game
    result = game.start_game(list(players))

    if "error" in result:
        await ctx.send(f"Error starting game: {result['error']}")
        del games[guild_id]
        if guild_id in game_channels:
            del game_channels[guild_id]
        return

    await ctx.send(f"🎭 **Clocktower Game Started!**\n"
                   f"Players: {', '.join(players)}\n"
                   f"Phase: {result['phase'].title()} {game.day_count}\n"
                   f"Night 0 has been executed automatically!")

    dm_failures = []
    for player in game.players:
        member = player_members.get(player.username)
        if member and player.role:
            try:
                embed = discord.Embed(
                    title="🎭 Your Role",
                    description=f"**{player.role.name}**\n{player.role.description}",
                    color=0x7289da
                )
                embed.add_field(name="Team", value=player.role.team.value.title(), inline=True)
                await member.send(embed=embed)
                await ctx.send(f"✅ Sent role to {player.username}", delete_after=3)
            except discord.Forbidden:
                dm_failures.append(player.username)
            except Exception as e:
                print(f"Failed to DM {player.username}: {e}")
                dm_failures.append(player.username)

    if dm_failures:
        await ctx.send(f"⚠️ **Could not send DMs to:** {', '.join(dm_failures)}\nThey may have DMs disabled. Please ask them to enable DMs from server members.")

    await send_night_0_results(ctx.guild, game, player_members, is_test_mode)

@bot.command(name='night')
async def progress_to_night(ctx):
    if ctx.guild is None:
        await ctx.send("This command must be used in a server.")
        return

    guild_id = ctx.guild.id
    if guild_id not in games:
        await ctx.send("No game running in this server!")
        return

    game = games[guild_id]
    result = game.progress_to_night()

    if "error" in result:
        await ctx.send(f"Error: {result['error']}")
        return

    await ctx.send(f"🌙 **Night {game.night_count} begins...**")

    await check_night_actions(ctx.guild)

def create_player_circle(players):
    if not players:
        return "No players"
    
    def get_player_symbol(player):
        if not player.is_alive:
            return "💀"
        else:
            return "🔵"
    
    def format_player(player):
        symbol = get_player_symbol(player)
        return f"{symbol} {player.username}"
    
    player_count = len(players)
    
    if player_count <= 6:
        formatted_players = [format_player(p) for p in players]
        return "\n".join(formatted_players)
    
    elif player_count <= 10:
        top_half = players[:player_count//2]
        bottom_half = players[player_count//2:]
        bottom_half.reverse()
        
        circle = []
        
        for player in top_half:
            circle.append(f"        {format_player(player)}")
        
        circle.append("")
        
        for player in bottom_half:
            circle.append(f"        {format_player(player)}")
        
        return "\n".join(circle)
    
    else:
        rows = []
        per_row = (player_count + 2) // 3
        
        for i in range(0, player_count, per_row):
            row_players = players[i:i+per_row]
            row_text = "  ".join([format_player(p) for p in row_players])
            rows.append(f"    {row_text}")
        
        return "\n".join(rows)

@bot.command(name='state')
async def game_state(ctx):
    if ctx.guild is None:
        await ctx.send("This command must be used in a server.")
        return

    guild_id = ctx.guild.id
    if guild_id not in games:
        await ctx.send("No game running in this server!")
        return

    game = games[guild_id]

    alive_players = [p.username for p in game.players if p.is_alive]
    dead_players = [p.username for p in game.players if not p.is_alive]

    embed = discord.Embed(title="🎭 Game State", color=0x7289da)
    embed.add_field(name="Phase", value=f"{game.phase.value.title()} {game.day_count if game.phase.value == 'day' else game.night_count}", inline=True)
    embed.add_field(name="Players Alive", value=str(len(alive_players)), inline=True)
    embed.add_field(name="Total Players", value=str(len(game.players)), inline=True)
    
    circle_visual = create_player_circle(game.players)
    embed.add_field(name="🔄 Player Circle", value=circle_visual, inline=False)
    embed.add_field(name="Legend", value="🔵 Alive  💀 Dead", inline=False)

    if game.phase.value == "night":
        status = game.action_collector.get_collection_status()
        pending_count = len(status["pending_players"])
        if pending_count > 0:
            embed.add_field(name="Pending Actions", value=f"{pending_count} players still need to submit actions", inline=False)

    await ctx.send(embed=embed)

async def send_night_0_results(guild, game, player_members, is_test_mode=False):
    night_0_results = game.get_night_0_results()
    
    if not night_0_results:
        return
    
    dm_failures = []
    
    if is_test_mode:
        guild_id = guild.id
        test_user_id = None
        for uid, gid in player_guilds.items():
            if gid == guild_id:
                test_user_id = uid
                break
        
        if test_user_id:
            test_member = guild.get_member(test_user_id)
            if test_member:
                embed = discord.Embed(
                    title="🧪🌙 Test Mode - Night 0 Information",
                    description="Here's what your characters learned:",
                    color=0x5865f2
                )
                
                for username, result in night_0_results.items():
                    player = next((p for p in game.players if p.username == username), None)
                    if player and player.role:
                        embed.add_field(
                            name=f"{username} ({player.role.name})",
                            value=result,
                            inline=False
                        )
                
                try:
                    await test_member.send(embed=embed)
                except discord.Forbidden:
                    dm_failures.extend(night_0_results.keys())
    else:
        for username, result in night_0_results.items():
            member = player_members.get(username)
            if not member:
                continue
                
            player = next((p for p in game.players if p.username == username), None)
            if not player or not player.role:
                continue
                
            embed = discord.Embed(
                title="🌙 Night 0 Information",
                description=f"**{player.role.name}**\nHere's what you learned during the first night:",
                color=0x5865f2
            )
            
            embed.add_field(name="Your Information", value=result, inline=False)
            embed.add_field(name="Remember", value="Keep this information secret! Use it wisely during the day.", inline=False)
            
            try:
                await member.send(embed=embed)
            except discord.Forbidden:
                dm_failures.append(username)
            except Exception as e:
                print(f"Failed to send night 0 result to {username}: {e}")
                dm_failures.append(username)
    
    if dm_failures:
        guild_id = guild.id
        channel_id = game_channels.get(guild_id)
        channel = guild.get_channel(channel_id) if channel_id else None
        if channel:
            await channel.send(f"⚠️ **Could not send night 0 results to:** {', '.join(dm_failures)}")

async def gitsend_night_action_results(guild, game):
    night_results = game.get_night_action_results()
    
    if not night_results:
        return
    
    is_test_mode = test_mode_guilds.get(guild.id, False)
    dm_failures = []
    
    if is_test_mode:
        guild_id = guild.id
        test_user_id = None
        for uid, gid in player_guilds.items():
            if gid == guild_id:
                test_user_id = uid
                break
        
        if test_user_id:
            test_member = guild.get_member(test_user_id)
            if test_member:
                embed = discord.Embed(
                    title=f"🧪🌙 Test Mode - Night {game.night_count} Results",
                    description="Your characters learned:",
                    color=0x5865f2
                )
                
                for username, result in night_results.items():
                    player = next((p for p in game.players if p.username == username), None)
                    if player and player.role:
                        embed.add_field(
                            name=f"{username} ({player.role.name})",
                            value=result,
                            inline=False
                        )
                
                try:
                    await test_member.send(embed=embed)
                except discord.Forbidden:
                    dm_failures.extend(night_results.keys())
    else:
        for username, result in night_results.items():
            member_id = None
            for uid, uname in player_usernames.items():
                if uname == username and player_guilds.get(uid) == guild.id:
                    member_id = uid
                    break
            
            if not member_id:
                continue
                
            member = guild.get_member(member_id)
            if not member:
                continue
                
            player = next((p for p in game.players if p.username == username), None)
            if not player or not player.role:
                continue
                
            embed = discord.Embed(
                title=f"🌙 Night {game.night_count} Information",
                description=f"**{player.role.name}**\nHere's what you learned:",
                color=0x5865f2
            )
            
            embed.add_field(name="Your Information", value=result, inline=False)
            
            try:
                await member.send(embed=embed)
            except discord.Forbidden:
                dm_failures.append(username)
            except Exception as e:
                print(f"Failed to send night result to {username}: {e}")
                dm_failures.append(username)
    
    if dm_failures:
        guild_id = guild.id
        channel_id = game_channels.get(guild_id)
        channel = guild.get_channel(channel_id) if channel_id else None
        if channel:
            await channel.send(f"⚠️ **Could not send night results to:** {', '.join(dm_failures)}")

async def check_night_actions(guild):
    guild_id = guild.id
    if guild_id not in games:
        return

    game = games[guild_id]
    if game.phase.value != "night":
        return

    status = game.action_collector.get_collection_status()
    
    if not status["pending_players"]:
        return

    is_test_mode = test_mode_guilds.get(guild_id, False)
    
    if is_test_mode:
        test_user_id = None
        for uid, gid in player_guilds.items():
            if gid == guild_id:
                test_user_id = uid
                break
        
        if test_user_id:
            test_member = guild.get_member(test_user_id)
            if test_member:
                embed = discord.Embed(
                    title="🧪🌙 Test Mode - Night Actions Required",
                    description="Your characters need to submit night actions:",
                    color=0x992d22
                )
                
                for username in status["pending_players"]:
                    player = next((p for p in game.players if p.username == username), None)
                    if player and player.role:
                        role_name = player.role.name
                        available = [p.username for p in game.players if p.is_alive and p.username != username]
                        
                        if role_name == "Fortune Teller":
                            action_text = f"Needs 2 targets\nExample: `!action {username} Alice Bob`"
                        elif role_name in ["Imp", "Poisoner", "Monk"]:
                            action_text = f"Needs 1 target\nExample: `!action {username} Charlie`"
                        else:
                            action_text = "Action required"
                        
                        embed.add_field(
                            name=f"{username} ({role_name})",
                            value=action_text,
                            inline=False
                        )
                
                embed.add_field(name="Available Targets", value=", ".join([p.username for p in game.players if p.is_alive]), inline=False)
                
                try:
                    await test_member.send(embed=embed)
                except discord.Forbidden:
                    pass
    else:
        for username in status["pending_players"]:
            member_id = None
            for uid, uname in player_usernames.items():
                if uname == username and player_guilds.get(uid) == guild_id:
                    member_id = uid
                    break
            
            if not member_id:
                continue
                
            member = guild.get_member(member_id)
            if not member:
                continue
                
            player = next((p for p in game.players if p.username == username), None)
            if not player or not player.role:
                continue
                
            role_name = player.role.name

            embed = discord.Embed(
                title="🌙 Night Action Required",
                description=f"**{role_name}**\nYou need to submit your night action!",
                color=0x992d22
            )

            if role_name == "Fortune Teller":
                embed.add_field(name="Action", value="Choose 2 players to read", inline=False)
                embed.add_field(name="Command", value="!action player1 player2", inline=False)
                embed.add_field(name="Example", value="!action Alice Bob", inline=False)
            elif role_name in ["Imp", "Poisoner", "Monk"]:
                embed.add_field(name="Action", value="Choose 1 player", inline=False)
                embed.add_field(name="Command", value="!action player_name", inline=False)
                embed.add_field(name="Example", value="!action Charlie", inline=False)
            
            embed.add_field(name="Available Players", value=", ".join([p.username for p in game.players if p.is_alive and p.username != username]), inline=False)

            try:
                await member.send(embed=embed)
            except discord.Forbidden:
                pass

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if isinstance(message.channel, discord.DMChannel):
        if message.content.startswith('!action'):
            await handle_action_dm(message)
        return

    await bot.process_commands(message)

async def handle_action_dm(message):
    user_id = message.author.id

    if user_id not in player_guilds:
        await message.channel.send("❌ You're not part of any active game!")
        return

    guild_id = player_guilds[user_id]
    if guild_id not in games:
        await message.channel.send("❌ No active game found!")
        return

    game = games[guild_id]
    is_test_mode = test_mode_guilds.get(guild_id, False)
    
    parts = message.content.split()[1:]
    
    if is_test_mode:
        if not parts:
            await message.channel.send("❌ Test mode: You must specify which character is acting!\nExample: `!action Alice Bob Charlie` (Alice targets Bob and Charlie)")
            return
        
        username = parts[0]
        action_targets = parts[1:]
        
        player = next((p for p in game.players if p.username == username), None)
        if not player:
            await message.channel.send(f"❌ Character '{username}' not found in the game!")
            return
    else:
        username = player_usernames.get(user_id)
        if not username:
            await message.channel.send("❌ Error: Could not find your game username!")
            return
        
        player = next((p for p in game.players if p.username == username), None)
        action_targets = parts

    if game.phase.value != "night":
        await message.channel.send("❌ You can only submit actions during the night phase!")
        return

    if not player or not player.is_alive:
        await message.channel.send(f"❌ {username} is not alive and cannot submit actions!")
        return

    if not player.role:
        await message.channel.send(f"❌ {username} doesn't have a role assigned!")
        return

    if not action_targets:
        embed = discord.Embed(
            title="❌ Missing Action Targets",
            description=f"**{username}** needs to specify targets!",
            color=0xff5555
        )
        
        role_name = player.role.name
        if role_name == "Fortune Teller":
            embed.add_field(name="Required", value="2 players", inline=False)
            if is_test_mode:
                embed.add_field(name="Example", value=f"!action {username} Alice Bob", inline=False)
            else:
                embed.add_field(name="Example", value="!action Alice Bob", inline=False)
        elif role_name in ["Imp", "Poisoner", "Monk"]:
            embed.add_field(name="Required", value="1 player", inline=False)
            if is_test_mode:
                embed.add_field(name="Example", value=f"!action {username} Charlie", inline=False)
            else:
                embed.add_field(name="Example", value="!action Charlie", inline=False)
        
        alive_targets = [p.username for p in game.players if p.is_alive and p.username != username]
        embed.add_field(name="Available Targets", value=", ".join(alive_targets), inline=False)
        
        await message.channel.send(embed=embed)
        return

    role_name = player.role.name
    expected_count = 2 if role_name == "Fortune Teller" else 1
    
    if len(action_targets) != expected_count:
        await message.channel.send(f"❌ {username} ({role_name}) requires exactly {expected_count} target{'s' if expected_count > 1 else ''}! You provided {len(action_targets)}.")
        return

    valid_targets = [p.username for p in game.players if p.is_alive and p.username != username]
    invalid_targets = [target for target in action_targets if target not in valid_targets]
    
    if invalid_targets:
        await message.channel.send(f"❌ Invalid targets: {', '.join(invalid_targets)}\nValid targets: {', '.join(valid_targets)}")
        return

    if len(set(action_targets)) != len(action_targets):
        await message.channel.send("❌ You cannot target the same player multiple times!")
        return

    embed = discord.Embed(
        title="🤔 Confirm Your Action",
        description=f"**{username} ({role_name})**\nAre you sure you want to target: **{', '.join(action_targets)}**?",
        color=0xffa500
    )
    embed.add_field(name="To Confirm", value="Type `y`, `yes`, or `!confirm`", inline=True)
    embed.add_field(name="To Cancel", value="Type `n`, `no`, or `!cancel`", inline=True)
    
    await message.channel.send(embed=embed)
    
    def check(m):
        return m.author == message.author and m.channel == message.channel and m.content.lower() in ['!confirm', '!cancel', 'y', 'yes', 'n', 'no']
    
    try:
        response = await bot.wait_for('message', check=check, timeout=60.0)
        
        if response.content.lower() in ['!cancel', 'n', 'no']:
            await message.channel.send("❌ Action cancelled.")
            return
        
        result = game.submit_night_action(username, action_targets)

        if "error" in result:
            await message.channel.send(f"❌ Error: {result['error']}")
            return

        embed = discord.Embed(
            title="✅ Action Submitted Successfully!",
            description=f"**{username} ({role_name})** action targeting: **{', '.join(action_targets)}**",
            color=0x00ff00
        )
        embed.add_field(name="Status", value="Action has been recorded and will be executed at the end of the night.", inline=False)
        
        await message.channel.send(embed=embed)

        if result.get("collection_complete"):
            guild = bot.get_guild(guild_id)
            if guild:
                channel_id = game_channels.get(guild_id)
                channel = guild.get_channel(channel_id) if channel_id else None
                if channel:
                    await channel.send("🌙 All night actions submitted! Processing...")
                    
                    game_result = result.get("game_result")
                    if game_result:
                        winner = game_result["winner"]
                        reason = game_result["reason"]
                        
                        embed = discord.Embed(
                            title="🎯 GAME OVER!",
                            description=f"**{winner.upper()} TEAM WINS!**",
                            color=0xff0000 if winner == "evil" else 0x00ff00
                        )
                        embed.add_field(name="Reason", value=reason, inline=False)
                        
                        alive_players = [p for p in game.players if p.is_alive]
                        dead_players = [p for p in game.players if not p.is_alive]
                        
                        if dead_players:
                            deaths_list = [p.username for p in dead_players]
                            embed.add_field(name="💀 Deaths", value=", ".join(deaths_list), inline=False)
                        
                        embed.add_field(name="🎭 Final Roles", value="\n".join([
                            f"{'💀' if not p.is_alive else '✅'} **{p.username}**: {p.role.name} ({p.role.team.value})"
                            for p in game.players
                        ]), inline=False)
                        
                        await gitsend_night_action_results(guild, game)
                        await channel.send(embed=embed)
                        
                        del games[guild_id]
                        if guild_id in game_channels:
                            del game_channels[guild_id]
                        to_remove = [uid for uid, gid in player_guilds.items() if gid == guild_id]
                        for uid in to_remove:
                            del player_guilds[uid]
                            if uid in player_usernames:
                                del player_usernames[uid]
                        if guild_id in test_mode_guilds:
                            del test_mode_guilds[guild_id]
                    else:
                        await gitsend_night_action_results(guild, game)
                        
                        await channel.send(f"☀️ **Day {game.day_count} begins!**")
                        
                        alive_players = [p for p in game.players if p.is_alive]
                        dead_players = [p for p in game.players if not p.is_alive]
                        
                        if dead_players:
                            deaths_this_phase = []
                            for p in dead_players:
                                deaths_this_phase.append(p.username)
                            if deaths_this_phase:
                                await channel.send(f"💀 **Deaths:** {', '.join(deaths_this_phase)}")
    
    except asyncio.TimeoutError:
        await message.channel.send("⏰ Confirmation timed out. Please submit your action again.")

@bot.command(name='debug')
async def debug_state(ctx):
    if ctx.guild is None:
        await ctx.send("This command must be used in a server.")
        return

    guild_id = ctx.guild.id
    if guild_id not in games:
        await ctx.send("No game running in this server!")
        return

    game = games[guild_id]

    embed = discord.Embed(title="🔧 Debug Game State", color=0xff5555)
    embed.add_field(name="Phase", value=f"{game.phase.value.title()}", inline=True)
    embed.add_field(name="Day Count", value=str(game.day_count), inline=True)
    embed.add_field(name="Night Count", value=str(game.night_count), inline=True)

    from role_executor import RoleExecutor
    executor = RoleExecutor(game.players)
    grimoire = executor.spy_action("debug", [])
    
    embed.add_field(name="🔍 GRIMOIRE", value=f"```{grimoire}```", inline=False)

    if game.phase.value == "night":
        status = game.action_collector.get_collection_status()
        embed.add_field(name="Expected Actions", value=str(len(status["pending_players"])), inline=True)
        embed.add_field(name="Collected Actions", value=str(status["collected"]), inline=True)
        embed.add_field(name="Collection Complete", value=str(status["is_complete"]), inline=True)
        
        if status["pending_players"]:
            embed.add_field(name="Pending Players", value=", ".join(status["pending_players"]), inline=False)

    embed.add_field(name="Win Condition Check", value=str(game.check_win_condition()), inline=False)

    await ctx.send(embed=embed)

@bot.command(name='guide')
async def help_command(ctx):
    embed = discord.Embed(title="🎭 Clocktower Bot Commands", color=0x7289da)
    
    embed.add_field(
        name="🎮 Game Commands",
        value="`!test` - Enable test mode (single user plays all characters)\n"
              "`!start player1 player2 ...` - Start a new game\n"
              "`!night` - Progress to night (manual)\n"
              "`!state` - Show public game state\n"
              "`!debug` - Show debug info (all roles visible)\n"
              "`!end` - End the current game",
        inline=False
    )
    
    embed.add_field(
        name="🌙 Night Actions (via DM)",
        value="**Normal Mode:**\n"
              "• `!action <targets>` - Submit action\n"
              "• Example: `!action Alice Bob`\n\n"
              "**Test Mode:**\n"
              "• `!action <character> <targets>` - Submit action for character\n"
              "• Example: `!action Diana Alice Bob` (Diana targets Alice and Bob)\n\n"
              "Both modes require `!confirm` or `!cancel` after submission.",
        inline=False
    )
    
    embed.add_field(
        name="ℹ️ Important Notes",
        value="• Night 0 executes automatically (no input needed)\n"
              "• You'll receive DMs with your starting information\n"
              "• Only alive players can submit actions\n"
              "• Actions can only be submitted during night phase\n"
              "• Day progression happens automatically after all actions",
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command(name='end')
async def end_game(ctx):
    if ctx.guild is None:
        await ctx.send("This command must be used in a server.")
        return

    guild_id = ctx.guild.id
    if guild_id not in games:
        await ctx.send("No game running in this server!")
        return

    del games[guild_id]
    if guild_id in game_channels:
        del game_channels[guild_id]
    to_remove = [uid for uid, gid in player_guilds.items() if gid == guild_id]
    for uid in to_remove:
        del player_guilds[uid]
        if uid in player_usernames:
            del player_usernames[uid]
    if guild_id in test_mode_guilds:
        del test_mode_guilds[guild_id]

    await ctx.send("🎭 Game ended!")

if __name__ == '__main__':
    token = os.getenv('TOKEN')
    if not token:
        print("Error: TOKEN environment variable not set!")
        exit(1)
    bot.run(token)