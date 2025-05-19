import discord
from discord.ext import commands
import logging
import json
import os
import asyncio
from datetime import datetime, timedelta
from config import CONFIG

logger = logging.getLogger('discord_bot')

class Moderation(commands.Cog):
    """Server moderation commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.moderation_settings = {}
        self.data_file = 'data/moderation_settings.json'
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        
        # Load settings
        self.load_settings()
        
        logger.info("Moderation cog initialized")
        
    def load_settings(self):
        """Load moderation settings from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    self.moderation_settings = json.load(f)
            else:
                self.moderation_settings = {}
                self.save_settings()
        except Exception as e:
            logger.error(f"Error loading moderation settings: {e}")
            self.moderation_settings = {}
            
    def save_settings(self):
        """Save moderation settings to file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.moderation_settings, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving moderation settings: {e}")
    
    @commands.group(name="mod", invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def mod(self, ctx):
        """Moderation commands"""
        embed = discord.Embed(
            title="Moderation Commands",
            description="Manage your server with these moderation commands",
            color=CONFIG['colors']['default']
        )
        
        # Add command examples
        commands = [
            f"`{CONFIG['prefix']}mod warn @user <reason>` - Warn a member",
            f"`{CONFIG['prefix']}mod warnings @user` - Check a member's warnings",
            f"`{CONFIG['prefix']}mod clearwarnings @user` - Clear a member's warnings",
            f"`{CONFIG['prefix']}mod kick @user <reason>` - Kick a member",
            f"`{CONFIG['prefix']}mod ban @user <reason>` - Ban a member",
            f"`{CONFIG['prefix']}mod unban User#1234` - Unban a member",
            f"`{CONFIG['prefix']}mod mute @user <duration> <reason>` - Mute a member",
            f"`{CONFIG['prefix']}mod unmute @user` - Unmute a member",
            f"`{CONFIG['prefix']}mod purge <number>` - Delete messages",
            f"`{CONFIG['prefix']}mod slowmode <seconds>` - Set channel slowmode"
        ]
        
        embed.add_field(
            name="Available Commands",
            value="\n".join(commands),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @mod.command(name="warn")
    @commands.has_permissions(kick_members=True)
    async def warn_member(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Warn a member
        
        Args:
            member: The member to warn
            reason: The reason for the warning
        """
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)
        
        # Initialize guild and user entries if needed
        if guild_id not in self.moderation_settings:
            self.moderation_settings[guild_id] = {"warnings": {}}
            
        if "warnings" not in self.moderation_settings[guild_id]:
            self.moderation_settings[guild_id]["warnings"] = {}
            
        if user_id not in self.moderation_settings[guild_id]["warnings"]:
            self.moderation_settings[guild_id]["warnings"][user_id] = []
        
        # Add warning
        warning = {
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
            "moderator_id": str(ctx.author.id),
            "moderator_name": str(ctx.author)
        }
        
        self.moderation_settings[guild_id]["warnings"][user_id].append(warning)
        self.save_settings()
        
        # Create warning embed
        embed = discord.Embed(
            title=f"⚠️ Warning",
            description=f"{member.mention} has been warned.",
            color=CONFIG['colors']['warning']
        )
        
        embed.add_field(
            name="Reason",
            value=reason,
            inline=False
        )
        
        embed.add_field(
            name="Warnings",
            value=f"This user now has {len(self.moderation_settings[guild_id]['warnings'][user_id])} warnings",
            inline=False
        )
        
        # Try to DM the user
        try:
            user_embed = discord.Embed(
                title=f"⚠️ Warning from {ctx.guild.name}",
                description=f"You have received a warning from a moderator.",
                color=CONFIG['colors']['warning']
            )
            
            user_embed.add_field(
                name="Reason",
                value=reason,
                inline=False
            )
            
            user_embed.add_field(
                name="Warned by",
                value=ctx.author.mention,
                inline=False
            )
            
            await member.send(embed=user_embed)
            embed.set_footer(text="User has been notified via DM")
        except Exception:
            embed.set_footer(text="Could not send DM to user")
            
        await ctx.send(embed=embed)
    
    @mod.command(name="warnings")
    @commands.has_permissions(kick_members=True)
    async def view_warnings(self, ctx, member: discord.Member):
        """View warnings for a member
        
        Args:
            member: The member to check warnings for
        """
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)
        
        # Check if guild and user have warnings
        if (guild_id not in self.moderation_settings or
            "warnings" not in self.moderation_settings[guild_id] or
            user_id not in self.moderation_settings[guild_id]["warnings"] or
            not self.moderation_settings[guild_id]["warnings"][user_id]):
            
            embed = discord.Embed(
                title=f"Warnings for {member}",
                description=f"{member.mention} has no warnings.",
                color=CONFIG['colors']['success']
            )
            
            await ctx.send(embed=embed)
            return
        
        # Create warnings embed
        embed = discord.Embed(
            title=f"Warnings for {member}",
            description=f"{member.mention} has {len(self.moderation_settings[guild_id]['warnings'][user_id])} warnings.",
            color=CONFIG['colors']['warning']
        )
        
        # Add each warning
        for i, warning in enumerate(self.moderation_settings[guild_id]["warnings"][user_id], 1):
            # Parse timestamp
            try:
                timestamp = datetime.fromisoformat(warning["timestamp"])
                time_str = timestamp.strftime("%Y-%m-%d %H:%M UTC")
            except:
                time_str = "Unknown date"
                
            # Add warning field
            embed.add_field(
                name=f"Warning #{i}",
                value=f"**Reason:** {warning['reason']}\n**By:** {warning.get('moderator_name', 'Unknown')}\n**Date:** {time_str}",
                inline=False
            )
            
        await ctx.send(embed=embed)
    
    @mod.command(name="clearwarnings")
    @commands.has_permissions(kick_members=True)
    async def clear_warnings(self, ctx, member: discord.Member):
        """Clear warnings for a member
        
        Args:
            member: The member to clear warnings for
        """
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)
        
        # Check if guild and user have warnings
        if (guild_id not in self.moderation_settings or
            "warnings" not in self.moderation_settings[guild_id] or
            user_id not in self.moderation_settings[guild_id]["warnings"] or
            not self.moderation_settings[guild_id]["warnings"][user_id]):
            
            embed = discord.Embed(
                title=f"Warnings for {member}",
                description=f"{member.mention} already has no warnings.",
                color=CONFIG['colors']['success']
            )
            
            await ctx.send(embed=embed)
            return
        
        # Get warning count
        warning_count = len(self.moderation_settings[guild_id]["warnings"][user_id])
        
        # Clear warnings
        self.moderation_settings[guild_id]["warnings"][user_id] = []
        self.save_settings()
        
        # Create embed
        embed = discord.Embed(
            title=f"✅ Warnings Cleared",
            description=f"Cleared {warning_count} warnings for {member.mention}.",
            color=CONFIG['colors']['success']
        )
        
        await ctx.send(embed=embed)
    
    @mod.command(name="kick")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick_member(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Kick a member from the server
        
        Args:
            member: The member to kick
            reason: The reason for the kick
        """
        # Check if user can be kicked
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Permission Error",
                description="You can't kick members with a higher or equal role to yours.",
                color=CONFIG['colors']['error']
            )
            await ctx.send(embed=embed)
            return
            
        # Create kick embed
        embed = discord.Embed(
            title=f"👢 Member Kicked",
            description=f"{member.mention} has been kicked from the server.",
            color=CONFIG['colors']['error']
        )
        
        embed.add_field(
            name="Reason",
            value=reason,
            inline=False
        )
        
        # Try to DM the user
        try:
            user_embed = discord.Embed(
                title=f"👢 Kicked from {ctx.guild.name}",
                description=f"You have been kicked from the server.",
                color=CONFIG['colors']['error']
            )
            
            user_embed.add_field(
                name="Reason",
                value=reason,
                inline=False
            )
            
            await member.send(embed=user_embed)
            embed.set_footer(text="User has been notified via DM")
        except Exception:
            embed.set_footer(text="Could not send DM to user")
        
        # Kick the member
        try:
            await member.kick(reason=reason)
            await ctx.send(embed=embed)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=f"Could not kick {member.mention}: {str(e)}",
                color=CONFIG['colors']['error']
            )
            await ctx.send(embed=error_embed)
    
    @mod.command(name="ban")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban_member(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Ban a member from the server
        
        Args:
            member: The member to ban
            reason: The reason for the ban
        """
        # Check if user can be banned
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Permission Error",
                description="You can't ban members with a higher or equal role to yours.",
                color=CONFIG['colors']['error']
            )
            await ctx.send(embed=embed)
            return
            
        # Create ban embed
        embed = discord.Embed(
            title=f"🔨 Member Banned",
            description=f"{member.mention} has been banned from the server.",
            color=CONFIG['colors']['error']
        )
        
        embed.add_field(
            name="Reason",
            value=reason,
            inline=False
        )
        
        # Try to DM the user
        try:
            user_embed = discord.Embed(
                title=f"🔨 Banned from {ctx.guild.name}",
                description=f"You have been banned from the server.",
                color=CONFIG['colors']['error']
            )
            
            user_embed.add_field(
                name="Reason",
                value=reason,
                inline=False
            )
            
            await member.send(embed=user_embed)
            embed.set_footer(text="User has been notified via DM")
        except Exception:
            embed.set_footer(text="Could not send DM to user")
        
        # Ban the member
        try:
            await member.ban(reason=reason)
            await ctx.send(embed=embed)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=f"Could not ban {member.mention}: {str(e)}",
                color=CONFIG['colors']['error']
            )
            await ctx.send(embed=error_embed)
    
    @mod.command(name="unban")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban_member(self, ctx, *, user_name):
        """Unban a member from the server
        
        Args:
            user_name: The username of the banned member (e.g. User#1234)
        """
        # Get ban list
        banned_users = [entry async for entry in ctx.guild.bans()]
        
        # Find user in ban list
        for ban_entry in banned_users:
            user = ban_entry.user
            
            # Check if username matches
            if user.name.lower() == user_name.lower() or str(user).lower() == user_name.lower():
                # Unban the user
                try:
                    await ctx.guild.unban(user)
                    
                    embed = discord.Embed(
                        title=f"✅ User Unbanned",
                        description=f"{user} has been unbanned from the server.",
                        color=CONFIG['colors']['success']
                    )
                    
                    await ctx.send(embed=embed)
                    return
                except Exception as e:
                    error_embed = discord.Embed(
                        title="❌ Error",
                        description=f"Could not unban {user}: {str(e)}",
                        color=CONFIG['colors']['error']
                    )
                    await ctx.send(embed=error_embed)
                    return
        
        # User not found
        embed = discord.Embed(
            title="❌ Not Found",
            description=f"Could not find a banned user with the name '{user_name}'. Please check the spelling.",
            color=CONFIG['colors']['error']
        )
        
        await ctx.send(embed=embed)
    
    @mod.command(name="purge")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge_messages(self, ctx, amount: int):
        """Delete a number of messages from the channel
        
        Args:
            amount: The number of messages to delete (1-100)
        """
        # Check amount
        if amount < 1 or amount > 100:
            embed = discord.Embed(
                title="❌ Invalid Amount",
                description="You can only delete between 1 and 100 messages at a time.",
                color=CONFIG['colors']['error']
            )
            await ctx.send(embed=embed)
            return
        
        # Delete messages
        try:
            deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include command message
            
            embed = discord.Embed(
                title=f"🧹 Channel Purged",
                description=f"Deleted {len(deleted) - 1} messages.",
                color=CONFIG['colors']['success']
            )
            
            # Send and delete confirmation message
            confirmation = await ctx.send(embed=embed)
            await asyncio.sleep(3)
            await confirmation.delete()
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=f"Could not delete messages: {str(e)}",
                color=CONFIG['colors']['error']
            )
            await ctx.send(embed=error_embed)
    
    @mod.command(name="slowmode")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def set_slowmode(self, ctx, seconds: int):
        """Set the slowmode delay for the current channel
        
        Args:
            seconds: The slowmode delay in seconds (0-21600)
        """
        # Check delay
        if seconds < 0 or seconds > 21600:
            embed = discord.Embed(
                title="❌ Invalid Delay",
                description="Slowmode delay must be between 0 and 21600 seconds (6 hours).",
                color=CONFIG['colors']['error']
            )
            await ctx.send(embed=embed)
            return
        
        # Set slowmode
        try:
            await ctx.channel.edit(slowmode_delay=seconds)
            
            if seconds == 0:
                description = "Slowmode has been turned off for this channel."
            else:
                description = f"Slowmode set to {seconds} seconds for this channel."
                
            embed = discord.Embed(
                title=f"⏱️ Slowmode Updated",
                description=description,
                color=CONFIG['colors']['success']
            )
            
            await ctx.send(embed=embed)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=f"Could not set slowmode: {str(e)}",
                color=CONFIG['colors']['error']
            )
            await ctx.send(embed=error_embed)
    
    @mod.command(name="mute")
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def mute_member(self, ctx, member: discord.Member, duration: str = None, *, reason="No reason provided"):
        """Mute a member in the server
        
        Args:
            member: The member to mute
            duration: The duration of the mute (e.g. 10m, 1h, 1d)
            reason: The reason for the mute
        """
        # Check if user can be muted
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = discord.Embed(
                title="❌ Permission Error",
                description="You can't mute members with a higher or equal role to yours.",
                color=CONFIG['colors']['error']
            )
            await ctx.send(embed=embed)
            return
        
        guild_id = str(ctx.guild.id)
        
        # Get or create muted role
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if muted_role is None:
            try:
                # Create muted role
                muted_role = await ctx.guild.create_role(
                    name="Muted",
                    reason="Created for mute command"
                )
                
                # Set role permissions for all channels
                for channel in ctx.guild.channels:
                    await channel.set_permissions(muted_role, speak=False, send_messages=False, add_reactions=False)
                    
            except Exception as e:
                error_embed = discord.Embed(
                    title="❌ Error",
                    description=f"Could not create Muted role: {str(e)}",
                    color=CONFIG['colors']['error']
                )
                await ctx.send(embed=error_embed)
                return
        
        # Parse duration
        seconds = 0
        if duration:
            time_units = {
                's': 1,
                'm': 60,
                'h': 3600,
                'd': 86400
            }
            
            try:
                unit = duration[-1].lower()
                value = int(duration[:-1])
                
                if unit in time_units:
                    seconds = value * time_units[unit]
                else:
                    seconds = int(duration)  # Try to parse as seconds
            except:
                embed = discord.Embed(
                    title="❌ Invalid Duration",
                    description="Please specify a valid duration (e.g. 10s, 5m, 1h, 1d).",
                    color=CONFIG['colors']['error']
                )
                await ctx.send(embed=embed)
                return
        
        # Add role to member
        try:
            await member.add_roles(muted_role, reason=reason)
            
            # Create mute embed
            if duration:
                description = f"{member.mention} has been muted for {duration}."
                unmute_time = datetime.utcnow() + timedelta(seconds=seconds)
                time_str = unmute_time.strftime("%Y-%m-%d %H:%M UTC")
            else:
                description = f"{member.mention} has been muted indefinitely."
                time_str = "Indefinite"
                
            embed = discord.Embed(
                title=f"🔇 Member Muted",
                description=description,
                color=CONFIG['colors']['error']
            )
            
            embed.add_field(
                name="Reason",
                value=reason,
                inline=False
            )
            
            embed.add_field(
                name="Duration",
                value=f"Until: {time_str}" if duration else "Indefinite",
                inline=False
            )
            
            # Try to DM the user
            try:
                user_embed = discord.Embed(
                    title=f"🔇 Muted in {ctx.guild.name}",
                    description=f"You have been muted in the server.",
                    color=CONFIG['colors']['error']
                )
                
                user_embed.add_field(
                    name="Reason",
                    value=reason,
                    inline=False
                )
                
                user_embed.add_field(
                    name="Duration",
                    value=f"Until: {time_str}" if duration else "Indefinite",
                    inline=False
                )
                
                await member.send(embed=user_embed)
                embed.set_footer(text="User has been notified via DM")
            except Exception:
                embed.set_footer(text="Could not send DM to user")
            
            await ctx.send(embed=embed)
            
            # Schedule unmute if duration was specified
            if duration:
                # Initialize mutes in settings
                if guild_id not in self.moderation_settings:
                    self.moderation_settings[guild_id] = {}
                    
                if "mutes" not in self.moderation_settings[guild_id]:
                    self.moderation_settings[guild_id]["mutes"] = {}
                
                # Store mute info
                self.moderation_settings[guild_id]["mutes"][str(member.id)] = {
                    "unmute_time": unmute_time.isoformat(),
                    "role_id": str(muted_role.id)
                }
                
                self.save_settings()
                
                # Schedule unmute
                await asyncio.sleep(seconds)
                
                # Check if still muted
                if (guild_id in self.moderation_settings and 
                    "mutes" in self.moderation_settings[guild_id] and
                    str(member.id) in self.moderation_settings[guild_id]["mutes"]):
                    
                    # Remove from muted list
                    del self.moderation_settings[guild_id]["mutes"][str(member.id)]
                    self.save_settings()
                    
                    # Remove role if member still in server
                    try:
                        member = ctx.guild.get_member(member.id)
                        if member and muted_role in member.roles:
                            await member.remove_roles(muted_role, reason="Mute duration expired")
                            
                            # Notify channel
                            unmute_embed = discord.Embed(
                                title=f"🔊 Member Unmuted",
                                description=f"{member.mention} has been automatically unmuted (duration expired).",
                                color=CONFIG['colors']['success']
                            )
                            
                            await ctx.send(embed=unmute_embed)
                    except Exception as e:
                        logger.error(f"Failed to auto-unmute {member.id}: {e}")
                
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=f"Could not mute {member.mention}: {str(e)}",
                color=CONFIG['colors']['error']
            )
            await ctx.send(embed=error_embed)
    
    @mod.command(name="unmute")
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def unmute_member(self, ctx, member: discord.Member):
        """Unmute a muted member
        
        Args:
            member: The member to unmute
        """
        guild_id = str(ctx.guild.id)
        
        # Get muted role
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if muted_role is None:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Could not find a role named 'Muted'.",
                color=CONFIG['colors']['error']
            )
            await ctx.send(embed=embed)
            return
        
        # Check if member has the muted role
        if muted_role not in member.roles:
            embed = discord.Embed(
                title="❌ Not Muted",
                description=f"{member.mention} is not muted.",
                color=CONFIG['colors']['error']
            )
            await ctx.send(embed=embed)
            return
        
        # Remove role
        try:
            await member.remove_roles(muted_role, reason=f"Unmuted by {ctx.author}")
            
            # Remove from muted list if present
            if (guild_id in self.moderation_settings and 
                "mutes" in self.moderation_settings[guild_id] and
                str(member.id) in self.moderation_settings[guild_id]["mutes"]):
                
                del self.moderation_settings[guild_id]["mutes"][str(member.id)]
                self.save_settings()
            
            # Create unmute embed
            embed = discord.Embed(
                title=f"🔊 Member Unmuted",
                description=f"{member.mention} has been unmuted.",
                color=CONFIG['colors']['success']
            )
            
            await ctx.send(embed=embed)
            
            # Try to DM the user
            try:
                user_embed = discord.Embed(
                    title=f"🔊 Unmuted in {ctx.guild.name}",
                    description=f"You have been unmuted in the server.",
                    color=CONFIG['colors']['success']
                )
                
                await member.send(embed=user_embed)
            except Exception:
                pass
                
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=f"Could not unmute {member.mention}: {str(e)}",
                color=CONFIG['colors']['error']
            )
            await ctx.send(embed=error_embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))