import discord
from discord.ext import commands
import logging
import json
import os
from config import CONFIG

logger = logging.getLogger('discord_bot')

class Welcome(commands.Cog):
    """Welcome message system for new members"""
    
    def __init__(self, bot):
        self.bot = bot
        self.welcome_settings = {}
        self.data_file = 'data/welcome_settings.json'
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        
        # Load settings
        self.load_settings()
        
        logger.info("Welcome cog initialized")
        
    def load_settings(self):
        """Load welcome settings from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    self.welcome_settings = json.load(f)
            else:
                self.welcome_settings = {}
                self.save_settings()
        except Exception as e:
            logger.error(f"Error loading welcome settings: {e}")
            self.welcome_settings = {}
            
    def save_settings(self):
        """Save welcome settings to file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.welcome_settings, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving welcome settings: {e}")
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Send welcome message when a new member joins"""
        guild_id = str(member.guild.id)
        
        # Check if welcome messages are enabled for this guild
        if guild_id not in self.welcome_settings:
            return
            
        settings = self.welcome_settings[guild_id]
        
        # Check if welcome messages are enabled
        if not settings.get('enabled', False):
            return
            
        # Get welcome channel
        channel_id = settings.get('channel_id')
        if not channel_id:
            return
            
        channel = member.guild.get_channel(int(channel_id))
        if not channel:
            logger.error(f"Welcome channel {channel_id} not found in guild {member.guild.name}")
            return
            
        # Create welcome embed
        embed = discord.Embed(
            title=f"Welcome to {member.guild.name}!",
            description=settings.get('message', f"Welcome {member.mention} to the server! We're glad to have you here."),
            color=CONFIG['colors']['default']
        )
        
        # Add member count field
        embed.add_field(
            name="Member Count",
            value=f"{member.guild.member_count} Members",
            inline=True
        )
        
        # Set member avatar as thumbnail
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Try to use welcome GIF if available
        try:
            gif_path = os.path.join("assets", "images", "welcome.gif")
            if os.path.exists(gif_path) and os.path.getsize(gif_path) > 0:
                file = discord.File(gif_path, filename="welcome.gif")
                embed.set_image(url="attachment://welcome.gif")
                await channel.send(file=file, embed=embed)
            else:
                # Send without image if not found
                await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Error sending welcome message: {e}")
            await channel.send(embed=embed)
    
    @commands.group(name="welcome", invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def welcome(self, ctx):
        """Welcome message settings"""
        guild_id = str(ctx.guild.id)
        settings = self.welcome_settings.get(guild_id, {})
        
        enabled = settings.get('enabled', False)
        channel_id = settings.get('channel_id')
        welcome_channel = ctx.guild.get_channel(int(channel_id)) if channel_id else None
        
        embed = discord.Embed(
            title="Welcome Message Settings",
            description="Configure welcome messages for new members",
            color=CONFIG['colors']['default']
        )
        
        # Add status field
        embed.add_field(
            name="Status",
            value="✅ Enabled" if enabled else "❌ Disabled",
            inline=True
        )
        
        # Add channel field
        if welcome_channel:
            channel_value = welcome_channel.mention
        else:
            channel_value = "Not set"
            
        embed.add_field(
            name="Welcome Channel",
            value=channel_value,
            inline=True
        )
        
        # Add message field
        message = settings.get('message', 'Default welcome message')
        if len(message) > 100:
            message = message[:97] + "..."
            
        embed.add_field(
            name="Custom Message",
            value=f"```{message}```",
            inline=False
        )
        
        # Add command examples
        commands = [
            f"`{CONFIG['prefix']}welcome on` - Enable welcome messages",
            f"`{CONFIG['prefix']}welcome off` - Disable welcome messages",
            f"`{CONFIG['prefix']}welcome channel #channel` - Set welcome channel",
            f"`{CONFIG['prefix']}welcome message Your message here` - Set custom message"
        ]
        
        embed.add_field(
            name="Commands",
            value="\n".join(commands),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @welcome.command(name="on")
    @commands.has_permissions(manage_guild=True)
    async def welcome_on(self, ctx):
        """Enable welcome messages"""
        guild_id = str(ctx.guild.id)
        
        # Get or create settings for this guild
        if guild_id not in self.welcome_settings:
            self.welcome_settings[guild_id] = {
                'enabled': True,
                'channel_id': None,
                'message': f"Welcome {{member}} to the server! We're glad to have you here."
            }
        else:
            self.welcome_settings[guild_id]['enabled'] = True
            
        # Save updated settings
        self.save_settings()
        
        embed = discord.Embed(
            title="✅ Welcome Messages Enabled",
            description="Welcome messages will now be sent when new members join.",
            color=CONFIG['colors']['success']
        )
        
        # Check if welcome channel is set
        if not self.welcome_settings[guild_id].get('channel_id'):
            embed.add_field(
                name="⚠️ Channel Not Set",
                value=f"Please set a welcome channel with `{CONFIG['prefix']}welcome channel #channel`",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @welcome.command(name="off")
    @commands.has_permissions(manage_guild=True)
    async def welcome_off(self, ctx):
        """Disable welcome messages"""
        guild_id = str(ctx.guild.id)
        
        # Get or create settings for this guild
        if guild_id not in self.welcome_settings:
            self.welcome_settings[guild_id] = {
                'enabled': False,
                'channel_id': None,
                'message': f"Welcome {{member}} to the server! We're glad to have you here."
            }
        else:
            self.welcome_settings[guild_id]['enabled'] = False
            
        # Save updated settings
        self.save_settings()
        
        embed = discord.Embed(
            title="❌ Welcome Messages Disabled",
            description="Welcome messages will no longer be sent when new members join.",
            color=CONFIG['colors']['error']
        )
        
        await ctx.send(embed=embed)
    
    @welcome.command(name="channel")
    @commands.has_permissions(manage_guild=True)
    async def welcome_channel(self, ctx, channel: discord.TextChannel):
        """Set the welcome channel
        
        Args:
            channel: The channel to send welcome messages to
        """
        guild_id = str(ctx.guild.id)
        
        # Get or create settings for this guild
        if guild_id not in self.welcome_settings:
            self.welcome_settings[guild_id] = {
                'enabled': True,
                'channel_id': str(channel.id),
                'message': f"Welcome {{member}} to the server! We're glad to have you here."
            }
        else:
            self.welcome_settings[guild_id]['channel_id'] = str(channel.id)
            
        # Save updated settings
        self.save_settings()
        
        embed = discord.Embed(
            title="✅ Welcome Channel Set",
            description=f"Welcome messages will now be sent to {channel.mention}.",
            color=CONFIG['colors']['success']
        )
        
        # Enable welcome messages if they're not already
        if not self.welcome_settings[guild_id].get('enabled', False):
            self.welcome_settings[guild_id]['enabled'] = True
            self.save_settings()
            
            embed.add_field(
                name="ℹ️ Welcome Messages Enabled",
                value="Welcome messages have been automatically enabled.",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @welcome.command(name="message")
    @commands.has_permissions(manage_guild=True)
    async def welcome_message(self, ctx, *, message):
        """Set the welcome message
        
        Args:
            message: The custom welcome message
        """
        guild_id = str(ctx.guild.id)
        
        # Get or create settings for this guild
        if guild_id not in self.welcome_settings:
            self.welcome_settings[guild_id] = {
                'enabled': True,
                'channel_id': None,
                'message': message
            }
        else:
            self.welcome_settings[guild_id]['message'] = message
            
        # Save updated settings
        self.save_settings()
        
        embed = discord.Embed(
            title="✅ Welcome Message Set",
            description="Your custom welcome message has been saved.",
            color=CONFIG['colors']['success']
        )
        
        embed.add_field(
            name="Message Preview",
            value=message.replace('{member}', ctx.author.mention),
            inline=False
        )
        
        embed.add_field(
            name="ℹ️ Available Tags",
            value="`{member}` - Mentions the new member",
            inline=False
        )
        
        # Check if welcome channel is set
        if not self.welcome_settings[guild_id].get('channel_id'):
            embed.add_field(
                name="⚠️ Channel Not Set",
                value=f"Please set a welcome channel with `{CONFIG['prefix']}welcome channel #channel`",
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))