import discord
from discord.ext import commands
from discord import app_commands
from typing import List, Dict, Optional
import logging

from config import CONFIG
from utils.embed_creator import EmbedCreator

logger = logging.getLogger('discord_bot')

# Command information for the help menu
COMMANDS_INFO = {
    "general": {
        "help": {
            "description": "Shows this help menu",
            "usage": "help"
        },
        "ping": {
            "description": "Check the bot's latency",
            "usage": "ping"
        },
        "info": {
            "description": "Get information about the bot",
            "usage": "info"
        }
    },
    "moderation": {
        "autorole": {
            "description": "Set a role to be automatically assigned to new members",
            "usage": "autorole <role>"
        },
        "ticket": {
            "description": "Set up the ticket system",
            "usage": "ticket setup"
        }
    },
    "levels": {
        "level": {
            "description": "Check your level or someone else's level",
            "usage": "level [user]"
        },
        "leaderboard": {
            "description": "View the server's leaderboard",
            "usage": "leaderboard <messages|levels|invites>"
        }
    },
    "invites": {
        "invites": {
            "description": "Check your invite stats or someone else's",
            "usage": "invites [user]"
        }
    },
    "messages": {
        "messages": {
            "description": "Check your message stats or someone else's",
            "usage": "messages [user]"
        }
    },
    "giveaways": {
        "gstart": {
            "description": "Start a giveaway",
            "usage": "gstart <duration> <winners> <prize>"
        },
        "gend": {
            "description": "End a giveaway early",
            "usage": "gend <message_id>"
        },
        "greroll": {
            "description": "Reroll a giveaway",
            "usage": "greroll <message_id>"
        }
    },
    "roles": {
        "reactionrole": {
            "description": "Set up a reaction role message",
            "usage": "reactionrole create"
        }
    }
}

class HelpDropdown(discord.ui.Select):
    """Dropdown menu for the help command"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
        # Create options for each category
        options = [
            discord.SelectOption(
                label="General",
                description="General commands",
                emoji="🏠",
                value="general"
            ),
            discord.SelectOption(
                label="Moderation",
                description="Moderation commands",
                emoji="🛡️",
                value="moderation"
            ),
            discord.SelectOption(
                label="Levels",
                description="Leveling system commands",
                emoji="⬆️",
                value="levels"
            ),
            discord.SelectOption(
                label="Invites",
                description="Invite tracking commands",
                emoji="📨",
                value="invites"
            ),
            discord.SelectOption(
                label="Messages",
                description="Message tracking commands",
                emoji="💬",
                value="messages"
            ),
            discord.SelectOption(
                label="Giveaways",
                description="Giveaway commands",
                emoji="🎉",
                value="giveaways"
            ),
            discord.SelectOption(
                label="Roles",
                description="Reaction roles commands",
                emoji="👑",
                value="roles"
            )
        ]
        
        super().__init__(
            placeholder="Select a category...",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Handle dropdown selection"""
        category = self.values[0]
        commands = COMMANDS_INFO.get(category, {})
        
        embed = EmbedCreator.create_category_embed(category, commands)
        await interaction.response.edit_message(embed=embed, view=self.view)

class HelpView(discord.ui.View):
    """View containing the help dropdown"""
    
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=180)  # 3 minute timeout
        self.add_item(HelpDropdown(bot))
        self.bot = bot
    
    async def on_timeout(self):
        """Disable all items when the view times out"""
        for item in self.children:
            item.disabled = True

class Help(commands.Cog):
    """Help command and menu system"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("Help cog initialized")
    
    @commands.command(name="help")
    async def help_command(self, ctx):
        """Shows the help menu with a dropdown for command categories"""
        embed = EmbedCreator.create_help_embed(self.bot)
        view = HelpView(self.bot)
        
        await ctx.send(embed=embed, view=view)
    
    @commands.hybrid_command(name="ping", description="Check the bot's latency")
    async def ping(self, ctx):
        """Check the bot's latency"""
        latency = round(self.bot.latency * 1000)
        embed = EmbedCreator.create_info_embed(
            "Pong!",
            f"Latency: {latency}ms"
        )
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="info", description="Get information about the bot")
    async def info(self, ctx):
        """Get information about the bot"""
        embed = discord.Embed(
            title=f"About {self.bot.user.name}",
            description="A multipurpose Discord bot with custom UI elements, member management, and statistics tracking features.",
            color=CONFIG['colors']['default']
        )
        
        # Add bot statistics
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="Users", value=str(sum(g.member_count for g in self.bot.guilds)), inline=True)
        embed.add_field(name="Prefix", value=f"`{CONFIG['prefix']}`", inline=True)
        embed.add_field(name="Uptime", value="<t:12345:R>", inline=True)  # Placeholder
        embed.add_field(name="Ping", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        
        # Add bot avatar as thumbnail
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        # Add footer
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
