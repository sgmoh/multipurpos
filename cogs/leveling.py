import discord
from discord.ext import commands
import asyncio
import random
import json
import os
import logging
from datetime import datetime
from utils.data_manager import DataManager
from utils.embed_creator import EmbedCreator
from utils.helpers import Helpers
from config import LEVEL_DATA_FILE, COLORS

logger = logging.getLogger('discord_bot')

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_manager = DataManager(LEVEL_DATA_FILE)
        self.xp_cooldown = commands.CooldownMapping.from_cooldown(1, 60, commands.BucketType.member)
        self.xp_per_message = 15  # Base XP per message
        self.xp_randomizer = 5    # Random XP bonus
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Give XP when a member sends a message."""
        # Don't give XP for bot messages or DMs
        if message.author.bot or not message.guild:
            return
        
        # Check if the channel is excluded from XP gain
        guild_settings = await self.data_manager.get(f"guild_{message.guild.id}", {})
        
        # If leveling is disabled, don't give XP
        if not guild_settings.get('enabled', True):
            return
        
        # Apply cooldown to prevent XP farming
        bucket = self.xp_cooldown.get_bucket(message)
        if bucket.update_rate_limit():
            return
        
        # Calculate XP to give
        xp_gain = self.xp_per_message + random.randint(0, self.xp_randomizer)
        
        # Get user's current XP
        user_key = f"user_{message.guild.id}_{message.author.id}"
        user_data = await self.data_manager.get(user_key, {'xp': 0, 'level': 0, 'messages': 0})
        
        # Increment message count
        user_data['messages'] = user_data.get('messages', 0) + 1
        
        # Add XP
        old_xp = user_data.get('xp', 0)
        new_xp = old_xp + xp_gain
        user_data['xp'] = new_xp
        
        # Calculate current level
        old_level = user_data.get('level', 0)
        new_level = Helpers.get_level_from_xp(new_xp)
        user_data['level'] = new_level
        
        # Save updated user data
        await self.data_manager.set(user_key, user_data)
        
        # Check for level up
        if new_level > old_level:
            # Get level up channel
            level_up_channel_id = guild_settings.get('level_up_channel_id')
            level_up_channel = None
            
            if level_up_channel_id:
                level_up_channel = message.guild.get_channel(int(level_up_channel_id))
            
            # Send level up message
            if level_up_channel:
                # Send in designated channel
                embed = EmbedCreator.create_level_up_embed(message.author, new_level)
                await level_up_channel.send(embed=embed)
            else:
                # Send in the current channel
                embed = EmbedCreator.create_level_up_embed(message.author, new_level)
                await message.channel.send(embed=embed)
    
    @commands.command(name="level", aliases=["rank", "lvl"])
    async def level(self, ctx, member: discord.Member = None):
        """Check your or another user's level and XP."""
        # If no member specified, use the command invoker
        if member is None:
            member = ctx.author
        
        # Get user data
        user_key = f"user_{ctx.guild.id}_{member.id}"
        user_data = await self.data_manager.get(user_key, {'xp': 0, 'level': 0, 'messages': 0})
        
        xp = user_data.get('xp', 0)
        level = user_data.get('level', 0)
        messages = user_data.get('messages', 0)
        
        # Calculate XP needed for next level
        next_level_xp = Helpers.get_xp_for_level(level + 1)
        current_level_xp = Helpers.get_xp_for_level(level)
        xp_progress = xp - current_level_xp
        xp_needed = next_level_xp - current_level_xp
        progress_percentage = int((xp_progress / xp_needed) * 100) if xp_needed > 0 else 100
        
        # Create progress bar
        progress_bar_length = 20
        filled_length = int(progress_bar_length * progress_percentage / 100)
        bar = '█' * filled_length + '░' * (progress_bar_length - filled_length)
        
        # Create embed
        embed = discord.Embed(
            title=f"{member.display_name}'s Level",
            color=COLORS["primary"],
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Level", value=str(level), inline=True)
        embed.add_field(name="XP", value=f"{xp}/{next_level_xp}", inline=True)
        embed.add_field(name="Messages", value=str(messages), inline=True)
        embed.add_field(name="Progress to Next Level", value=f"`{bar}` {progress_percentage}%", inline=False)
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="leaderboard", aliases=["top", "lb"])
    async def leaderboard(self, ctx, category="level"):
        """Show the server leaderboard."""
        guild_id = ctx.guild.id
        
        if category.lower() not in ["level", "xp", "messages"]:
            category = "level"  # Default to level
        
        # Get all user data for this guild
        all_data = await self.data_manager.get_all()
        guild_users = []
        
        for key, value in all_data.items():
            if key.startswith(f"user_{guild_id}_"):
                user_id = int(key.split('_')[2])
                guild_users.append({
                    "user_id": user_id,
                    "xp": value.get('xp', 0),
                    "level": value.get('level', 0),
                    "messages": value.get('messages', 0)
                })
        
        # Sort by the requested category
        if category.lower() in ["level", "xp"]:
            guild_users.sort(key=lambda x: x["xp"], reverse=True)
            leaderboard_type = "Levels"
            display_key = "level"
        else:  # messages
            guild_users.sort(key=lambda x: x["messages"], reverse=True)
            leaderboard_type = "Messages"
            display_key = "messages"
        
        # Create the leaderboard entries
        entries = []
        for user_data in guild_users[:10]:  # Get top 10
            user_id = user_data["user_id"]
            count = user_data[display_key]
            entries.append({"user_id": user_id, "count": count})
        
        # Create the embed
        embed = EmbedCreator.create_leaderboard_embed(leaderboard_type, entries)
        
        await ctx.send(embed=embed)
    
    @commands.group(name="leveling", invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def leveling(self, ctx):
        """Manage leveling system settings."""
        await ctx.send_help(ctx.command)
    
    @leveling.command(name="on")
    @commands.has_permissions(manage_guild=True)
    async def leveling_on(self, ctx):
        """Enable the leveling system."""
        guild_id = ctx.guild.id
        guild_key = f"guild_{guild_id}"
        
        guild_settings = await self.data_manager.get(guild_key, {})
        guild_settings['enabled'] = True
        
        await self.data_manager.set(guild_key, guild_settings)
        
        embed = EmbedCreator.create_basic_embed(
            title="Leveling System Enabled",
            description="Members will now gain XP and levels from sending messages.",
            color=COLORS["success"]
        )
        
        await ctx.send(embed=embed)
    
    @leveling.command(name="off")
    @commands.has_permissions(manage_guild=True)
    async def leveling_off(self, ctx):
        """Disable the leveling system."""
        guild_id = ctx.guild.id
        guild_key = f"guild_{guild_id}"
        
        guild_settings = await self.data_manager.get(guild_key, {})
        guild_settings['enabled'] = False
        
        await self.data_manager.set(guild_key, guild_settings)
        
        embed = EmbedCreator.create_basic_embed(
            title="Leveling System Disabled",
            description="Members will no longer gain XP and levels from sending messages.",
            color=COLORS["error"]
        )
        
        await ctx.send(embed=embed)
    
    @leveling.command(name="channel")
    @commands.has_permissions(manage_guild=True)
    async def leveling_channel(self, ctx, channel: discord.TextChannel = None):
        """Set the channel for level-up notifications."""
        guild_id = ctx.guild.id
        guild_key = f"guild_{guild_id}"
        
        guild_settings = await self.data_manager.get(guild_key, {})
        
        if channel:
            guild_settings['level_up_channel_id'] = channel.id
            message = f"Level-up notifications will now be sent in {channel.mention}."
            color = COLORS["success"]
        else:
            if 'level_up_channel_id' in guild_settings:
                del guild_settings['level_up_channel_id']
            message = "Level-up notifications will now be sent in the channel where the message was sent."
            color = COLORS["info"]
        
        await self.data_manager.set(guild_key, guild_settings)
        
        embed = EmbedCreator.create_basic_embed(
            title="Level-Up Channel Updated",
            description=message,
            color=color
        )
        
        await ctx.send(embed=embed)
    
    @leveling.command(name="reset")
    @commands.has_permissions(administrator=True)
    async def leveling_reset(self, ctx, member: discord.Member = None):
        """Reset level data for a user or the entire server."""
        guild_id = ctx.guild.id
        
        if member:
            # Reset for specific user
            user_key = f"user_{guild_id}_{member.id}"
            await self.data_manager.delete(user_key)
            
            embed = EmbedCreator.create_basic_embed(
                title="Level Data Reset",
                description=f"Level data for {member.mention} has been reset.",
                color=COLORS["success"]
            )
        else:
            # Confirmation for resetting the entire server
            embed = EmbedCreator.create_basic_embed(
                title="Confirm Reset",
                description="Are you sure you want to reset level data for the entire server? This action cannot be undone.\n\nReply with 'yes' to confirm or 'no' to cancel.",
                color=COLORS["warning"]
            )
            confirm_message = await ctx.send(embed=embed)
            
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["yes", "no"]
            
            try:
                response = await self.bot.wait_for("message", check=check, timeout=30.0)
                if response.content.lower() == "yes":
                    # Reset for entire server
                    all_data = await self.data_manager.get_all()
                    keys_to_delete = [key for key in all_data if key.startswith(f"user_{guild_id}_")]
                    
                    for key in keys_to_delete:
                        await self.data_manager.delete(key)
                    
                    embed = EmbedCreator.create_basic_embed(
                        title="Level Data Reset",
                        description=f"Level data for all members in the server has been reset.",
                        color=COLORS["success"]
                    )
                else:
                    embed = EmbedCreator.create_basic_embed(
                        title="Reset Cancelled",
                        description="Level data reset has been cancelled.",
                        color=COLORS["info"]
                    )
            except asyncio.TimeoutError:
                embed = EmbedCreator.create_basic_embed(
                    title="Reset Cancelled",
                    description="Level data reset has been cancelled due to timeout.",
                    color=COLORS["info"]
                )
        
        await ctx.send(embed=embed)
    
    @level.error
    @leaderboard.error
    @leveling_on.error
    @leveling_off.error
    @leveling_channel.error
    @leveling_reset.error
    async def leveling_error(self, ctx, error):
        """Handle errors in leveling commands."""
        if isinstance(error, commands.MissingPermissions):
            embed = EmbedCreator.create_basic_embed(
                title="Error",
                description="You don't have permission to use this command.",
                color=COLORS["error"]
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = EmbedCreator.create_basic_embed(
                title="Error",
                description="Invalid argument provided. Please check the command usage.",
                color=COLORS["error"]
            )
            await ctx.send(embed=embed)
        else:
            logger.error(f"Leveling command error: {error}")

async def setup(bot):
    await bot.add_cog(Leveling(bot))
