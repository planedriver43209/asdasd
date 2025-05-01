import os
import discord
import logging
import asyncio
from discord.ext import commands
import datetime
import traceback
from config import Config
from database import setup_database
import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('discord_bot')

class DiscordBot(commands.Bot):
    def __init__(self, config):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix=self._get_prefix,
            intents=intents,
            case_insensitive=True,
            help_command=None,  # Custom help command will be implemented
        )
        self.config = config
        self.db = None
        self.start_time = datetime.datetime.utcnow()
        self.session = None
        
    async def _get_prefix(self, bot, message):
        default_prefix = self.config.DEFAULT_PREFIX
        
        # If it's a DM, just use the default prefix
        if not message.guild:
            return commands.when_mentioned_or(default_prefix)(bot, message)
        
        # Get custom prefix from database if exists
        custom_prefix = await self.db.get_guild_prefix(message.guild.id)
        prefix = custom_prefix if custom_prefix else default_prefix
        
        return commands.when_mentioned_or(prefix)(bot, message)
    
    async def setup_hook(self):
        # Initialize database connection
        self.db = await setup_database()
        
        # Create aiohttp session
        self.session = aiohttp.ClientSession()
        
        # Load extensions
        await self.load_extensions()
        
        logger.info("Bot is ready to start!")
    
    async def load_extensions(self):
        """Load all cogs"""
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and not filename.startswith('_'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    logger.info(f"Loaded extension: {filename}")
                except Exception as e:
                    logger.error(f"Failed to load extension {filename}: {e}")
                    traceback.print_exc()
    
    async def on_ready(self):
        """Event triggered when the bot is ready"""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guilds")
        
        # Set activity
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name=f"{self.config.DEFAULT_PREFIX}help | /help"
        )
        await self.change_presence(activity=activity)
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")
    
    async def on_command_error(self, ctx, error):
        """Global error handler for command errors"""
        if isinstance(error, commands.CommandNotFound):
            return
        
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"⚠️ Missing required argument: `{error.param.name}`\nUse `{ctx.prefix}help {ctx.command}` for proper usage.")
            return
            
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have the required permissions to use this command.")
            return
            
        if isinstance(error, commands.BotMissingPermissions):
            await ctx.send(f"❌ I need the following permissions to execute this command: {', '.join(error.missing_permissions)}")
            return
            
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏱️ This command is on cooldown. Try again in {error.retry_after:.2f}s")
            return
            
        if isinstance(error, commands.CheckFailure):
            await ctx.send("❌ You don't have permission to use this command.")
            return
            
        # Log other errors
        logger.error(f"Command error in {ctx.command}: {error}")
        traceback.print_exception(type(error), error, error.__traceback__)
        
        # Send error to user
        await ctx.send("❌ An error occurred while executing this command. Please try again later.")
    
    async def close(self):
        """Proper cleanup on bot shutdown"""
        if self.session:
            await self.session.close()
        
        if self.db:
            await self.db.close()
            
        await super().close()
    
    async def start_bot(self):
        """Start the bot with the token"""
        try:
            await self.start(self.config.TOKEN)
        except discord.errors.LoginFailure:
            logger.error("Invalid Discord token. Please check your .env file.")
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            traceback.print_exc()
        finally:
            await self.close()

def initialize_bot():
    """Initialize the bot with configuration"""
    config = Config()
    return DiscordBot(config)
