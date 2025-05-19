import discord
from discord.ext import commands
from discord.ui import Select, View
import logging
from typing import Dict, List, Optional

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
        "clearautorole": {
            "description": "Clear the autorole setting",
            "usage": "clearautorole"
        },
        "ticket": {
            "description": "Set up the ticket system",
            "usage": "ticket setup"
        },
        "close": {
            "description": "Close a ticket channel",
            "usage": "close"
        }
    },
    "levels": {
        "level": {
            "description": "Check your level or someone else's level",
            "usage": "level [user]"
        },
        "leaderboard": {
            "description": "View the server's leaderboard",
            "usage": "leaderboard <levels|messages|invites>"
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
        },
        "topmessages": {
            "description": "Show top message senders in the server",
            "usage": "topmessages [all_time|today]"
        },
        "resetmessages": {
            "description": "Reset message stats for a user (Admin only)",
            "usage": "resetmessages <user>"
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
        },
        "reactionrole delete": {
            "description": "Delete a reaction role message",
            "usage": "reactionrole delete <message_id>"
        },
        "reactionrole list": {
            "description": "List all reaction role messages",
            "usage": "reactionrole list"
        }
    }
}

class HelpCommandDropdown(Select):
    def __init__(self, bot):
        self.bot = bot
        
        # Create options for each category with emojis and descriptions
        options = [
            discord.SelectOption(
                label="General",
                description="General bot commands",
                emoji="🏠",
                value="general"
            ),
            discord.SelectOption(
                label="Moderation",
                description="Server moderation commands",
                emoji="🛡️",
                value="moderation"
            ),
            discord.SelectOption(
                label="Levels",
                description="Level tracking and rewards",
                emoji="⬆️",
                value="levels"
            ),
            discord.SelectOption(
                label="Invites",
                description="Invite tracking and statistics",
                emoji="📨",
                value="invites"
            ),
            discord.SelectOption(
                label="Messages",
                description="Message tracking and leaderboards",
                emoji="💬",
                value="messages"
            ),
            discord.SelectOption(
                label="Giveaways",
                description="Create and manage giveaways",
                emoji="🎉",
                value="giveaways"
            ),
            discord.SelectOption(
                label="Roles",
                description="Self-assignable reaction roles",
                emoji="👑",
                value="roles"
            )
        ]
        
        super().__init__(
            placeholder="Select a command category...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="help_category_select"
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Handles the dropdown selection."""
        selected_category = self.values[0]
        embed = await self.create_category_embed(selected_category)
        await interaction.response.edit_message(embed=embed, view=self.view)
    
    async def create_category_embed(self, category):
        """Create an embed for the selected category.
        
        Args:
            category (str): The selected category
            
        Returns:
            discord.Embed: The category embed
        """
        commands_info = COMMANDS_INFO.get(category, {})
        
        # Category emojis mapping
        category_emojis = {
            "general": "🏠",
            "moderation": "🛡️",
            "levels": "⬆️",
            "invites": "📨",
            "messages": "💬",
            "giveaways": "🎉",
            "roles": "👑"
        }
        
        emoji = category_emojis.get(category, "ℹ️")
        
        embed = discord.Embed(
            title=f"{emoji} {category.title()} Commands",
            description=f"Use `{CONFIG['prefix']}help <command>` for more details on a command.",
            color=CONFIG['colors']['default']
        )
        
        for cmd_name, cmd_info in commands_info.items():
            embed.add_field(
                name=f"{CONFIG['prefix']}{cmd_name}",
                value=f"{cmd_info['description']}\nUsage: `{CONFIG['prefix']}{cmd_info['usage']}`",
                inline=False
            )
        
        # Add placeholder for custom GIF or image
        embed.set_thumbnail(url=CONFIG['placeholders']['thumbnail_url'])
        
        # Set footer with navigation hint
        embed.set_footer(text="Use the dropdown menu to navigate between categories", 
                        icon_url=self.bot.user.display_avatar.url)
        
        return embed

class HelpCommandView(View):
    def __init__(self, bot):
        super().__init__(timeout=180)  # 3 minute timeout
        self.add_item(HelpCommandDropdown(bot))

class HelpCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("HelpCommands cog initialized")
    
    @commands.hybrid_command(name="help", description="Shows the help menu with interactive dropdown.")
    async def help_command(self, ctx, command=None):
        """Show the help menu with interactive dropdown."""
        if command is not None:
            # Show help for a specific command
            cmd = self.bot.get_command(command)
            if cmd:
                embed = discord.Embed(
                    title=f"Help: {CONFIG['prefix']}{cmd.name}",
                    description=cmd.help or "No description available.",
                    color=CONFIG['colors']['default']
                )
                
                if cmd.aliases:
                    embed.add_field(name="Aliases", value=", ".join(cmd.aliases), inline=False)
                
                usage = f"{CONFIG['prefix']}{cmd.name}"
                if cmd.signature:
                    usage += f" {cmd.signature}"
                
                embed.add_field(name="Usage", value=f"`{usage}`", inline=False)
                
                # Add examples if available
                # Find command in our COMMANDS_INFO
                for category, commands in COMMANDS_INFO.items():
                    if cmd.name in commands:
                        cmd_info = commands[cmd.name]
                        embed.add_field(
                            name="Example", 
                            value=f"`{CONFIG['prefix']}{cmd_info['usage']}`", 
                            inline=False
                        )
                        break
                
                await ctx.send(embed=embed)
                return
            else:
                # Command not found
                embed = EmbedCreator.create_error_embed(
                    "Command Not Found",
                    f"Cannot find command `{command}`. Use `{CONFIG['prefix']}help` to see all available commands."
                )
                await ctx.send(embed=embed)
                return
        
        # Show the main help menu
        embed = discord.Embed(
            title="Bot Help Menu",
            description=f"Created by gh_sman\nMy prefix is `{CONFIG['prefix']}`\nUse the dropdown menu below to browse commands.",
            color=CONFIG['colors']['default']
        )
        
        # Add custom GIF banner
        # Using file attachment for the GIF to ensure it displays properly
        file = discord.File("assets/images/help_banner.gif", filename="help_banner.gif")
        embed.set_image(url="attachment://help_banner.gif")
        
        # Add bot's avatar as thumbnail
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        # Add footer
        embed.set_footer(text="A powerful, multipurpose bot designed to serve a wide range of Discord servers", 
                         icon_url=ctx.author.display_avatar.url)
        
        view = HelpCommandView(self.bot)
        
        await ctx.send(file=file, embed=embed, view=view)
    
    @commands.hybrid_command(name="ping", description="Check the bot's latency.")
    async def ping(self, ctx):
        """Check the bot's latency."""
        latency = round(self.bot.latency * 1000)
        embed = EmbedCreator.create_info_embed(
            "Pong!",
            f"Latency: {latency}ms"
        )
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="info", description="Get information about the bot.")
    async def info(self, ctx):
        """Get information about the bot."""
        embed = discord.Embed(
            title=f"About {self.bot.user.name}",
            description="Created by gh_sman - a powerful, multipurpose bot designed to serve a wide range of Discord servers.",
            color=CONFIG['colors']['default']
        )
        
        # Add bot statistics
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="Users", value=str(sum(g.member_count for g in self.bot.guilds)), inline=True)
        embed.add_field(name="Prefix", value=f"`{CONFIG['prefix']}`", inline=True)
        
        # Add features
        features = "**Features:**\n• Autorole\n• Giveaways\n• Leveling\n• Tickets\n• Invite Tracking\n• Message Stats\n• Reaction Roles"
        embed.add_field(name="", value=features, inline=False)
        
        # Add bot avatar as thumbnail
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        # Add footer
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpCommands(bot))