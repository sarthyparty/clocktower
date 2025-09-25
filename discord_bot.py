import discord
from discord.ext import commands
from clocktower_game import ClocktowerGame
from typing import Dict, List, Optional
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

games: Dict[int, ClocktowerGame] = {}  # guild_id -> game instance
player_guilds: Dict[int, int] = {}  # user_id -> guild_id

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

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

    # Validate all players are in the server
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

    # Create new game
    game = ClocktowerGame()
    games[guild_id] = game

    # Map members to this guild and store their IDs
    player_members = {}  # username -> member object
    for i, member in enumerate(members):
        player_guilds[member.id] = guild_id
        player_members[players[i]] = member

    # Start the game
    result = game.start_game(list(players))

    if "error" in result:
        await ctx.send(f"Error starting game: {result['error']}")
        del games[guild_id]
        return

    await ctx.send(f"🎭 **Clocktower Game Started!**\n"
                   f"Players: {', '.join(players)}\n"
                   f"Phase: {result['phase'].title()}\n"
                   f"Night {game.night_count}")

    # Send role info to players via DM
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

    # Check if any players need to submit actions
    await check_night_actions(ctx.guild)

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

    # Check for night actions
    await check_night_actions(ctx.guild)

@bot.command(name='day')
async def progress_to_day(ctx):
    if ctx.guild is None:
        await ctx.send("This command must be used in a server.")
        return

    guild_id = ctx.guild.id
    if guild_id not in games:
        await ctx.send("No game running in this server!")
        return

    game = games[guild_id]
    result = game.progress_to_day()

    if "error" in result:
        await ctx.send(f"Error: {result['error']}")
        if "pending_players" in result:
            await ctx.send(f"Waiting for: {', '.join(result['pending_players'])}")
        return

    await ctx.send(f"☀️ **Day {game.day_count} begins!**")

    if "night_results" in result and result["night_results"].get("deaths"):
        deaths = result["night_results"]["deaths"]
        await ctx.send(f"💀 **Deaths:** {', '.join(deaths)}")

@bot.command(name='status')
async def game_status(ctx):
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

    embed = discord.Embed(title="🎭 Game Status", color=0x7289da)
    embed.add_field(name="Phase", value=f"{game.phase.value.title()}", inline=True)
    embed.add_field(name="Day", value=str(game.day_count), inline=True)
    embed.add_field(name="Night", value=str(game.night_count), inline=True)
    embed.add_field(name="Alive", value=', '.join(alive_players) if alive_players else "None", inline=False)

    if dead_players:
        embed.add_field(name="Dead", value=', '.join(dead_players), inline=False)

    if game.phase.value == "night":
        status = game.action_collector.get_collection_status()
        if status["pending_players"]:
            embed.add_field(name="Waiting for Actions", value=', '.join(status["pending_players"]), inline=False)

    await ctx.send(embed=embed)

async def check_night_actions(guild):
    guild_id = guild.id
    if guild_id not in games:
        return

    game = games[guild_id]
    if game.phase.value != "night":
        return

    status = game.action_collector.get_collection_status()

    for username in status["pending_players"]:
        member = discord.utils.find(lambda m: m.name == username or m.display_name == username, guild.members)
        if member:
            player = next(p for p in game.players if p.username == username)
            role_name = player.role.name

            embed = discord.Embed(
                title="🌙 Night Action Required",
                description=f"**{role_name}**\nYou need to submit your night action!",
                color=0x992d22
            )

            # Add specific instructions based on role
            if role_name == "Fortune Teller":
                embed.add_field(name="Action", value="Choose 2 players to read", inline=False)
                embed.add_field(name="Command", value="!action player1 player2", inline=False)
            elif role_name in ["Imp", "Poisoner", "Monk"]:
                embed.add_field(name="Action", value="Choose 1 player", inline=False)
                embed.add_field(name="Command", value="!action player_name", inline=False)

            try:
                await member.send(embed=embed)
            except discord.Forbidden:
                pass

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Handle DM commands
    if isinstance(message.channel, discord.DMChannel):
        if message.content.startswith('!action'):
            await handle_action_dm(message)
        return

    await bot.process_commands(message)

async def handle_action_dm(message):
    user_id = message.author.id

    if user_id not in player_guilds:
        await message.channel.send("You're not part of any active game!")
        return

    guild_id = player_guilds[user_id]
    if guild_id not in games:
        await message.channel.send("No active game found!")
        return

    game = games[guild_id]
    username = message.author.name

    # Parse action command
    parts = message.content.split()[1:]  # Remove '!action'

    if not parts:
        await message.channel.send("Please specify your choices! Example: `!action player1 player2`")
        return

    # Submit the action
    result = game.submit_night_action(username, parts)

    if "error" in result:
        await message.channel.send(f"Error: {result['error']}")
        return

    await message.channel.send(f"✅ Action submitted: {', '.join(parts)}")

    if result.get("collection_complete"):
        guild = bot.get_guild(guild_id)
        if guild:
            # Find a general channel to announce
            channel = discord.utils.find(lambda c: c.name in ['general', 'game', 'clocktower'], guild.text_channels)
            if channel:
                await channel.send("🌙 All night actions submitted! Executing...")

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
    # Remove player mappings for this guild
    to_remove = [uid for uid, gid in player_guilds.items() if gid == guild_id]
    for uid in to_remove:
        del player_guilds[uid]

    await ctx.send("🎭 Game ended!")

if __name__ == '__main__':
    token = os.getenv('TOKEN')
    if not token:
        print("Error: TOKEN environment variable not set!")
        exit(1)
    bot.run(token)