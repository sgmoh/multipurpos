import discord
import datetime
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
    def create_level_up_embed(user, level):
        """Create a level-up notification embed
        
        Args:
            user: The discord.Member who leveled up
            level: The new level they reached
            
        Returns:
            discord.Embed: The level-up embed
        """
        embed = discord.Embed(
            title="⬆️ Level Up!",
            description=f"**{user.mention}** Your Level Increased to **{level}**. Chat More!",
            color=CONFIG['colors']['success']
        )
        
        # Set user avatar as thumbnail
        embed.set_thumbnail(url=user.display_avatar.url)
        
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
        
    @staticmethod
    def create_basic_embed(title, description, color=None):
        """Create a basic embed with the given information
        
        Args:
            title: The embed title
            description: The embed description
            color: The embed color
            
        Returns:
            discord.Embed: The created embed
        """
        return EmbedCreator.create_embed(title, description, color)
        
    @staticmethod
    def create_leaderboard_embed(leaderboard_type, entries):
        """Create a leaderboard embed
        
        Args:
            leaderboard_type: The type of leaderboard (Levels, Messages, etc.)
            entries: List of user entries to display
            
        Returns:
            discord.Embed: The leaderboard embed
        """
        embed = discord.Embed(
            title=f"{leaderboard_type} Leaderboard",
            description="Top members in the server:",
            color=CONFIG['colors']['default']
        )
        
        # Add empty field to create space if needed
        if len(entries) == 0:
            embed.add_field(name="No data available", value="No members have earned XP yet.", inline=False)
            return embed
            
        # Format leaderboard entries
        value = ""
        for i, entry in enumerate(entries):
            medal = ""
            if i == 0:
                medal = "🥇"
            elif i == 1:
                medal = "🥈"
            elif i == 2:
                medal = "🥉"
            else:
                medal = f"{i+1}."
                
            value += f"{medal} <@{entry['user_id']}> - **{entry['count']}**\n"
            
        embed.add_field(name="Rankings", value=value, inline=False)
        
        return embed
        
    @staticmethod
    def create_ticket_embed(user, ticket_number, guild_name):
        """Create a ticket embed
        
        Args:
            user: The user who created the ticket
            ticket_number: The ticket number
            guild_name: The name of the guild where the ticket was created
            
        Returns:
            discord.Embed: The ticket embed
        """
        embed = discord.Embed(
            title=f"Support Ticket #{ticket_number}",
            description=f"Thank you for creating a support ticket! Staff will be with you shortly.",
            color=CONFIG['colors']['info']
        )
        
        embed.add_field(name="User", value=user.mention, inline=True)
        embed.add_field(name="Server", value=guild_name, inline=True)
        embed.add_field(name="Created", value=f"<t:{int(datetime.datetime.now().timestamp())}:R>", inline=True)
        
        embed.add_field(
            name="Instructions",
            value="Please describe your issue in detail, and a staff member will assist you soon.\n"
                  "To close this ticket when resolved, use the `.close` command.",
            inline=False
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        
        return embed