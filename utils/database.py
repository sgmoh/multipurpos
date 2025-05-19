import json
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger('discord_bot')

class JsonDatabase:
    """Simple JSON file-based database for storing bot data"""
    
    def __init__(self):
        """Initialize the database"""
        self.data = {
            'autoroles': {},
            'levels': {},
            'tickets': {},
            'invites': {},
            'message_counts': {},
            'reaction_roles': {},
            'giveaways': {}
        }
        self.db_file = 'bot_database.json'
        self._load_data()
    
    def _load_data(self):
        """Load data from the JSON file"""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f:
                    self.data = json.load(f)
                logger.info(f"Database loaded from {self.db_file}")
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON from {self.db_file}, using default data")
            except Exception as e:
                logger.error(f"Error loading database: {e}")
        else:
            logger.info(f"Database file {self.db_file} not found, creating new database")
            self._save_data()
    
    def _save_data(self):
        """Save data to the JSON file"""
        try:
            with open(self.db_file, 'w') as f:
                json.dump(self.data, f, indent=4)
            logger.info(f"Database saved to {self.db_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving database: {e}")
            return False
    
    # Autorole methods
    def set_autorole(self, guild_id, role_id):
        """Set an autorole for a guild"""
        guild_id = str(guild_id)
        if 'autoroles' not in self.data:
            self.data['autoroles'] = {}
        self.data['autoroles'][guild_id] = role_id
        return self._save_data()
    
    def get_autorole(self, guild_id):
        """Get the autorole for a guild"""
        guild_id = str(guild_id)
        return self.data.get('autoroles', {}).get(guild_id)
    
    def remove_autorole(self, guild_id):
        """Remove the autorole for a guild"""
        guild_id = str(guild_id)
        if guild_id in self.data.get('autoroles', {}):
            del self.data['autoroles'][guild_id]
            return self._save_data()
        return False
    
    # Levels methods
    def get_user_level(self, guild_id, user_id):
        """Get a user's level and XP"""
        guild_id, user_id = str(guild_id), str(user_id)
        guild_levels = self.data.get('levels', {}).get(guild_id, {})
        user_data = guild_levels.get(user_id, {'level': 0, 'xp': 0})
        return user_data
    
    def add_user_xp(self, guild_id, user_id, xp_to_add=1):
        """Add XP to a user and return whether they leveled up"""
        guild_id, user_id = str(guild_id), str(user_id)
        
        if 'levels' not in self.data:
            self.data['levels'] = {}
        if guild_id not in self.data['levels']:
            self.data['levels'][guild_id] = {}
        if user_id not in self.data['levels'][guild_id]:
            self.data['levels'][guild_id][user_id] = {'level': 0, 'xp': 0}
        
        user_data = self.data['levels'][guild_id][user_id]
        old_level = user_data['level']
        user_data['xp'] += xp_to_add
        
        # Calculate new level
        # Simple level formula: level = xp // 100
        new_level = user_data['xp'] // 100
        user_data['level'] = new_level
        
        self._save_data()
        
        # Return True if user leveled up
        return new_level > old_level
    
    def get_level_leaderboard(self, guild_id, limit=10):
        """Get the level leaderboard for a guild"""
        guild_id = str(guild_id)
        guild_levels = self.data.get('levels', {}).get(guild_id, {})
        
        # Sort users by level and then by XP
        sorted_users = sorted(
            guild_levels.items(),
            key=lambda x: (x[1]['level'], x[1]['xp']),
            reverse=True
        )
        
        return sorted_users[:limit]
    
    # Ticket methods
    def create_ticket(self, guild_id, channel_id, user_id):
        """Create a new ticket"""
        guild_id, channel_id, user_id = str(guild_id), str(channel_id), str(user_id)
        
        if 'tickets' not in self.data:
            self.data['tickets'] = {}
        if guild_id not in self.data['tickets']:
            self.data['tickets'][guild_id] = {}
        
        self.data['tickets'][guild_id][channel_id] = {
            'user_id': user_id,
            'created_at': datetime.now().isoformat(),
            'status': 'open'
        }
        
        return self._save_data()
    
    def close_ticket(self, guild_id, channel_id):
        """Close a ticket"""
        guild_id, channel_id = str(guild_id), str(channel_id)
        
        if channel_id in self.data.get('tickets', {}).get(guild_id, {}):
            self.data['tickets'][guild_id][channel_id]['status'] = 'closed'
            self.data['tickets'][guild_id][channel_id]['closed_at'] = datetime.now().isoformat()
            return self._save_data()
        
        return False
    
    def get_ticket(self, guild_id, channel_id):
        """Get ticket information"""
        guild_id, channel_id = str(guild_id), str(channel_id)
        return self.data.get('tickets', {}).get(guild_id, {}).get(channel_id)
    
    # Invite methods
    def track_invite(self, guild_id, inviter_id, invitee_id, is_fake=False, is_rejoin=False):
        """Track an invite"""
        guild_id, inviter_id, invitee_id = str(guild_id), str(inviter_id), str(invitee_id)
        
        if 'invites' not in self.data:
            self.data['invites'] = {}
        if guild_id not in self.data['invites']:
            self.data['invites'][guild_id] = {}
        if inviter_id not in self.data['invites'][guild_id]:
            self.data['invites'][guild_id][inviter_id] = {
                'joins': 0,
                'left': 0,
                'fake': 0,
                'rejoins': 0,
                'invitees': []
            }
        
        inviter_data = self.data['invites'][guild_id][inviter_id]
        
        # Track the invite
        inviter_data['joins'] += 1
        
        if is_fake:
            inviter_data['fake'] += 1
        
        if is_rejoin:
            inviter_data['rejoins'] += 1
        
        # Add the invitee to the list
        inviter_data['invitees'].append({
            'user_id': invitee_id,
            'joined_at': datetime.now().isoformat(),
            'is_fake': is_fake,
            'is_rejoin': is_rejoin
        })
        
        return self._save_data()
    
    def track_leave(self, guild_id, user_id):
        """Track a user leaving"""
        guild_id, user_id = str(guild_id), str(user_id)
        
        # Find which inviter invited this user
        for inviter_id, inviter_data in self.data.get('invites', {}).get(guild_id, {}).items():
            for invitee in inviter_data.get('invitees', []):
                if invitee['user_id'] == user_id:
                    # Found the inviter, increment left count
                    self.data['invites'][guild_id][inviter_id]['left'] += 1
                    return self._save_data()
        
        return False
    
    def get_invite_stats(self, guild_id, user_id):
        """Get invite statistics for a user"""
        guild_id, user_id = str(guild_id), str(user_id)
        
        inviter_data = self.data.get('invites', {}).get(guild_id, {}).get(user_id, {
            'joins': 0,
            'left': 0,
            'fake': 0,
            'rejoins': 0,
            'invitees': []
        })
        
        # Calculate total invites (real invites only)
        total_invites = inviter_data['joins'] - inviter_data['left'] - inviter_data['fake']
        if total_invites < 0:
            total_invites = 0
        
        return {
            'total': total_invites,
            'joins': inviter_data['joins'],
            'left': inviter_data['left'],
            'fake': inviter_data['fake'],
            'rejoins': inviter_data['rejoins']
        }
    
    def get_invite_leaderboard(self, guild_id, limit=10):
        """Get the invite leaderboard for a guild"""
        guild_id = str(guild_id)
        guild_invites = self.data.get('invites', {}).get(guild_id, {})
        
        # Calculate total invites for each user
        leaderboard = []
        for user_id, data in guild_invites.items():
            total = data['joins'] - data['left'] - data['fake']
            if total < 0:
                total = 0
            leaderboard.append({
                'user_id': user_id,
                'total': total
            })
        
        # Sort by total invites
        leaderboard.sort(key=lambda x: x['total'], reverse=True)
        
        return leaderboard[:limit]
    
    # Message tracking methods
    def increment_message_count(self, guild_id, user_id):
        """Increment message count for a user"""
        guild_id, user_id = str(guild_id), str(user_id)
        
        if 'message_counts' not in self.data:
            self.data['message_counts'] = {}
        if guild_id not in self.data['message_counts']:
            self.data['message_counts'][guild_id] = {}
        if user_id not in self.data['message_counts'][guild_id]:
            self.data['message_counts'][guild_id][user_id] = {
                'all_time': 0,
                'daily': {},
            }
        
        # Increment all-time counter
        self.data['message_counts'][guild_id][user_id]['all_time'] += 1
        
        # Increment today's counter
        today = datetime.now().strftime("%Y-%m-%d")
        if 'daily' not in self.data['message_counts'][guild_id][user_id]:
            self.data['message_counts'][guild_id][user_id]['daily'] = {}
        
        if today not in self.data['message_counts'][guild_id][user_id]['daily']:
            self.data['message_counts'][guild_id][user_id]['daily'][today] = 0
        
        self.data['message_counts'][guild_id][user_id]['daily'][today] += 1
        
        return self._save_data()
    
    def get_message_stats(self, guild_id, user_id):
        """Get message statistics for a user"""
        guild_id, user_id = str(guild_id), str(user_id)
        
        user_data = self.data.get('message_counts', {}).get(guild_id, {}).get(user_id, {
            'all_time': 0,
            'daily': {}
        })
        
        today = datetime.now().strftime("%Y-%m-%d")
        today_count = user_data.get('daily', {}).get(today, 0)
        
        return {
            'all_time': user_data.get('all_time', 0),
            'today': today_count
        }
    
    def get_message_leaderboard(self, guild_id, limit=10, period='all_time'):
        """Get the message leaderboard for a guild"""
        guild_id = str(guild_id)
        guild_messages = self.data.get('message_counts', {}).get(guild_id, {})
        
        leaderboard = []
        
        if period == 'all_time':
            # Get all-time message counts
            for user_id, data in guild_messages.items():
                leaderboard.append({
                    'user_id': user_id,
                    'count': data.get('all_time', 0)
                })
        elif period == 'today':
            # Get today's message counts
            today = datetime.now().strftime("%Y-%m-%d")
            for user_id, data in guild_messages.items():
                count = data.get('daily', {}).get(today, 0)
                leaderboard.append({
                    'user_id': user_id,
                    'count': count
                })
        
        # Sort by message count
        leaderboard.sort(key=lambda x: x['count'], reverse=True)
        
        return leaderboard[:limit]
    
    # Reaction roles methods
    def set_reaction_role(self, guild_id, message_id, role_id, emoji):
        """Set a reaction role"""
        guild_id, message_id = str(guild_id), str(message_id)
        
        if 'reaction_roles' not in self.data:
            self.data['reaction_roles'] = {}
        if guild_id not in self.data['reaction_roles']:
            self.data['reaction_roles'][guild_id] = {}
        if message_id not in self.data['reaction_roles'][guild_id]:
            self.data['reaction_roles'][guild_id][message_id] = []
        
        # Check if role already exists for this emoji
        for i, role in enumerate(self.data['reaction_roles'][guild_id][message_id]):
            if role['emoji'] == emoji:
                # Update existing role
                self.data['reaction_roles'][guild_id][message_id][i]['role_id'] = role_id
                return self._save_data()
        
        # Add new role
        self.data['reaction_roles'][guild_id][message_id].append({
            'role_id': role_id,
            'emoji': emoji
        })
        
        return self._save_data()
    
    def get_reaction_roles(self, guild_id, message_id):
        """Get reaction roles for a message"""
        guild_id, message_id = str(guild_id), str(message_id)
        return self.data.get('reaction_roles', {}).get(guild_id, {}).get(message_id, [])
    
    def remove_reaction_role(self, guild_id, message_id, emoji):
        """Remove a reaction role"""
        guild_id, message_id = str(guild_id), str(message_id)
        
        if message_id in self.data.get('reaction_roles', {}).get(guild_id, {}):
            roles = self.data['reaction_roles'][guild_id][message_id]
            for i, role in enumerate(roles):
                if role['emoji'] == emoji:
                    del self.data['reaction_roles'][guild_id][message_id][i]
                    return self._save_data()
        
        return False
    
    # Giveaway methods
    def create_giveaway(self, guild_id, channel_id, message_id, prize, host_id, end_time, winners=1):
        """Create a new giveaway"""
        guild_id, channel_id, message_id = str(guild_id), str(channel_id), str(message_id)
        host_id = str(host_id)
        
        if 'giveaways' not in self.data:
            self.data['giveaways'] = {}
        if guild_id not in self.data['giveaways']:
            self.data['giveaways'][guild_id] = {}
        
        self.data['giveaways'][guild_id][message_id] = {
            'channel_id': channel_id,
            'prize': prize,
            'host_id': host_id,
            'end_time': end_time.isoformat(),
            'winners': winners,
            'participants': []
        }
        
        return self._save_data()
    
    def add_giveaway_participant(self, guild_id, message_id, user_id):
        """Add a participant to a giveaway"""
        guild_id, message_id, user_id = str(guild_id), str(message_id), str(user_id)
        
        if message_id in self.data.get('giveaways', {}).get(guild_id, {}):
            if user_id not in self.data['giveaways'][guild_id][message_id]['participants']:
                self.data['giveaways'][guild_id][message_id]['participants'].append(user_id)
                return self._save_data()
        
        return False
    
    def remove_giveaway_participant(self, guild_id, message_id, user_id):
        """Remove a participant from a giveaway"""
        guild_id, message_id, user_id = str(guild_id), str(message_id), str(user_id)
        
        if message_id in self.data.get('giveaways', {}).get(guild_id, {}):
            if user_id in self.data['giveaways'][guild_id][message_id]['participants']:
                self.data['giveaways'][guild_id][message_id]['participants'].remove(user_id)
                return self._save_data()
        
        return False
    
    def get_giveaway(self, guild_id, message_id):
        """Get giveaway information"""
        guild_id, message_id = str(guild_id), str(message_id)
        return self.data.get('giveaways', {}).get(guild_id, {}).get(message_id)
    
    def get_active_giveaways(self):
        """Get all active giveaways"""
        active_giveaways = []
        now = datetime.now()
        
        for guild_id, guild_giveaways in self.data.get('giveaways', {}).items():
            for message_id, giveaway in guild_giveaways.items():
                end_time = datetime.fromisoformat(giveaway['end_time'])
                if end_time > now:
                    active_giveaways.append({
                        'guild_id': guild_id,
                        'message_id': message_id,
                        'channel_id': giveaway['channel_id'],
                        'end_time': end_time,
                        'data': giveaway
                    })
        
        return active_giveaways
    
    def end_giveaway(self, guild_id, message_id):
        """Mark a giveaway as ended"""
        guild_id, message_id = str(guild_id), str(message_id)
        
        if message_id in self.data.get('giveaways', {}).get(guild_id, {}):
            self.data['giveaways'][guild_id][message_id]['ended'] = True
            self.data['giveaways'][guild_id][message_id]['end_time'] = datetime.now().isoformat()
            return self._save_data()
        
        return False

# Create a global instance of the database
db = JsonDatabase()
