import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for the bot"""
    def __init__(self):
        # Discord bot token and application ID
        self.TOKEN = os.getenv('TOKEN')
        self.CLIENT_SECRET = os.getenv('CLIENT_SECRET')
        self.DEFAULT_PREFIX = os.getenv('DEFAULT_PREFIX', '?')
        
        # Database configuration
        self.DATABASE_NAME = "discord_bot.db"
        
        # API endpoints for fun commands
        self.CAT_API = "https://api.thecatapi.com/v1/images/search"
        self.DOG_API = "https://api.thedogapi.com/v1/images/search"
        self.PUG_API = "https://dog.ceo/api/breed/pug/images/random"
        self.DAD_JOKE_API = "https://icanhazdadjoke.com/"
        self.POKEMON_API = "https://pokeapi.co/api/v2/pokemon/"
        self.SPACE_API = "https://api.nasa.gov/planetary/apod"
        self.GITHUB_API = "https://api.github.com/repos/"
        self.ITUNES_API = "https://itunes.apple.com/search"
        
        # Command cooldowns in seconds
        self.COOLDOWNS = {
            "default": 3,
            "fun": 5,
            "moderation": 3,
            "utility": 3
        }
        
        # Color codes for embeds
        self.COLORS = {
            "main": 0x5865F2,  # Discord blurple
            "success": 0x57F287,  # Green
            "warning": 0xFEE75C,  # Yellow
            "error": 0xED4245,  # Red
            "info": 0x5865F2,  # Blurple
            "moderation": 0xEB459E  # Pink
        }
