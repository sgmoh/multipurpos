import discord
from discord.ext import commands
import random
import logging
import datetime
import json
import os
from utils.helpers import Helpers
from utils.data_manager import DataManager
from utils.embed_creator import EmbedCreator
from config import CONFIG

logger = logging.getLogger('discord_bot')

class Levels(commands.Cog):
    """Level tracking system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_manager = DataManager("bot_database.json")
        self.xp_cooldown = commands.CooldownMapping.from_cooldown(
            1, 60, commands.BucketType.member
        )
        logger.info("Levels cog initialized")
        
    @commands.Cog.listener()
    async def on_message(self, message):
        """Award XP for messages"""
        # Don't process commands or bot messages
        if message.author.bot or not message.guild:
            return
            
        # Get guild settings
        guild_key = f"guild_{message.guild.id}"
        guild_settings = await self.data_manager.get(guild_key, {})
        
        # Check if leveling is enabled for this guild
        if guild_settings.get('leveling_enabled', True) is False:
            return
            
        # Apply cooldown to prevent XP farming
        bucket = self.xp_cooldown.get_bucket(message)
        if bucket.update_rate_limit():
            return
            
        # Calculate random XP gain
        xp_gain = 15 + random.randint(0, 5)  # Base XP (15) + random bonus (0-5)
        
        # Get user's current XP and level
        user_key = f"user_{message.guild.id}_{message.author.id}"
        user_data = await self.data_manager.get(user_key, {'xp': 0, 'level': 0, 'messages': 0})
        
        # Update message count
        user_data['messages'] = user_data.get('messages', 0) + 1
        
        # Get current XP and level
        current_xp = user_data.get('xp', 0)
        current_level = user_data.get('level', 0)
        
        # Add XP
        new_xp = current_xp + xp_gain
        user_data['xp'] = new_xp
        
        # Calculate new level
        new_level = Helpers.get_level_from_xp(new_xp)
        user_data['level'] = new_level
        
        # Save updated user data
        await self.data_manager.set(user_key, user_data)
        
        # Check for level up
        if new_level > current_level:
            # Determine which channel to send the level up message to
            level_up_channel = None
            
            # First check for a server-specific level up channel
            level_up_channel_id = guild_settings.get('level_up_channel_id')
            if level_up_channel_id:
                level_up_channel = message.guild.get_channel(level_up_channel_id)
                
            # If no server-specific channel, check global config
            if not level_up_channel and CONFIG['levels']['level_up_channel_id']:
                level_up_channel = message.guild.get_channel(CONFIG['levels']['level_up_channel_id'])
                
            # Create level up embed
            embed = EmbedCreator.create_level_up_embed(message.author, new_level)
            
            # Send to appropriate channel
            if level_up_channel:
                await level_up_channel.send(embed=embed)
            else:
                # If no dedicated channel, send to the current channel
                await message.channel.send(embed=embed)
                
            # Check for level roles
            for level, role_id in CONFIG['levels']['level_roles'].items():
                if new_level >= level and role_id:
                    try:
                        role = message.guild.get_role(role_id)
                        if role and role not in message.author.roles:
                            await message.author.add_roles(role)
                            logger.info(f"Added role {role.name} to {message.author} for reaching level {level}")
                    except Exception as e:
                        logger.error(f"Error adding level role: {e}")
    
    @commands.command(name="level", aliases=["rank", "lvl"])
    async def level(self, ctx, member: discord.Member = None):
        """Check level and XP for a user
        
        Args:
            member: The member to check. If None, checks the command user.
        """
        if member is None:
            member = ctx.author
            
        # Get user data
        user_key = f"user_{ctx.guild.id}_{member.id}"
        user_data = await self.data_manager.get(user_key, {'xp': 0, 'level': 0, 'messages': 0})
        
        xp = user_data.get('xp', 0)
        level = user_data.get('level', 0)
        messages = user_data.get('messages', 0)
        
        # Calculate XP for next level
        next_level_xp = Helpers.get_xp_for_level(level + 1)
        current_level_xp = Helpers.get_xp_for_level(level)
        
        # Calculate progress to next level
        xp_needed = next_level_xp - current_level_xp
        xp_progress = xp - current_level_xp
        
        # Calculate percentage
        progress_percentage = min(100, int((xp_progress / max(1, xp_needed)) * 100))
        
        # Create progress bar
        bar_length = 20
        filled_blocks = int(bar_length * progress_percentage / 100)
        progress_bar = "█" * filled_blocks + "░" * (bar_length - filled_blocks)
        
        # Create embed
        embed = discord.Embed(
            title=f"{member.display_name}'s Level Stats",
            description=f"**Level:** {level}\n**XP:** {xp}/{next_level_xp}\n**Messages:** {messages}",
            color=CONFIG['colors']['default'],
            timestamp=datetime.datetime.utcnow()
        )
        
        # Add progress bar
        embed.add_field(
            name=f"Progress to Level {level+1}",
            value=f"`{progress_bar}` {progress_percentage}%",
            inline=False
        )
        
        # Set thumbnail to member avatar
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Set footer
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="leaderboard", aliases=["lb", "top"])
    async def leaderboard(self, ctx, type: str = "levels"):
        """Show the server leaderboard
        
        Args:
            type: The type of leaderboard to show (levels, messages, invites)
        """
        if type.lower() not in ["levels", "messages", "invites"]:
            type = "levels"  # Default to levels
            
        # Get all data
        all_data = await self.data_manager.get_all()
        
        # Filter users from this guild
        guild_users = []
        for key, data in all_data.items():
            if key.startswith(f"user_{ctx.guild.id}_"):
                try:
                    user_id = int(key.split('_')[2])
                    
                    if type.lower() == "levels":
                        value = data.get('level', 0)
                        secondary = data.get('xp', 0)
                    elif type.lower() == "messages":
                        value = data.get('messages', 0)
                        secondary = 0
                    # Invites are handled by a different cog
                    else:
                        continue
                        
                    guild_users.append({
                        'user_id': user_id,
                        'value': value,
                        'secondary': secondary
                    })
                except (IndexError, ValueError):
                    continue
        
        # Sort users by value (descending)
        guild_users.sort(key=lambda x: (x['value'], x['secondary']), reverse=True)
        
        # Take top 10
        top_users = guild_users[:10]
        
        if not top_users:
            await ctx.send(f"No data available for the {type} leaderboard.")
            return
            
        # Create embed
        embed = discord.Embed(
            title=f"{type.title()} Leaderboard",
            description=f"Top members in {ctx.guild.name}",
            color=CONFIG['colors']['default'],
            timestamp=datetime.datetime.utcnow()
        )
        
        # Format leaderboard entries
        lb_text = ""
        for i, user_data in enumerate(top_users):
            user_id = user_data['user_id']
            value = user_data['value']
            
            # Get medal emoji based on position
            if i == 0:
                medal = "🥇"
            elif i == 1:
                medal = "🥈"
            elif i == 2:
                medal = "🥉"
            else:
                medal = f"`{i+1}.`"
                
            lb_text += f"{medal} <@{user_id}> - **{value}**\n"
            
        embed.add_field(name="Rankings", value=lb_text, inline=False)
        
        # Set footer
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.group(name="leveling", invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def leveling(self, ctx):
        """Manage leveling system settings"""
        # Show current leveling settings
        guild_key = f"guild_{ctx.guild.id}"
        guild_settings = await self.data_manager.get(guild_key, {})
        
        # Get current status
        enabled = guild_settings.get('leveling_enabled', True)
        level_up_channel_id = guild_settings.get('level_up_channel_id', None)
        level_up_channel = ctx.guild.get_channel(level_up_channel_id) if level_up_channel_id else None
        
        # Create settings embed
        embed = discord.Embed(
            title="Leveling System Settings",
            description="Current configuration for the leveling system",
            color=CONFIG['colors']['default']
        )
        
        # Add status field
        embed.add_field(
            name="Status",
            value="✅ Enabled" if enabled else "❌ Disabled",
            inline=True
        )
        
        # Add level-up channel field
        if level_up_channel:
            channel_value = level_up_channel.mention
        else:
            channel_value = "Same channel as message (default)"
            
        embed.add_field(
            name="Level-Up Channel",
            value=channel_value,
            inline=True
        )
        
        # Add command examples
        examples = [
            f"`{CONFIG['prefix']}leveling on` - Enable leveling system",
            f"`{CONFIG['prefix']}leveling off` - Disable leveling system",
            f"`{CONFIG['prefix']}leveling channel #level-ups` - Set level-up channel",
            f"`{CONFIG['prefix']}leveling channel reset` - Reset to default (current channel)"
        ]
        
        embed.add_field(
            name="Commands",
            value="\n".join(examples),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @leveling.command(name="on")
    @commands.has_permissions(manage_guild=True)
    async def leveling_on(self, ctx):
        """Enable the leveling system"""
        guild_key = f"guild_{ctx.guild.id}"
        guild_settings = await self.data_manager.get(guild_key, {})
        
        # Enable leveling
        guild_settings['leveling_enabled'] = True
        await self.data_manager.set(guild_key, guild_settings)
        
        # Send confirmation
        embed = discord.Embed(
            title="✅ Leveling System Enabled",
            description="Members will now earn XP and levels from sending messages.",
            color=CONFIG['colors']['success']
        )
        
        await ctx.send(embed=embed)
    
    @leveling.command(name="off")
    @commands.has_permissions(manage_guild=True)
    async def leveling_off(self, ctx):
        """Disable the leveling system"""
        guild_key = f"guild_{ctx.guild.id}"
        guild_settings = await self.data_manager.get(guild_key, {})
        
        # Disable leveling
        guild_settings['leveling_enabled'] = False
        await self.data_manager.set(guild_key, guild_settings)
        
        # Send confirmation
        embed = discord.Embed(
            title="❌ Leveling System Disabled",
            description="Members will no longer earn XP and levels from sending messages.",
            color=CONFIG['colors']['error']
        )
        
        await ctx.send(embed=embed)
    
    @leveling.command(name="channel")
    @commands.has_permissions(manage_guild=True)
    async def leveling_channel(self, ctx, channel: discord.TextChannel = None):
        """Set the channel for level-up notifications
        
        Args:
            channel: The channel for level-up messages. Can be "reset" to use message channel.
        """
        guild_key = f"guild_{ctx.guild.id}"
        guild_settings = await self.data_manager.get(guild_key, {})
        
        # Check if resetting to default
        if isinstance(channel, str) and channel.lower() == "reset":
            if 'level_up_channel_id' in guild_settings:
                del guild_settings['level_up_channel_id']
                
            embed = discord.Embed(
                title="ℹ️ Level-Up Channel Reset",
                description="Level-up messages will now be sent in the same channel where the message was sent.",
                color=CONFIG['colors']['info']
            )
        elif channel:
            # Set new channel
            guild_settings['level_up_channel_id'] = channel.id
            
            embed = discord.Embed(
                title="✅ Level-Up Channel Set",
                description=f"Level-up messages will now be sent in {channel.mention}.",
                color=CONFIG['colors']['success']
            )
        else:
            # Show current setting
            current_channel_id = guild_settings.get('level_up_channel_id')
            current_channel = ctx.guild.get_channel(current_channel_id) if current_channel_id else None
            
            if current_channel:
                description = f"Level-up messages are currently sent in {current_channel.mention}."
            else:
                description = "Level-up messages are currently sent in the same channel where the message was sent."
                
            embed = discord.Embed(
                title="ℹ️ Level-Up Channel",
                description=description,
                color=CONFIG['colors']['info']
            )
            
            # Add usage example
            embed.add_field(
                name="Usage",
                value=f"`{CONFIG['prefix']}leveling channel #channel` - Set a specific channel\n"
                     f"`{CONFIG['prefix']}leveling channel reset` - Use message channel (default)",
                inline=False
            )
            
            await ctx.send(embed=embed)
            return
            
        # Save settings
        await self.data_manager.set(guild_key, guild_settings)
        
        # Send confirmation
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Levels(bot))