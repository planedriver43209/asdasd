import discord
from discord.ext import commands

class PermissionChecker:
    """Class for checking user permissions in a guild"""
    
    @staticmethod
    async def is_mod(ctx, db):
        """Check if a user is a moderator"""
        # Server owner is always a mod
        if ctx.author.id == ctx.guild.owner_id:
            return True
            
        # Check if user has admin permissions
        if ctx.author.guild_permissions.administrator:
            return True
            
        # Check if user has ban permissions
        if ctx.author.guild_permissions.ban_members:
            return True
            
        # Check if user has mod role
        mod_roles = await db.get_mod_roles(ctx.guild.id)
        return any(role.id in mod_roles for role in ctx.author.roles)
    
    @staticmethod
    async def is_admin(ctx):
        """Check if a user is an admin"""
        # Server owner is always an admin
        if ctx.author.id == ctx.guild.owner_id:
            return True
            
        # Check if user has admin permissions
        return ctx.author.guild_permissions.administrator
    
    @staticmethod
    async def check_hierarchy(ctx, target):
        """Check if the bot and user have permission to modify the target"""
        # Can't modify the owner
        if target.id == ctx.guild.owner_id:
            return False
            
        # Check bot's hierarchy
        if ctx.guild.me.top_role <= target.top_role:
            return False
            
        # Check user's hierarchy (unless they're the owner)
        if ctx.author.id != ctx.guild.owner_id and ctx.author.top_role <= target.top_role:
            return False
            
        return True
    
    @staticmethod
    async def is_ignored(ctx, db):
        """Check if a channel, role, or user is ignored"""
        # DMs are never ignored
        if not ctx.guild:
            return False
            
        # Check if channel is ignored
        ignored_channels = await db.get_ignored_channels(ctx.guild.id)
        if ctx.channel.id in ignored_channels:
            return True
            
        # Check if user is ignored
        ignored_users = await db.get_ignored_users(ctx.guild.id)
        if any(user['id'] == ctx.author.id for user in ignored_users):
            return True
            
        # Check if any of the user's roles are ignored
        ignored_roles = await db.get_ignored_roles(ctx.guild.id)
        return any(role.id in ignored_roles for role in ctx.author.roles)
    
    @staticmethod
    async def check_module_enabled(ctx, db, module):
        """Check if a module is enabled in the guild"""
        modules = await db.get_modules(ctx.guild.id)
        return modules.get(module, True)
    
    @staticmethod
    def mod_or_permissions(**perms):
        """Check if user is a mod or has specific permissions"""
        async def predicate(ctx):
            # DMs always pass permission checks
            if ctx.guild is None:
                return True
                
            # Check if user is a mod
            if await PermissionChecker.is_mod(ctx, ctx.bot.db):
                return True
                
            # Check for specific permissions
            permissions = ctx.channel.permissions_for(ctx.author)
            return any(getattr(permissions, perm, None) == value for perm, value in perms.items())
            
        return commands.check(predicate)
    
    @staticmethod
    def admin_or_permissions(**perms):
        """Check if user is an admin or has specific permissions"""
        async def predicate(ctx):
            # DMs always pass permission checks
            if ctx.guild is None:
                return True
                
            # Check if user is an admin
            if await PermissionChecker.is_admin(ctx):
                return True
                
            # Check for specific permissions
            permissions = ctx.channel.permissions_for(ctx.author)
            return any(getattr(permissions, perm, None) == value for perm, value in perms.items())
            
        return commands.check(predicate)
    
    @staticmethod
    def bot_has_permissions(**perms):
        """Check if the bot has specific permissions"""
        async def predicate(ctx):
            # DMs always pass permission checks
            if ctx.guild is None:
                return True
                
            # Check for specific permissions
            permissions = ctx.channel.permissions_for(ctx.guild.me)
            missing = [perm for perm, value in perms.items() if getattr(permissions, perm, None) != value]
            
            if not missing:
                return True
                
            # If permissions are missing, let the user know
            raise commands.BotMissingPermissions(missing)
            
        return commands.check(predicate)
