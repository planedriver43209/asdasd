import aiosqlite
import logging
import json
from datetime import datetime

logger = logging.getLogger('discord_bot.database')

class Database:
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = None
    
    async def connect(self):
        """Connect to the SQLite database"""
        try:
            self.conn = await aiosqlite.connect(self.db_name)
            self.conn.row_factory = aiosqlite.Row
            await self._create_tables()
            logger.info(f"Connected to database: {self.db_name}")
            return self
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            raise
    
    async def close(self):
        """Close the database connection"""
        if self.conn:
            await self.conn.close()
            logger.info("Database connection closed")
    
    async def _create_tables(self):
        """Create necessary tables if they don't exist"""
        async with self.conn.cursor() as cursor:
            # Guild settings table
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id INTEGER PRIMARY KEY,
                    prefix TEXT,
                    mod_roles TEXT,
                    ignored_channels TEXT,
                    ignored_roles TEXT,
                    ignored_users TEXT,
                    modules TEXT
                )
            ''')
            
            # Moderation cases table
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS mod_cases (
                    case_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    moderator_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    reason TEXT,
                    timestamp INTEGER NOT NULL,
                    duration INTEGER,
                    active BOOLEAN DEFAULT 0
                )
            ''')
            
            # User notes table
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    moderator_id INTEGER NOT NULL,
                    note TEXT NOT NULL,
                    timestamp INTEGER NOT NULL
                )
            ''')
            
            # Role persistence table
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS role_persistence (
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    role_id INTEGER NOT NULL,
                    added_by INTEGER NOT NULL,
                    reason TEXT,
                    timestamp INTEGER NOT NULL,
                    PRIMARY KEY (guild_id, user_id, role_id)
                )
            ''')
            
            # Giveaways table
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS giveaways (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    creator_id INTEGER NOT NULL,
                    prize TEXT NOT NULL,
                    winners INTEGER NOT NULL,
                    end_time INTEGER NOT NULL,
                    ended BOOLEAN DEFAULT 0
                )
            ''')
            
            # Custom commands table
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS custom_commands (
                    guild_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    response TEXT NOT NULL,
                    creator_id INTEGER NOT NULL,
                    created_at INTEGER NOT NULL,
                    PRIMARY KEY (guild_id, name)
                )
            ''')
            
            await self.conn.commit()
    
    # Guild settings methods
    
    async def get_guild_prefix(self, guild_id):
        """Get custom prefix for a guild"""
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                "SELECT prefix FROM guild_settings WHERE guild_id = ?", 
                (guild_id,)
            )
            result = await cursor.fetchone()
            return result['prefix'] if result else None
    
    async def set_guild_prefix(self, guild_id, prefix):
        """Set custom prefix for a guild"""
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO guild_settings (guild_id, prefix) 
                VALUES (?, ?) 
                ON CONFLICT(guild_id) DO UPDATE SET prefix = ?
                """, 
                (guild_id, prefix, prefix)
            )
            await self.conn.commit()
    
    async def get_mod_roles(self, guild_id):
        """Get moderator roles for a guild"""
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                "SELECT mod_roles FROM guild_settings WHERE guild_id = ?", 
                (guild_id,)
            )
            result = await cursor.fetchone()
            
            if result and result['mod_roles']:
                return json.loads(result['mod_roles'])
            return []
    
    async def add_mod_role(self, guild_id, role_id):
        """Add a moderator role to a guild"""
        current_roles = await self.get_mod_roles(guild_id)
        
        if role_id in current_roles:
            return False
            
        current_roles.append(role_id)
        
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO guild_settings (guild_id, mod_roles) 
                VALUES (?, ?) 
                ON CONFLICT(guild_id) DO UPDATE SET mod_roles = ?
                """, 
                (guild_id, json.dumps(current_roles), json.dumps(current_roles))
            )
            await self.conn.commit()
            return True
    
    async def remove_mod_role(self, guild_id, role_id):
        """Remove a moderator role from a guild"""
        current_roles = await self.get_mod_roles(guild_id)
        
        if role_id not in current_roles:
            return False
            
        current_roles.remove(role_id)
        
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                UPDATE guild_settings SET mod_roles = ?
                WHERE guild_id = ?
                """, 
                (json.dumps(current_roles), guild_id)
            )
            await self.conn.commit()
            return True
    
    # Ignored channels, roles, users methods
    
    async def get_ignored_channels(self, guild_id):
        """Get ignored channels for a guild"""
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                "SELECT ignored_channels FROM guild_settings WHERE guild_id = ?", 
                (guild_id,)
            )
            result = await cursor.fetchone()
            
            if result and result['ignored_channels']:
                return json.loads(result['ignored_channels'])
            return []
    
    async def add_ignored_channel(self, guild_id, channel_id):
        """Add an ignored channel to a guild"""
        current_channels = await self.get_ignored_channels(guild_id)
        
        if channel_id in current_channels:
            return False
            
        current_channels.append(channel_id)
        
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO guild_settings (guild_id, ignored_channels) 
                VALUES (?, ?) 
                ON CONFLICT(guild_id) DO UPDATE SET ignored_channels = ?
                """, 
                (guild_id, json.dumps(current_channels), json.dumps(current_channels))
            )
            await self.conn.commit()
            return True
    
    async def remove_ignored_channel(self, guild_id, channel_id):
        """Remove an ignored channel from a guild"""
        current_channels = await self.get_ignored_channels(guild_id)
        
        if channel_id not in current_channels:
            return False
            
        current_channels.remove(channel_id)
        
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                UPDATE guild_settings SET ignored_channels = ?
                WHERE guild_id = ?
                """, 
                (json.dumps(current_channels), guild_id)
            )
            await self.conn.commit()
            return True
    
    async def get_ignored_roles(self, guild_id):
        """Get ignored roles for a guild"""
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                "SELECT ignored_roles FROM guild_settings WHERE guild_id = ?", 
                (guild_id,)
            )
            result = await cursor.fetchone()
            
            if result and result['ignored_roles']:
                return json.loads(result['ignored_roles'])
            return []
    
    async def add_ignored_role(self, guild_id, role_id):
        """Add an ignored role to a guild"""
        current_roles = await self.get_ignored_roles(guild_id)
        
        if role_id in current_roles:
            return False
            
        current_roles.append(role_id)
        
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO guild_settings (guild_id, ignored_roles) 
                VALUES (?, ?) 
                ON CONFLICT(guild_id) DO UPDATE SET ignored_roles = ?
                """, 
                (guild_id, json.dumps(current_roles), json.dumps(current_roles))
            )
            await self.conn.commit()
            return True
    
    async def remove_ignored_role(self, guild_id, role_id):
        """Remove an ignored role from a guild"""
        current_roles = await self.get_ignored_roles(guild_id)
        
        if role_id not in current_roles:
            return False
            
        current_roles.remove(role_id)
        
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                UPDATE guild_settings SET ignored_roles = ?
                WHERE guild_id = ?
                """, 
                (json.dumps(current_roles), guild_id)
            )
            await self.conn.commit()
            return True
    
    async def get_ignored_users(self, guild_id):
        """Get ignored users for a guild"""
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                "SELECT ignored_users FROM guild_settings WHERE guild_id = ?", 
                (guild_id,)
            )
            result = await cursor.fetchone()
            
            if result and result['ignored_users']:
                return json.loads(result['ignored_users'])
            return []
    
    async def add_ignored_user(self, guild_id, user_id, reason=None):
        """Add an ignored user to a guild"""
        current_users = await self.get_ignored_users(guild_id)
        
        # Check if user is already ignored
        for user in current_users:
            if user['id'] == user_id:
                return False
        
        # Add user with reason
        current_users.append({
            'id': user_id,
            'reason': reason,
            'timestamp': datetime.utcnow().timestamp()
        })
        
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO guild_settings (guild_id, ignored_users) 
                VALUES (?, ?) 
                ON CONFLICT(guild_id) DO UPDATE SET ignored_users = ?
                """, 
                (guild_id, json.dumps(current_users), json.dumps(current_users))
            )
            await self.conn.commit()
            return True
    
    async def remove_ignored_user(self, guild_id, user_id):
        """Remove an ignored user from a guild"""
        current_users = await self.get_ignored_users(guild_id)
        
        # Find user to remove
        user_found = False
        for i, user in enumerate(current_users):
            if user['id'] == user_id:
                current_users.pop(i)
                user_found = True
                break
        
        if not user_found:
            return False
        
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                UPDATE guild_settings SET ignored_users = ?
                WHERE guild_id = ?
                """, 
                (json.dumps(current_users), guild_id)
            )
            await self.conn.commit()
            return True
    
    # Module settings
    
    async def get_modules(self, guild_id):
        """Get enabled/disabled modules for a guild"""
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                "SELECT modules FROM guild_settings WHERE guild_id = ?", 
                (guild_id,)
            )
            result = await cursor.fetchone()
            
            if result and result['modules']:
                return json.loads(result['modules'])
            
            # Default modules all enabled
            default_modules = {
                "moderation": True,
                "utility": True,
                "fun": True
            }
            return default_modules
    
    async def toggle_module(self, guild_id, module_name):
        """Toggle a module on/off for a guild"""
        current_modules = await self.get_modules(guild_id)
        
        if module_name not in current_modules:
            return False
        
        # Toggle the module
        current_modules[module_name] = not current_modules[module_name]
        
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO guild_settings (guild_id, modules) 
                VALUES (?, ?) 
                ON CONFLICT(guild_id) DO UPDATE SET modules = ?
                """, 
                (guild_id, json.dumps(current_modules), json.dumps(current_modules))
            )
            await self.conn.commit()
            return True
    
    # Moderation cases
    
    async def create_mod_case(self, guild_id, user_id, moderator_id, action, reason=None, duration=None):
        """Create a new moderation case"""
        timestamp = int(datetime.utcnow().timestamp())
        active = 1 if action in ['ban', 'mute', 'lock', 'timeout'] and duration else 0
        
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO mod_cases 
                (guild_id, user_id, moderator_id, action, reason, timestamp, duration, active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, 
                (guild_id, user_id, moderator_id, action, reason, timestamp, duration, active)
            )
            await self.conn.commit()
            
            # Get the last inserted case ID
            await cursor.execute("SELECT last_insert_rowid()")
            case_id = await cursor.fetchone()
            return case_id[0]
    
    async def get_case(self, case_id):
        """Get a moderation case by ID"""
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM mod_cases WHERE case_id = ?", 
                (case_id,)
            )
            return await cursor.fetchone()
    
    async def update_case_reason(self, case_id, reason):
        """Update the reason for a moderation case"""
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                "UPDATE mod_cases SET reason = ? WHERE case_id = ?", 
                (reason, case_id)
            )
            await self.conn.commit()
            return await cursor.rowcount > 0
    
    async def update_case_duration(self, case_id, duration):
        """Update the duration for a moderation case"""
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                "UPDATE mod_cases SET duration = ? WHERE case_id = ?", 
                (duration, case_id)
            )
            await self.conn.commit()
            return await cursor.rowcount > 0
    
    async def set_case_inactive(self, case_id):
        """Set a moderation case as inactive"""
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                "UPDATE mod_cases SET active = 0 WHERE case_id = ?", 
                (case_id,)
            )
            await self.conn.commit()
            return await cursor.rowcount > 0
    
    async def get_user_cases(self, guild_id, user_id, limit=10, offset=0):
        """Get moderation cases for a user in a guild"""
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                SELECT * FROM mod_cases 
                WHERE guild_id = ? AND user_id = ? 
                ORDER BY case_id DESC LIMIT ? OFFSET ?
                """, 
                (guild_id, user_id, limit, offset)
            )
            return await cursor.fetchall()
    
    async def get_active_cases(self, guild_id):
        """Get all active moderation cases in a guild"""
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM mod_cases WHERE guild_id = ? AND active = 1", 
                (guild_id,)
            )
            return await cursor.fetchall()
    
    async def count_user_cases(self, guild_id, user_id):
        """Count total moderation cases for a user in a guild"""
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                "SELECT COUNT(*) FROM mod_cases WHERE guild_id = ? AND user_id = ?", 
                (guild_id, user_id)
            )
            result = await cursor.fetchone()
            return result[0] if result else 0
    
    # User notes
    
    async def add_note(self, guild_id, user_id, moderator_id, note):
        """Add a note to a user"""
        timestamp = int(datetime.utcnow().timestamp())
        
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO user_notes 
                (guild_id, user_id, moderator_id, note, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """, 
                (guild_id, user_id, moderator_id, note, timestamp)
            )
            await self.conn.commit()
            
            # Get the last inserted note ID
            await cursor.execute("SELECT last_insert_rowid()")
            note_id = await cursor.fetchone()
            return note_id[0]
    
    async def get_notes(self, guild_id, user_id):
        """Get all notes for a user in a guild"""
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                SELECT * FROM user_notes 
                WHERE guild_id = ? AND user_id = ? 
                ORDER BY timestamp DESC
                """, 
                (guild_id, user_id)
            )
            return await cursor.fetchall()
    
    async def get_note(self, note_id):
        """Get a specific note by ID"""
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM user_notes WHERE id = ?", 
                (note_id,)
            )
            return await cursor.fetchone()
    
    async def edit_note(self, note_id, new_note):
        """Edit a user note"""
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                "UPDATE user_notes SET note = ? WHERE id = ?", 
                (new_note, note_id)
            )
            await self.conn.commit()
            return await cursor.rowcount > 0
    
    async def delete_note(self, note_id):
        """Delete a user note"""
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                "DELETE FROM user_notes WHERE id = ?", 
                (note_id,)
            )
            await self.conn.commit()
            return await cursor.rowcount > 0
    
    async def clear_notes(self, guild_id, user_id):
        """Clear all notes for a user in a guild"""
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                "DELETE FROM user_notes WHERE guild_id = ? AND user_id = ?", 
                (guild_id, user_id)
            )
            await self.conn.commit()
            return await cursor.rowcount
    
    # Role persistence
    
    async def add_persisted_role(self, guild_id, user_id, role_id, added_by, reason=None):
        """Add a persisted role for a user"""
        timestamp = int(datetime.utcnow().timestamp())
        
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                INSERT OR REPLACE INTO role_persistence 
                (guild_id, user_id, role_id, added_by, reason, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                """, 
                (guild_id, user_id, role_id, added_by, reason, timestamp)
            )
            await self.conn.commit()
            return True
    
    async def remove_persisted_role(self, guild_id, user_id, role_id):
        """Remove a persisted role for a user"""
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                DELETE FROM role_persistence 
                WHERE guild_id = ? AND user_id = ? AND role_id = ?
                """, 
                (guild_id, user_id, role_id)
            )
            await self.conn.commit()
            return await cursor.rowcount > 0
    
    async def get_persisted_roles(self, guild_id, user_id):
        """Get all persisted roles for a user in a guild"""
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                SELECT * FROM role_persistence 
                WHERE guild_id = ? AND user_id = ?
                """, 
                (guild_id, user_id)
            )
            return await cursor.fetchall()
    
    # Custom commands
    
    async def add_custom_command(self, guild_id, name, response, creator_id):
        """Add a custom command to a guild"""
        timestamp = int(datetime.utcnow().timestamp())
        
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                INSERT OR REPLACE INTO custom_commands 
                (guild_id, name, response, creator_id, created_at)
                VALUES (?, ?, ?, ?, ?)
                """, 
                (guild_id, name.lower(), response, creator_id, timestamp)
            )
            await self.conn.commit()
            return True
    
    async def remove_custom_command(self, guild_id, name):
        """Remove a custom command from a guild"""
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                DELETE FROM custom_commands 
                WHERE guild_id = ? AND name = ?
                """, 
                (guild_id, name.lower())
            )
            await self.conn.commit()
            return await cursor.rowcount > 0
    
    async def get_custom_command(self, guild_id, name):
        """Get a custom command from a guild"""
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                SELECT * FROM custom_commands 
                WHERE guild_id = ? AND name = ?
                """, 
                (guild_id, name.lower())
            )
            return await cursor.fetchone()
    
    async def get_all_custom_commands(self, guild_id):
        """Get all custom commands for a guild"""
        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                SELECT * FROM custom_commands 
                WHERE guild_id = ?
                ORDER BY name
                """, 
                (guild_id,)
            )
            return await cursor.fetchall()

async def setup_database():
    """Setup and initialize the database"""
    from config import Config
    
    config = Config()
    db = Database(config.DATABASE_NAME)
    return await db.connect()
