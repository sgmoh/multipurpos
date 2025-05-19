import discord
from discord.ext import commands
from discord.ui import Select, View
import logging
import os
from typing import Dict, List, Optional

from config import CONFIG
from utils.embed_creator import EmbedCreator

logger = logging.getLogger('discord_bot')

# Command information for the help menu - same as in help_commands.py but with compact display
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

class HelpDropdown(discord.ui.Select):
    """Dropdown menu for selecting command categories"""
    
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
        
        # Get category color
        category_colors = {
            "general": 0x7289DA,    # Discord Blue
            "moderation": 0xE74C3C,  # Red
            "levels": 0x2ECC71,     # Green
            "invites": 0x3498DB,    # Blue
            "messages": 0x9B59B6,   # Purple
            "giveaways": 0xF1C40F,  # Yellow
            "roles": 0xE67E22      # Orange
        }
        color = category_colors.get(selected_category, CONFIG['colors']['default'])
        
        # Category emojis
        category_emojis = {
            "general": "🏠",
            "moderation": "🛡️",
            "levels": "⬆️",
            "invites": "📨",
            "messages": "💬",
            "giveaways": "🎉",
            "roles": "👑"
        }
        emoji = category_emojis.get(selected_category, "ℹ️")
        
        # Create embed
        embed = discord.Embed(
            title=f"{emoji} {selected_category.title()} Commands",
            description=f"Use `{CONFIG['prefix']}help <command>` for more details on a command.",
            color=color
        )
        
        # Consistent image size across all categories - don't set image for category pages
        # This will prevent the GIF from getting bigger
        
        # Get commands for the selected category
        commands_info = COMMANDS_INFO.get(selected_category, {})
        
        # Create a compact display with command groups
        if commands_info:
            # Group commands by common prefixes or keep them separate
            command_list = []
            for cmd_name, cmd_info in commands_info.items():
                command_list.append(f"`{CONFIG['prefix']}{cmd_name}` - {cmd_info['description']}")
            
            if command_list:
                # Join with newlines for better readability
                if embed.description:
                    embed.description = f"{embed.description}\n\n" + "\n".join(command_list)
                else:
                    embed.description = "\n".join(command_list)
        else:
            if embed.description:
                embed.description = f"{embed.description}\n\nNo commands available in this category."
            else:
                embed.description = "No commands available in this category."
        
        # Set thumbnail to show category icon (placeholder)
        embed.set_thumbnail(url=CONFIG['placeholders']['thumbnail_url'])
        
        # Keep the same dimensions as the main help menu
        # embed.set_image(url=CONFIG['placeholders']['gif_url'])
        
        # Set footer with attribution
        embed.set_footer(text="Created by gh_sman • Use the dropdown to navigate", 
                         icon_url=self.bot.user.display_avatar.url)
        
        # Update the message with the new embed
        await interaction.response.edit_message(embed=embed)

class HelpView(discord.ui.View):
    """View for the help menu containing the dropdown and buttons"""
    
    def __init__(self, bot):
        super().__init__(timeout=180)  # 3 minute timeout
        self.bot = bot
        
        # Add the dropdown
        self.add_item(HelpDropdown(bot))
        
        # Add a home button
        self.home_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Home",
            emoji="🏠",
            custom_id="help_home_button",
            row=1
        )
        self.home_button.callback = self.home_button_callback
        self.add_item(self.home_button)
        
        # Add invite button
        self.invite_button = discord.ui.Button(
            style=discord.ButtonStyle.link,
            label="Invite",
            emoji="📨",
            url="https://discord.com/api/oauth2/authorize?client_id=1234567890&permissions=8&scope=bot%20applications.commands",
            row=1
        )
        self.add_item(self.invite_button)
        
        # Add support button
        self.support_button = discord.ui.Button(
            style=discord.ButtonStyle.link,
            label="Support",
            emoji="❓",
            url="https://discord.gg/placeholder",
            row=1
        )
        self.add_item(self.support_button)
    
    async def home_button_callback(self, interaction: discord.Interaction):
        """Return to the main help menu"""
        embed = discord.Embed(
            title="Bot Help Menu",
            description=f"Created by gh_sman\nMy prefix is `{CONFIG['prefix']}`\nUse the dropdown menu below to browse commands.",
            color=CONFIG['colors']['default']
        )
        
        # Set default values
        file = None
        
        # Try adding the gif image
        try:
            gif_path = os.path.join("assets", "images", "help_banner.gif")
            if os.path.exists(gif_path) and os.path.getsize(gif_path) > 0:
                # We can't edit with a file attachment, so use fallback URL
                embed.set_image(url=CONFIG['placeholders']['gif_url'])
            else:
                embed.set_image(url=CONFIG['placeholders']['gif_url'])
        except Exception as e:
            logger.error(f"Error with help banner: {e}")
            embed.set_image(url=CONFIG['placeholders']['gif_url'])
        
        # Add bot's avatar as thumbnail
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        # Add footer
        embed.set_footer(text="A powerful, multipurpose bot designed to serve a wide range of Discord servers", 
                         icon_url=interaction.user.display_avatar.url)
        
        await interaction.response.edit_message(embed=embed)

class HelpMenu(commands.Cog):
    """Help menu with interactive dropdown and buttons"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("HelpMenu cog initialized")
    
    @commands.hybrid_command(name="help", description="Shows the help menu with interactive dropdown")
    async def help_command(self, ctx, command=None):
        """Show the help menu with interactive dropdown"""
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
        
        # Add custom GIF using direct file attachment
        file = None
        has_file = False
        try:
            gif_path = os.path.join("assets", "images", "help_banner.gif")
            if os.path.exists(gif_path) and os.path.getsize(gif_path) > 0:
                file = discord.File(gif_path, filename="help_banner.gif")
                embed.set_image(url="attachment://help_banner.gif")
                has_file = True
                logger.info(f"Successfully loaded help banner GIF from {gif_path}")
            else:
                embed.set_image(url=CONFIG['placeholders']['gif_url'])
                logger.warning(f"Help banner GIF not found at {gif_path} or is empty")
        except Exception as e:
            embed.set_image(url=CONFIG['placeholders']['gif_url'])
            logger.error(f"Error loading help banner GIF: {e}")
        
        # Add bot's avatar as thumbnail
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        # Add footer
        embed.set_footer(text="A powerful, multipurpose bot designed to serve a wide range of Discord servers", 
                       icon_url=ctx.author.display_avatar.url)
        
        # Create the view with dropdown and buttons
        view = HelpView(self.bot)
        
        # Send the help menu
        if has_file:
            await ctx.send(file=file, embed=embed, view=view)
        else:
            await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(HelpMenu(bot))