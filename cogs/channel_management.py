import discord
from discord.ext import commands
import logging
from config import CONFIG
from utils.embed_creator import EmbedCreator

logger = logging.getLogger('discord_bot')

class ChannelManagement(commands.Cog):
    """Commands for managing channel permissions and settings"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("ChannelManagement cog initialized")
    
    @commands.command(name="lock")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def lock_channel(self, ctx, channel: discord.TextChannel = None, *, reason: str = "No reason provided"):
        """Lock a channel to prevent members from sending messages
        
        Args:
            channel: The channel to lock (defaults to current channel)
            reason: The reason for locking the channel
        """
        # Default to current channel if none provided
        channel = channel or ctx.channel
        
        # Update permissions for the default role (@everyone)
        try:
            # Get the default role
            default_role = ctx.guild.default_role
            
            # Update permissions
            current_perms = channel.overwrites_for(default_role)
            
            # Check if already locked
            if current_perms.send_messages is False:
                await ctx.send(embed=EmbedCreator.create_info_embed(
                    "Channel Already Locked",
                    f"{channel.mention} is already locked."
                ))
                return
            
            # Set send_messages to False
            current_perms.send_messages = False
            
            # Update the channel permissions
            await channel.set_permissions(default_role, overwrite=current_perms, reason=reason)
            
            # Create and send embed
            embed = discord.Embed(
                title="🔒 Channel Locked",
                description=f"{channel.mention} has been locked.",
                color=CONFIG['colors']['warning']
            )
            
            embed.add_field(
                name="Reason",
                value=reason,
                inline=False
            )
            
            embed.add_field(
                name="Unlock Command",
                value=f"Use `.unlock {channel.mention}` to unlock this channel.",
                inline=False
            )
            
            # Send to the context channel
            await ctx.send(embed=embed)
            
            # If locking a different channel, also send notification there
            if channel != ctx.channel:
                notification = discord.Embed(
                    title="🔒 Channel Locked",
                    description=f"This channel has been locked by {ctx.author.mention}.",
                    color=CONFIG['colors']['warning']
                )
                
                notification.add_field(
                    name="Reason",
                    value=reason,
                    inline=False
                )
                
                await channel.send(embed=notification)
            
        except Exception as e:
            logger.error(f"Error locking channel: {e}")
            await ctx.send(embed=EmbedCreator.create_error_embed(
                "Error",
                f"Failed to lock {channel.mention}: {str(e)}"
            ))
    
    @commands.command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def unlock_channel(self, ctx, channel: discord.TextChannel = None, *, reason: str = "No reason provided"):
        """Unlock a previously locked channel
        
        Args:
            channel: The channel to unlock (defaults to current channel)
            reason: The reason for unlocking the channel
        """
        # Default to current channel if none provided
        channel = channel or ctx.channel
        
        # Update permissions for the default role (@everyone)
        try:
            # Get the default role
            default_role = ctx.guild.default_role
            
            # Update permissions
            current_perms = channel.overwrites_for(default_role)
            
            # Check if already unlocked
            if current_perms.send_messages is None or current_perms.send_messages is True:
                await ctx.send(embed=EmbedCreator.create_info_embed(
                    "Channel Not Locked",
                    f"{channel.mention} is not locked."
                ))
                return
            
            # Reset send_messages permission
            current_perms.send_messages = None
            
            # If all permissions are None, remove the override
            if all(getattr(current_perms, attr) is None for attr in dir(current_perms) if not attr.startswith('_') and attr != 'pair'):
                await channel.set_permissions(default_role, overwrite=None, reason=reason)
            else:
                await channel.set_permissions(default_role, overwrite=current_perms, reason=reason)
            
            # Create and send embed
            embed = discord.Embed(
                title="🔓 Channel Unlocked",
                description=f"{channel.mention} has been unlocked.",
                color=CONFIG['colors']['success']
            )
            
            embed.add_field(
                name="Reason",
                value=reason,
                inline=False
            )
            
            # Send to the context channel
            await ctx.send(embed=embed)
            
            # If unlocking a different channel, also send notification there
            if channel != ctx.channel:
                notification = discord.Embed(
                    title="🔓 Channel Unlocked",
                    description=f"This channel has been unlocked by {ctx.author.mention}.",
                    color=CONFIG['colors']['success']
                )
                
                notification.add_field(
                    name="Reason",
                    value=reason,
                    inline=False
                )
                
                await channel.send(embed=notification)
            
        except Exception as e:
            logger.error(f"Error unlocking channel: {e}")
            await ctx.send(embed=EmbedCreator.create_error_embed(
                "Error",
                f"Failed to unlock {channel.mention}: {str(e)}"
            ))
    
    @commands.command(name="slowmode")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def set_slowmode(self, ctx, seconds: int, channel: discord.TextChannel = None, *, reason: str = "No reason provided"):
        """Set the slowmode delay for a channel
        
        Args:
            seconds: The slowmode delay in seconds (0-21600)
            channel: The channel to set slowmode for (defaults to current channel)
            reason: The reason for changing slowmode
        """
        # Default to current channel if none provided
        channel = channel or ctx.channel
        
        # Check delay
        if seconds < 0 or seconds > 21600:
            await ctx.send(embed=EmbedCreator.create_error_embed(
                "Invalid Delay",
                "Slowmode delay must be between 0 and 21600 seconds (6 hours)."
            ))
            return
        
        # Set slowmode
        try:
            await channel.edit(slowmode_delay=seconds, reason=reason)
            
            if seconds == 0:
                description = f"Slowmode has been turned off for {channel.mention}."
                title = "⏱️ Slowmode Disabled"
            else:
                # Format time for display
                if seconds < 60:
                    time_str = f"{seconds} seconds"
                elif seconds < 3600:
                    minutes = seconds // 60
                    time_str = f"{minutes} minute{'s' if minutes != 1 else ''}"
                else:
                    hours = seconds // 3600
                    time_str = f"{hours} hour{'s' if hours != 1 else ''}"
                    
                description = f"Slowmode set to {time_str} for {channel.mention}."
                title = "⏱️ Slowmode Enabled"
                
            embed = discord.Embed(
                title=title,
                description=description,
                color=CONFIG['colors']['info']
            )
            
            embed.add_field(
                name="Reason",
                value=reason,
                inline=False
            )
            
            # Send to the context channel
            await ctx.send(embed=embed)
            
            # If setting slowmode for a different channel, also send notification there
            if channel != ctx.channel:
                if seconds == 0:
                    notification_desc = "Slowmode has been disabled for this channel."
                else:
                    notification_desc = f"Slowmode has been set to {time_str} for this channel."
                
                notification = discord.Embed(
                    title=title,
                    description=notification_desc,
                    color=CONFIG['colors']['info']
                )
                
                notification.add_field(
                    name="Set By",
                    value=ctx.author.mention,
                    inline=True
                )
                
                notification.add_field(
                    name="Reason",
                    value=reason,
                    inline=True
                )
                
                await channel.send(embed=notification)
                
        except Exception as e:
            logger.error(f"Error setting slowmode: {e}")
            await ctx.send(embed=EmbedCreator.create_error_embed(
                "Error",
                f"Failed to set slowmode for {channel.mention}: {str(e)}"
            ))
    
    @commands.command(name="channelinfo")
    async def channel_info(self, ctx, channel: discord.TextChannel = None):
        """Show information about a channel
        
        Args:
            channel: The channel to show info for (defaults to current channel)
        """
        # Default to current channel if none provided
        channel = channel or ctx.channel
        
        # Create embed
        embed = discord.Embed(
            title=f"#{channel.name} Channel Information",
            description=channel.topic or "No topic set",
            color=CONFIG['colors']['info']
        )
        
        # Add channel ID
        embed.add_field(
            name="🆔 Channel ID",
            value=channel.id,
            inline=True
        )
        
        # Add category
        embed.add_field(
            name="📁 Category",
            value=channel.category.name if channel.category else "None",
            inline=True
        )
        
        # Add creation date
        created_timestamp = int(channel.created_at.timestamp())
        created_date = f"<t:{created_timestamp}:F>\n<t:{created_timestamp}:R>"
        
        embed.add_field(
            name="📅 Created",
            value=created_date,
            inline=True
        )
        
        # Add slowmode
        slowmode = channel.slowmode_delay
        if slowmode > 0:
            # Format slowmode (e.g. 5s, 1m, 1h)
            if slowmode < 60:
                slowmode_str = f"{slowmode}s"
            elif slowmode < 3600:
                slowmode_str = f"{slowmode // 60}m"
            else:
                slowmode_str = f"{slowmode // 3600}h"
        else:
            slowmode_str = "Off"
            
        embed.add_field(
            name="⏱️ Slowmode",
            value=slowmode_str,
            inline=True
        )
        
        # Add NSFW status
        embed.add_field(
            name="🔞 NSFW",
            value="Yes" if channel.is_nsfw() else "No",
            inline=True
        )
        
        # Add news status (if applicable)
        if hasattr(channel, 'is_news'):
            embed.add_field(
                name="📰 Announcement Channel",
                value="Yes" if channel.is_news() else "No",
                inline=True
            )
        
        # Add permission synced status
        synced = channel.permissions_synced
        if synced is not None:
            embed.add_field(
                name="🔄 Synced Permissions",
                value="Yes" if synced else "No",
                inline=True
            )
        
        # Add message count if available
        try:
            message_count = 0
            async for _ in channel.history(limit=None):
                message_count += 1
                if message_count >= 100:  # Cap at 100 for performance
                    message_count = "100+"
                    break
            
            if isinstance(message_count, int):
                count_str = str(message_count)
            else:
                count_str = message_count
                
            embed.add_field(
                name="💬 Message Count",
                value=count_str,
                inline=True
            )
        except:
            pass
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ChannelManagement(bot))