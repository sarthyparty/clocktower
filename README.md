# Blood on the Clocktower Discord Bot

A Discord bot implementation of the social deduction game Blood on the Clocktower.

## Setup

1. Install dependencies:
```bash
pip install discord.py
```

2. Set your Discord bot token:
```bash
export TOKEN=your_discord_bot_token
```

3. Run the bot:
```bash
python discord_bot.py
```

## Usage

### Game Commands

| Command | Description |
|---------|-------------|
| `!test` | Enable test mode (single user plays all characters) |
| `!start player1 player2 ...` | Start game with 5-15 players |
| `!night` | Progress to night phase |
| `!state` | Show game state and player circle |
| `!debug` | Show all roles (debug info) |
| `!guide` | Show command help |
| `!end` | End current game |

### Night Actions (DM Only)

**Normal Mode:**
- `!action <targets>` - Submit your action
- Example: `!action Alice Bob`

**Test Mode:**
- `!action <character> <targets>` - Submit action for character
- Example: `!action Diana Alice Bob`

Both modes require `!confirm` or `!cancel` after submission.

## Game Flow

1. **Setup**: Use `!start` with 5-15 player names
2. **Night 0**: Automatically executes, sends role DMs
3. **Day/Night Cycles**: Use `!night` to progress phases
4. **Night Actions**: Players submit actions via DM
5. **Win Conditions**: Game ends automatically when conditions are met

## Features

- **Role Distribution**: Automatic based on player count
- **Test Mode**: Single user controls all characters for testing
- **Rich Discord Integration**: Embeds, DMs, visual player circle
- **Multi-Server Support**: Independent games per Discord server
- **Action Validation**: Proper targeting and confirmation system
- **Win Detection**: Automatic good vs evil team victory conditions

## Player Count & Roles

| Players | Townsfolk | Outsiders | Minions | Demons |
|---------|-----------|-----------|---------|---------|
| 5       | 3         | 0         | 1       | 1       |
| 6       | 3         | 1         | 1       | 1       |
| 7       | 5         | 0         | 1       | 1       |
| 8       | 5         | 1         | 1       | 1       |
| 9       | 5         | 2         | 1       | 1       |
| 10      | 7         | 0         | 2       | 1       |