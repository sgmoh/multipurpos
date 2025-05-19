import discord
from discord.ext import commands
import logging
import datetime
from config import CONFIG
from utils.embed_creator import EmbedCreator

logger = logging.getLogger('discord_bot')

class Timeout(commands.Cog):
    """Commands for using Discord's timeout feature"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("Timeout cog initialized")
    
    @commands.command(name="timeout")
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def timeout_user(self, ctx, member: discord.Member, duration: str, *, reason: str = "No reason provided"):
        """Timeout a member using Discord's built-in timeout feature
        
        Args:
            member: The member to timeout
            duration: The duration (e.g. 10m, 1h, 1d)
            reason: The reason for the timeout
        """
        # Check if user can be timed out
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send(embed=EmbedCreator.create_error_embed(
                "Permission Error",
                "You can't timeout members with a higher or equal role to yours."
            ))
            return
            
        if member.guild_permissions.administrator:
            await ctx.send(embed=EmbedCreator.create_error_embed(
                "Cannot Timeout Administrator",
                "Administrators cannot be timed out."
            ))
            return
            
        # Parse duration
        try:
            duration_seconds = 0
            unit = duration[-1].lower()
            value = int(duration[:-1])
            
            if unit == 's':
                duration_seconds = value
            elif unit == 'm':
                duration_seconds = value * 60
            elif unit == 'h':
                duration_seconds = value * 3600
            elif unit == 'd':
                duration_seconds = value * 86400
            else:
                # Try to parse as seconds
                duration_seconds = int(duration)
                
            # Check if duration is valid (max 28 days)
            if duration_seconds < 1:
                await ctx.send(embed=EmbedCreator.create_error_embed(
                    "Invalid Duration",
                    "Duration must be at least 1 second."
                ))
                return
                
            if duration_seconds > 28 * 86400:
                await ctx.send(embed=EmbedCreator.create_error_embed(
                    "Invalid Duration",
                    "Duration cannot exceed 28 days (Discord limit)."
                ))
                return
                
            # Calculate end time
            until = datetime.datetime.utcnow() + datetime.timedelta(seconds=duration_seconds)
            
            # Format time for display
            if duration_seconds < 60:
                time_str = f"{duration_seconds} seconds"
            elif duration_seconds < 3600:
                minutes = duration_seconds // 60
                time_str = f"{minutes} minute{'s' if minutes != 1 else ''}"
            elif duration_seconds < 86400:
                hours = duration_seconds // 3600
                time_str = f"{hours} hour{'s' if hours != 1 else ''}"
            else:
                days = duration_seconds // 86400
                time_str = f"{days} day{'s' if days != 1 else ''}"
            
            # Apply timeout
            try:
                await member.timeout(until, reason=reason)
                
                # Create timeout embed
                embed = discord.Embed(
                    title="⏱️ User Timed Out",
                    description=f"{member.mention} has been timed out for {time_str}.",
                    color=CONFIG['colors']['warning']
                )
                
                embed.add_field(
                    name="Reason",
                    value=reason,
                    inline=False
                )
                
                embed.add_field(
                    name="Expires",
                    value=f"<t:{int(until.timestamp())}:F> (<t:{int(until.timestamp())}:R>)",
                    inline=False
                )
                
                # Try to DM the user
                try:
                    user_embed = discord.Embed(
                        title=f"⏱️ You've been timed out in {ctx.guild.name}",
                        description=f"A moderator has timed you out for {time_str}.",
                        color=CONFIG['colors']['warning']
                    )
                    
                    user_embed.add_field(
                        name="Reason",
                        value=reason,
                        inline=False
                    )
                    
                    user_embed.add_field(
                        name="Expires",
                        value=f"<t:{int(until.timestamp())}:F> (<t:{int(until.timestamp())}:R>)",
                        inline=False
                    )
                    
                    await member.send(embed=user_embed)
                    embed.set_footer(text="User has been notified via DM")
                except:
                    embed.set_footer(text="Could not send DM to user")
                
                await ctx.send(embed=embed)
                
            except Exception as e:
                await ctx.send(embed=EmbedCreator.create_error_embed(
                    "Error",
                    f"Failed to timeout {member.mention}: {str(e)}"
                ))
                
        except ValueError:
            await ctx.send(embed=EmbedCreator.create_error_embed(
                "Invalid Format",
                "Please use format like `10s`, `5m`, `1h`, or `1d` for the duration."
            ))
    
    @commands.command(name="untimeout", aliases=["removetimeout"])
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def remove_timeout(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Remove a timeout from a member
        
        Args:
            member: The member to remove timeout from
            reason: The reason for removing the timeout
        """
        # Check if user is timed out
        if not member.is_timed_out():
            await ctx.send(embed=EmbedCreator.create_error_embed(
                "Not Timed Out",
                f"{member.mention} is not currently timed out."
            ))
            return
            
        # Remove timeout
        try:
            await member.timeout(None, reason=reason)
            
            # Create embed
            embed = discord.Embed(
                title="✅ Timeout Removed",
                description=f"Timeout has been removed from {member.mention}.",
                color=CONFIG['colors']['success']
            )
            
            embed.add_field(
                name="Reason",
                value=reason,
                inline=False
            )
            
            # Try to DM the user
            try:
                user_embed = discord.Embed(
                    title=f"✅ Your timeout in {ctx.guild.name} has been removed",
                    description="A moderator has removed your timeout.",
                    color=CONFIG['colors']['success']
                )
                
                user_embed.add_field(
                    name="Reason",
                    value=reason,
                    inline=False
                )
                
                await member.send(embed=user_embed)
                embed.set_footer(text="User has been notified via DM")
            except:
                embed.set_footer(text="Could not send DM to user")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(embed=EmbedCreator.create_error_embed(
                "Error",
                f"Failed to remove timeout from {member.mention}: {str(e)}"
            ))
    
    @commands.command(name="timeoutinfo")
    @commands.has_permissions(moderate_members=True)
    async def timeout_info(self, ctx, member: discord.Member):
        """Show timeout information for a member
        
        Args:
            member: The member to check timeout for
        """
        # Check if user is timed out
        if not member.is_timed_out():
            await ctx.send(embed=EmbedCreator.create_info_embed(
                "Not Timed Out",
                f"{member.mention} is not currently timed out."
            ))
            return
            
        # Get timeout info
        timeout_until = member.timed_out_until
        
        # Create embed
        embed = discord.Embed(
            title="⏱️ Timeout Information",
            description=f"{member.mention} is currently timed out.",
            color=CONFIG['colors']['warning']
        )
        
        embed.add_field(
            name="Expires",
            value=f"<t:{int(timeout_until.timestamp())}:F> (<t:{int(timeout_until.timestamp())}:R>)",
            inline=False
        )
        
        # Calculate remaining time
        now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        remaining = timeout_until - now
        remaining_seconds = remaining.total_seconds()
        
        # Format remaining time
        if remaining_seconds < 60:
            time_str = f"{int(remaining_seconds)} seconds"
        elif remaining_seconds < 3600:
            minutes = int(remaining_seconds // 60)
            time_str = f"{minutes} minute{'s' if minutes != 1 else ''}"
        elif remaining_seconds < 86400:
            hours = int(remaining_seconds // 3600)
            time_str = f"{hours} hour{'s' if hours != 1 else ''}"
        else:
            days = int(remaining_seconds // 86400)
            time_str = f"{days} day{'s' if days != 1 else ''}"
            
        embed.add_field(
            name="Remaining Time",
            value=time_str,
            inline=False
        )
        
        # Add commands for removing timeout
        embed.add_field(
            name="Remove Timeout",
            value=f"Use `.untimeout {member.mention} [reason]` to remove this timeout.",
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Timeout(bot))