import discord
from config import CONFIG

class EmbedCreator:
    @staticmethod
    def create_embed(title, description, color=None):
        """Create a styled embed with the given information
        
        Args:
            title: The embed title
            description: The embed description
            color: The embed color (defaults to default color from config)
            
        Returns:
            discord.Embed: The created embed
        """
        if color is None:
            color = CONFIG['colors']['default']
            
        embed = discord.Embed(
            title=title,
            description=description,
            color=color
        )
        
        return embed
    
    @staticmethod
    def create_success_embed(title, description):
        """Create a success-themed embed
        
        Args:
            title: The embed title
            description: The embed description
            
        Returns:
            discord.Embed: The created embed
        """
        embed = EmbedCreator.create_embed(
            title=f"{CONFIG['emojis']['success']} {title}",
            description=description,
            color=CONFIG['colors']['success']
        )
        
        return embed
    
    @staticmethod
    def create_error_embed(title, description):
        """Create an error-themed embed
        
        Args:
            title: The embed title
            description: The embed description
            
        Returns:
            discord.Embed: The created embed
        """
        embed = EmbedCreator.create_embed(
            title=f"{CONFIG['emojis']['error']} {title}",
            description=description,
            color=CONFIG['colors']['error']
        )
        
        return embed
    
    @staticmethod
    def create_warning_embed(title, description):
        """Create a warning-themed embed
        
        Args:
            title: The embed title
            description: The embed description
            
        Returns:
            discord.Embed: The created embed
        """
        embed = EmbedCreator.create_embed(
            title=f"{CONFIG['emojis']['warning']} {title}",
            description=description,
            color=CONFIG['colors']['warning']
        )
        
        return embed