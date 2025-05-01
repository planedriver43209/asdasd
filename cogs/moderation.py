import discord
from discord import app_commands
from discord.ext import commands
import datetime
import asyncio
import re
from utils.embed_generator import EmbedGenerator
from utils.permissions import PermissionChecker

class Moderation(commands.Cog):
    """Moderation commands for server management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.duration_regex = re.compile(r"(\d+)([smhdw])")
        self.active_lockdowns = {}
    
    def parse_duration(self, duration_str):
        """Parse a duration string into seconds"""
        if not duration_str:
            return None
            
        matches = self.duration_regex.findall(duration_str.lower())
        if not matches:
            return None
            
        total_seconds = 0
        for amount, unit in matches:
            amount = int(amount)
            if unit == "s":
                total_seconds += amount
            elif unit == "m":
                total_seconds += amount * 60
            elif unit == "h":
                total_seconds += amount * 3600
            elif unit == "d":
                total_seconds += amount * 86400
            elif unit == "w":
                total_seconds += amount * 604800
                
        return total_seconds
    
    def format_duration(self, seconds):
        """Format seconds into a readable duration string"""
        if seconds is None:
            return "Permanent"
            
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        weeks, days = divmod(days, 7)
        
        parts = []
        if weeks:
            parts.append(f"{weeks}w")
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        if seconds:
            parts.append(f"{seconds}s")
            
        return " ".join(parts) if parts else "0s"
    
    async def get_user_by_id(self, guild, user_id):
        """Get a user object from ID, checking both members and bans"""
        # Check if it's a member
        member = guild.get_member(user_id)
        if member:
            return member
            
        # Check if it's a banned user
        try:
            ban_entry = await guild.fetch_ban(discord.Object(id=user_id))
            return ban_entry.user
        except discord.NotFound:
            pass
            
        # Try to get user from API
        try:
            return await self.bot.fetch_user(user_id)
        except discord.NotFound:
            return None
    
    # Ban command
    @commands.command(name="ban")
    @commands.guild_only()
    @PermissionChecker.mod_or_permissions(ban_members=True)
    @PermissionChecker.bot_has_permissions(ban_members=True)
    async def ban_command(self, ctx, user: discord.Member, limit: str = None, *, reason=None):
        """Bans a user from the server with an optional time limit"""
        # Check hierarchy
        if not await PermissionChecker.check_hierarchy(ctx, user):
            embed = EmbedGenerator.error(
                "Cannot Ban User",
                "You cannot ban this user due to role hierarchy. "
                "Make sure both your role and the bot's role are higher than the user's highest role."
            )
            return await ctx.send(embed=embed)
        
        # Parse duration if provided
        duration = None
        if limit:
            duration = self.parse_duration(limit)
            if duration is None:
                # If limit is provided but invalid, assume it's part of the reason
                if reason:
                    reason = f"{limit} {reason}"
                else:
                    reason = limit
                limit = None
        
        # Create the ban case
        case_id = await self.bot.db.create_mod_case(
            ctx.guild.id,
            user.id,
            ctx.author.id,
            "ban",
            reason,
            duration
        )
        
        # Get formatted duration for display
        duration_text = self.format_duration(duration) if duration else "Permanent"
        
        # Create ban embed for logging
        embed = EmbedGenerator.mod_case(
            {
                'case_id': case_id,
                'action': 'ban',
                'reason': reason,
                'timestamp': int(datetime.datetime.utcnow().timestamp()),
                'duration': duration
            },
            ctx.guild,
            ctx.author,
            user
        )
        
        # Try to DM the user
        try:
            dm_embed = discord.Embed(
                title=f"You have been banned from {ctx.guild.name}",
                color=EmbedGenerator.get_color("error"),
                timestamp=datetime.datetime.utcnow()
            )
            
            dm_embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
            dm_embed.add_field(name="Duration", value=duration_text, inline=False)
            dm_embed.add_field(name="Moderator", value=f"{ctx.author} ({ctx.author.id})", inline=False)
            
            await user.send(embed=dm_embed)
        except (discord.Forbidden, discord.HTTPException):
            # Cannot DM user, continue with ban
            pass
        
        # Execute the ban
        try:
            await ctx.guild.ban(user, reason=f"[Case #{case_id}] {reason or 'No reason provided'}")
            
            # Confirm the ban
            confirmation = EmbedGenerator.success(
                "User Banned",
                f"{user.mention} has been banned from the server.",
                fields=[
                    {"name": "User", "value": f"{user} ({user.id})", "inline": True},
                    {"name": "Duration", "value": duration_text, "inline": True},
                    {"name": "Case ID", "value": f"#{case_id}", "inline": True}
                ]
            )
            
            await ctx.send(embed=confirmation)
            
            # If temporary ban, schedule unban
            if duration:
                # Schedule removal
                async def unban_user():
                    await asyncio.sleep(duration)
                    try:
                        await ctx.guild.unban(user, reason=f"Temporary ban (Case #{case_id}) expired")
                        # Update case as inactive
                        await self.bot.db.set_case_inactive(case_id)
                    except discord.HTTPException:
                        # Failed to unban, probably already unbanned manually
                        pass
                
                # Start the unban task
                self.bot.loop.create_task(unban_user())
        
        except discord.HTTPException as e:
            error_embed = EmbedGenerator.error(
                "Error Banning User",
                f"An error occurred while banning {user.mention}: {str(e)}"
            )
            await ctx.send(embed=error_embed)
    
    @app_commands.command(name="ban", description="Bans a user from the server")
    @app_commands.describe(
        user="The user to ban",
        limit="Duration of the ban (e.g., 1d, 7d, 30d)",
        reason="Reason for the ban"
    )
    @app_commands.guild_only()
    async def ban_slash(self, interaction, user: discord.Member, limit: str = None, reason: str = None):
        """Slash command version of ban"""
        ctx = await self.bot.get_context(interaction)
        
        if ctx.author.guild_permissions.ban_members or await PermissionChecker.is_mod(ctx, self.bot.db):
            await interaction.response.defer()
            await self.ban_command(ctx, user, limit, reason=reason)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need the 'Ban Members' permission to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Case command
    @commands.command(name="case")
    @commands.guild_only()
    @PermissionChecker.mod_or_permissions(manage_messages=True)
    async def case_command(self, ctx, case_number: int):
        """Shows information about a specific moderation case"""
        # Get the case from the database
        case = await self.bot.db.get_case(case_number)
        
        if not case or case['guild_id'] != ctx.guild.id:
            embed = EmbedGenerator.error(
                "Case Not Found",
                f"No case with ID #{case_number} was found in this server."
            )
            return await ctx.send(embed=embed)
        
        # Get the user and moderator
        user = await self.get_user_by_id(ctx.guild, case['user_id'])
        moderator = await self.get_user_by_id(ctx.guild, case['moderator_id'])
        
        if not user:
            user_display = f"Unknown User ({case['user_id']})"
        else:
            user_display = f"{user} ({user.id})"
        
        if not moderator:
            mod_display = f"Unknown Moderator ({case['moderator_id']})"
        else:
            mod_display = f"{moderator} ({moderator.id})"
        
        # Format timestamps
        timestamp = datetime.datetime.fromtimestamp(case['timestamp'])
        formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Format duration if present
        duration_text = "Permanent"
        if case['duration']:
            duration_text = self.format_duration(case['duration'])
        
        # Create the case embed
        embed = discord.Embed(
            title=f"Case #{case['case_id']} | {case['action'].capitalize()}",
            color=EmbedGenerator.get_color("moderation"),
            timestamp=datetime.datetime.utcnow()
        )
        
        embed.add_field(name="User", value=user_display, inline=True)
        embed.add_field(name="Moderator", value=mod_display, inline=True)
        embed.add_field(name="Action", value=case['action'].capitalize(), inline=True)
        
        reason = case['reason'] if case['reason'] else "No reason provided"
        embed.add_field(name="Reason", value=reason, inline=False)
        
        if case['duration']:
            embed.add_field(name="Duration", value=duration_text, inline=True)
            
        embed.add_field(name="Status", value="Active" if case['active'] else "Inactive", inline=True)
        embed.add_field(name="Date", value=formatted_time, inline=True)
        
        await ctx.send(embed=embed)
    
    @app_commands.command(name="case", description="Shows information about a specific moderation case")
    @app_commands.describe(case_number="The ID of the case to view")
    @app_commands.guild_only()
    async def case_slash(self, interaction, case_number: int):
        """Slash command version of case"""
        ctx = await self.bot.get_context(interaction)
        
        if ctx.author.guild_permissions.manage_messages or await PermissionChecker.is_mod(ctx, self.bot.db):
            await self.case_command(ctx, case_number)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need to be a moderator to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Clean command
    @commands.command(name="clean", aliases=["purge", "clear"])
    @commands.guild_only()
    @PermissionChecker.mod_or_permissions(manage_messages=True)
    @PermissionChecker.bot_has_permissions(manage_messages=True)
    async def clean_command(self, ctx, count: int = 100):
        """Deletes a specified number of messages from the channel"""
        # Check if count is valid
        if count < 1 or count > 1000:
            embed = EmbedGenerator.error(
                "Invalid Count",
                "You must specify a number between 1 and 1000."
            )
            return await ctx.send(embed=embed)
        
        # Delete command message first
        await ctx.message.delete()
        
        # Delete messages in batches of 100 (Discord API limitation)
        deleted = 0
        
        # Process in batches to prevent API limitations
        for i in range(0, count, 100):
            batch_size = min(100, count - i)
            try:
                batch_messages = await ctx.channel.purge(limit=batch_size)
                deleted += len(batch_messages)
                
                # If we deleted fewer messages than requested, we've hit the end of the channel
                if len(batch_messages) < batch_size:
                    break
            except discord.Forbidden:
                embed = EmbedGenerator.error(
                    "Permission Error",
                    "I don't have permission to delete messages in this channel."
                )
                return await ctx.send(embed=embed)
            except discord.HTTPException as e:
                embed = EmbedGenerator.error(
                    "Error Deleting Messages",
                    f"An error occurred: {str(e)}"
                )
                return await ctx.send(embed=embed)
        
        # Send confirmation (and delete it after 5 seconds)
        confirmation = await ctx.send(
            embed=EmbedGenerator.success(
                "Messages Deleted",
                f"Successfully deleted {deleted} message{'s' if deleted != 1 else ''}."
            )
        )
        
        await asyncio.sleep(5)
        try:
            await confirmation.delete()
        except discord.NotFound:
            pass
    
    @app_commands.command(name="clean", description="Deletes a specified number of messages from the channel")
    @app_commands.describe(count="The number of messages to delete (default: 100)")
    @app_commands.guild_only()
    async def clean_slash(self, interaction, count: int = 100):
        """Slash command version of clean"""
        ctx = await self.bot.get_context(interaction)
        
        if ctx.author.guild_permissions.manage_messages or await PermissionChecker.is_mod(ctx, self.bot.db):
            await interaction.response.defer(ephemeral=True)
            await self.clean_command(ctx, count)
            await interaction.followup.send(
                embed=EmbedGenerator.success(
                    "Messages Deleted",
                    f"Successfully deleted {count} message{'s' if count != 1 else ''}."
                ),
                ephemeral=True
            )
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need the 'Manage Messages' permission to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Clearnotes command
    @commands.command(name="clearnotes")
    @commands.guild_only()
    @PermissionChecker.mod_or_permissions(manage_messages=True)
    async def clearnotes_command(self, ctx, user: discord.Member):
        """Clears all notes for a user"""
        # Clear notes from database
        note_count = await self.bot.db.clear_notes(ctx.guild.id, user.id)
        
        if note_count > 0:
            embed = EmbedGenerator.success(
                "Notes Cleared",
                f"Successfully cleared {note_count} note{'s' if note_count != 1 else ''} for {user.mention}.",
                footer=f"Cleared by {ctx.author}"
            )
            await ctx.send(embed=embed)
        else:
            embed = EmbedGenerator.info(
                "No Notes Found",
                f"{user.mention} has no notes to clear."
            )
            await ctx.send(embed=embed)
    
    @app_commands.command(name="clearnotes", description="Clears all notes for a user")
    @app_commands.describe(user="The user to clear notes for")
    @app_commands.guild_only()
    async def clearnotes_slash(self, interaction, user: discord.Member):
        """Slash command version of clearnotes"""
        ctx = await self.bot.get_context(interaction)
        
        if ctx.author.guild_permissions.manage_messages or await PermissionChecker.is_mod(ctx, self.bot.db):
            await self.clearnotes_command(ctx, user)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need to be a moderator to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Deafen command
    @commands.command(name="deafen")
    @commands.guild_only()
    @PermissionChecker.mod_or_permissions(deafen_members=True)
    @PermissionChecker.bot_has_permissions(deafen_members=True)
    async def deafen_command(self, ctx, member: discord.Member, *, reason=None):
        """Server deafens a member in voice channels"""
        # Check if member is in a voice channel
        if not member.voice:
            embed = EmbedGenerator.error(
                "Not in Voice Channel",
                f"{member.mention} is not connected to a voice channel."
            )
            return await ctx.send(embed=embed)
        
        # Check if already deafened
        if member.voice.deaf:
            embed = EmbedGenerator.error(
                "Already Deafened",
                f"{member.mention} is already server deafened."
            )
            return await ctx.send(embed=embed)
        
        # Check hierarchy
        if not await PermissionChecker.check_hierarchy(ctx, member):
            embed = EmbedGenerator.error(
                "Cannot Deafen Member",
                "You cannot deafen this member due to role hierarchy."
            )
            return await ctx.send(embed=embed)
        
        # Deafen the member
        try:
            await member.edit(deafen=True, reason=f"Deafened by {ctx.author}: {reason}" if reason else f"Deafened by {ctx.author}")
            
            # Create a moderation case
            case_id = await self.bot.db.create_mod_case(
                ctx.guild.id,
                member.id,
                ctx.author.id,
                "deafen",
                reason
            )
            
            # Send confirmation
            embed = EmbedGenerator.success(
                "Member Deafened",
                f"{member.mention} has been server deafened.",
                fields=[
                    {"name": "Reason", "value": reason or "No reason provided", "inline": False},
                    {"name": "Case ID", "value": f"#{case_id}", "inline": True}
                ]
            )
            await ctx.send(embed=embed)
        
        except discord.Forbidden:
            embed = EmbedGenerator.error(
                "Permission Error",
                "I don't have permission to server deafen members."
            )
            await ctx.send(embed=embed)
        
        except discord.HTTPException as e:
            embed = EmbedGenerator.error(
                "Error Deafening Member",
                f"An error occurred: {str(e)}"
            )
            await ctx.send(embed=embed)
    
    @app_commands.command(name="deafen", description="Server deafens a member in voice channels")
    @app_commands.describe(
        member="The member to deafen",
        reason="Reason for deafening the member"
    )
    @app_commands.guild_only()
    async def deafen_slash(self, interaction, member: discord.Member, reason: str = None):
        """Slash command version of deafen"""
        ctx = await self.bot.get_context(interaction)
        
        if ctx.author.guild_permissions.deafen_members or await PermissionChecker.is_mod(ctx, self.bot.db):
            await self.deafen_command(ctx, member, reason=reason)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need the 'Deafen Members' permission to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Delnote command
    @commands.command(name="delnote", aliases=["deletenote"])
    @commands.guild_only()
    @PermissionChecker.mod_or_permissions(manage_messages=True)
    async def delnote_command(self, ctx, user: discord.Member, note_id: int = None):
        """Deletes a specific note or the latest note for a user"""
        if note_id is None:
            # Get all notes for the user
            notes = await self.bot.db.get_notes(ctx.guild.id, user.id)
            
            if not notes:
                embed = EmbedGenerator.error(
                    "No Notes Found",
                    f"{user.mention} has no notes to delete."
                )
                return await ctx.send(embed=embed)
            
            # Delete the most recent note
            latest_note = notes[0]
            success = await self.bot.db.delete_note(latest_note['id'])
            
            if success:
                embed = EmbedGenerator.success(
                    "Note Deleted",
                    f"Successfully deleted the latest note for {user.mention}."
                )
                await ctx.send(embed=embed)
            else:
                embed = EmbedGenerator.error(
                    "Error Deleting Note",
                    "An error occurred while trying to delete the note."
                )
                await ctx.send(embed=embed)
        
        else:
            # Get the specific note
            note = await self.bot.db.get_note(note_id)
            
            if not note or note['guild_id'] != ctx.guild.id or note['user_id'] != user.id:
                embed = EmbedGenerator.error(
                    "Note Not Found",
                    f"No note with ID #{note_id} was found for {user.mention} in this server."
                )
                return await ctx.send(embed=embed)
            
            # Delete the note
            success = await self.bot.db.delete_note(note_id)
            
            if success:
                embed = EmbedGenerator.success(
                    "Note Deleted",
                    f"Successfully deleted note #{note_id} for {user.mention}."
                )
                await ctx.send(embed=embed)
            else:
                embed = EmbedGenerator.error(
                    "Error Deleting Note",
                    "An error occurred while trying to delete the note."
                )
                await ctx.send(embed=embed)
    
    @app_commands.command(name="delnote", description="Deletes a specific note or the latest note for a user")
    @app_commands.describe(
        user="The user whose note to delete",
        note_id="ID of the specific note to delete (optional)"
    )
    @app_commands.guild_only()
    async def delnote_slash(self, interaction, user: discord.Member, note_id: int = None):
        """Slash command version of delnote"""
        ctx = await self.bot.get_context(interaction)
        
        if ctx.author.guild_permissions.manage_messages or await PermissionChecker.is_mod(ctx, self.bot.db):
            await self.delnote_command(ctx, user, note_id)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need to be a moderator to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Delwarn command
    @commands.command(name="delwarn", aliases=["deletewarning"])
    @commands.guild_only()
    @PermissionChecker.mod_or_permissions(manage_messages=True)
    async def delwarn_command(self, ctx, user: discord.Member, case_id: int = None):
        """Deletes a specific warning or the latest warning for a user"""
        # Get user cases
        cases = await self.bot.db.get_user_cases(ctx.guild.id, user.id)
        
        # Filter warning cases
        warning_cases = [case for case in cases if case['action'] == 'warn']
        
        if not warning_cases:
            embed = EmbedGenerator.error(
                "No Warnings Found",
                f"{user.mention} has no warnings to delete."
            )
            return await ctx.send(embed=embed)
        
        if case_id is None:
            # Get the most recent warning
            case_to_delete = warning_cases[0]
        else:
            # Find the specific warning
            case_to_delete = None
            for case in warning_cases:
                if case['case_id'] == case_id:
                    case_to_delete = case
                    break
            
            if not case_to_delete:
                embed = EmbedGenerator.error(
                    "Warning Not Found",
                    f"No warning with case ID #{case_id} was found for {user.mention}."
                )
                return await ctx.send(embed=embed)
        
        # Set the warning case as inactive
        success = await self.bot.db.set_case_inactive(case_to_delete['case_id'])
        
        if success:
            embed = EmbedGenerator.success(
                "Warning Deleted",
                f"Successfully deleted warning (Case #{case_to_delete['case_id']}) for {user.mention}."
            )
            await ctx.send(embed=embed)
        else:
            embed = EmbedGenerator.error(
                "Error Deleting Warning",
                "An error occurred while trying to delete the warning."
            )
            await ctx.send(embed=embed)
    
    @app_commands.command(name="delwarn", description="Deletes a specific warning or the latest warning for a user")
    @app_commands.describe(
        user="The user whose warning to delete",
        case_id="ID of the specific warning case to delete (optional)"
    )
    @app_commands.guild_only()
    async def delwarn_slash(self, interaction, user: discord.Member, case_id: int = None):
        """Slash command version of delwarn"""
        ctx = await self.bot.get_context(interaction)
        
        if ctx.author.guild_permissions.manage_messages or await PermissionChecker.is_mod(ctx, self.bot.db):
            await self.delwarn_command(ctx, user, case_id)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need to be a moderator to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Diagnose command
    @commands.command(name="diagnose")
    @commands.guild_only()
    @PermissionChecker.admin_or_permissions(administrator=True)
    async def diagnose_command(self, ctx, *, command_or_module):
        """Diagnoses issues with a command or module"""
        # Check if it's a command
        cmd = self.bot.get_command(command_or_module)
        if cmd:
            # Check bot permissions
            missing_perms = []
            
            # Get required permissions from commands.check decorators if any
            required_perms = getattr(cmd.callback, "__commands_checks__", [])
            
            # Check common permissions based on command name
            if cmd.name in ["ban", "unban"]:
                if not ctx.guild.me.guild_permissions.ban_members:
                    missing_perms.append("Ban Members")
            
            elif cmd.name in ["kick"]:
                if not ctx.guild.me.guild_permissions.kick_members:
                    missing_perms.append("Kick Members")
            
            elif cmd.name in ["mute", "unmute"]:
                if not ctx.guild.me.guild_permissions.manage_roles:
                    missing_perms.append("Manage Roles")
            
            elif cmd.name in ["clean", "purge", "clear"]:
                if not ctx.guild.me.guild_permissions.manage_messages:
                    missing_perms.append("Manage Messages")
            
            elif cmd.name in ["deafen", "undeafen"]:
                if not ctx.guild.me.guild_permissions.deafen_members:
                    missing_perms.append("Deafen Members")
            
            # Check if module is enabled
            module_enabled = True
            if cmd.cog:
                module_name = cmd.cog.qualified_name.lower()
                modules = await self.bot.db.get_modules(ctx.guild.id)
                module_enabled = modules.get(module_name, True)
            
            # Create diagnosis embed
            embed = discord.Embed(
                title=f"Command Diagnosis: {cmd.name}",
                color=EmbedGenerator.get_color("info"),
                timestamp=datetime.datetime.utcnow()
            )
            
            embed.add_field(
                name="Command Status",
                value="✅ Command exists",
                inline=False
            )
            
            embed.add_field(
                name="Module Status",
                value=f"{'✅ Module is enabled' if module_enabled else '❌ Module is disabled'}\n"
                      f"Use `{ctx.prefix}module {module_name}` to toggle it",
                inline=False
            )
            
            if missing_perms:
                embed.add_field(
                    name="Permission Issues",
                    value="❌ Missing bot permissions:\n• " + "\n• ".join(missing_perms),
                    inline=False
                )
            else:
                embed.add_field(
                    name="Permission Status",
                    value="✅ Bot has required permissions",
                    inline=False
                )
            
            # Check if the command is being used correctly
            usage = f"{ctx.prefix}{cmd.name} {cmd.signature}"
            embed.add_field(
                name="Proper Usage",
                value=f"`{usage}`",
                inline=False
            )
            
            await ctx.send(embed=embed)
            return
        
        # Check if it's a module
        module_name = command_or_module.lower()
        valid_modules = ["moderation", "utility", "fun"]
        
        if module_name in valid_modules:
            # Check if module is enabled
            modules = await self.bot.db.get_modules(ctx.guild.id)
            module_enabled = modules.get(module_name, True)
            
            # Count commands in module
            module_commands = [cmd for cmd in self.bot.commands if cmd.cog and cmd.cog.qualified_name.lower() == module_name]
            
            # Create diagnosis embed
            embed = discord.Embed(
                title=f"Module Diagnosis: {module_name.capitalize()}",
                color=EmbedGenerator.get_color("info"),
                timestamp=datetime.datetime.utcnow()
            )
            
            embed.add_field(
                name="Module Status",
                value=f"{'✅ Module is enabled' if module_enabled else '❌ Module is disabled'}\n"
                      f"Use `{ctx.prefix}module {module_name}` to toggle it",
                inline=False
            )
            
            embed.add_field(
                name="Commands",
                value=f"This module has {len(module_commands)} commands\n"
                      f"Use `{ctx.prefix}help {module_name}` to see them",
                inline=False
            )
            
            # Check common permissions for the module
            missing_perms = []
            
            if module_name == "moderation":
                perms = ["kick_members", "ban_members", "manage_messages", "manage_roles"]
                for perm in perms:
                    if not getattr(ctx.guild.me.guild_permissions, perm):
                        missing_perms.append(perm.replace("_", " ").title())
            
            if missing_perms:
                embed.add_field(
                    name="Permission Issues",
                    value="❌ Missing bot permissions:\n• " + "\n• ".join(missing_perms),
                    inline=False
                )
            else:
                embed.add_field(
                    name="Permission Status",
                    value="✅ Bot has common required permissions for this module",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            return
        
        # Neither a command nor a module
        embed = EmbedGenerator.error(
            "Not Found",
            f"No command or module named '{command_or_module}' was found.\n\n"
            f"Use `{ctx.prefix}help` to see available commands and modules."
        )
        await ctx.send(embed=embed)
    
    @app_commands.command(name="diagnose", description="Diagnoses issues with a command or module")
    @app_commands.describe(command_or_module="The command or module name to diagnose")
    @app_commands.guild_only()
    async def diagnose_slash(self, interaction, command_or_module: str):
        """Slash command version of diagnose"""
        ctx = await self.bot.get_context(interaction)
        
        if await PermissionChecker.is_admin(ctx):
            await self.diagnose_command(ctx, command_or_module=command_or_module)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need Administrator permissions to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Duration command
    @commands.command(name="duration")
    @commands.guild_only()
    @PermissionChecker.mod_or_permissions(manage_messages=True)
    async def duration_command(self, ctx, case_id: int, new_duration: str):
        """Updates the duration of a temporary moderation action"""
        # Get the case from the database
        case = await self.bot.db.get_case(case_id)
        
        if not case or case['guild_id'] != ctx.guild.id:
            embed = EmbedGenerator.error(
                "Case Not Found",
                f"No case with ID #{case_id} was found in this server."
            )
            return await ctx.send(embed=embed)
        
        # Check if case is active
        if not case['active']:
            embed = EmbedGenerator.error(
                "Case Inactive",
                f"Case #{case_id} is not active. Only active cases can have their duration updated."
            )
            return await ctx.send(embed=embed)
        
        # Parse the new duration
        new_duration_seconds = self.parse_duration(new_duration)
        if new_duration_seconds is None:
            embed = EmbedGenerator.error(
                "Invalid Duration",
                "Please provide a valid duration (e.g., 1h, 1d, 7d)."
            )
            return await ctx.send(embed=embed)
        
        # Update the case duration
        success = await self.bot.db.update_case_duration(case_id, new_duration_seconds)
        
        if not success:
            embed = EmbedGenerator.error(
                "Update Failed",
                "Failed to update the case duration."
            )
            return await ctx.send(embed=embed)
        
        # Get formatted durations for display
        old_duration_text = self.format_duration(case['duration'])
        new_duration_text = self.format_duration(new_duration_seconds)
        
        # Send confirmation
        embed = EmbedGenerator.success(
            "Duration Updated",
            f"Updated the duration for case #{case_id}.",
            fields=[
                {"name": "Action", "value": case['action'].capitalize(), "inline": True},
                {"name": "Old Duration", "value": old_duration_text, "inline": True},
                {"name": "New Duration", "value": new_duration_text, "inline": True}
            ]
        )
        
        await ctx.send(embed=embed)
    
    @app_commands.command(name="duration", description="Updates the duration of a temporary moderation action")
    @app_commands.describe(
        case_id="The ID of the case to update",
        new_duration="The new duration (e.g., 1h, 1d, 7d)"
    )
    @app_commands.guild_only()
    async def duration_slash(self, interaction, case_id: int, new_duration: str):
        """Slash command version of duration"""
        ctx = await self.bot.get_context(interaction)
        
        if ctx.author.guild_permissions.manage_messages or await PermissionChecker.is_mod(ctx, self.bot.db):
            await self.duration_command(ctx, case_id, new_duration)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need to be a moderator to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Editnote command
    @commands.command(name="editnote")
    @commands.guild_only()
    @PermissionChecker.mod_or_permissions(manage_messages=True)
    async def editnote_command(self, ctx, user: discord.Member, note_id: int = None, *, new_text=None):
        """Edits a note for a user"""
        if note_id is None or new_text is None:
            embed = EmbedGenerator.error(
                "Invalid Usage",
                f"Usage: `{ctx.prefix}editnote @user <note_id> <new text>`"
            )
            return await ctx.send(embed=embed)
        
        # Get the note
        note = await self.bot.db.get_note(note_id)
        
        if not note or note['guild_id'] != ctx.guild.id or note['user_id'] != user.id:
            embed = EmbedGenerator.error(
                "Note Not Found",
                f"No note with ID #{note_id} was found for {user.mention} in this server."
            )
            return await ctx.send(embed=embed)
        
        # Update the note
        success = await self.bot.db.edit_note(note_id, new_text)
        
        if success:
            embed = EmbedGenerator.success(
                "Note Updated",
                f"Successfully updated note #{note_id} for {user.mention}."
            )
            await ctx.send(embed=embed)
        else:
            embed = EmbedGenerator.error(
                "Error Updating Note",
                "An error occurred while trying to update the note."
            )
            await ctx.send(embed=embed)
    
    @app_commands.command(name="editnote", description="Edits a note for a user")
    @app_commands.describe(
        user="The user whose note to edit",
        note_id="ID of the note to edit",
        new_text="The new text for the note"
    )
    @app_commands.guild_only()
    async def editnote_slash(self, interaction, user: discord.Member, note_id: int, new_text: str):
        """Slash command version of editnote"""
        ctx = await self.bot.get_context(interaction)
        
        if ctx.author.guild_permissions.manage_messages or await PermissionChecker.is_mod(ctx, self.bot.db):
            await self.editnote_command(ctx, user, note_id, new_text=new_text)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need to be a moderator to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Ignored command
    @commands.command(name="ignored")
    @commands.guild_only()
    @PermissionChecker.mod_or_permissions(manage_guild=True)
    async def ignored_command(self, ctx):
        """Lists all ignored channels, roles, and users"""
        # Get ignored channels
        ignored_channels = await self.bot.db.get_ignored_channels(ctx.guild.id)
        channel_mentions = []
        for channel_id in ignored_channels:
            channel = ctx.guild.get_channel(channel_id)
            if channel:
                channel_mentions.append(channel.mention)
        
        # Get ignored roles
        ignored_roles = await self.bot.db.get_ignored_roles(ctx.guild.id)
        role_mentions = []
        for role_id in ignored_roles:
            role = ctx.guild.get_role(role_id)
            if role:
                role_mentions.append(role.mention)
        
        # Get ignored users
        ignored_users = await self.bot.db.get_ignored_users(ctx.guild.id)
        user_details = []
        for user_data in ignored_users:
            user = ctx.guild.get_member(user_data["id"])
            if user:
                reason = f" - {user_data['reason']}" if user_data.get('reason') else ""
                user_details.append(f"{user.mention}{reason}")
        
        # Create embed
        embed = discord.Embed(
            title="Ignored Entities",
            description="These channels, roles, and users are ignored by the bot.",
            color=EmbedGenerator.get_color("info"),
            timestamp=datetime.datetime.utcnow()
        )
        
        # Add fields
        if channel_mentions:
            embed.add_field(
                name="Ignored Channels",
                value=", ".join(channel_mentions) if len(channel_mentions) <= 10 else ", ".join(channel_mentions[:10]) + f" and {len(channel_mentions) - 10} more...",
                inline=False
            )
        else:
            embed.add_field(
                name="Ignored Channels",
                value="No ignored channels",
                inline=False
            )
        
        if role_mentions:
            embed.add_field(
                name="Ignored Roles",
                value=", ".join(role_mentions) if len(role_mentions) <= 10 else ", ".join(role_mentions[:10]) + f" and {len(role_mentions) - 10} more...",
                inline=False
            )
        else:
            embed.add_field(
                name="Ignored Roles",
                value="No ignored roles",
                inline=False
            )
        
        if user_details:
            embed.add_field(
                name="Ignored Users",
                value="\n".join(user_details) if len(user_details) <= 10 else "\n".join(user_details[:10]) + f"\n...and {len(user_details) - 10} more",
                inline=False
            )
        else:
            embed.add_field(
                name="Ignored Users",
                value="No ignored users",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @app_commands.command(name="ignored", description="Lists all ignored channels, roles, and users")
    @app_commands.guild_only()
    async def ignored_slash(self, interaction):
        """Slash command version of ignored"""
        ctx = await self.bot.get_context(interaction)
        
        if ctx.author.guild_permissions.manage_guild or await PermissionChecker.is_mod(ctx, self.bot.db):
            await self.ignored_command(ctx)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need to be a moderator to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Kick command
    @commands.command(name="kick")
    @commands.guild_only()
    @PermissionChecker.mod_or_permissions(kick_members=True)
    @PermissionChecker.bot_has_permissions(kick_members=True)
    async def kick_command(self, ctx, member: discord.Member, *, reason=None):
        """Kicks a member from the server"""
        # Check hierarchy
        if not await PermissionChecker.check_hierarchy(ctx, member):
            embed = EmbedGenerator.error(
                "Cannot Kick Member",
                "You cannot kick this member due to role hierarchy."
            )
            return await ctx.send(embed=embed)
        
        # Create the kick case
        case_id = await self.bot.db.create_mod_case(
            ctx.guild.id,
            member.id,
            ctx.author.id,
            "kick",
            reason
        )
        
        # Try to DM the member
        try:
            dm_embed = discord.Embed(
                title=f"You have been kicked from {ctx.guild.name}",
                color=EmbedGenerator.get_color("error"),
                timestamp=datetime.datetime.utcnow()
            )
            
            dm_embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
            dm_embed.add_field(name="Moderator", value=f"{ctx.author} ({ctx.author.id})", inline=False)
            
            await member.send(embed=dm_embed)
        except (discord.Forbidden, discord.HTTPException):
            # Cannot DM user, continue with kick
            pass
        
        # Execute the kick
        try:
            await ctx.guild.kick(member, reason=f"[Case #{case_id}] {reason or 'No reason provided'}")
            
            # Confirm the kick
            confirmation = EmbedGenerator.success(
                "Member Kicked",
                f"{member.mention} has been kicked from the server.",
                fields=[
                    {"name": "User", "value": f"{member} ({member.id})", "inline": True},
                    {"name": "Reason", "value": reason or "No reason provided", "inline": True},
                    {"name": "Case ID", "value": f"#{case_id}", "inline": True}
                ]
            )
            
            await ctx.send(embed=confirmation)
        
        except discord.HTTPException as e:
            error_embed = EmbedGenerator.error(
                "Error Kicking Member",
                f"An error occurred while kicking {member.mention}: {str(e)}"
            )
            await ctx.send(embed=error_embed)
    
    @app_commands.command(name="kick", description="Kicks a member from the server")
    @app_commands.describe(
        member="The member to kick",
        reason="Reason for kicking the member"
    )
    @app_commands.guild_only()
    async def kick_slash(self, interaction, member: discord.Member, reason: str = None):
        """Slash command version of kick"""
        ctx = await self.bot.get_context(interaction)
        
        if ctx.author.guild_permissions.kick_members or await PermissionChecker.is_mod(ctx, self.bot.db):
            await interaction.response.defer()
            await self.kick_command(ctx, member, reason=reason)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need the 'Kick Members' permission to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Lock command
    @commands.command(name="lock")
    @commands.guild_only()
    @PermissionChecker.mod_or_permissions(manage_channels=True)
    @PermissionChecker.bot_has_permissions(manage_channels=True)
    async def lock_command(self, ctx, channel: discord.TextChannel = None, limit: str = None, *, reason=None):
        """Locks a channel to prevent members from sending messages"""
        # If no channel specified, use the current channel
        channel = channel or ctx.channel
        
        # Parse duration if provided
        duration = None
        if limit:
            duration = self.parse_duration(limit)
            if duration is None:
                # If limit is provided but invalid, assume it's part of the reason
                if reason:
                    reason = f"{limit} {reason}"
                else:
                    reason = limit
                limit = None
        
        # Get the @everyone role
        everyone_role = ctx.guild.default_role
        
        # Check current permissions
        current_perms = channel.overwrites_for(everyone_role)
        
        if current_perms.send_messages is False:
            embed = EmbedGenerator.error(
                "Channel Already Locked",
                f"{channel.mention} is already locked."
            )
            return await ctx.send(embed=embed)
        
        # Update permissions
        try:
            overwrite = discord.PermissionOverwrite(**dict(current_perms))
            overwrite.send_messages = False
            
            await channel.set_permissions(
                everyone_role,
                overwrite=overwrite,
                reason=f"Channel locked by {ctx.author}: {reason}" if reason else f"Channel locked by {ctx.author}"
            )
            
            # Create a case
            case_id = await self.bot.db.create_mod_case(
                ctx.guild.id,
                0,  # No specific user
                ctx.author.id,
                "lock",
                reason,
                duration
            )
            
            # Send confirmation
            duration_text = f" for {self.format_duration(duration)}" if duration else ""
            
            embed = EmbedGenerator.success(
                "Channel Locked",
                f"{channel.mention} has been locked{duration_text}. Members cannot send messages.",
                fields=[
                    {"name": "Reason", "value": reason or "No reason provided", "inline": False},
                    {"name": "Case ID", "value": f"#{case_id}", "inline": True}
                ]
            )
            
            await ctx.send(embed=embed)
            
            # If duration is set, schedule unlock
            if duration:
                async def unlock_channel():
                    await asyncio.sleep(duration)
                    try:
                        # Reset to previous permissions
                        overwrite = discord.PermissionOverwrite(**dict(current_perms))
                        await channel.set_permissions(
                            everyone_role,
                            overwrite=overwrite,
                            reason=f"Temporary lock expired (Case #{case_id})"
                        )
                        
                        # Update case as inactive
                        await self.bot.db.set_case_inactive(case_id)
                        
                        # Send notification
                        await channel.send(
                            embed=EmbedGenerator.info(
                                "Channel Unlocked",
                                f"This channel has been automatically unlocked after the set duration.",
                                footer=f"Case #{case_id}"
                            )
                        )
                    except discord.HTTPException:
                        # Failed to unlock, possibly channel deleted or permissions changed
                        pass
                
                # Start the unlock task
                self.bot.loop.create_task(unlock_channel())
        
        except discord.Forbidden:
            embed = EmbedGenerator.error(
                "Permission Error",
                "I don't have permission to manage channel permissions."
            )
            await ctx.send(embed=embed)
        
        except discord.HTTPException as e:
            embed = EmbedGenerator.error(
                "Error Locking Channel",
                f"An error occurred: {str(e)}"
            )
            await ctx.send(embed=embed)
    
    @app_commands.command(name="lock", description="Locks a channel to prevent members from sending messages")
    @app_commands.describe(
        channel="The channel to lock (default: current channel)",
        limit="Duration of the lock (e.g., 1h, 1d)",
        reason="Reason for locking the channel"
    )
    @app_commands.guild_only()
    async def lock_slash(self, interaction, channel: discord.TextChannel = None, limit: str = None, reason: str = None):
        """Slash command version of lock"""
        ctx = await self.bot.get_context(interaction)
        
        if ctx.author.guild_permissions.manage_channels or await PermissionChecker.is_mod(ctx, self.bot.db):
            # If no channel specified in slash command, use the current channel
            channel = channel or ctx.channel
            await self.lock_command(ctx, channel, limit, reason=reason)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need the 'Manage Channels' permission to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Lockdown command
    @commands.command(name="lockdown")
    @commands.guild_only()
    @PermissionChecker.admin_or_permissions(administrator=True)
    @PermissionChecker.bot_has_permissions(manage_channels=True)
    async def lockdown_command(self, ctx, *, message=None):
        """Locks down all text channels in the server"""
        # Check if a lockdown is already in progress
        if ctx.guild.id in self.active_lockdowns:
            embed = EmbedGenerator.error(
                "Lockdown Already Active",
                f"A lockdown is already in progress. Use `{ctx.prefix}unlockdown` to end it."
            )
            return await ctx.send(embed=embed)
        
        # Confirm action
        confirm_embed = EmbedGenerator.warning(
            "Confirm Lockdown",
            "This will lock all text channels in the server, preventing members from sending messages.\n\n"
            "React with ✅ to confirm or ❌ to cancel."
        )
        
        confirm_msg = await ctx.send(embed=confirm_embed)
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirm_msg.id
        
        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
            
            if str(reaction.emoji) == "❌":
                await confirm_msg.delete()
                await ctx.send("Lockdown cancelled.")
                return
            
            await confirm_msg.delete()
        except asyncio.TimeoutError:
            await confirm_msg.delete()
            await ctx.send("Lockdown cancelled due to timeout.")
            return
        
        # Track original permissions and locked channels
        locked_channels = []
        original_permissions = {}
        
        # Get all text channels
        text_channels = [channel for channel in ctx.guild.channels if isinstance(channel, discord.TextChannel)]
        
        # Start status message
        status_msg = await ctx.send("Locking down channels... 0%")
        
        # Lock each channel
        for i, channel in enumerate(text_channels):
            try:
                # Get current permissions
                everyone_role = ctx.guild.default_role
                current_perms = channel.overwrites_for(everyone_role)
                
                # Store original permissions
                original_permissions[channel.id] = dict(current_perms)
                
                # Skip already locked channels
                if current_perms.send_messages is False:
                    continue
                
                # Update permissions
                overwrite = discord.PermissionOverwrite(**dict(current_perms))
                overwrite.send_messages = False
                
                await channel.set_permissions(
                    everyone_role,
                    overwrite=overwrite,
                    reason=f"Server lockdown by {ctx.author}"
                )
                
                locked_channels.append(channel)
                
                # Send lockdown message if provided
                if message and i < 5:  # Only send to first 5 channels to avoid spam
                    try:
                        lockdown_embed = EmbedGenerator.warning(
                            "Server Lockdown",
                            message or "This server is currently in lockdown. Please wait for further instructions."
                        )
                        await channel.send(embed=lockdown_embed)
                    except discord.HTTPException:
                        pass
                
                # Update status message periodically
                if i % 5 == 0 or i == len(text_channels) - 1:
                    progress = int((i + 1) / len(text_channels) * 100)
                    await status_msg.edit(content=f"Locking down channels... {progress}%")
            
            except discord.Forbidden:
                continue
            except discord.HTTPException:
                continue
        
        # Store lockdown data
        self.active_lockdowns[ctx.guild.id] = {
            "original_permissions": original_permissions,
            "locked_channels": [channel.id for channel in locked_channels],
            "initiator": ctx.author.id,
            "timestamp": datetime.datetime.utcnow().timestamp()
        }
        
        # Create a case
        case_id = await self.bot.db.create_mod_case(
            ctx.guild.id,
            0,  # No specific user
            ctx.author.id,
            "lockdown",
            message
        )
        
        # Final confirmation
        embed = EmbedGenerator.success(
            "Server Lockdown",
            f"Successfully locked {len(locked_channels)} channel{'s' if len(locked_channels) != 1 else ''}.",
            fields=[
                {"name": "Locked Channels", "value": str(len(locked_channels)), "inline": True},
                {"name": "Initiator", "value": ctx.author.mention, "inline": True},
                {"name": "Case ID", "value": f"#{case_id}", "inline": True}
            ],
            footer=f"Use {ctx.prefix}unlockdown to end the lockdown"
        )
        
        await status_msg.edit(content=None, embed=embed)
    
    @app_commands.command(name="lockdown", description="Locks down all text channels in the server")
    @app_commands.describe(message="Optional message to display in channels")
    @app_commands.guild_only()
    async def lockdown_slash(self, interaction, message: str = None):
        """Slash command version of lockdown"""
        ctx = await self.bot.get_context(interaction)
        
        if ctx.author.guild_permissions.administrator or await PermissionChecker.is_admin(ctx):
            await interaction.response.defer()
            await self.lockdown_command(ctx, message=message)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need Administrator permissions to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Members command
    @commands.command(name="members")
    @commands.guild_only()
    async def members_command(self, ctx, *, role: discord.Role):
        """Lists all members with a specific role"""
        # Get members with the role
        members = [member for member in ctx.guild.members if role in member.roles]
        
        if not members:
            embed = EmbedGenerator.info(
                f"Members with {role.name}",
                f"No members have the {role.mention} role."
            )
            return await ctx.send(embed=embed)
        
        # Create base embed
        embed = discord.Embed(
            title=f"Members with {role.name}",
            description=f"Found {len(members)} member{'s' if len(members) != 1 else ''} with the {role.mention} role.",
            color=role.color or EmbedGenerator.get_color("info"),
            timestamp=datetime.datetime.utcnow()
        )
        
        # Add role info
        embed.add_field(name="Role ID", value=role.id, inline=True)
        embed.add_field(name="Color", value=str(role.color), inline=True)
        embed.add_field(name="Position", value=role.position, inline=True)
        
        # If there are too many members, just show the count
        if len(members) > 20:
            embed.add_field(
                name="Members",
                value=f"There are {len(members)} members with this role. Use `/memberlist {role.name}` for a complete list.",
                inline=False
            )
        else:
            # Otherwise list up to 20 members
            member_list = "\n".join([f"{i+1}. {member.mention} ({member.id})" for i, member in enumerate(members[:20])])
            embed.add_field(name="Members", value=member_list, inline=False)
        
        await ctx.send(embed=embed)
    
    @app_commands.command(name="members", description="Lists all members with a specific role")
    @app_commands.describe(role="The role to check members for")
    @app_commands.guild_only()
    async def members_slash(self, interaction, role: discord.Role):
        """Slash command version of members"""
        ctx = await self.bot.get_context(interaction)
        await self.members_command(ctx, role=role)
    
    # Moderations command
    @commands.command(name="moderations", aliases=["modlogs", "infractions"])
    @commands.guild_only()
    @PermissionChecker.mod_or_permissions(manage_messages=True)
    async def moderations_command(self, ctx, user: discord.Member, page: int = 1):
        """Shows moderation cases for a user"""
        # Validate page number
        if page < 1:
            page = 1
        
        # Get total count of cases
        total_cases = await self.bot.db.count_user_cases(ctx.guild.id, user.id)
        
        if total_cases == 0:
            embed = EmbedGenerator.info(
                f"Moderation Cases for {user}",
                f"{user.mention} has no moderation cases."
            )
            return await ctx.send(embed=embed)
        
        # Calculate pagination
        items_per_page = 5
        total_pages = (total_cases + items_per_page - 1) // items_per_page
        
        if page > total_pages:
            page = total_pages
        
        # Get cases for this page
        offset = (page - 1) * items_per_page
        cases = await self.bot.db.get_user_cases(ctx.guild.id, user.id, items_per_page, offset)
        
        # Create embed
        embed = discord.Embed(
            title=f"Moderation Cases for {user}",
            description=f"Showing page {page}/{total_pages} ({total_cases} total cases)",
            color=EmbedGenerator.get_color("moderation"),
            timestamp=datetime.datetime.utcnow()
        )
        
        # Add user info
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="User", value=f"{user.mention} ({user.id})", inline=False)
        
        # Add case information
        for case in cases:
            # Format timestamps
            timestamp = datetime.datetime.fromtimestamp(case['timestamp'])
            formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            # Format case info
            moderator = ctx.guild.get_member(case['moderator_id'])
            mod_name = moderator.mention if moderator else f"Unknown Moderator ({case['moderator_id']})"
            
            reason = case['reason'] if case['reason'] else "No reason provided"
            if len(reason) > 100:
                reason = reason[:97] + "..."
            
            duration = self.format_duration(case['duration']) if case['duration'] else "Permanent"
            status = "Active" if case['active'] else "Inactive"
            
            case_text = f"**Moderator:** {mod_name}\n"
            case_text += f"**Reason:** {reason}\n"
            
            if case['duration']:
                case_text += f"**Duration:** {duration}\n"
                
            case_text += f"**Date:** {formatted_time}\n"
            case_text += f"**Status:** {status}"
            
            embed.add_field(
                name=f"Case #{case['case_id']} | {case['action'].capitalize()}",
                value=case_text,
                inline=False
            )
        
        # Add navigation footer
        embed.set_footer(text=f"Use {ctx.prefix}moderations {user} [page] to navigate pages")
        
        await ctx.send(embed=embed)
    
    @app_commands.command(name="moderations", description="Shows moderation cases for a user")
    @app_commands.describe(
        user="The user to check moderation cases for",
        page="Page number to view (default: 1)"
    )
    @app_commands.guild_only()
    async def moderations_slash(self, interaction, user: discord.Member, page: int = 1):
        """Slash command version of moderations"""
        ctx = await self.bot.get_context(interaction)
        
        if ctx.author.guild_permissions.manage_messages or await PermissionChecker.is_mod(ctx, self.bot.db):
            await self.moderations_command(ctx, user, page)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need to be a moderator to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Viewlogs command (alias for moderations)
    @commands.command(name="viewlogs", aliases=["modlogs_alt"])
    @commands.guild_only()
    @PermissionChecker.mod_or_permissions(manage_messages=True)
    async def viewlogs_command(self, ctx, user: discord.Member, page: int = 1):
        """Alias for ?moderations - shows moderation cases for a user"""
        await self.moderations_command(ctx, user, page)
    
    @app_commands.command(name="viewlogs", description="Shows moderation cases for a user (alias for moderations)")
    @app_commands.describe(
        user="The user to check moderation cases for",
        page="Page number to view (default: 1)"
    )
    @app_commands.guild_only()
    async def viewlogs_slash(self, interaction, user: discord.Member, page: int = 1):
        """Slash command version of viewlogs"""
        ctx = await self.bot.get_context(interaction)
        
        if ctx.author.guild_permissions.manage_messages or await PermissionChecker.is_mod(ctx, self.bot.db):
            await self.moderations_command(ctx, user, page)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need to be a moderator to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Modstats command
    @commands.command(name="modstats")
    @commands.guild_only()
    @PermissionChecker.mod_or_permissions(manage_messages=True)
    async def modstats_command(self, ctx, user: discord.User = None):
        """Shows moderation statistics for a moderator or the server"""
        # If no user specified, get server-wide stats
        if user is None:
            user = ctx.author
        
        # Get all cases where the user is the moderator
        async with self.bot.db.conn.cursor() as cursor:
            await cursor.execute(
                """
                SELECT action, COUNT(*) as count
                FROM mod_cases 
                WHERE guild_id = ? AND moderator_id = ?
                GROUP BY action
                ORDER BY count DESC
                """, 
                (ctx.guild.id, user.id)
            )
            
            action_counts = await cursor.fetchall()
            
            # Get total count
            await cursor.execute(
                """
                SELECT COUNT(*) as total
                FROM mod_cases 
                WHERE guild_id = ? AND moderator_id = ?
                """, 
                (ctx.guild.id, user.id)
            )
            
            total_count = await cursor.fetchone()
            total = total_count['total'] if total_count else 0
            
            # Get active cases
            await cursor.execute(
                """
                SELECT COUNT(*) as active
                FROM mod_cases 
                WHERE guild_id = ? AND moderator_id = ? AND active = 1
                """, 
                (ctx.guild.id, user.id)
            )
            
            active_count = await cursor.fetchone()
            active = active_count['active'] if active_count else 0
        
        if not action_counts:
            embed = EmbedGenerator.info(
                f"Moderation Stats for {user}",
                f"{user.mention} has not performed any moderation actions in this server."
            )
            return await ctx.send(embed=embed)
        
        # Create stats embed
        embed = discord.Embed(
            title=f"Moderation Stats for {user}",
            color=EmbedGenerator.get_color("moderation"),
            timestamp=datetime.datetime.utcnow()
        )
        
        # Add user info
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="Moderator", value=f"{user.mention} ({user.id})", inline=False)
        
        # Add stats
        stats_text = "\n".join([f"**{action['action'].capitalize()}:** {action['count']}" for action in action_counts])
        embed.add_field(name="Actions", value=stats_text, inline=True)
        
        # Add total and active counts
        embed.add_field(name="Total Cases", value=str(total), inline=True)
        embed.add_field(name="Active Cases", value=str(active), inline=True)
        
        await ctx.send(embed=embed)
    
    @app_commands.command(name="modstats", description="Shows moderation statistics for a moderator")
    @app_commands.describe(user="The moderator to check stats for (default: yourself)")
    @app_commands.guild_only()
    async def modstats_slash(self, interaction, user: discord.User = None):
        """Slash command version of modstats"""
        ctx = await self.bot.get_context(interaction)
        user = user or ctx.author
        
        if ctx.author.guild_permissions.manage_messages or await PermissionChecker.is_mod(ctx, self.bot.db):
            await self.modstats_command(ctx, user)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need to be a moderator to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Mute command
    @commands.command(name="mute")
    @commands.guild_only()
    @PermissionChecker.mod_or_permissions(manage_roles=True)
    @PermissionChecker.bot_has_permissions(manage_roles=True)
    async def mute_command(self, ctx, member: discord.Member, limit: str = None, *, reason=None):
        """Mutes a member to prevent them from sending messages"""
        # Check hierarchy
        if not await PermissionChecker.check_hierarchy(ctx, member):
            embed = EmbedGenerator.error(
                "Cannot Mute Member",
                "You cannot mute this member due to role hierarchy."
            )
            return await ctx.send(embed=embed)
        
        # Parse duration if provided
        duration = None
        if limit:
            duration = self.parse_duration(limit)
            if duration is None:
                # If limit is provided but invalid, assume it's part of the reason
                if reason:
                    reason = f"{limit} {reason}"
                else:
                    reason = limit
                limit = None
        
        # Check if the guild has timeout feature (Discord Timeouts)
        if hasattr(member, "timeout"):
            # Use Discord's built-in timeout feature
            if duration:
                until = datetime.datetime.utcnow() + datetime.timedelta(seconds=duration)
                
                # Apply timeout
                try:
                    await member.timeout(until, reason=f"Muted by {ctx.author}: {reason}" if reason else f"Muted by {ctx.author}")
                except discord.Forbidden:
                    embed = EmbedGenerator.error(
                        "Missing Permissions",
                        "I don't have permission to timeout this member."
                    )
                    return await ctx.send(embed=embed)
                except discord.HTTPException as e:
                    embed = EmbedGenerator.error(
                        "Error Applying Timeout",
                        f"An error occurred: {str(e)}"
                    )
                    return await ctx.send(embed=embed)
            else:
                # Apply indefinite timeout (28 days is the max Discord allows)
                try:
                    max_timeout = datetime.datetime.utcnow() + datetime.timedelta(days=28)
                    await member.timeout(max_timeout, reason=f"Muted by {ctx.author}: {reason}" if reason else f"Muted by {ctx.author}")
                except discord.Forbidden:
                    embed = EmbedGenerator.error(
                        "Missing Permissions",
                        "I don't have permission to timeout this member."
                    )
                    return await ctx.send(embed=embed)
                except discord.HTTPException as e:
                    embed = EmbedGenerator.error(
                        "Error Applying Timeout",
                        f"An error occurred: {str(e)}"
                    )
                    return await ctx.send(embed=embed)
            
            # Create the case
            case_id = await self.bot.db.create_mod_case(
                ctx.guild.id,
                member.id,
                ctx.author.id,
                "mute",
                reason,
                duration
            )
            
            # Format duration for display
            duration_text = self.format_duration(duration) if duration else "28 days (maximum)"
            
            # Send confirmation
            embed = EmbedGenerator.success(
                "Member Muted",
                f"{member.mention} has been muted for {duration_text}.",
                fields=[
                    {"name": "User", "value": f"{member} ({member.id})", "inline": True},
                    {"name": "Duration", "value": duration_text, "inline": True},
                    {"name": "Case ID", "value": f"#{case_id}", "inline": True},
                    {"name": "Reason", "value": reason or "No reason provided", "inline": False}
                ]
            )
            
            await ctx.send(embed=embed)
            
            # Try to DM the user
            try:
                dm_embed = discord.Embed(
                    title=f"You have been muted in {ctx.guild.name}",
                    color=EmbedGenerator.get_color("error"),
                    timestamp=datetime.datetime.utcnow()
                )
                
                dm_embed.add_field(name="Duration", value=duration_text, inline=False)
                dm_embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
                dm_embed.add_field(name="Moderator", value=f"{ctx.author} ({ctx.author.id})", inline=False)
                
                await member.send(embed=dm_embed)
            except (discord.Forbidden, discord.HTTPException):
                # Cannot DM user, continue
                pass
            
            return
        
        # Fall back to role-based mute if timeout isn't available
        # Get or create mute role
        mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
        
        if not mute_role:
            # Create mute role
            try:
                mute_role = await ctx.guild.create_role(
                    name="Muted",
                    reason="Auto-created mute role",
                    permissions=discord.Permissions(
                        send_messages=False,
                        add_reactions=False,
                        speak=False
                    )
                )
                
                # Set permissions in all channels
                for channel in ctx.guild.channels:
                    try:
                        await channel.set_permissions(
                            mute_role,
                            send_messages=False,
                            add_reactions=False,
                            speak=False
                        )
                    except discord.HTTPException:
                        continue
            except discord.Forbidden:
                embed = EmbedGenerator.error(
                    "Missing Permissions",
                    "I don't have permission to create roles."
                )
                return await ctx.send(embed=embed)
            except discord.HTTPException as e:
                embed = EmbedGenerator.error(
                    "Error Creating Mute Role",
                    f"An error occurred: {str(e)}"
                )
                return await ctx.send(embed=embed)
        
        # Add mute role to member
        try:
            await member.add_roles(mute_role, reason=f"Muted by {ctx.author}: {reason}" if reason else f"Muted by {ctx.author}")
            
            # Create the case
            case_id = await self.bot.db.create_mod_case(
                ctx.guild.id,
                member.id,
                ctx.author.id,
                "mute",
                reason,
                duration
            )
            
            # Format duration for display
            duration_text = self.format_duration(duration) if duration else "Indefinite"
            
            # Send confirmation
            embed = EmbedGenerator.success(
                "Member Muted",
                f"{member.mention} has been muted for {duration_text}.",
                fields=[
                    {"name": "User", "value": f"{member} ({member.id})", "inline": True},
                    {"name": "Duration", "value": duration_text, "inline": True},
                    {"name": "Case ID", "value": f"#{case_id}", "inline": True},
                    {"name": "Reason", "value": reason or "No reason provided", "inline": False}
                ]
            )
            
            await ctx.send(embed=embed)
            
            # Try to DM the user
            try:
                dm_embed = discord.Embed(
                    title=f"You have been muted in {ctx.guild.name}",
                    color=EmbedGenerator.get_color("error"),
                    timestamp=datetime.datetime.utcnow()
                )
                
                dm_embed.add_field(name="Duration", value=duration_text, inline=False)
                dm_embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
                dm_embed.add_field(name="Moderator", value=f"{ctx.author} ({ctx.author.id})", inline=False)
                
                await member.send(embed=dm_embed)
            except (discord.Forbidden, discord.HTTPException):
                # Cannot DM user, continue
                pass
            
            # If duration is set, schedule unmute
            if duration:
                async def unmute_member():
                    await asyncio.sleep(duration)
                    try:
                        # Check if member is still in guild
                        member_obj = ctx.guild.get_member(member.id)
                        if member_obj:
                            # Remove mute role
                            await member_obj.remove_roles(mute_role, reason=f"Temporary mute (Case #{case_id}) expired")
                        
                        # Update case as inactive
                        await self.bot.db.set_case_inactive(case_id)
                    except discord.HTTPException:
                        # Failed to unmute, probably already unmuted manually
                        pass
                
                # Start the unmute task
                self.bot.loop.create_task(unmute_member())
        
        except discord.Forbidden:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "I don't have permission to manage roles for this member."
            )
            await ctx.send(embed=embed)
        
        except discord.HTTPException as e:
            embed = EmbedGenerator.error(
                "Error Muting Member",
                f"An error occurred: {str(e)}"
            )
            await ctx.send(embed=embed)
    
    @app_commands.command(name="mute", description="Mutes a member to prevent them from sending messages")
    @app_commands.describe(
        member="The member to mute",
        limit="Duration of the mute (e.g., 1h, 1d)",
        reason="Reason for muting the member"
    )
    @app_commands.guild_only()
    async def mute_slash(self, interaction, member: discord.Member, limit: str = None, reason: str = None):
        """Slash command version of mute"""
        ctx = await self.bot.get_context(interaction)
        
        if ctx.author.guild_permissions.manage_roles or await PermissionChecker.is_mod(ctx, self.bot.db):
            await interaction.response.defer()
            await self.mute_command(ctx, member, limit, reason=reason)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need the 'Manage Roles' permission to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Note command
    @commands.command(name="note")
    @commands.guild_only()
    @PermissionChecker.mod_or_permissions(manage_messages=True)
    async def note_command(self, ctx, user: discord.Member, *, note_text):
        """Adds a note to a user"""
        # Check if note is too long
        if len(note_text) > 1000:
            embed = EmbedGenerator.error(
                "Note Too Long",
                "Notes cannot be longer than 1000 characters."
            )
            return await ctx.send(embed=embed)
        
        # Add the note
        note_id = await self.bot.db.add_note(ctx.guild.id, user.id, ctx.author.id, note_text)
        
        if note_id:
            embed = EmbedGenerator.success(
                "Note Added",
                f"Successfully added note to {user.mention}.",
                fields=[
                    {"name": "Note ID", "value": f"#{note_id}", "inline": True},
                    {"name": "Content", "value": note_text, "inline": False}
                ],
                footer=f"Added by {ctx.author}"
            )
            await ctx.send(embed=embed)
        else:
            embed = EmbedGenerator.error(
                "Error Adding Note",
                "An error occurred while trying to add the note."
            )
            await ctx.send(embed=embed)
    
    @app_commands.command(name="note", description="Adds a note to a user")
    @app_commands.describe(
        user="The user to add a note to",
        note_text="The content of the note"
    )
    @app_commands.guild_only()
    async def note_slash(self, interaction, user: discord.Member, note_text: str):
        """Slash command version of note"""
        ctx = await self.bot.get_context(interaction)
        
        if ctx.author.guild_permissions.manage_messages or await PermissionChecker.is_mod(ctx, self.bot.db):
            await self.note_command(ctx, user, note_text=note_text)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need to be a moderator to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Notes command
    @commands.command(name="notes")
    @commands.guild_only()
    @PermissionChecker.mod_or_permissions(manage_messages=True)
    async def notes_command(self, ctx, user: discord.Member):
        """Shows all notes for a user"""
        # Get all notes for the user
        notes = await self.bot.db.get_notes(ctx.guild.id, user.id)
        
        if not notes:
            embed = EmbedGenerator.info(
                f"Notes for {user}",
                f"{user.mention} has no notes."
            )
            return await ctx.send(embed=embed)
        
        # Create embed
        embed = discord.Embed(
            title=f"Notes for {user}",
            description=f"Found {len(notes)} note{'s' if len(notes) != 1 else ''}",
            color=EmbedGenerator.get_color("info"),
            timestamp=datetime.datetime.utcnow()
        )
        
        # Add user info
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="User", value=f"{user.mention} ({user.id})", inline=False)
        
        # Add notes
        for note in notes[:15]:  # Limit to 15 notes to avoid hitting embed limits
            # Get moderator info
            moderator = await self.get_user_by_id(ctx.guild, note['moderator_id'])
            mod_name = f"{moderator.mention}" if moderator else f"Unknown Moderator ({note['moderator_id']})"
            
            # Format timestamp
            timestamp = datetime.datetime.fromtimestamp(note['timestamp'])
            formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            # Add field for note
            embed.add_field(
                name=f"Note #{note['id']} | {formatted_time}",
                value=f"**By:** {mod_name}\n**Content:** {note['note']}",
                inline=False
            )
        
        # If there are more notes, add a note about it
        if len(notes) > 15:
            embed.add_field(
                name="Note",
                value=f"Only showing 15 out of {len(notes)} notes. Use `/notes {user.name}` to see more.",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @app_commands.command(name="notes", description="Shows all notes for a user")
    @app_commands.describe(user="The user to view notes for")
    @app_commands.guild_only()
    async def notes_slash(self, interaction, user: discord.Member):
        """Slash command version of notes"""
        ctx = await self.bot.get_context(interaction)
        
        if ctx.author.guild_permissions.manage_messages or await PermissionChecker.is_mod(ctx, self.bot.db):
            await self.notes_command(ctx, user)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need to be a moderator to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Reason command
    @commands.command(name="reason")
    @commands.guild_only()
    @PermissionChecker.mod_or_permissions(manage_messages=True)
    async def reason_command(self, ctx, case_id: int, *, reason):
        """Updates the reason for a moderation case"""
        # Get the case
        case = await self.bot.db.get_case(case_id)
        
        if not case or case['guild_id'] != ctx.guild.id:
            embed = EmbedGenerator.error(
                "Case Not Found",
                f"No case with ID #{case_id} was found in this server."
            )
            return await ctx.send(embed=embed)
        
        # Check if reason is too long
        if len(reason) > 1000:
            embed = EmbedGenerator.error(
                "Reason Too Long",
                "Reasons cannot be longer than 1000 characters."
            )
            return await ctx.send(embed=embed)
        
        # Update the reason
        success = await self.bot.db.update_case_reason(case_id, reason)
        
        if success:
            # Get user info
            user = await self.get_user_by_id(ctx.guild, case['user_id'])
            user_display = f"{user.mention}" if user else f"Unknown User ({case['user_id']})"
            
            embed = EmbedGenerator.success(
                "Reason Updated",
                f"Successfully updated the reason for case #{case_id}.",
                fields=[
                    {"name": "User", "value": user_display, "inline": True},
                    {"name": "Action", "value": case['action'].capitalize(), "inline": True},
                    {"name": "New Reason", "value": reason, "inline": False}
                ],
                footer=f"Updated by {ctx.author}"
            )
            await ctx.send(embed=embed)
        else:
            embed = EmbedGenerator.error(
                "Error Updating Reason",
                "An error occurred while trying to update the reason."
            )
            await ctx.send(embed=embed)
    
    @app_commands.command(name="reason", description="Updates the reason for a moderation case")
    @app_commands.describe(
        case_id="The ID of the case to update",
        reason="The new reason for the case"
    )
    @app_commands.guild_only()
    async def reason_slash(self, interaction, case_id: int, reason: str):
        """Slash command version of reason"""
        ctx = await self.bot.get_context(interaction)
        
        if ctx.author.guild_permissions.manage_messages or await PermissionChecker.is_mod(ctx, self.bot.db):
            await self.reason_command(ctx, case_id, reason=reason)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need to be a moderator to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Rolepersist command
    @commands.command(name="rolepersist", aliases=["persistrole"])
    @commands.guild_only()
    @PermissionChecker.mod_or_permissions(manage_roles=True)
    @PermissionChecker.bot_has_permissions(manage_roles=True)
    async def rolepersist_command(self, ctx, user: discord.Member, role: discord.Role, *, reason=None):
        """Makes a role persist for a user even if they leave and rejoin"""
        # Check if the role is manageable
        if not ctx.guild.me.guild_permissions.manage_roles or ctx.guild.me.top_role <= role:
            embed = EmbedGenerator.error(
                "Cannot Manage Role",
                "I don't have permission to manage this role. Make sure my highest role is above the role you want to assign."
            )
            return await ctx.send(embed=embed)
        
        # Check if the user already has the role
        if role in user.roles:
            # Add to persistence database
            await self.bot.db.add_persisted_role(ctx.guild.id, user.id, role.id, ctx.author.id, reason)
            
            embed = EmbedGenerator.success(
                "Role Persistence Added",
                f"{role.mention} will now persist for {user.mention} even if they leave and rejoin.",
                fields=[
                    {"name": "User", "value": f"{user} ({user.id})", "inline": True},
                    {"name": "Role", "value": f"{role.name} ({role.id})", "inline": True},
                    {"name": "Reason", "value": reason or "No reason provided", "inline": False}
                ]
            )
            await ctx.send(embed=embed)
        else:
            # Add the role and add to persistence database
            try:
                await user.add_roles(role, reason=f"Persistent role added by {ctx.author}: {reason}" if reason else f"Persistent role added by {ctx.author}")
                
                # Add to persistence database
                await self.bot.db.add_persisted_role(ctx.guild.id, user.id, role.id, ctx.author.id, reason)
                
                embed = EmbedGenerator.success(
                    "Role Persistence Added",
                    f"{role.mention} has been added to {user.mention} and will persist even if they leave and rejoin.",
                    fields=[
                        {"name": "User", "value": f"{user} ({user.id})", "inline": True},
                        {"name": "Role", "value": f"{role.name} ({role.id})", "inline": True},
                        {"name": "Reason", "value": reason or "No reason provided", "inline": False}
                    ]
                )
                await ctx.send(embed=embed)
            except discord.Forbidden:
                embed = EmbedGenerator.error(
                    "Missing Permissions",
                    "I don't have permission to add roles to this user."
                )
                await ctx.send(embed=embed)
            except discord.HTTPException as e:
                embed = EmbedGenerator.error(
                    "Error Adding Role",
                    f"An error occurred: {str(e)}"
                )
                await ctx.send(embed=embed)
    
    @app_commands.command(name="rolepersist", description="Makes a role persist for a user even if they leave and rejoin")
    @app_commands.describe(
        user="The user to add the persistent role to",
        role="The role to make persistent",
        reason="Reason for making the role persistent"
    )
    @app_commands.guild_only()
    async def rolepersist_slash(self, interaction, user: discord.Member, role: discord.Role, reason: str = None):
        """Slash command version of rolepersist"""
        ctx = await self.bot.get_context(interaction)
        
        if ctx.author.guild_permissions.manage_roles or await PermissionChecker.is_mod(ctx, self.bot.db):
            await self.rolepersist_command(ctx, user, role, reason=reason)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need the 'Manage Roles' permission to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Softban command
    @commands.command(name="softban")
    @commands.guild_only()
    @PermissionChecker.mod_or_permissions(ban_members=True)
    @PermissionChecker.bot_has_permissions(ban_members=True)
    async def softban_command(self, ctx, user: discord.Member, *, reason=None):
        """Bans and immediately unbans a user to delete their messages"""
        # Check hierarchy
        if not await PermissionChecker.check_hierarchy(ctx, user):
            embed = EmbedGenerator.error(
                "Cannot Softban User",
                "You cannot softban this user due to role hierarchy."
            )
            return await ctx.send(embed=embed)
        
        # Create the softban case
        case_id = await self.bot.db.create_mod_case(
            ctx.guild.id,
            user.id,
            ctx.author.id,
            "softban",
            reason
        )
        
        # Try to DM the user
        try:
            dm_embed = discord.Embed(
                title=f"You have been softbanned from {ctx.guild.name}",
                description="A softban is a ban and immediate unban used to remove your messages.",
                color=EmbedGenerator.get_color("error"),
                timestamp=datetime.datetime.utcnow()
            )
            
            dm_embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
            dm_embed.add_field(name="Moderator", value=f"{ctx.author} ({ctx.author.id})", inline=False)
            
            await user.send(embed=dm_embed)
        except (discord.Forbidden, discord.HTTPException):
            # Cannot DM user, continue with softban
            pass
        
        # Ban and then unban the user
        try:
            await ctx.guild.ban(user, reason=f"[Softban: Case #{case_id}] {reason or 'No reason provided'}", delete_message_days=1)
            await ctx.guild.unban(user, reason=f"Softban: Automatic unban")
            
            # Confirm the softban
            confirmation = EmbedGenerator.success(
                "User Softbanned",
                f"{user.mention} has been softbanned from the server.",
                fields=[
                    {"name": "User", "value": f"{user} ({user.id})", "inline": True},
                    {"name": "Reason", "value": reason or "No reason provided", "inline": True},
                    {"name": "Case ID", "value": f"#{case_id}", "inline": True}
                ]
            )
            
            await ctx.send(embed=confirmation)
        
        except discord.HTTPException as e:
            error_embed = EmbedGenerator.error(
                "Error Softbanning User",
                f"An error occurred while softbanning {user.mention}: {str(e)}"
            )
            await ctx.send(embed=error_embed)
    
    @app_commands.command(name="softban", description="Bans and immediately unbans a user to delete their messages")
    @app_commands.describe(
        user="The user to softban",
        reason="Reason for the softban"
    )
    @app_commands.guild_only()
    async def softban_slash(self, interaction, user: discord.Member, reason: str = None):
        """Slash command version of softban"""
        ctx = await self.bot.get_context(interaction)
        
        if ctx.author.guild_permissions.ban_members or await PermissionChecker.is_mod(ctx, self.bot.db):
            await interaction.response.defer()
            await self.softban_command(ctx, user, reason=reason)
        else:
            embed = EmbedGenerator.error(
                "Missing Permissions",
                "You need the 'Ban Members' permission to use this command."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Star command
    @commands.command(name="star")
    @commands.guild_only()
    async def star_command(self, ctx, message_id_or_link):
        """Stars a message to save it for later"""
        # Extract message ID from link or use provided ID
        message_id = None
        if "discord.com/channels/" in message_id_or_link:
            try:
                parts = message_id_or_link.split("/")
                message_id = int(parts[-1])
            except (ValueError, IndexError):
                embed = EmbedGenerator.error(
                    "Invalid Message Link",
                    "The provided link is not a valid Discord message link."
                )
                return await ctx.send(embed=embed)
        else:
            try:
                message_id = int(message_id_or_link)
            except ValueError:
                embed = EmbedGenerator.error(
                    "Invalid Message ID",
                    "Please provide a valid message ID or link."
                )
                return await ctx.send(embed=embed)
        
        # Try to fetch the message
        message = None
        for channel in ctx.guild.text_channels:
            try:
                message = await channel.fetch_message(message_id)
                break
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                continue
        
        if not message:
            embed = EmbedGenerator.error(
                "Message Not Found",
                "I couldn't find that message. Make sure the ID is correct and I have access to the channel."
            )
            return await ctx.send(embed=embed)
        
        # Create the star embed
        star_embed = discord.Embed(
            description=message.content or "No content",
            color=0xFACB1B,  # Star color (yellow)
            timestamp=message.created_at
        )
        
        # Add author info
        star_embed.set_author(
            name=message.author.display_name,
            icon_url=message.author.display_avatar.url
        )
        
        # Add attachments if any
        if message.attachments:
            # Only add image attachments to the embed
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith("image/"):
                    star_embed.set_image(url=attachment.url)
                    break
                    
            # List all attachments
            if len(message.attachments) > 1 or (len(message.attachments) == 1 and not message.attachments[0].content_type.startswith("image/")):
                attachment_list = "\n".join([f"[{a.filename}]({a.url})" for a in message.attachments])
                star_embed.add_field(name="Attachments", value=attachment_list, inline=False)
        
        # Add footer with source
        star_embed.set_footer(
            text=f"Starred by {ctx.author.display_name} • In #{message.channel.name}",
            icon_url=ctx.author.display_avatar.url
        )
        
        # Add jump link
        star_embed.add_field(
            name="Source",
            value=f"[Jump to Message]({message.jump_url})",
            inline=False
        )
        
        await ctx.send(embed=star_embed)
    
    @app_commands.command(name="star", description="Stars a message to save it for later")
    @app_commands.describe(message_id_or_link="The ID or link of the message to star")
    @app_commands.guild_only()
    async def star_slash(self, interaction, message_id_or_link: str):
        """Slash command version of star"""
        ctx = await self.bot.get_context(interaction)
        await self.star_command(ctx, message_id_or_link)
    
    # Event handlers for role persistence
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Reapply persistent roles when a member rejoins"""
        # Get persisted roles for this user
        persisted_roles = await self.bot.db.get_persisted_roles(member.guild.id, member.id)
        
        if not persisted_roles:
            return
        
        # Get role objects
        roles_to_add = []
        for role_data in persisted_roles:
            role = member.guild.get_role(role_data['role_id'])
            if role and role < member.guild.me.top_role:
                roles_to_add.append(role)
        
        if not roles_to_add:
            return
        
        # Add roles
        try:
            await member.add_roles(*roles_to_add, reason="Reapplying persistent roles")
        except discord.HTTPException:
            # Failed to add roles, log it or handle appropriately
            pass

async def setup(bot):
    await bot.add_cog(Moderation(bot))
