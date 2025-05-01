import discord
import datetime
from config import Config

config = Config()

class EmbedGenerator:
    """Class for generating consistent embeds for the bot"""
    
    @staticmethod
    def get_color(color_type="main"):
        """Get a color from the config"""
        return config.COLORS.get(color_type, config.COLORS["main"])
    
    @staticmethod
    def success(title, description=None, footer=None, fields=None, thumbnail=None):
        """Create a success embed"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=EmbedGenerator.get_color("success"),
            timestamp=datetime.datetime.utcnow()
        )
        
        if footer:
            embed.set_footer(text=footer)
            
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
            
        if fields:
            for field in fields:
                embed.add_field(
                    name=field["name"],
                    value=field["value"],
                    inline=field.get("inline", False)
                )
                
        return embed
    
    @staticmethod
    def error(title, description=None, footer=None):
        """Create an error embed"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=EmbedGenerator.get_color("error"),
            timestamp=datetime.datetime.utcnow()
        )
        
        if footer:
            embed.set_footer(text=footer)
                
        return embed
    
    @staticmethod
    def warning(title, description=None, footer=None):
        """Create a warning embed"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=EmbedGenerator.get_color("warning"),
            timestamp=datetime.datetime.utcnow()
        )
        
        if footer:
            embed.set_footer(text=footer)
                
        return embed
    
    @staticmethod
    def info(title, description=None, footer=None, fields=None, thumbnail=None):
        """Create an info embed"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=EmbedGenerator.get_color("info"),
            timestamp=datetime.datetime.utcnow()
        )
        
        if footer:
            embed.set_footer(text=footer)
            
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
            
        if fields:
            for field in fields:
                embed.add_field(
                    name=field["name"],
                    value=field["value"],
                    inline=field.get("inline", False)
                )
                
        return embed
    
    @staticmethod
    def moderation(title, description=None, footer=None, fields=None, thumbnail=None):
        """Create a moderation embed"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=EmbedGenerator.get_color("moderation"),
            timestamp=datetime.datetime.utcnow()
        )
        
        if footer:
            embed.set_footer(text=footer)
            
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
            
        if fields:
            for field in fields:
                embed.add_field(
                    name=field["name"],
                    value=field["value"],
                    inline=field.get("inline", False)
                )
                
        return embed
    
    @staticmethod
    def help_command(command, description, usage, examples, category):
        """Create a help embed for a command"""
        embed = discord.Embed(
            title=f"Command: {command}",
            description=description,
            color=EmbedGenerator.get_color("main"),
            timestamp=datetime.datetime.utcnow()
        )
        
        embed.add_field(name="Usage", value=f"```{usage}```", inline=False)
        
        if examples:
            embed.add_field(name="Examples", value=examples, inline=False)
            
        embed.add_field(name="Category", value=category, inline=True)
        
        embed.set_footer(text="<> = required, () = optional")
        
        return embed
    
    @staticmethod
    def help_category(category, commands, prefix):
        """Create a help embed for a category"""
        embed = discord.Embed(
            title=f"{category.capitalize()} Commands",
            color=EmbedGenerator.get_color("main"),
            timestamp=datetime.datetime.utcnow()
        )
        
        for cmd in commands:
            embed.add_field(
                name=f"{prefix}{cmd['name']}",
                value=cmd['description'],
                inline=False
            )
            
        embed.set_footer(text=f"Use {prefix}help [command] for more information about a command")
        
        return embed
    
    @staticmethod
    def help_main(categories, prefix):
        """Create the main help embed"""
        embed = discord.Embed(
            title="Discord Bot Help",
            description=f"Use `{prefix}help [category]` or `{prefix}help [command]` for more information",
            color=EmbedGenerator.get_color("main"),
            timestamp=datetime.datetime.utcnow()
        )
        
        for category, cmds in categories.items():
            cmd_list = ", ".join([f"`{prefix}{cmd['name']}`" for cmd in cmds[:5]])
            
            if len(cmds) > 5:
                cmd_list += f" and {len(cmds) - 5} more..."
                
            embed.add_field(
                name=f"{category.capitalize()} Commands",
                value=cmd_list,
                inline=False
            )
            
        embed.set_footer(text=f"Use {prefix}help [category] to see all commands in a category")
        
        return embed
    
    @staticmethod
    def mod_case(case, guild, moderator, user):
        """Create an embed for a moderation case"""
        # Format timestamps
        timestamp = datetime.datetime.fromtimestamp(case['timestamp'])
        formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Format duration if present
        duration_text = ""
        if case['duration']:
            duration_seconds = case['duration']
            if duration_seconds < 60:
                duration_text = f"{duration_seconds} seconds"
            elif duration_seconds < 3600:
                duration_text = f"{duration_seconds // 60} minutes"
            elif duration_seconds < 86400:
                duration_text = f"{duration_seconds // 3600} hours"
            else:
                duration_text = f"{duration_seconds // 86400} days"
        
        # Create embed
        embed = discord.Embed(
            title=f"Case #{case['case_id']} | {case['action'].capitalize()}",
            color=EmbedGenerator.get_color("moderation"),
            timestamp=datetime.datetime.utcnow()
        )
        
        # Add user information
        user_text = f"{user.mention} ({user.name})"
        embed.add_field(name="User", value=user_text, inline=True)
        
        # Add moderator information
        mod_text = f"{moderator.mention} ({moderator.name})"
        embed.add_field(name="Moderator", value=mod_text, inline=True)
        
        # Add server information
        embed.add_field(name="Server", value=guild.name, inline=True)
        
        # Add reason
        reason = case['reason'] if case['reason'] else "No reason provided"
        embed.add_field(name="Reason", value=reason, inline=False)
        
        # Add duration if present
        if duration_text:
            embed.add_field(name="Duration", value=duration_text, inline=True)
            
        # Add timestamp
        embed.add_field(name="Timestamp", value=formatted_time, inline=True)
        
        # Set footer
        embed.set_footer(text=f"Case ID: {case['case_id']}")
        
        return embed
    
    @staticmethod
    def user_info(user, member=None, mod_cases=None, notes=None):
        """Create an embed with user information"""
        embed = discord.Embed(
            title=f"User Information: {user.name}",
            color=EmbedGenerator.get_color("info"),
            timestamp=datetime.datetime.utcnow()
        )
        
        # Set user avatar as thumbnail
        embed.set_thumbnail(url=user.display_avatar.url)
        
        # Add user ID
        embed.add_field(name="User ID", value=user.id, inline=True)
        
        # Add account creation date
        created_at = int(user.created_at.timestamp())
        embed.add_field(name="Account Created", value=f"<t:{created_at}:R>", inline=True)
        
        # Add server-specific information if member is provided
        if member:
            joined_at = int(member.joined_at.timestamp()) if member.joined_at else None
            embed.add_field(name="Joined Server", value=f"<t:{joined_at}:R>" if joined_at else "Unknown", inline=True)
            
            roles = [role.mention for role in member.roles if role.name != "@everyone"]
            if roles:
                embed.add_field(name=f"Roles [{len(roles)}]", value=" ".join(roles[:10]) + ("..." if len(roles) > 10 else ""), inline=False)
            
            if member.nick:
                embed.add_field(name="Nickname", value=member.nick, inline=True)
        
        # Add moderation cases if provided
        if mod_cases:
            case_count = len(mod_cases)
            recent_cases = []
            
            for case in mod_cases[:3]:
                action = case['action'].capitalize()
                case_id = case['case_id']
                reason = case['reason'] if case['reason'] else "No reason provided"
                
                if len(reason) > 50:
                    reason = reason[:50] + "..."
                    
                recent_cases.append(f"**#{case_id}** | {action}: {reason}")
            
            if recent_cases:
                embed.add_field(name=f"Recent Cases ({case_count} total)", value="\n".join(recent_cases), inline=False)
        
        # Add notes if provided
        if notes:
            note_count = len(notes)
            recent_notes = []
            
            for note in notes[:3]:
                note_text = note['note']
                
                if len(note_text) > 50:
                    note_text = note_text[:50] + "..."
                    
                timestamp = datetime.datetime.fromtimestamp(note['timestamp']).strftime("%Y-%m-%d")
                recent_notes.append(f"**{timestamp}**: {note_text}")
            
            if recent_notes:
                embed.add_field(name=f"Recent Notes ({note_count} total)", value="\n".join(recent_notes), inline=False)
        
        return embed
    
    @staticmethod
    def command_list(commands, prefix):
        """Create an embed with a list of commands"""
        embed = discord.Embed(
            title="Command List",
            description=f"Here are all the available commands. Use `{prefix}help [command]` for more information.",
            color=EmbedGenerator.get_color("main"),
            timestamp=datetime.datetime.utcnow()
        )
        
        for category, cmds in commands.items():
            value = ", ".join([f"`{cmd['name']}`" for cmd in cmds])
            embed.add_field(name=f"{category.capitalize()} Commands", value=value, inline=False)
            
        embed.set_footer(text=f"Prefix: {prefix}")
        
        return embed
