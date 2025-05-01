# Discord Bot

A powerful Discord bot with moderation, utility, and fun commands using discord.py.

## Features

This bot includes three main modules:

1. **Moderation Commands** - Tools for server management like ban, kick, mute, warn, and more
2. **Utility Commands** - Server management features like role management, info commands, and server statistics
3. **Fun Commands** - Entertainment features including animal images, games, polls, and API integrations

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- A Discord account and a bot application created in the [Discord Developer Portal](https://discord.com/developers/applications)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/discord-bot.git
cd discord-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with the following variables:
```
TOKEN=your_discord_bot_token
CLIENT_ID=your_discord_client_id
CLIENT_SECRET=your_discord_client_secret
DEFAULT_PREFIX=?
```

### Running the Bot

```bash
python main.py
```

## Command Usage

The bot uses `?` as the default prefix, but this can be changed using the `?prefix` command or by modifying the .env file.

All commands are also available as slash commands for easier use.

### Some Common Commands

- `?help` - Shows the help menu
- `?info` - Displays information about the bot
- `?ping` - Checks the bot's latency
- `?ban <user> [reason]` - Bans a user from the server
- `?kick <user> [reason]` - Kicks a user from the server
- `?mute <user> [duration] [reason]` - Mutes a user
- `?warn <user> [reason]` - Warns a user
- `?notes <user>` - Shows all notes for a user
- `?moderations <user>` - Shows moderation cases for a user
- `?cat` - Shows a random cat image
- `?dog` - Shows a random dog image
- `?poll <question> <options...>` - Creates a poll
- `?roll [dice]` - Rolls one or more dice

## Configuration

### Adding the Bot to Your Server

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your bot application
3. Go to the "OAuth2" section
4. Under "OAuth2 URL Generator", select the "bot" and "applications.commands" scopes
5. Select the permissions your bot needs
6. Copy the generated URL and paste it in your browser
7. Select the server you want to add the bot to and confirm

### Custom Prefix

You can change the command prefix for your server using:
```
?prefix <new_prefix>
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.