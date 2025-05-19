import discord
from discord.ext import commands
import random
import json
import os
import logging
import math
from datetime import datetime

# Set up logging
logger = logging.getLogger('discord_bot')

class SimpleLevel:
    def __init__(self, user_id, xp=0, level=0, messages=0):
        self.user_id = user_id
        self.xp = xp
        self.level = level
        self.messages = messages
    
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "xp": self.xp,
            "level": self.level,
            "messages": self.messages
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            user_id=data.get("user_id", 0),
            xp=data.get("xp", 0),
            level=data.get("level", 0),
            messages=data.get("messages", 0)
        )

class SimpleLevels(commands.Cog):
    """Level tracking system with dedicated notification channel"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/levels.json"
        self.cooldowns = {}  # Store user cooldowns
        self.level_up_channels = {}  # Store guild-specific level up channels
        self.load_data()
        
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        
        logger.info("SimpleLevels cog initialized")
    
    def load_data(self):
        """Load level data from JSON file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.level_up_channels = data.get("level_up_channels", {})
            else:
                self.level_up_channels = {}
                self.save_data()
        except Exception as e:
            logger.error(f"Error loading level data: {e}")
            self.level_up_channels = {}
    
    def save_data(self):
        """Save level data to JSON file"""
        try:
            data = {
                "level_up_channels": self.level_up_channels
            }
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving level data: {e}")
    
    def get_user_data(self, guild_id, user_id):
        """Get user data from the database or create a new entry"""
        guild_data_file = f"data/guild_{guild_id}_levels.json"
        
        try:
            if os.path.exists(guild_data_file):
                with open(guild_data_file, 'r') as f:
                    all_data = json.load(f)
                    user_data = all_data.get(str(user_id))
                    if user_data:
                        return SimpleLevel.from_dict(user_data)
            else:
                # Create a new guild data file
                with open(guild_data_file, 'w') as f:
                    json.dump({}, f, indent=4)
        except Exception as e:
            logger.error(f"Error retrieving user data: {e}")
        
        # Return a new user object if not found
        return SimpleLevel(user_id=user_id)
    
    def save_user_data(self, guild_id, user_data):
        """Save user data to the database"""
        guild_data_file = f"data/guild_{guild_id}_levels.json"
        
        try:
            # Load existing data
            all_data = {}
            if os.path.exists(guild_data_file):
                with open(guild_data_file, 'r') as f:
                    all_data = json.load(f)
            
            # Update user data
            all_data[str(user_data.user_id)] = user_data.to_dict()
            
            # Save back to file
            with open(guild_data_file, 'w') as f:
                json.dump(all_data, f, indent=4)
                
            return True
        except Exception as e:
            logger.error(f"Error saving user data: {e}")
            return False
    
    def get_level_from_xp(self, xp):
        """Calculate level based on XP"""
        # Simple formula: level = sqrt(xp / 100)
        return int(math.sqrt(xp / 100))
    
    def get_xp_for_level(self, level):
        """Calculate XP needed for a specific level"""
        # XP = level² * 100
        return level * level * 100
    
    def is_on_cooldown(self, user_id):
        """Check if user is on XP cooldown"""
        if user_id in self.cooldowns:
            # Check if 60 seconds have passed since last XP gain
            last_time = self.cooldowns[user_id]
            now = datetime.now().timestamp()
            
            if now - last_time < 60:  # 60 second cooldown
                return True
                
        # Set new cooldown time
        self.cooldowns[user_id] = datetime.now().timestamp()
        return False
    
    def get_level_up_channel(self, guild):
        """Get the level up channel for a guild"""
        # Check if there's a configured channel for this guild
        guild_id_str = str(guild.id)
        
        if guild_id_str in self.level_up_channels:
            channel_id = int(self.level_up_channels[guild_id_str])
            channel = guild.get_channel(channel_id)
            return channel
            
        # Return None if no channel is configured
        return None
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Award XP for messages"""
        # Don't process commands or bot messages
        if message.author.bot or not message.guild:
            return
        
        user_id = message.author.id
        guild_id = message.guild.id
        
        # Check cooldown to prevent XP farming
        if self.is_on_cooldown(user_id):
            return
        
        # Get current user data
        user_data = self.get_user_data(guild_id, user_id)
        
        # Calculate XP to award
        xp_gain = 15 + random.randint(0, 5)  # Base 15 XP + random 0-5 bonus
        
        # Get current values
        old_level = user_data.level
        old_xp = user_data.xp
        
        # Update values
        user_data.xp += xp_gain
        user_data.messages += 1
        user_data.level = self.get_level_from_xp(user_data.xp)
        
        # Save updated data
        self.save_user_data(guild_id, user_data)
        
        # Check for level up
        if user_data.level > old_level:
            # Get the level up channel or use current channel
            level_up_channel = self.get_level_up_channel(message.guild)
            
            # Create level up embed
            embed = discord.Embed(
                title="⬆️ Level Up!",
                description=f"{message.author.mention} Your Level Increased to **{user_data.level}**. Chat More!",
                color=0x57F287
            )
            embed.set_thumbnail(url=message.author.display_avatar.url)
            
            # Send level up message
            if level_up_channel:
                await level_up_channel.send(embed=embed)
            else:
                await message.channel.send(embed=embed)
    
    @commands.command(name="level", aliases=["rank", "lvl"])
    async def level_command(self, ctx, member: discord.Member = None):
        """Check level and XP for a user
        
        Args:
            member: The member to check. If None, checks the command user.
        """
        # Use command invoker if no member specified
        if not member:
            member = ctx.author
            
        # Get user data
        user_data = self.get_user_data(ctx.guild.id, member.id)
        
        # Calculate progress to next level
        current_level_xp = self.get_xp_for_level(user_data.level)
        next_level_xp = self.get_xp_for_level(user_data.level + 1)
        xp_progress = user_data.xp - current_level_xp
        xp_needed = next_level_xp - current_level_xp
        
        # Calculate percentage (avoid division by zero)
        if xp_needed == 0:
            percentage = 100
        else:
            percentage = int((xp_progress / xp_needed) * 100)
            
        # Create progress bar
        bar_length = 20
        filled_blocks = int(bar_length * percentage / 100)
        progress_bar = "█" * filled_blocks + "░" * (bar_length - filled_blocks)
        
        # Create embed
        embed = discord.Embed(
            title=f"{member.display_name}'s Level Stats",
            description=f"**Level:** {user_data.level}\n**XP:** {user_data.xp}/{next_level_xp}\n**Messages:** {user_data.messages}",
            color=0x5865F2,
            timestamp=datetime.utcnow()
        )
        
        # Add progress bar
        embed.add_field(
            name=f"Progress to Level {user_data.level + 1}",
            value=f"`{progress_bar}` {percentage}%",
            inline=False
        )
        
        # Set thumbnail to member avatar
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Set footer
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="leaderboard", aliases=["lb", "top"])
    async def leaderboard_command(self, ctx, type="level"):
        """Show the server leaderboard
        
        Args:
            type: The type of leaderboard (level or messages)
        """
        guild_id = ctx.guild.id
        guild_data_file = f"data/guild_{guild_id}_levels.json"
        
        if not os.path.exists(guild_data_file):
            await ctx.send("No leveling data found for this server.")
            return
            
        try:
            with open(guild_data_file, 'r') as f:
                data = json.load(f)
                
            # Convert to list of user data objects
            users = [SimpleLevel.from_dict({**user_data, "user_id": int(user_id)}) 
                    for user_id, user_data in data.items()]
            
            # Sort based on type
            if type.lower() in ["message", "messages", "msg"]:
                users.sort(key=lambda x: x.messages, reverse=True)
                title = "Messages Leaderboard"
                value_key = "messages"
            else:
                # Sort by level and then by XP
                users.sort(key=lambda x: (x.level, x.xp), reverse=True)
                title = "Levels Leaderboard"
                value_key = "level"
            
            # Take top 10
            top_users = users[:10]
            
            # Create embed
            embed = discord.Embed(
                title=title,
                description=f"Top members in {ctx.guild.name}",
                color=0x5865F2,
                timestamp=datetime.utcnow()
            )
            
            # Generate leaderboard text
            lb_text = ""
            for i, user in enumerate(top_users):
                # Get medal emoji based on position
                if i == 0:
                    medal = "🥇"
                elif i == 1:
                    medal = "🥈"
                elif i == 2:
                    medal = "🥉"
                else:
                    medal = f"`{i+1}.`"
                    
                value = getattr(user, value_key)
                lb_text += f"{medal} <@{user.user_id}> - **{value}**\n"
                
            # Add leaderboard text to embed
            if lb_text:
                embed.add_field(name="Rankings", value=lb_text, inline=False)
            else:
                embed.add_field(name="No Data", value="No users have gained XP yet.", inline=False)
                
            # Set footer
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error retrieving leaderboard: {e}")
            await ctx.send("An error occurred while generating the leaderboard.")
    
    @commands.group(name="levelchannel", invoke_without_command=True)
    @commands.has_permissions(manage_channels=True)
    async def level_channel(self, ctx):
        """Configure the channel for level-up notifications"""
        # Get current level up channel for this guild
        guild_id = str(ctx.guild.id)
        current_channel_id = self.level_up_channels.get(guild_id)
        current_channel = None
        
        if current_channel_id:
            current_channel = ctx.guild.get_channel(int(current_channel_id))
            
        # Create embed to show current configuration
        embed = discord.Embed(
            title="Level-Up Notification Channel",
            color=0x5865F2
        )
        
        if current_channel:
            embed.description = f"Level-up notifications are currently being sent to {current_channel.mention}."
        else:
            embed.description = "Level-up notifications are currently being sent to the same channel where messages are sent."
            
        embed.add_field(
            name="Commands",
            value=f"`.levelchannel set #channel` - Set a dedicated channel\n"
                  f"`.levelchannel reset` - Use message channel (default)",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @level_channel.command(name="set")
    @commands.has_permissions(manage_channels=True)
    async def level_channel_set(self, ctx, channel: discord.TextChannel):
        """Set the channel for level-up notifications
        
        Args:
            channel: The channel to send level-up notifications to
        """
        # Save the channel
        guild_id = str(ctx.guild.id)
        self.level_up_channels[guild_id] = channel.id
        self.save_data()
        
        # Send confirmation
        embed = discord.Embed(
            title="✅ Level-Up Channel Set",
            description=f"Level-up notifications will now be sent to {channel.mention}.",
            color=0x57F287
        )
        
        await ctx.send(embed=embed)
    
    @level_channel.command(name="reset")
    @commands.has_permissions(manage_channels=True)
    async def level_channel_reset(self, ctx):
        """Reset to use the message channel for level-up notifications"""
        guild_id = str(ctx.guild.id)
        
        # Remove the channel setting
        if guild_id in self.level_up_channels:
            del self.level_up_channels[guild_id]
            self.save_data()
            
        # Send confirmation
        embed = discord.Embed(
            title="ℹ️ Level-Up Channel Reset",
            description="Level-up notifications will now be sent in the same channel where the message was sent.",
            color=0x3498DB
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SimpleLevels(bot))