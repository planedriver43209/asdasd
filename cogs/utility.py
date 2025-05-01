import discord
from discord import app_commands
from discord.ext import commands
import time
import datetime
import asyncio
import platform
import re
import sys
import os
import psutil
from utils.embed_generator import EmbedGenerator
from utils.permissions import PermissionChecker

class Utility(commands.Cog):
    """Utility commands for server management and information"""
    
    def __init__(self, bot):
        self.bot = bot
        self.emoji_regex = re.compile(r'<a?:[a-zA-Z0-9_]+:([0-9]+)>')
    
    # Help command
    @commands.command(name="help", aliases=["h"])
    async def help_command(self, ctx, *, query=None):
        """Shows help information for commands or categories"""
        prefix = ctx.prefix
        
        # Create a dictionary of all commands grouped by cog
        command_dict = {}
        for cmd in self.bot.commands:
            if cmd.hidden:
                continue
                
            cog_name = cmd.cog.qualified_name if cmd.cog else "No Category"
            
            if cog_name not in command_dict:
                command_dict[cog_name] = []
                
            command_dict[cog_name].append({
                "name": cmd.name,
                "description": cmd.help or "No description available"
            })
        
        # If no query provided, show the main help page
        if not query:
            embed = EmbedGenerator.help_main(command_dict, prefix)
            return await ctx.send(embed=embed)
        
        # Check if query is a command
        found_command = self.bot.get_command(query)
        if found_command:
            # Get command info
            description = found_command.help or "No description available"
            usage = f"{prefix}{found_command.name} {found_command.signature}"
            
            # Generate examples
            examples = []
            if found_command.name == "ban":
                examples.append(f"`{prefix}ban @user`\n`{prefix}ban @user 7d Spamming`")
            elif found_command.name == "kick":
                examples.append(f"`{prefix}kick @user`\n`{prefix}kick @user Breaking rules`")
            elif found_command.name == "mute":
                examples.append(f"`{prefix}mute @user`\n`{prefix}mute @user 2h Excessive mentions`")
            
            examples_text = "\n".join(examples) if examples else "No examples available"
            
            # Get category
            category = found_command.cog.qualified_name if found_command.cog else "No Category"
            
            embed = EmbedGenerator.help_command(
                found_command.name,
                description,
                usage,
                examples_text,
                category
            )
            
            return await ctx.send(embed=embed)
        
        # Check if query is a category
        for category in command_dict:
            if query.lower() == category.lower():
                embed = EmbedGenerator.help_category(category, command_dict[category], prefix)
                return await ctx.send(embed=embed)
        
        # If we get here, the query didn't match anything
        embed = EmbedGenerator.error(
            "Command or category not found",
            f"Could not find a command or category matching `{query}`.\nUse `{prefix}help` to see all available commands."
        )
        await ctx.send(embed=embed)
    
    @app_commands.command(name="help", description="Shows help information for commands or categories")
    @app_commands.describe(command="The command or category to get help for")
    async def help_slash(self, interaction, command: str = None):
        """Slash command version of help"""
        ctx = await self.bot.get_context(interaction)
        await self.help_command(ctx, query=command)
    
    # Info command
    @commands.command(name="info")
    async def info_command(self, ctx):
        """Shows information about the bot"""
        embed = discord.Embed(
            title="Discord Bot Info",
            description="A powerful Discord bot with moderation, utility, and fun commands",
            color=EmbedGenerator.get_color("main"),
            timestamp=datetime.datetime.utcnow()
        )
        
        # Bot information
        embed.add_field(name="Bot Version", value="1.0.0", inline=True)
        embed.add_field(name="discord.py Version", value=discord.__version__, inline=True)
        embed.add_field(name="Python Version", value=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}", inline=True)
        
        # System info
        embed.add_field(name="Platform", value=platform.system(), inline=True)
        embed.add_field(name="Memory Usage", value=f"{psutil.Process().memory_info().rss / 1024 ** 2:.2f} MB", inline=True)
        embed.add_field(name="CPU Usage", value=f"{psutil.cpu_percent()}%", inline=True)
        
        # Bot stats
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="Users", value=str(sum(g.member_count for g in self.bot.guilds)), inline=True)
        embed.add_field(name="Commands", value=str(len(self.bot.commands)), inline=True)
        
        # Set bot avatar as thumbnail if available
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        
        embed.set_footer(text=f"Requested by {ctx.author}")
        
        await ctx.send(embed=embed)
    
    @app_commands.command(name="info", description="Shows information about the bot")
    async def info_slash(self, interaction):
        """Slash command version of info"""
        ctx = await self.bot.get_context(interaction)
        await self.info_command(ctx)
    
    # Ping command
    @commands.command(name="ping")
    async def ping_command(self, ctx):
        """Shows the bot's latency to Discord"""
        start_time = time.time()
        message = await ctx.send("Pinging...")
        end_time = time.time()
        
        api_latency = round(self.bot.latency * 1000)
        message_latency = round((end_time - start_time) * 1000)
        
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Bot Latency: {message_latency}ms\nWebSocket: {api_latency}ms",
            color=EmbedGenerator.get_color("info"),
            timestamp=datetime.datetime.utcnow()
        )
        
        await message.edit(content=None, embed=embed)
    
    @app_commands.command(name="ping", description="Shows the bot's latency to Discord")
    async def ping_slash(self, interaction):
        """Slash command version of ping"""
        ctx = await self.bot.get_context(interaction)
        await self.ping_command(ctx)
    
    # Premium command (placeholder)
    @commands.command(name="premium")
    async def premium_command(self, ctx):
        """Information about premium features"""
        embed = discord.Embed(
            title="Premium Features",
            description="Premium features are not currently available. This is a demonstration command.",
            color=EmbedGenerator.get_color("main"),
            timestamp=datetime.datetime.utcnow()
        )
        
        embed.add_field(
            name="Premium Features",
            value="• Advanced automod features\n• Custom command limits increased\n• Premium support\n• Additional features",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @app_commands.command(name="premium", description="Information about premium features")
    async def premium_slash(self, interaction):
        """Slash command version of premium"""
        ctx = await self.bot.get_context(interaction)
        await self.premium_command(ctx)
    
    # Stats command
    @commands.command(name="stats")
    async def stats_command(self, ctx):
        """Shows bot statistics and system information"""
        embed = discord.Embed(
            title="Bot Statistics",
            color=EmbedGenerator.get_color("info"),
            timestamp=datetime.datetime.utcnow()
        )
        
        # System stats
        system_stats = f"**OS:** {platform.system()} {platform.release()}\n"
        system_stats += f"**Python:** {sys.version.split()[0]}\n"
        system_stats += f"**discord.py:** {discord.__version__}\n"
        embed.add_field(name="System", value=system_stats, inline=False)
        
        # Performance stats
        performance_stats = f"**Memory:** {psutil.Process().memory_info().rss / 1024 ** 2:.2f} MB\n"
        performance_stats += f"**CPU:** {psutil.cpu_percent()}%\n"
        performance_stats += f"**Threads:** {psutil.Process().num_threads()}"
        embed.add_field(name="Performance", value=performance_stats, inline=False)
        
        # Discord stats
        discord_stats = f"**Servers:** {len(self.bot.guilds)}\n"
        discord_stats += f"**Users:** {sum(g.member_count for g in self.bot.guilds)}\n"
        discord_stats += f"**Channels:** {sum(len(g.channels) for g in self.bot.guilds)}"
        embed.add_field(name="Discord", value=discord_stats, inline=False)
        
        # Command stats
        command_count = len(self.bot.commands)
        cog_count = len(self.bot.cogs)
        embed.add_field(name="Commands", value=f"**Total:** {command_count}\n**Categories:** {cog_count}", inline=False)
        
        # Uptime
        uptime = datetime.datetime.utcnow() - self.bot.start_time
        uptime_str = self.format_uptime(uptime)
        embed.add_field(name="Uptime", value=uptime_str, inline=False)
        
        await ctx.send(embed=embed)
    
    @app_commands.command(name="stats", description="Shows bot statistics and system information")
    async def stats_slash(self, interaction):
        """Slash command version of stats"""
        ctx = await self.bot.get_context(interaction)
        await self.stats_command(ctx)
    
    # Uptime command
    @commands.command(name="uptime")
    async def uptime_command(self, ctx):
        """Shows how long the bot has been online"""
        uptime = datetime.datetime.utcnow() - self.bot.start_time
        uptime_str = self.format_uptime(uptime)
        
        embed = discord.Embed(
            title="Bot Uptime",
            description=f"The bot has been online for: **{uptime_str}**",
            color=EmbedGenerator.get_color("info"),
            timestamp=datetime.datetime.utcnow()
        )
        
        started_at = int(self.bot.start_time.timestamp())
        embed.add_field(name="Started At", value=f"<t:{started_at}:F> (<t:{started_at}:R>)")
        
        await ctx.send(embed=embed)
    
    @app_commands.command(name="uptime", description="Shows how long the bot has been online")
    async def uptime_slash(self, interaction):
        """Slash command version of uptime"""
        ctx = await self.bot.get_context(interaction)
        await self.uptime_command(ctx)
    
    # Addemote command
    @commands.command(name="addemote", aliases=["addemoji"])
    @commands.guild_only()
    @PermissionChecker.admin_or_permissions(manage_emojis=True)
    @PermissionChecker.bot_has_permissions(manage_emojis=True)
    async def addemote_command(self, ctx, name: str, *, url=None):
        """Adds an emoji to the server from a URL or attachment"""
        if len(name) < 2 or len(name) > 32:
            embed = EmbedGenerator.error(
                "Invalid emoji name",
                "Emoji name must be between 2 and 32 characters."
            )
            return await ctx.send(embed=embed)
        
        # Check if URL is actually an emoji ID
        emoji_match = self.emoji_regex.search(url) if url else None
        
        # Check for attachments or embeds
        image_url = None
        if ctx.message.attachments and ctx.message.attachments[0].content_type.startswith("image/"):
            image_url = ctx.message.attachments[0].url
        elif emoji_match:
            emoji_id = emoji_match.group(1)
            is_animated = url.startswith("<a:")
            image_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{'gif' if is_animated else 'png'}"
        elif url:
            image_url = url
        
        if not image_url:
            embed = EmbedGenerator.error(
                "No image provided",
                "Please provide an image URL, upload an image, or specify an existing emoji."
            )
            return await ctx.send(embed=embed)
        
        async with self.bot.session.get(image_url) as resp:
            if resp.status != 200:
                embed = EmbedGenerator.error(
                    "Failed to download image",
                    "Could not download the image. Make sure the URL is valid."
                )
                return await ctx.send(embed=embed)
            
            image_data = await resp.read()
            
            try:
                emoji = await ctx.guild.create_custom_emoji(name=name, image=image_data)
                embed = EmbedGenerator.success(
                    "Emoji added",
                    f"Successfully added {emoji} as `{name}`"
                )
                await ctx.send(embed=embed)
            except discord.HTTPException as e:
                error_msg = "Unknown error"
                if "maximum number of emojis reached" in str(e):
                    error_msg = "This server has reached the maximum number of emoji slots."
                elif "Invalid image data" in str(e):
                    error_msg = "The image data is invalid. Only PNG, JPG, and GIF images are supported."
                elif "File cannot be larger than" in str(e):
                    error_msg = "The image file is too large. Discord limits emoji to 256KB."
                
                embed = EmbedGenerator.error(
                    "Failed to add emoji",
                    f"Error: {error_msg}"
                )
                await ctx.send(embed=embed)
    
    @app_commands.command(name="addemote", description="Adds an emoji to the server")
    @app_commands.describe(
        name="The name of the emoji",
        url="URL of the image to use (can be omitted if you upload an image)"
    )
    @app_commands.guild_only()
    async def addemote_slash(self, interaction, name: str, url: str = None):
        """Slash command version of addemote"""
        ctx = await self.bot.get_context(interaction)
        if await PermissionChecker.is_admin(ctx) or ctx.author.guild_permissions.manage_emojis:
            await self.addemote_command(ctx, name, url=url)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need the 'Manage Emojis' permission to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Addmod command
    @commands.command(name="addmod", aliases=["addmodrole"])
    @commands.guild_only()
    @PermissionChecker.admin_or_permissions(administrator=True)
    async def addmod_command(self, ctx, *, role: discord.Role):
        """Adds a moderator role to the server"""
        success = await self.bot.db.add_mod_role(ctx.guild.id, role.id)
        
        if success:
            embed = EmbedGenerator.success(
                "Moderator Role Added",
                f"Added {role.mention} as a moderator role.\nUsers with this role can now use moderation commands."
            )
            await ctx.send(embed=embed)
        else:
            embed = EmbedGenerator.error(
                "Role Already a Moderator",
                f"{role.mention} is already set as a moderator role."
            )
            await ctx.send(embed=embed)
    
    @app_commands.command(name="addmod", description="Adds a moderator role to the server")
    @app_commands.describe(role="The role to add as a moderator")
    @app_commands.guild_only()
    async def addmod_slash(self, interaction, role: discord.Role):
        """Slash command version of addmod"""
        ctx = await self.bot.get_context(interaction)
        if await PermissionChecker.is_admin(ctx):
            await self.addmod_command(ctx, role=role)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need Administrator permissions to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Addrole command
    @commands.command(name="addrole", aliases=["createrole"])
    @commands.guild_only()
    @PermissionChecker.admin_or_permissions(manage_roles=True)
    @PermissionChecker.bot_has_permissions(manage_roles=True)
    async def addrole_command(self, ctx, name: str, color: discord.Color = None, hoist: bool = False):
        """Creates a new role with the specified name, color, and visibility"""
        try:
            role = await ctx.guild.create_role(
                name=name,
                color=color or discord.Color.default(),
                hoist=hoist,
                reason=f"Created by {ctx.author}"
            )
            
            embed = EmbedGenerator.success(
                "Role Created",
                f"Successfully created role {role.mention}",
                fields=[
                    {"name": "Name", "value": role.name, "inline": True},
                    {"name": "Color", "value": str(role.color), "inline": True},
                    {"name": "Hoisted", "value": "Yes" if role.hoist else "No", "inline": True}
                ]
            )
            await ctx.send(embed=embed)
        except discord.HTTPException as e:
            embed = EmbedGenerator.error(
                "Failed to Create Role",
                f"Error: {str(e)}"
            )
            await ctx.send(embed=embed)
    
    @app_commands.command(name="addrole", description="Creates a new role")
    @app_commands.describe(
        name="The name of the role",
        color="The color for the role (hex format like #FF5733)",
        hoist="Whether the role should be displayed separately in the member list"
    )
    @app_commands.guild_only()
    async def addrole_slash(self, interaction, name: str, color: str = None, hoist: bool = False):
        """Slash command version of addrole"""
        ctx = await self.bot.get_context(interaction)
        if ctx.author.guild_permissions.manage_roles:
            # Convert hex color to discord.Color
            discord_color = None
            if color:
                try:
                    color = color.lstrip('#')
                    discord_color = discord.Color(int(color, 16))
                except ValueError:
                    embed = EmbedGenerator.error(
                        "Invalid Color Format",
                        "Please provide a valid hex color (e.g., #FF5733)"
                    )
                    return await interaction.response.send_message(embed=embed, ephemeral=True)
            
            await self.addrole_command(ctx, name, discord_color, hoist)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need the 'Manage Roles' permission to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Announce command
    @commands.command(name="announce")
    @commands.guild_only()
    @PermissionChecker.admin_or_permissions(manage_messages=True)
    @PermissionChecker.bot_has_permissions(send_messages=True)
    async def announce_command(self, ctx, channel: discord.TextChannel, *, message):
        """Sends an announcement message to the specified channel"""
        # Check if bot can send messages in the target channel
        if not channel.permissions_for(ctx.guild.me).send_messages:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                f"I don't have permission to send messages in {channel.mention}."
            )
            return await ctx.send(embed=embed)
        
        # Create the announcement embed
        embed = discord.Embed(
            title="Announcement",
            description=message,
            color=EmbedGenerator.get_color("main"),
            timestamp=datetime.datetime.utcnow()
        )
        
        embed.set_footer(text=f"Announced by {ctx.author}")
        
        # Send the announcement
        try:
            announcement = await channel.send(embed=embed)
            
            # Send confirmation
            confirm_embed = EmbedGenerator.success(
                "Announcement Sent",
                f"Announcement was successfully sent to {channel.mention}",
                fields=[
                    {"name": "Jump to Message", "value": f"[Click Here]({announcement.jump_url})"}
                ]
            )
            await ctx.send(embed=confirm_embed)
        except discord.HTTPException as e:
            error_embed = EmbedGenerator.error(
                "Failed to Send Announcement",
                f"Error: {str(e)}"
            )
            await ctx.send(embed=error_embed)
    
    @app_commands.command(name="announce", description="Sends an announcement message to a channel")
    @app_commands.describe(
        channel="The channel to send the announcement to",
        message="The announcement message to send"
    )
    @app_commands.guild_only()
    async def announce_slash(self, interaction, channel: discord.TextChannel, message: str):
        """Slash command version of announce"""
        ctx = await self.bot.get_context(interaction)
        if ctx.author.guild_permissions.manage_messages:
            await interaction.response.defer()
            await self.announce_command(ctx, channel, message=message)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need the 'Manage Messages' permission to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Clearwarn command
    @commands.command(name="clearwarn", aliases=["clearwarnings"])
    @commands.guild_only()
    @PermissionChecker.mod_or_permissions(manage_messages=True)
    async def clearwarn_command(self, ctx, user: discord.Member):
        """Clears all warnings for a user"""
        # Get user cases
        cases = await self.bot.db.get_user_cases(ctx.guild.id, user.id)
        
        # Filter warning cases
        warning_cases = [case for case in cases if case['action'] == 'warn']
        
        if not warning_cases:
            embed = EmbedGenerator.error(
                "No Warnings Found",
                f"{user.mention} has no warnings to clear."
            )
            return await ctx.send(embed=embed)
        
        # Set all warning cases as inactive
        for case in warning_cases:
            await self.bot.db.set_case_inactive(case['case_id'])
        
        # Send confirmation
        embed = EmbedGenerator.success(
            "Warnings Cleared",
            f"Successfully cleared {len(warning_cases)} warning(s) for {user.mention}.",
            footer=f"Cleared by {ctx.author}"
        )
        await ctx.send(embed=embed)
    
    @app_commands.command(name="clearwarn", description="Clears all warnings for a user")
    @app_commands.describe(user="The user to clear warnings for")
    @app_commands.guild_only()
    async def clearwarn_slash(self, interaction, user: discord.Member):
        """Slash command version of clearwarn"""
        ctx = await self.bot.get_context(interaction)
        if await PermissionChecker.is_mod(ctx, self.bot.db):
            await self.clearwarn_command(ctx, user)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need to be a moderator to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Command command
    @commands.command(name="command")
    @commands.guild_only()
    @PermissionChecker.admin_or_permissions(administrator=True)
    async def command_command(self, ctx, command_name: str = None):
        """Manages custom commands (view, create, edit, delete)"""
        if not command_name:
            # List all custom commands
            custom_commands = await self.bot.db.get_all_custom_commands(ctx.guild.id)
            
            if not custom_commands:
                embed = EmbedGenerator.info(
                    "Custom Commands",
                    "No custom commands have been created for this server.\n"
                    f"Use `{ctx.prefix}command add [name] [response]` to create one."
                )
                return await ctx.send(embed=embed)
            
            cmd_list = "\n".join([f"• **{cmd['name']}**" for cmd in custom_commands])
            
            embed = EmbedGenerator.info(
                "Custom Commands",
                f"This server has {len(custom_commands)} custom command(s).\n\n{cmd_list}\n\n"
                f"Use `{ctx.prefix}command [name]` to view a specific command."
            )
            return await ctx.send(embed=embed)
        
        # Check for subcommands
        args = command_name.split()
        if args[0] in ["add", "create", "new"]:
            if len(args) < 3:
                embed = EmbedGenerator.error(
                    "Invalid Usage",
                    f"Usage: `{ctx.prefix}command add [name] [response]`"
                )
                return await ctx.send(embed=embed)
            
            name = args[1].lower()
            response = " ".join(args[2:])
            
            # Check if command already exists
            existing_cmd = await self.bot.db.get_custom_command(ctx.guild.id, name)
            if existing_cmd:
                embed = EmbedGenerator.error(
                    "Command Already Exists",
                    f"A command with the name `{name}` already exists.\n"
                    f"Use `{ctx.prefix}command edit {name} [new response]` to edit it."
                )
                return await ctx.send(embed=embed)
            
            # Create the command
            await self.bot.db.add_custom_command(ctx.guild.id, name, response, ctx.author.id)
            
            embed = EmbedGenerator.success(
                "Command Created",
                f"Created custom command `{name}`.\n\n"
                f"You can use it with `{ctx.prefix}{name}`."
            )
            return await ctx.send(embed=embed)
        
        elif args[0] in ["edit", "update"]:
            if len(args) < 3:
                embed = EmbedGenerator.error(
                    "Invalid Usage",
                    f"Usage: `{ctx.prefix}command edit [name] [new response]`"
                )
                return await ctx.send(embed=embed)
            
            name = args[1].lower()
            response = " ".join(args[2:])
            
            # Check if command exists
            existing_cmd = await self.bot.db.get_custom_command(ctx.guild.id, name)
            if not existing_cmd:
                embed = EmbedGenerator.error(
                    "Command Not Found",
                    f"No command with the name `{name}` exists.\n"
                    f"Use `{ctx.prefix}command add {name} [response]` to create it."
                )
                return await ctx.send(embed=embed)
            
            # Update the command
            await self.bot.db.add_custom_command(ctx.guild.id, name, response, ctx.author.id)
            
            embed = EmbedGenerator.success(
                "Command Updated",
                f"Updated custom command `{name}`."
            )
            return await ctx.send(embed=embed)
        
        elif args[0] in ["delete", "remove", "del", "rm"]:
            if len(args) < 2:
                embed = EmbedGenerator.error(
                    "Invalid Usage",
                    f"Usage: `{ctx.prefix}command delete [name]`"
                )
                return await ctx.send(embed=embed)
            
            name = args[1].lower()
            
            # Check if command exists
            existing_cmd = await self.bot.db.get_custom_command(ctx.guild.id, name)
            if not existing_cmd:
                embed = EmbedGenerator.error(
                    "Command Not Found",
                    f"No command with the name `{name}` exists."
                )
                return await ctx.send(embed=embed)
            
            # Delete the command
            await self.bot.db.remove_custom_command(ctx.guild.id, name)
            
            embed = EmbedGenerator.success(
                "Command Deleted",
                f"Deleted custom command `{name}`."
            )
            return await ctx.send(embed=embed)
        
        # View a specific command
        command_info = await self.bot.db.get_custom_command(ctx.guild.id, command_name)
        
        if not command_info:
            embed = EmbedGenerator.error(
                "Command Not Found",
                f"No custom command with the name `{command_name}` was found.\n\n"
                f"Use `{ctx.prefix}command` to see all custom commands, or\n"
                f"`{ctx.prefix}command add {command_name} [response]` to create it."
            )
            return await ctx.send(embed=embed)
        
        # Format created time
        created_time = datetime.datetime.fromtimestamp(command_info['created_at'])
        created_time_str = created_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Get creator info
        creator = self.bot.get_user(command_info['creator_id'])
        creator_str = creator.mention if creator else f"Unknown User ({command_info['creator_id']})"
        
        embed = EmbedGenerator.info(
            f"Custom Command: {command_info['name']}",
            f"**Response:**\n{command_info['response']}",
            fields=[
                {"name": "Created By", "value": creator_str, "inline": True},
                {"name": "Created On", "value": created_time_str, "inline": True}
            ]
        )
        
        embed.set_footer(text=f"Use {ctx.prefix}{command_info['name']} to execute this command")
        
        await ctx.send(embed=embed)
    
    @app_commands.command(name="command", description="Manages custom commands")
    @app_commands.describe(
        action="The action to perform (view, add, edit, delete)",
        name="The name of the command",
        response="The response for the command"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="view", value="view"),
        app_commands.Choice(name="add", value="add"),
        app_commands.Choice(name="edit", value="edit"),
        app_commands.Choice(name="delete", value="delete"),
        app_commands.Choice(name="list", value="list")
    ])
    @app_commands.guild_only()
    async def command_slash(self, interaction, action: str, name: str = None, response: str = None):
        """Slash command version of command"""
        ctx = await self.bot.get_context(interaction)
        
        if not await PermissionChecker.is_admin(ctx):
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need Administrator permissions to manage custom commands."
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        await interaction.response.defer()
        
        if action == "list" or (action == "view" and not name):
            # List all commands
            await self.command_command(ctx)
        elif action == "view" and name:
            # View a specific command
            await self.command_command(ctx, name)
        elif action == "add":
            if not name or not response:
                embed = EmbedGenerator.error(
                    "Missing Parameters",
                    "You need to provide both a name and a response to add a command."
                )
                return await interaction.followup.send(embed=embed)
            
            await self.command_command(ctx, f"add {name} {response}")
        elif action == "edit":
            if not name or not response:
                embed = EmbedGenerator.error(
                    "Missing Parameters",
                    "You need to provide both a name and a response to edit a command."
                )
                return await interaction.followup.send(embed=embed)
            
            await self.command_command(ctx, f"edit {name} {response}")
        elif action == "delete":
            if not name:
                embed = EmbedGenerator.error(
                    "Missing Parameters",
                    "You need to provide a name to delete a command."
                )
                return await interaction.followup.send(embed=embed)
            
            await self.command_command(ctx, f"delete {name}")
    
    # Customs command
    @commands.command(name="customs", aliases=["customcommands"])
    @commands.guild_only()
    async def customs_command(self, ctx):
        """Lists all custom commands for the server"""
        custom_commands = await self.bot.db.get_all_custom_commands(ctx.guild.id)
        
        if not custom_commands:
            embed = EmbedGenerator.info(
                "Custom Commands",
                "No custom commands have been created for this server.\n\n"
                f"Administrators can create custom commands with `{ctx.prefix}command add [name] [response]`."
            )
            return await ctx.send(embed=embed)
        
        # Group commands in chunks of 15 to avoid hitting character limits
        commands_chunks = [custom_commands[i:i + 15] for i in range(0, len(custom_commands), 15)]
        
        for i, chunk in enumerate(commands_chunks):
            chunk_list = "\n".join([f"• **{cmd['name']}**" for cmd in chunk])
            
            if i == 0:
                embed = EmbedGenerator.info(
                    "Custom Commands",
                    f"This server has {len(custom_commands)} custom command(s):\n\n{chunk_list}"
                )
                
                if len(commands_chunks) > 1:
                    embed.set_footer(text=f"Page 1/{len(commands_chunks)}")
                
                await ctx.send(embed=embed)
            else:
                embed = EmbedGenerator.info(
                    f"Custom Commands (Page {i+1}/{len(commands_chunks)})",
                    chunk_list
                )
                await ctx.send(embed=embed)
    
    @app_commands.command(name="customs", description="Lists all custom commands for the server")
    @app_commands.guild_only()
    async def customs_slash(self, interaction):
        """Slash command version of customs"""
        ctx = await self.bot.get_context(interaction)
        await self.customs_command(ctx)
    
    # Delmod command
    @commands.command(name="delmod", aliases=["removemodrole", "removemoderator"])
    @commands.guild_only()
    @PermissionChecker.admin_or_permissions(administrator=True)
    async def delmod_command(self, ctx, *, role: discord.Role):
        """Removes a moderator role from the server"""
        success = await self.bot.db.remove_mod_role(ctx.guild.id, role.id)
        
        if success:
            embed = EmbedGenerator.success(
                "Moderator Role Removed",
                f"Removed {role.mention} as a moderator role."
            )
            await ctx.send(embed=embed)
        else:
            embed = EmbedGenerator.error(
                "Role Not a Moderator",
                f"{role.mention} is not set as a moderator role."
            )
            await ctx.send(embed=embed)
    
    @app_commands.command(name="delmod", description="Removes a moderator role from the server")
    @app_commands.describe(role="The role to remove as a moderator")
    @app_commands.guild_only()
    async def delmod_slash(self, interaction, role: discord.Role):
        """Slash command version of delmod"""
        ctx = await self.bot.get_context(interaction)
        if await PermissionChecker.is_admin(ctx):
            await self.delmod_command(ctx, role=role)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need Administrator permissions to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Delrole command
    @commands.command(name="delrole", aliases=["removerole", "deleterole"])
    @commands.guild_only()
    @PermissionChecker.admin_or_permissions(manage_roles=True)
    @PermissionChecker.bot_has_permissions(manage_roles=True)
    async def delrole_command(self, ctx, *, role: discord.Role):
        """Deletes a role from the server"""
        # Check if the role is higher than the bot's highest role
        if ctx.guild.me.top_role <= role:
            embed = EmbedGenerator.error(
                "Role Hierarchy Error",
                "I cannot delete a role that is higher than or equal to my highest role."
            )
            return await ctx.send(embed=embed)
        
        # Check if the role is higher than the user's highest role
        if ctx.author.id != ctx.guild.owner_id and ctx.author.top_role <= role:
            embed = EmbedGenerator.error(
                "Role Hierarchy Error",
                "You cannot delete a role that is higher than or equal to your highest role."
            )
            return await ctx.send(embed=embed)
        
        role_name = role.name
        
        try:
            await role.delete(reason=f"Deleted by {ctx.author}")
            
            embed = EmbedGenerator.success(
                "Role Deleted",
                f"Successfully deleted role **{role_name}**."
            )
            await ctx.send(embed=embed)
        except discord.HTTPException as e:
            embed = EmbedGenerator.error(
                "Failed to Delete Role",
                f"Error: {str(e)}"
            )
            await ctx.send(embed=embed)
    
    @app_commands.command(name="delrole", description="Deletes a role from the server")
    @app_commands.describe(role="The role to delete")
    @app_commands.guild_only()
    async def delrole_slash(self, interaction, role: discord.Role):
        """Slash command version of delrole"""
        ctx = await self.bot.get_context(interaction)
        if ctx.author.guild_permissions.manage_roles:
            await self.delrole_command(ctx, role=role)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need the 'Manage Roles' permission to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Giveaway command
    @commands.command(name="giveaway")
    @commands.guild_only()
    @PermissionChecker.admin_or_permissions(manage_guild=True)
    @PermissionChecker.bot_has_permissions(embed_links=True, add_reactions=True)
    async def giveaway_command(self, ctx):
        """Creates a giveaway (interactive setup)"""
        # Initial message
        embed = EmbedGenerator.info(
            "Giveaway Setup",
            "Let's set up a giveaway! Answer the following questions.\n"
            "Type `cancel` at any time to cancel the setup."
        )
        await ctx.send(embed=embed)
        
        # Check function for responses
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        
        # Ask for the channel
        channel_embed = EmbedGenerator.info(
            "Giveaway Channel",
            "In which channel should the giveaway be posted? Mention the channel or enter its ID."
        )
        await ctx.send(embed=channel_embed)
        
        try:
            channel_msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            
            if channel_msg.content.lower() == 'cancel':
                return await ctx.send("Giveaway setup cancelled.")
            
            # Parse channel from mention or ID
            channel = None
            if channel_msg.channel_mentions:
                channel = channel_msg.channel_mentions[0]
            else:
                try:
                    channel_id = int(channel_msg.content.strip())
                    channel = ctx.guild.get_channel(channel_id)
                except ValueError:
                    pass
            
            if not channel or not isinstance(channel, discord.TextChannel):
                return await ctx.send("Invalid channel. Giveaway setup cancelled.")
            
            # Check if bot can send messages in the channel
            if not channel.permissions_for(ctx.guild.me).send_messages:
                return await ctx.send(f"I don't have permission to send messages in {channel.mention}. Giveaway setup cancelled.")
            
            # Ask for the prize
            prize_embed = EmbedGenerator.info(
                "Giveaway Prize",
                "What is the prize for this giveaway?"
            )
            await ctx.send(embed=prize_embed)
            
            prize_msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            
            if prize_msg.content.lower() == 'cancel':
                return await ctx.send("Giveaway setup cancelled.")
            
            prize = prize_msg.content.strip()
            
            # Ask for the duration
            duration_embed = EmbedGenerator.info(
                "Giveaway Duration",
                "How long should the giveaway last? Examples: `10m`, `2h`, `1d`\n\n"
                "**Valid units:** `s` (seconds), `m` (minutes), `h` (hours), `d` (days)"
            )
            await ctx.send(embed=duration_embed)
            
            duration_msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            
            if duration_msg.content.lower() == 'cancel':
                return await ctx.send("Giveaway setup cancelled.")
            
            # Parse duration
            duration_str = duration_msg.content.lower().strip()
            duration_seconds = 0
            
            if duration_str.endswith('s'):
                try:
                    duration_seconds = int(duration_str[:-1])
                except ValueError:
                    return await ctx.send("Invalid duration format. Giveaway setup cancelled.")
            elif duration_str.endswith('m'):
                try:
                    duration_seconds = int(duration_str[:-1]) * 60
                except ValueError:
                    return await ctx.send("Invalid duration format. Giveaway setup cancelled.")
            elif duration_str.endswith('h'):
                try:
                    duration_seconds = int(duration_str[:-1]) * 3600
                except ValueError:
                    return await ctx.send("Invalid duration format. Giveaway setup cancelled.")
            elif duration_str.endswith('d'):
                try:
                    duration_seconds = int(duration_str[:-1]) * 86400
                except ValueError:
                    return await ctx.send("Invalid duration format. Giveaway setup cancelled.")
            else:
                return await ctx.send("Invalid duration format. Giveaway setup cancelled.")
            
            if duration_seconds < 10:
                return await ctx.send("Duration must be at least 10 seconds. Giveaway setup cancelled.")
            
            # Ask for the number of winners
            winners_embed = EmbedGenerator.info(
                "Number of Winners",
                "How many winners should be selected? Enter a number between 1 and 20."
            )
            await ctx.send(embed=winners_embed)
            
            winners_msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            
            if winners_msg.content.lower() == 'cancel':
                return await ctx.send("Giveaway setup cancelled.")
            
            try:
                winners_count = int(winners_msg.content.strip())
                if winners_count < 1 or winners_count > 20:
                    return await ctx.send("Number of winners must be between 1 and 20. Giveaway setup cancelled.")
            except ValueError:
                return await ctx.send("Invalid number. Giveaway setup cancelled.")
            
            # Calculate end time
            end_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=duration_seconds)
            end_timestamp = int(end_time.timestamp())
            
            # Create giveaway embed
            giveaway_embed = discord.Embed(
                title="🎉 GIVEAWAY 🎉",
                description=f"**Prize:** {prize}\n\n"
                            f"React with 🎉 to enter!\n\n"
                            f"**Winners:** {winners_count}\n"
                            f"**Ends:** <t:{end_timestamp}:R> (<t:{end_timestamp}:F>)",
                color=0x5865F2,
                timestamp=datetime.datetime.utcnow()
            )
            
            giveaway_embed.set_footer(text=f"Hosted by {ctx.author}", icon_url=ctx.author.display_avatar.url)
            
            # Send the giveaway message
            giveaway_message = await channel.send(embed=giveaway_embed)
            
            # Add the reaction
            await giveaway_message.add_reaction("🎉")
            
            # Store the giveaway in the database
            # We would typically store this in the database for tracking
            # This is a simplified version
            
            # Send confirmation
            confirm_embed = EmbedGenerator.success(
                "Giveaway Created",
                f"Giveaway for **{prize}** has been created in {channel.mention}!\n\n"
                f"[Jump to Giveaway]({giveaway_message.jump_url})",
                fields=[
                    {"name": "End Time", "value": f"<t:{end_timestamp}:F>", "inline": True},
                    {"name": "Winners", "value": str(winners_count), "inline": True}
                ]
            )
            await ctx.send(embed=confirm_embed)
            
            # Wait for the giveaway to end
            await asyncio.sleep(duration_seconds)
            
            # Fetch the message to get updated reactions
            try:
                message = await channel.fetch_message(giveaway_message.id)
                
                # Get all users who reacted (excluding the bot)
                reaction = [r for r in message.reactions if str(r.emoji) == "🎉"][0]
                users = await reaction.users().flatten()
                users = [user for user in users if not user.bot]
                
                # Create the winners message
                if users:
                    # Randomly select winners
                    import random
                    winners = random.sample(users, min(winners_count, len(users)))
                    
                    winners_text = ", ".join([winner.mention for winner in winners])
                    
                    # Update giveaway embed
                    ended_embed = discord.Embed(
                        title="🎉 GIVEAWAY ENDED 🎉",
                        description=f"**Prize:** {prize}\n\n"
                                    f"**Winners:** {winners_text}\n\n"
                                    f"**Ended:** <t:{end_timestamp}:R> (<t:{end_timestamp}:F>)",
                        color=0x5865F2,
                        timestamp=datetime.datetime.utcnow()
                    )
                    
                    ended_embed.set_footer(text=f"Hosted by {ctx.author}", icon_url=ctx.author.display_avatar.url)
                    
                    await message.edit(embed=ended_embed)
                    
                    # Send winner announcement
                    await channel.send(
                        f"🎉 Congratulations {winners_text}! You won **{prize}**!\n"
                        f"[Jump to Giveaway]({message.jump_url})"
                    )
                else:
                    # No valid entries
                    no_entries_embed = discord.Embed(
                        title="🎉 GIVEAWAY ENDED 🎉",
                        description=f"**Prize:** {prize}\n\n"
                                    f"**Winners:** No valid entries\n\n"
                                    f"**Ended:** <t:{end_timestamp}:R> (<t:{end_timestamp}:F>)",
                        color=0x5865F2,
                        timestamp=datetime.datetime.utcnow()
                    )
                    
                    no_entries_embed.set_footer(text=f"Hosted by {ctx.author}", icon_url=ctx.author.display_avatar.url)
                    
                    await message.edit(embed=no_entries_embed)
                    await channel.send("No valid entries for this giveaway.")
            except discord.NotFound:
                # Message was deleted, can't end the giveaway
                pass
            except Exception as e:
                print(f"Error ending giveaway: {e}")
        
        except asyncio.TimeoutError:
            await ctx.send("Giveaway setup timed out.")
    
    @app_commands.command(name="giveaway", description="Creates a giveaway")
    @app_commands.guild_only()
    async def giveaway_slash(self, interaction):
        """Slash command version of giveaway"""
        ctx = await self.bot.get_context(interaction)
        
        if ctx.author.guild_permissions.manage_guild:
            await interaction.response.send_message("Starting giveaway setup...", ephemeral=True)
            await self.giveaway_command(ctx)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need the 'Manage Server' permission to create giveaways."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Ignorechannel command
    @commands.command(name="ignorechannel")
    @commands.guild_only()
    @PermissionChecker.admin_or_permissions(administrator=True)
    async def ignorechannel_command(self, ctx, channel: discord.TextChannel):
        """Toggles whether the bot ignores a channel"""
        # Check if channel is already ignored
        ignored_channels = await self.bot.db.get_ignored_channels(ctx.guild.id)
        
        if channel.id in ignored_channels:
            # Remove from ignored channels
            success = await self.bot.db.remove_ignored_channel(ctx.guild.id, channel.id)
            
            if success:
                embed = EmbedGenerator.success(
                    "Channel Unignored",
                    f"{channel.mention} will no longer be ignored by the bot."
                )
                await ctx.send(embed=embed)
            else:
                embed = EmbedGenerator.error(
                    "Error",
                    "An error occurred while trying to update the ignored channels list."
                )
                await ctx.send(embed=embed)
        else:
            # Add to ignored channels
            success = await self.bot.db.add_ignored_channel(ctx.guild.id, channel.id)
            
            if success:
                embed = EmbedGenerator.success(
                    "Channel Ignored",
                    f"{channel.mention} will now be ignored by the bot."
                )
                await ctx.send(embed=embed)
            else:
                embed = EmbedGenerator.error(
                    "Error",
                    "An error occurred while trying to update the ignored channels list."
                )
                await ctx.send(embed=embed)
    
    @app_commands.command(name="ignorechannel", description="Toggles whether the bot ignores a channel")
    @app_commands.describe(channel="The channel to ignore or unignore")
    @app_commands.guild_only()
    async def ignorechannel_slash(self, interaction, channel: discord.TextChannel):
        """Slash command version of ignorechannel"""
        ctx = await self.bot.get_context(interaction)
        
        if await PermissionChecker.is_admin(ctx):
            await self.ignorechannel_command(ctx, channel)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need Administrator permissions to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Ignorerole command
    @commands.command(name="ignorerole")
    @commands.guild_only()
    @PermissionChecker.admin_or_permissions(administrator=True)
    async def ignorerole_command(self, ctx, role: discord.Role):
        """Toggles whether the bot ignores a role"""
        # Check if role is already ignored
        ignored_roles = await self.bot.db.get_ignored_roles(ctx.guild.id)
        
        if role.id in ignored_roles:
            # Remove from ignored roles
            success = await self.bot.db.remove_ignored_role(ctx.guild.id, role.id)
            
            if success:
                embed = EmbedGenerator.success(
                    "Role Unignored",
                    f"{role.mention} will no longer be ignored by the bot."
                )
                await ctx.send(embed=embed)
            else:
                embed = EmbedGenerator.error(
                    "Error",
                    "An error occurred while trying to update the ignored roles list."
                )
                await ctx.send(embed=embed)
        else:
            # Add to ignored roles
            success = await self.bot.db.add_ignored_role(ctx.guild.id, role.id)
            
            if success:
                embed = EmbedGenerator.success(
                    "Role Ignored",
                    f"{role.mention} will now be ignored by the bot."
                )
                await ctx.send(embed=embed)
            else:
                embed = EmbedGenerator.error(
                    "Error",
                    "An error occurred while trying to update the ignored roles list."
                )
                await ctx.send(embed=embed)
    
    @app_commands.command(name="ignorerole", description="Toggles whether the bot ignores a role")
    @app_commands.describe(role="The role to ignore or unignore")
    @app_commands.guild_only()
    async def ignorerole_slash(self, interaction, role: discord.Role):
        """Slash command version of ignorerole"""
        ctx = await self.bot.get_context(interaction)
        
        if await PermissionChecker.is_admin(ctx):
            await self.ignorerole_command(ctx, role)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need Administrator permissions to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Ignoreuser command
    @commands.command(name="ignoreuser")
    @commands.guild_only()
    @PermissionChecker.admin_or_permissions(administrator=True)
    async def ignoreuser_command(self, ctx, user: discord.Member, *, reason=None):
        """Toggles whether the bot ignores a user"""
        # Check if user is already ignored
        ignored_users = await self.bot.db.get_ignored_users(ctx.guild.id)
        is_ignored = any(ignored_user["id"] == user.id for ignored_user in ignored_users)
        
        if is_ignored:
            # Remove from ignored users
            success = await self.bot.db.remove_ignored_user(ctx.guild.id, user.id)
            
            if success:
                embed = EmbedGenerator.success(
                    "User Unignored",
                    f"{user.mention} will no longer be ignored by the bot."
                )
                await ctx.send(embed=embed)
            else:
                embed = EmbedGenerator.error(
                    "Error",
                    "An error occurred while trying to update the ignored users list."
                )
                await ctx.send(embed=embed)
        else:
            # Add to ignored users
            success = await self.bot.db.add_ignored_user(ctx.guild.id, user.id, reason)
            
            if success:
                embed = EmbedGenerator.success(
                    "User Ignored",
                    f"{user.mention} will now be ignored by the bot."
                )
                if reason:
                    embed.add_field(name="Reason", value=reason)
                await ctx.send(embed=embed)
            else:
                embed = EmbedGenerator.error(
                    "Error",
                    "An error occurred while trying to update the ignored users list."
                )
                await ctx.send(embed=embed)
    
    @app_commands.command(name="ignoreuser", description="Toggles whether the bot ignores a user")
    @app_commands.describe(
        user="The user to ignore or unignore",
        reason="The reason for ignoring the user"
    )
    @app_commands.guild_only()
    async def ignoreuser_slash(self, interaction, user: discord.Member, reason: str = None):
        """Slash command version of ignoreuser"""
        ctx = await self.bot.get_context(interaction)
        
        if await PermissionChecker.is_admin(ctx):
            await self.ignoreuser_command(ctx, user, reason=reason)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need Administrator permissions to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Listmods command
    @commands.command(name="listmods", aliases=["moderators", "modroles"])
    @commands.guild_only()
    async def listmods_command(self, ctx):
        """Lists all moderator roles in the server"""
        mod_role_ids = await self.bot.db.get_mod_roles(ctx.guild.id)
        
        if not mod_role_ids:
            embed = EmbedGenerator.info(
                "Moderator Roles",
                "No moderator roles have been set up for this server.\n\n"
                f"Administrators can add moderator roles with `{ctx.prefix}addmod [role]`."
            )
            return await ctx.send(embed=embed)
        
        # Get role objects
        mod_roles = []
        for role_id in mod_role_ids:
            role = ctx.guild.get_role(role_id)
            if role:
                mod_roles.append(role)
        
        if not mod_roles:
            embed = EmbedGenerator.warning(
                "Moderator Roles",
                "All configured moderator roles have been deleted from the server."
            )
            return await ctx.send(embed=embed)
        
        # Create list of roles
        role_list = "\n".join([f"• {role.mention} (ID: {role.id})" for role in mod_roles])
        
        embed = EmbedGenerator.info(
            "Moderator Roles",
            f"The following roles have moderator permissions:\n\n{role_list}"
        )
        
        await ctx.send(embed=embed)
    
    @app_commands.command(name="listmods", description="Lists all moderator roles in the server")
    @app_commands.guild_only()
    async def listmods_slash(self, interaction):
        """Slash command version of listmods"""
        ctx = await self.bot.get_context(interaction)
        await self.listmods_command(ctx)
    
    # Mentionable command
    @commands.command(name="mentionable")
    @commands.guild_only()
    @PermissionChecker.admin_or_permissions(manage_roles=True)
    @PermissionChecker.bot_has_permissions(manage_roles=True)
    async def mentionable_command(self, ctx, *, role: discord.Role):
        """Toggles whether a role is mentionable"""
        # Check if the role is higher than the bot's highest role
        if ctx.guild.me.top_role <= role:
            embed = EmbedGenerator.error(
                "Role Hierarchy Error",
                "I cannot modify a role that is higher than or equal to my highest role."
            )
            return await ctx.send(embed=embed)
        
        # Check if the role is higher than the user's highest role
        if ctx.author.id != ctx.guild.owner_id and ctx.author.top_role <= role:
            embed = EmbedGenerator.error(
                "Role Hierarchy Error",
                "You cannot modify a role that is higher than or equal to your highest role."
            )
            return await ctx.send(embed=embed)
        
        try:
            await role.edit(mentionable=not role.mentionable, reason=f"Toggled by {ctx.author}")
            
            status = "now" if role.mentionable else "no longer"
            embed = EmbedGenerator.success(
                "Role Updated",
                f"{role.mention} is {status} mentionable."
            )
            await ctx.send(embed=embed)
        except discord.HTTPException as e:
            embed = EmbedGenerator.error(
                "Failed to Update Role",
                f"Error: {str(e)}"
            )
            await ctx.send(embed=embed)
    
    @app_commands.command(name="mentionable", description="Toggles whether a role is mentionable")
    @app_commands.describe(role="The role to toggle mentionable status")
    @app_commands.guild_only()
    async def mentionable_slash(self, interaction, role: discord.Role):
        """Slash command version of mentionable"""
        ctx = await self.bot.get_context(interaction)
        
        if ctx.author.guild_permissions.manage_roles:
            await self.mentionable_command(ctx, role=role)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need the 'Manage Roles' permission to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Module command
    @commands.command(name="module")
    @commands.guild_only()
    @PermissionChecker.admin_or_permissions(administrator=True)
    async def module_command(self, ctx, module: str):
        """Toggles a module on or off"""
        valid_modules = ["moderation", "utility", "fun"]
        
        if module.lower() not in valid_modules:
            embed = EmbedGenerator.error(
                "Invalid Module",
                f"Module must be one of: {', '.join(valid_modules)}"
            )
            return await ctx.send(embed=embed)
        
        success = await self.bot.db.toggle_module(ctx.guild.id, module.lower())
        
        if success:
            modules = await self.bot.db.get_modules(ctx.guild.id)
            status = "enabled" if modules[module.lower()] else "disabled"
            
            embed = EmbedGenerator.success(
                "Module Updated",
                f"The **{module.capitalize()}** module is now **{status}**."
            )
            await ctx.send(embed=embed)
        else:
            embed = EmbedGenerator.error(
                "Error",
                "An error occurred while trying to update the module status."
            )
            await ctx.send(embed=embed)
    
    @app_commands.command(name="module", description="Toggles a module on or off")
    @app_commands.describe(module="The module to toggle")
    @app_commands.choices(module=[
        app_commands.Choice(name="Moderation", value="moderation"),
        app_commands.Choice(name="Utility", value="utility"),
        app_commands.Choice(name="Fun", value="fun")
    ])
    @app_commands.guild_only()
    async def module_slash(self, interaction, module: str):
        """Slash command version of module"""
        ctx = await self.bot.get_context(interaction)
        
        if await PermissionChecker.is_admin(ctx):
            await self.module_command(ctx, module)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need Administrator permissions to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Modules command
    @commands.command(name="modules")
    @commands.guild_only()
    async def modules_command(self, ctx):
        """Lists all modules and their status"""
        modules = await self.bot.db.get_modules(ctx.guild.id)
        
        # Create list of modules and their status
        module_list = ""
        for module, enabled in modules.items():
            status = "✅ Enabled" if enabled else "❌ Disabled"
            module_list += f"• **{module.capitalize()}**: {status}\n"
        
        embed = EmbedGenerator.info(
            "Bot Modules",
            f"Here are all available modules and their status:\n\n{module_list}\n\n"
            f"Administrators can toggle modules with `{ctx.prefix}module [module]`."
        )
        
        await ctx.send(embed=embed)
    
    @app_commands.command(name="modules", description="Lists all modules and their status")
    @app_commands.guild_only()
    async def modules_slash(self, interaction):
        """Slash command version of modules"""
        ctx = await self.bot.get_context(interaction)
        await self.modules_command(ctx)
    
    # Nick command
    @commands.command(name="nick", aliases=["nickname"])
    @commands.guild_only()
    @PermissionChecker.bot_has_permissions(manage_nicknames=True)
    async def nick_command(self, ctx, *, new_nickname=None):
        """Changes your nickname or clears it if no nickname is provided"""
        try:
            old_nick = ctx.author.nick or ctx.author.name
            await ctx.author.edit(nick=new_nickname)
            
            if new_nickname:
                embed = EmbedGenerator.success(
                    "Nickname Changed",
                    f"Your nickname has been changed from **{old_nick}** to **{new_nickname}**."
                )
            else:
                embed = EmbedGenerator.success(
                    "Nickname Cleared",
                    f"Your nickname has been reset to your username (**{ctx.author.name}**)."
                )
            
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = EmbedGenerator.error(
                "Permission Error",
                "I don't have permission to change your nickname. This might be because you are the server owner or have a higher role than me."
            )
            await ctx.send(embed=embed)
        except discord.HTTPException as e:
            embed = EmbedGenerator.error(
                "Error Changing Nickname",
                f"An error occurred: {str(e)}"
            )
            await ctx.send(embed=embed)
    
    @app_commands.command(name="nick", description="Changes your nickname or clears it")
    @app_commands.describe(new_nickname="Your new nickname (leave empty to reset)")
    @app_commands.guild_only()
    async def nick_slash(self, interaction, new_nickname: str = None):
        """Slash command version of nick"""
        ctx = await self.bot.get_context(interaction)
        await self.nick_command(ctx, new_nickname=new_nickname)
    
    # Prefix command
    @commands.command(name="prefix")
    @commands.guild_only()
    @PermissionChecker.admin_or_permissions(administrator=True)
    async def prefix_command(self, ctx, new_prefix=None):
        """Views or changes the server's command prefix"""
        if new_prefix is None:
            # Show current prefix
            current_prefix = await self.bot.db.get_guild_prefix(ctx.guild.id) or self.bot.config.DEFAULT_PREFIX
            
            embed = EmbedGenerator.info(
                "Command Prefix",
                f"The current command prefix is `{current_prefix}`\n\n"
                f"To change it, use `{current_prefix}prefix [new prefix]`"
            )
            return await ctx.send(embed=embed)
        
        # Validate prefix
        if len(new_prefix) > 10:
            embed = EmbedGenerator.error(
                "Invalid Prefix",
                "The prefix cannot be longer than 10 characters."
            )
            return await ctx.send(embed=embed)
        
        # Update prefix
        await self.bot.db.set_guild_prefix(ctx.guild.id, new_prefix)
        
        embed = EmbedGenerator.success(
            "Prefix Changed",
            f"The command prefix has been changed to `{new_prefix}`\n\n"
            f"You can now use commands like `{new_prefix}help`"
        )
        await ctx.send(embed=embed)
    
    @app_commands.command(name="prefix", description="Views or changes the server's command prefix")
    @app_commands.describe(new_prefix="The new prefix for commands (leave empty to view current)")
    @app_commands.guild_only()
    async def prefix_slash(self, interaction, new_prefix: str = None):
        """Slash command version of prefix"""
        ctx = await self.bot.get_context(interaction)
        
        if new_prefix is None:
            # Anyone can view the prefix
            await self.prefix_command(ctx)
        elif await PermissionChecker.is_admin(ctx):
            # Only admins can change the prefix
            await self.prefix_command(ctx, new_prefix)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need Administrator permissions to change the prefix."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Helper methods
    def format_uptime(self, uptime):
        """Format a timedelta into a readable string"""
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if days:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if seconds or not parts:
            parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
        
        return ", ".join(parts)
    
    # Process custom commands
    @commands.Cog.listener()
    async def on_message(self, message):
        """Process custom commands when they are used"""
        # Ignore messages from bots
        if message.author.bot or not message.guild:
            return
        
        # Get the prefix
        prefix = await self.bot.db.get_guild_prefix(message.guild.id) or self.bot.config.DEFAULT_PREFIX
        
        # Check if message starts with prefix
        if not message.content.startswith(prefix):
            return
        
        # Parse the command name
        command_name = message.content[len(prefix):].split()[0].lower()
        
        # Check if it's a custom command
        custom_command = await self.bot.db.get_custom_command(message.guild.id, command_name)
        
        if custom_command:
            # Send the custom command response
            await message.channel.send(custom_command['response'])

async def setup(bot):
    await bot.add_cog(Utility(bot))
