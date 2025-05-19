import discord
import datetime
from config import CONFIG

class EmbedCreator:
    """Utility class for creating Discord embeds with consistent styling"""
    
    @staticmethod
    def create_basic_embed(title, description, color=None):
        """Creates a basic embed with title and description"""
        if color is None:
            color = CONFIG['colors']['default']
        
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.datetime.now()
        )
        return embed
    
    @staticmethod
    def create_help_embed(bot):
        """Creates the help menu embed"""
        embed = discord.Embed(
            title="Bot Help Menu",
            description=f"My prefix is `{CONFIG['prefix']}`\nUse the dropdown menu below to browse commands.",
            color=CONFIG['colors']['default'],
            timestamp=datetime.datetime.now()
        )
        
        # Add placeholder for custom GIF
        embed.set_image(url=CONFIG['placeholders']['gif_url'])
        
        # Add bot's avatar as thumbnail
        embed.set_thumbnail(url=bot.user.display_avatar.url)
        
        # Add footer
        embed.set_footer(text=f"Requested • {bot.user.name}", icon_url=bot.user.display_avatar.url)
        
        return embed
    
    @staticmethod
    def create_category_embed(category, commands):
        """Creates an embed for a specific command category"""
        embed = discord.Embed(
            title=f"{category.title()} Commands",
            description="Below are the available commands in this category:",
            color=CONFIG['colors']['default'],
            timestamp=datetime.datetime.now()
        )
        
        for cmd_name, cmd_info in commands.items():
            embed.add_field(
                name=f"{CONFIG['prefix']}{cmd_name}",
                value=f"{cmd_info['description']}\nUsage: `{CONFIG['prefix']}{cmd_info['usage']}`",
                inline=False
            )
        
        # Add placeholder for custom GIF
        embed.set_thumbnail(url=CONFIG['placeholders']['thumbnail_url'])
        
        return embed
    
    @staticmethod
    def create_success_embed(title, description):
        """Creates a success embed"""
        return EmbedCreator.create_basic_embed(
            f"{CONFIG['emojis']['success']} {title}",
            description,
            CONFIG['colors']['success']
        )
    
    @staticmethod
    def create_error_embed(title, description):
        """Creates an error embed"""
        return EmbedCreator.create_basic_embed(
            f"{CONFIG['emojis']['error']} {title}",
            description,
            CONFIG['colors']['error']
        )
    
    @staticmethod
    def create_info_embed(title, description):
        """Creates an info embed"""
        return EmbedCreator.create_basic_embed(
            f"{CONFIG['emojis']['info']} {title}",
            description,
            CONFIG['colors']['default']
        )
    
    @staticmethod
    def create_warning_embed(title, description):
        """Creates a warning embed"""
        return EmbedCreator.create_basic_embed(
            f"{CONFIG['emojis']['warning']} {title}",
            description,
            CONFIG['colors']['warning']
        )
    
    @staticmethod
    def create_level_up_embed(user, level):
        """Creates a level up notification embed"""
        embed = discord.Embed(
            title=f"{CONFIG['emojis']['level']} Level Up!",
            description=f"{user.mention} Your Level Increased to {level}. Chat More!",
            color=CONFIG['colors']['success'],
            timestamp=datetime.datetime.now()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        return embed
    
    @staticmethod
    def create_ticket_embed():
        """Creates a ticket system embed"""
        embed = discord.Embed(
            title=f"{CONFIG['emojis']['ticket']} Support Ticket System",
            description="If you need assistance from our staff team, please click the button below to create a support ticket.",
            color=CONFIG['colors']['default'],
            timestamp=datetime.datetime.now()
        )
        return embed
    
    @staticmethod
    def create_invite_stats_embed(user, stats):
        """Creates an invite statistics embed"""
        embed = discord.Embed(
            title=f"{CONFIG['emojis']['invite']} Invite Statistics",
            description=f"{user.mention} has {stats['total']} invites",
            color=CONFIG['colors']['default'],
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(name="Joins", value=stats['joins'], inline=True)
        embed.add_field(name="Left", value=stats['left'], inline=True)
        embed.add_field(name="Fake", value=stats['fake'], inline=True)
        embed.add_field(name="Rejoins", value=stats['rejoins'], inline=True)
        embed.add_field(name="Time Period", value="(7d)", inline=True)
        
        embed.set_thumbnail(url=user.display_avatar.url)
        
        return embed
    
    @staticmethod
    def create_message_stats_embed(user, stats):
        """Creates a message statistics embed"""
        embed = discord.Embed(
            title=f"{CONFIG['emojis']['message']} Message Statistics",
            description=f"Message statistics for {user.mention}",
            color=CONFIG['colors']['default'],
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(
            name="All time",
            value=f"• {stats['all_time']} messages in this server!",
            inline=False
        )
        
        embed.add_field(
            name="Today",
            value=f"• {stats['today']} messages in this server",
            inline=False
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        
        return embed
    
    @staticmethod
    def create_leaderboard_embed(leaderboard_type, entries):
        """Creates a leaderboard embed"""
        title_emoji = {
            'messages': CONFIG['emojis']['message'],
            'invites': CONFIG['emojis']['invite'],
            'levels': CONFIG['emojis']['level']
        }.get(leaderboard_type, '📊')
        
        embed = discord.Embed(
            title=f"{title_emoji} {leaderboard_type.title()} Leaderboard",
            description=f"The {leaderboard_type} are being updated in real-time!",
            color=CONFIG['colors']['default'],
            timestamp=datetime.datetime.now()
        )
        
        for i, entry in enumerate(entries, 1):
            medal = {1: '🥇', 2: '🥈', 3: '🥉'}.get(i, f"{i}.")
            embed.add_field(
                name=f"{medal} {entry['name']}",
                value=f"{entry['value']} {leaderboard_type}",
                inline=(i > 3)  # Top 3 not inline, rest are inline
            )
        
        return embed
    
    @staticmethod
    def create_reaction_roles_embed(title, description, roles):
        """Creates a reaction roles embed"""
        embed = discord.Embed(
            title=f"{CONFIG['emojis']['role']} {title}",
            description=description,
            color=CONFIG['colors']['default'],
            timestamp=datetime.datetime.now()
        )
        
        for role in roles:
            embed.add_field(
                name=role['name'],
                value=f"{role['emoji']} - {role['description']}",
                inline=True
            )
        
        embed.set_footer(text="Select roles from the dropdown menu below")
        
        return embed
    
    @staticmethod
    def create_giveaway_embed(prize, host, end_time, winners=1):
        """Creates a giveaway embed"""
        embed = discord.Embed(
            title=f"{CONFIG['emojis']['giveaway']} GIVEAWAY: {prize}",
            description=f"React with {CONFIG['emojis']['giveaway']} to enter!",
            color=CONFIG['colors']['default'],
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(name="Hosted by:", value=host.mention, inline=True)
        embed.add_field(name="Winners:", value=str(winners), inline=True)
        embed.add_field(name="Ends at:", value=f"<t:{int(end_time.timestamp())}:R>", inline=True)
        
        embed.set_footer(text="Ends")
        
        return embed
