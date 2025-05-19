import discord
from datetime import datetime, timedelta
import re

class Helpers:
    @staticmethod
    def parse_time(time_str):
        """Parse a time string into a timedelta object.
        
        Args:
            time_str (str): A string in the format "5d" (5 days), "3h" (3 hours), etc.
            
        Returns:
            timedelta: A timedelta object representing the parsed time
        """
        time_regex = re.compile(r'(\d+)([smhdw])')
        match = time_regex.match(time_str.lower())
        
        if not match:
            raise ValueError(f"Invalid time format: {time_str}")
        
        value, unit = match.groups()
        value = int(value)
        
        if unit == 's':
            return timedelta(seconds=value)
        elif unit == 'm':
            return timedelta(minutes=value)
        elif unit == 'h':
            return timedelta(hours=value)
        elif unit == 'd':
            return timedelta(days=value)
        elif unit == 'w':
            return timedelta(weeks=value)
        else:
            raise ValueError(f"Unknown time unit: {unit}")
    
    @staticmethod
    async def get_member_from_string(ctx, user_str):
        """Get a member from a string (mention, ID, or name).
        
        Args:
            ctx (commands.Context): The command context
            user_str (str): The user string to parse
            
        Returns:
            discord.Member: The member object, or None if not found
        """
        # Check if it's a mention
        mention_match = re.match(r'<@!?(\d+)>', user_str)
        if mention_match:
            user_id = int(mention_match.group(1))
            return ctx.guild.get_member(user_id)
        
        # Check if it's an ID
        if user_str.isdigit():
            return ctx.guild.get_member(int(user_str))
        
        # Try to find by name
        members = [m for m in ctx.guild.members if m.display_name.lower() == user_str.lower()]
        if members:
            return members[0]
        
        # Try to find by name#discriminator
        if '#' in user_str:
            name, discrim = user_str.rsplit('#', 1)
            if discrim.isdigit():
                members = [m for m in ctx.guild.members 
                         if m.name.lower() == name.lower() and m.discriminator == discrim]
                if members:
                    return members[0]
        
        return None
    
    @staticmethod
    def get_level_from_xp(xp):
        """Calculate level from XP.
        
        Args:
            xp (int): The XP amount
            
        Returns:
            int: The level
        """
        # Simple level formula: level = sqrt(xp / 100)
        import math
        return math.floor(math.sqrt(xp / 100))
    
    @staticmethod
    def get_xp_for_level(level):
        """Calculate XP required for a specific level.
        
        Args:
            level (int): The level
            
        Returns:
            int: The XP required
        """
        return level ** 2 * 100
    
    @staticmethod
    def format_relative_time(timestamp):
        """Format a timestamp as a relative time for Discord.
        
        Args:
            timestamp (int): Unix timestamp
            
        Returns:
            str: Formatted relative time for Discord
        """
        return f"<t:{int(timestamp)}:R>"
    
    @staticmethod
    def is_url_image(url):
        """Check if a URL points to an image.
        
        Args:
            url (str): URL to check
            
        Returns:
            bool: True if the URL points to an image
        """
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        return any(url.lower().endswith(ext) for ext in image_extensions)
    
    @staticmethod
    def truncate_string(string, max_length=100, suffix='...'):
        """Truncate a string to a maximum length.
        
        Args:
            string (str): The string to truncate
            max_length (int): Maximum length
            suffix (str): Suffix to add if truncated
            
        Returns:
            str: Truncated string
        """
        if len(string) <= max_length:
            return string
        return string[:max_length-len(suffix)] + suffix
