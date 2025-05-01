# Dependencies

This Discord bot requires the following Python packages:

```
aiohttp>=3.8.5
aiosqlite>=0.19.0
discord.py>=2.3.2
python-dotenv>=1.0.0
psutil>=5.9.6
```

## Installation

To install these dependencies, use pip:

```bash
pip install -r requirements.txt
```

Or install each package individually:

```bash
pip install aiohttp aiosqlite discord.py python-dotenv psutil
```

## Environment Variables

Create a `.env` file in the project root with the following variables:

```
TOKEN=your_discord_bot_token
CLIENT_ID=your_discord_client_id
CLIENT_SECRET=your_discord_client_secret
DEFAULT_PREFIX=?
```

## Database

The bot uses SQLite for data storage. The database file `discord_bot.db` will be created automatically when the bot is first run.