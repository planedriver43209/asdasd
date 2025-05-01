import discord
from discord import app_commands
from discord.ext import commands
import random
import json
import datetime
import asyncio
import io
from utils.embed_generator import EmbedGenerator
from utils.permissions import PermissionChecker

class Fun(commands.Cog):
    """Fun commands for entertainment"""
    
    def __init__(self, bot):
        self.bot = bot
    
    # Cat command
    @commands.command(name="cat")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def cat_command(self, ctx):
        """Shows a random cat image"""
        async with self.bot.session.get(self.bot.config.CAT_API) as response:
            if response.status != 200:
                embed = EmbedGenerator.error(
                    "Cat API Error",
                    f"Could not fetch cat image. Status code: {response.status}"
                )
                return await ctx.send(embed=embed)
            
            data = await response.json()
            
            if not data or len(data) == 0:
                embed = EmbedGenerator.error(
                    "Cat API Error",
                    "No cat images available at the moment."
                )
                return await ctx.send(embed=embed)
            
            cat_url = data[0]["url"]
            
            embed = discord.Embed(
                title="Random Cat 🐱",
                color=EmbedGenerator.get_color("main"),
                timestamp=datetime.datetime.utcnow()
            )
            
            embed.set_image(url=cat_url)
            embed.set_footer(text=f"Requested by {ctx.author}")
            
            await ctx.send(embed=embed)
    
    @app_commands.command(name="cat", description="Shows a random cat image")
    async def cat_slash(self, interaction):
        """Slash command version of cat"""
        ctx = await self.bot.get_context(interaction)
        await self.cat_command(ctx)
    
    # Dad joke command
    @commands.command(name="dadjoke")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def dadjoke_command(self, ctx):
        """Tells a random dad joke"""
        headers = {"Accept": "application/json"}
        
        async with self.bot.session.get(self.bot.config.DAD_JOKE_API, headers=headers) as response:
            if response.status != 200:
                embed = EmbedGenerator.error(
                    "Dad Joke API Error",
                    f"Could not fetch dad joke. Status code: {response.status}"
                )
                return await ctx.send(embed=embed)
            
            data = await response.json()
            
            if "joke" not in data:
                embed = EmbedGenerator.error(
                    "Dad Joke API Error",
                    "No dad jokes available at the moment."
                )
                return await ctx.send(embed=embed)
            
            joke = data["joke"]
            
            embed = discord.Embed(
                title="Dad Joke 👨",
                description=joke,
                color=EmbedGenerator.get_color("main"),
                timestamp=datetime.datetime.utcnow()
            )
            
            embed.set_footer(text=f"Requested by {ctx.author}")
            
            await ctx.send(embed=embed)
    
    @app_commands.command(name="dadjoke", description="Tells a random dad joke")
    async def dadjoke_slash(self, interaction):
        """Slash command version of dadjoke"""
        ctx = await self.bot.get_context(interaction)
        await self.dadjoke_command(ctx)
    
    # Dog command
    @commands.command(name="dog")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def dog_command(self, ctx):
        """Shows a random dog image"""
        async with self.bot.session.get(self.bot.config.DOG_API) as response:
            if response.status != 200:
                embed = EmbedGenerator.error(
                    "Dog API Error",
                    f"Could not fetch dog image. Status code: {response.status}"
                )
                return await ctx.send(embed=embed)
            
            data = await response.json()
            
            if not data or len(data) == 0:
                embed = EmbedGenerator.error(
                    "Dog API Error",
                    "No dog images available at the moment."
                )
                return await ctx.send(embed=embed)
            
            dog_url = data[0]["url"]
            
            embed = discord.Embed(
                title="Random Dog 🐶",
                color=EmbedGenerator.get_color("main"),
                timestamp=datetime.datetime.utcnow()
            )
            
            embed.set_image(url=dog_url)
            embed.set_footer(text=f"Requested by {ctx.author}")
            
            await ctx.send(embed=embed)
    
    @app_commands.command(name="dog", description="Shows a random dog image")
    async def dog_slash(self, interaction):
        """Slash command version of dog"""
        ctx = await self.bot.get_context(interaction)
        await self.dog_command(ctx)
    
    # Flip command
    @commands.command(name="flip")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def flip_command(self, ctx):
        """Flips a coin"""
        result = random.choice(["Heads", "Tails"])
        
        embed = discord.Embed(
            title="Coin Flip 🪙",
            description=f"The coin landed on: **{result}**",
            color=EmbedGenerator.get_color("main"),
            timestamp=datetime.datetime.utcnow()
        )
        
        embed.set_footer(text=f"Flipped by {ctx.author}")
        
        await ctx.send(embed=embed)
    
    @app_commands.command(name="flip", description="Flips a coin")
    async def flip_slash(self, interaction):
        """Slash command version of flip"""
        ctx = await self.bot.get_context(interaction)
        await self.flip_command(ctx)
    
    # GitHub command
    @commands.command(name="github", aliases=["gh"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def github_command(self, ctx, *, repo_path):
        """Shows information about a GitHub repository"""
        # Clean up repository path
        repo_path = repo_path.strip()
        
        # Remove GitHub URL parts if included
        if "github.com/" in repo_path:
            repo_path = repo_path.split("github.com/")[1]
        
        # Remove trailing slashes and other URL components
        repo_path = repo_path.split("/")[0:2]
        if len(repo_path) < 2:
            embed = EmbedGenerator.error(
                "Invalid Repository",
                "Please provide a valid repository path in the format `owner/repo`."
            )
            return await ctx.send(embed=embed)
        
        repo_path = "/".join(repo_path)
        
        # Fetch repository data
        async with self.bot.session.get(f"{self.bot.config.GITHUB_API}{repo_path}") as response:
            if response.status == 404:
                embed = EmbedGenerator.error(
                    "Repository Not Found",
                    f"The repository `{repo_path}` was not found on GitHub."
                )
                return await ctx.send(embed=embed)
            
            if response.status != 200:
                embed = EmbedGenerator.error(
                    "GitHub API Error",
                    f"Could not fetch repository information. Status code: {response.status}"
                )
                return await ctx.send(embed=embed)
            
            data = await response.json()
            
            # Create embed
            embed = discord.Embed(
                title=data["full_name"],
                description=data["description"] or "No description provided",
                url=data["html_url"],
                color=0x2b3137,  # GitHub dark color
                timestamp=datetime.datetime.utcnow()
            )
            
            # Add repository owner avatar
            embed.set_author(
                name=data["owner"]["login"],
                icon_url=data["owner"]["avatar_url"],
                url=data["owner"]["html_url"]
            )
            
            # Add repository stats
            embed.add_field(name="Stars", value=f"⭐ {data['stargazers_count']}", inline=True)
            embed.add_field(name="Forks", value=f"🍴 {data['forks_count']}", inline=True)
            embed.add_field(name="Issues", value=f"⚠️ {data['open_issues_count']}", inline=True)
            
            # Add language info if available
            if data["language"]:
                embed.add_field(name="Language", value=data["language"], inline=True)
            
            # Add repository creation and update info
            created_at = datetime.datetime.strptime(data["created_at"], "%Y-%m-%dT%H:%M:%SZ")
            updated_at = datetime.datetime.strptime(data["updated_at"], "%Y-%m-%dT%H:%M:%SZ")
            
            embed.add_field(name="Created", value=f"<t:{int(created_at.timestamp())}:R>", inline=True)
            embed.add_field(name="Last Updated", value=f"<t:{int(updated_at.timestamp())}:R>", inline=True)
            
            embed.set_footer(text=f"Requested by {ctx.author}")
            
            await ctx.send(embed=embed)
    
    @app_commands.command(name="github", description="Shows information about a GitHub repository")
    @app_commands.describe(repo_path="Repository path in the format owner/repo")
    async def github_slash(self, interaction, repo_path: str):
        """Slash command version of github"""
        ctx = await self.bot.get_context(interaction)
        await self.github_command(ctx, repo_path=repo_path)
    
    # iTunes command
    @commands.command(name="itunes")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def itunes_command(self, ctx, *, song_name):
        """Searches for a song on iTunes"""
        # Create search parameters
        params = {
            "term": song_name,
            "media": "music",
            "entity": "song",
            "limit": 5
        }
        
        async with self.bot.session.get(self.bot.config.ITUNES_API, params=params) as response:
            if response.status != 200:
                embed = EmbedGenerator.error(
                    "iTunes API Error",
                    f"Could not search iTunes. Status code: {response.status}"
                )
                return await ctx.send(embed=embed)
            
            data = await response.json()
            
            if "results" not in data or len(data["results"]) == 0:
                embed = EmbedGenerator.error(
                    "No Results",
                    f"No songs found for \"{song_name}\""
                )
                return await ctx.send(embed=embed)
            
            # Get first result
            result = data["results"][0]
            
            # Create embed
            embed = discord.Embed(
                title=result["trackName"],
                description=f"By {result['artistName']}",
                url=result["trackViewUrl"],
                color=0xFC3C44,  # iTunes red color
                timestamp=datetime.datetime.utcnow()
            )
            
            # Add album cover
            embed.set_thumbnail(url=result["artworkUrl100"].replace("100x100", "300x300"))
            
            # Add song info
            embed.add_field(name="Album", value=result["collectionName"], inline=True)
            embed.add_field(name="Release Date", value=result["releaseDate"].split("T")[0], inline=True)
            
            # Add duration
            duration_ms = result["trackTimeMillis"]
            minutes, seconds = divmod(duration_ms // 1000, 60)
            embed.add_field(name="Duration", value=f"{minutes}:{seconds:02d}", inline=True)
            
            # Add preview if available
            if "previewUrl" in result:
                embed.add_field(name="Preview", value=f"[Listen to preview]({result['previewUrl']})", inline=True)
            
            # Add price if available
            if "trackPrice" in result and "currency" in result:
                embed.add_field(name="Price", value=f"{result['trackPrice']} {result['currency']}", inline=True)
            
            embed.set_footer(text=f"Requested by {ctx.author}")
            
            await ctx.send(embed=embed)
    
    @app_commands.command(name="itunes", description="Searches for a song on iTunes")
    @app_commands.describe(song_name="Name of the song to search for")
    async def itunes_slash(self, interaction, song_name: str):
        """Slash command version of itunes"""
        ctx = await self.bot.get_context(interaction)
        await self.itunes_command(ctx, song_name=song_name)
    
    # Pokemon command
    @commands.command(name="pokemon")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def pokemon_command(self, ctx, *, pokemon_name):
        """Shows information about a Pokemon"""
        # Clean up Pokemon name
        pokemon_name = pokemon_name.lower().strip()
        
        # Fetch Pokemon data
        async with self.bot.session.get(f"{self.bot.config.POKEMON_API}{pokemon_name}") as response:
            if response.status == 404:
                embed = EmbedGenerator.error(
                    "Pokemon Not Found",
                    f"No Pokemon named \"{pokemon_name}\" was found."
                )
                return await ctx.send(embed=embed)
            
            if response.status != 200:
                embed = EmbedGenerator.error(
                    "Pokemon API Error",
                    f"Could not fetch Pokemon information. Status code: {response.status}"
                )
                return await ctx.send(embed=embed)
            
            data = await response.json()
            
            # Create embed
            embed = discord.Embed(
                title=f"#{data['id']} - {data['name'].capitalize()}",
                color=0xDD2D51,  # Pokemon red color
                timestamp=datetime.datetime.utcnow()
            )
            
            # Add Pokemon sprite
            embed.set_thumbnail(url=data["sprites"]["front_default"])
            
            # Add type information
            types = [t["type"]["name"].capitalize() for t in data["types"]]
            embed.add_field(name="Type", value=", ".join(types), inline=True)
            
            # Add base stats
            stats = {}
            for stat in data["stats"]:
                stats[stat["stat"]["name"]] = stat["base_stat"]
            
            stats_text = f"HP: {stats.get('hp', 'N/A')}\n"
            stats_text += f"Attack: {stats.get('attack', 'N/A')}\n"
            stats_text += f"Defense: {stats.get('defense', 'N/A')}\n"
            stats_text += f"Sp. Atk: {stats.get('special-attack', 'N/A')}\n"
            stats_text += f"Sp. Def: {stats.get('special-defense', 'N/A')}\n"
            stats_text += f"Speed: {stats.get('speed', 'N/A')}"
            
            embed.add_field(name="Base Stats", value=stats_text, inline=True)
            
            # Add abilities
            abilities = [a["ability"]["name"].replace("-", " ").title() for a in data["abilities"]]
            embed.add_field(name="Abilities", value=", ".join(abilities), inline=False)
            
            # Add height and weight
            height_m = data["height"] / 10
            weight_kg = data["weight"] / 10
            embed.add_field(name="Height", value=f"{height_m} m", inline=True)
            embed.add_field(name="Weight", value=f"{weight_kg} kg", inline=True)
            
            embed.set_footer(text=f"Requested by {ctx.author}")
            
            await ctx.send(embed=embed)
    
    @app_commands.command(name="pokemon", description="Shows information about a Pokemon")
    @app_commands.describe(pokemon_name="Name of the Pokemon to look up")
    async def pokemon_slash(self, interaction, pokemon_name: str):
        """Slash command version of pokemon"""
        ctx = await self.bot.get_context(interaction)
        await self.pokemon_command(ctx, pokemon_name=pokemon_name)
    
    # Poll command
    @commands.command(name="poll")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def poll_command(self, ctx, question, *options):
        """Creates a poll with reactions as voting options"""
        # Check if valid arguments
        if not question:
            embed = EmbedGenerator.error(
                "Invalid Usage",
                f"Usage: `{ctx.prefix}poll \"question\" \"option1\" \"option2\" ...`"
            )
            return await ctx.send(embed=embed)
        
        # Strip quotes if present
        if question.startswith('"') and question.endswith('"'):
            question = question[1:-1]
        
        # Format options
        formatted_options = []
        for i, option in enumerate(options):
            option_text = option
            if option.startswith('"') and option.endswith('"'):
                option_text = option[1:-1]
            formatted_options.append(f"{i+1}. {option_text}")
        
        # If no options provided, create a yes/no poll
        if not formatted_options:
            embed = discord.Embed(
                title="📊 " + question,
                description="React with 👍 for Yes or 👎 for No",
                color=EmbedGenerator.get_color("main"),
                timestamp=datetime.datetime.utcnow()
            )
            
            embed.set_footer(text=f"Poll by {ctx.author}")
            
            poll_message = await ctx.send(embed=embed)
            await poll_message.add_reaction("👍")
            await poll_message.add_reaction("👎")
            
        else:
            # Create a poll with custom options (max 10)
            if len(formatted_options) > 10:
                embed = EmbedGenerator.error(
                    "Too Many Options",
                    "Polls can have a maximum of 10 options."
                )
                return await ctx.send(embed=embed)
                
            embed = discord.Embed(
                title="📊 " + question,
                description="\n".join(formatted_options),
                color=EmbedGenerator.get_color("main"),
                timestamp=datetime.datetime.utcnow()
            )
            
            embed.set_footer(text=f"Poll by {ctx.author}")
            
            poll_message = await ctx.send(embed=embed)
            
            # Add number reactions
            reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            for i in range(len(formatted_options)):
                await poll_message.add_reaction(reactions[i])
    
    @app_commands.command(name="poll", description="Creates a poll with reactions as voting options")
    @app_commands.describe(
        question="The poll question",
        option1="Option 1",
        option2="Option 2",
        option3="Option 3 (optional)",
        option4="Option 4 (optional)",
        option5="Option 5 (optional)"
    )
    async def poll_slash(
        self, interaction, question: str, option1: str = None, option2: str = None,
        option3: str = None, option4: str = None, option5: str = None
    ):
        """Slash command version of poll"""
        ctx = await self.bot.get_context(interaction)
        
        # Collect non-None options
        options = []
        for option in [option1, option2, option3, option4, option5]:
            if option:
                options.append(f'"{option}"')
        
        # If no options provided, create yes/no poll
        if not options:
            await self.poll_command(ctx, f'"{question}"')
        else:
            await self.poll_command(ctx, f'"{question}"', *options)
    
    # Pug command
    @commands.command(name="pug")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def pug_command(self, ctx):
        """Shows a random pug image"""
        async with self.bot.session.get(self.bot.config.PUG_API) as response:
            if response.status != 200:
                embed = EmbedGenerator.error(
                    "Pug API Error",
                    f"Could not fetch pug image. Status code: {response.status}"
                )
                return await ctx.send(embed=embed)
            
            data = await response.json()
            
            if "message" not in data:
                embed = EmbedGenerator.error(
                    "Pug API Error",
                    "No pug images available at the moment."
                )
                return await ctx.send(embed=embed)
            
            pug_url = data["message"]
            
            embed = discord.Embed(
                title="Random Pug 🐶",
                color=EmbedGenerator.get_color("main"),
                timestamp=datetime.datetime.utcnow()
            )
            
            embed.set_image(url=pug_url)
            embed.set_footer(text=f"Requested by {ctx.author}")
            
            await ctx.send(embed=embed)
    
    @app_commands.command(name="pug", description="Shows a random pug image")
    async def pug_slash(self, interaction):
        """Slash command version of pug"""
        ctx = await self.bot.get_context(interaction)
        await self.pug_command(ctx)
    
    # Roll command
    @commands.command(name="roll")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def roll_command(self, ctx, size: int = 6, count: int = 1):
        """Rolls one or more dice"""
        # Validate inputs
        if size < 2:
            embed = EmbedGenerator.error(
                "Invalid Dice Size",
                "Dice size must be at least 2."
            )
            return await ctx.send(embed=embed)
        
        if count < 1 or count > 20:
            embed = EmbedGenerator.error(
                "Invalid Dice Count",
                "You can roll between 1 and 20 dice at once."
            )
            return await ctx.send(embed=embed)
        
        # Roll the dice
        results = [random.randint(1, size) for _ in range(count)]
        total = sum(results)
        
        # Format the results
        result_text = ", ".join(str(r) for r in results)
        
        # Create embed
        embed = discord.Embed(
            title=f"🎲 Dice Roll: {count}d{size}",
            color=EmbedGenerator.get_color("main"),
            timestamp=datetime.datetime.utcnow()
        )
        
        embed.add_field(name="Results", value=result_text, inline=False)
        
        if count > 1:
            embed.add_field(name="Total", value=str(total), inline=True)
            
        embed.set_footer(text=f"Rolled by {ctx.author}")
        
        await ctx.send(embed=embed)
    
    @app_commands.command(name="roll", description="Rolls one or more dice")
    @app_commands.describe(
        size="Number of sides on each die (default: 6)",
        count="Number of dice to roll (default: 1)"
    )
    async def roll_slash(self, interaction, size: int = 6, count: int = 1):
        """Slash command version of roll"""
        ctx = await self.bot.get_context(interaction)
        await self.roll_command(ctx, size, count)
    
    # RPS command
    @commands.command(name="rps")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def rps_command(self, ctx, choice: str = None):
        """Play rock paper scissors against the bot"""
        valid_choices = ["rock", "paper", "scissors", "r", "p", "s"]
        
        if not choice or choice.lower() not in valid_choices:
            embed = EmbedGenerator.error(
                "Invalid Choice",
                f"Please choose one of: rock (r), paper (p), scissors (s)"
            )
            return await ctx.send(embed=embed)
        
        # Normalize player choice
        player_choice = choice.lower()
        if player_choice == "r":
            player_choice = "rock"
        elif player_choice == "p":
            player_choice = "paper"
        elif player_choice == "s":
            player_choice = "scissors"
        
        # Bot's choice
        bot_choice = random.choice(["rock", "paper", "scissors"])
        
        # Determine winner
        result = "Tie"
        if player_choice == "rock":
            if bot_choice == "paper":
                result = "You lose"
            elif bot_choice == "scissors":
                result = "You win"
        elif player_choice == "paper":
            if bot_choice == "scissors":
                result = "You lose"
            elif bot_choice == "rock":
                result = "You win"
        elif player_choice == "scissors":
            if bot_choice == "rock":
                result = "You lose"
            elif bot_choice == "paper":
                result = "You win"
        
        # Get emojis for choices
        emojis = {
            "rock": "🪨",
            "paper": "📄",
            "scissors": "✂️"
        }
        
        # Create embed
        embed = discord.Embed(
            title="Rock Paper Scissors",
            description=f"**{result}!**",
            color=EmbedGenerator.get_color("main"),
            timestamp=datetime.datetime.utcnow()
        )
        
        embed.add_field(name=f"{ctx.author.display_name}", value=f"{emojis[player_choice]} {player_choice.capitalize()}", inline=True)
        embed.add_field(name=f"{ctx.guild.me.display_name}", value=f"{emojis[bot_choice]} {bot_choice.capitalize()}", inline=True)
        
        embed.set_footer(text=f"Game with {ctx.author}")
        
        await ctx.send(embed=embed)
    
    @app_commands.command(name="rps", description="Play rock paper scissors against the bot")
    @app_commands.describe(choice="Your choice: rock, paper, or scissors")
    @app_commands.choices(choice=[
        app_commands.Choice(name="Rock", value="rock"),
        app_commands.Choice(name="Paper", value="paper"),
        app_commands.Choice(name="Scissors", value="scissors")
    ])
    async def rps_slash(self, interaction, choice: str):
        """Slash command version of rps"""
        ctx = await self.bot.get_context(interaction)
        await self.rps_command(ctx, choice)
    
    # Space command
    @commands.command(name="space")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def space_command(self, ctx):
        """Shows NASA's Astronomy Picture of the Day"""
        # We would typically use an API key here, but will use demo key for example
        params = {"api_key": "DEMO_KEY"}
        
        async with self.bot.session.get(self.bot.config.SPACE_API, params=params) as response:
            if response.status != 200:
                embed = EmbedGenerator.error(
                    "NASA API Error",
                    f"Could not fetch space image. Status code: {response.status}"
                )
                return await ctx.send(embed=embed)
            
            data = await response.json()
            
            if "url" not in data:
                embed = EmbedGenerator.error(
                    "NASA API Error",
                    "No space image available at the moment."
                )
                return await ctx.send(embed=embed)
            
            # Create embed
            embed = discord.Embed(
                title=data.get("title", "Astronomy Picture of the Day"),
                description=data.get("explanation", "No description available.")[:1000] + "..." if len(data.get("explanation", "")) > 1000 else data.get("explanation", "No description available."),
                color=0x0B3D91,  # NASA blue
                timestamp=datetime.datetime.utcnow()
            )
            
            # Add image or video
            if data.get("media_type") == "video":
                embed.add_field(name="Video", value=f"[Watch here]({data['url']})", inline=False)
                if "thumbnail_url" in data:
                    embed.set_image(url=data["thumbnail_url"])
            else:
                embed.set_image(url=data["url"])
            
            embed.add_field(name="Date", value=data.get("date", "Unknown"), inline=True)
            
            if "copyright" in data:
                embed.add_field(name="Copyright", value=data["copyright"], inline=True)
            
            embed.set_footer(text=f"Requested by {ctx.author} | NASA Astronomy Picture of the Day")
            
            await ctx.send(embed=embed)
    
    @app_commands.command(name="space", description="Shows NASA's Astronomy Picture of the Day")
    async def space_slash(self, interaction):
        """Slash command version of space"""
        ctx = await self.bot.get_context(interaction)
        await self.space_command(ctx)

async def setup(bot):
    await bot.add_cog(Fun(bot))
