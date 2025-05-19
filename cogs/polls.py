import discord
from discord.ext import commands
import logging
import json
import os
import asyncio
import datetime
from config import CONFIG

logger = logging.getLogger('discord_bot')

class Polls(commands.Cog):
    """Poll creation system for voting"""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_polls = {}
        self.data_file = 'data/polls_data.json'
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        
        # Load active polls
        self.load_polls()
        
        logger.info("Polls cog initialized")
        
    def load_polls(self):
        """Load active polls from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    self.active_polls = json.load(f)
            else:
                self.active_polls = {}
                self.save_polls()
        except Exception as e:
            logger.error(f"Error loading polls: {e}")
            self.active_polls = {}
            
    def save_polls(self):
        """Save active polls to file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.active_polls, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving polls: {e}")
    
    @commands.group(name="poll", invoke_without_command=True)
    async def poll(self, ctx):
        """Poll commands"""
        embed = discord.Embed(
            title="📊 Poll Commands",
            description="Create and manage polls for server voting",
            color=CONFIG['colors']['info']
        )
        
        # Add command examples
        commands = [
            f"`{CONFIG['prefix']}poll create \"Question?\" \"Option 1\" \"Option 2\" ...` - Create a poll",
            f"`{CONFIG['prefix']}poll timed \"Question?\" 1h \"Option 1\" \"Option 2\" ...` - Create a timed poll",
            f"`{CONFIG['prefix']}poll end <poll_id>` - End a poll early and show results",
            f"`{CONFIG['prefix']}poll list` - View active polls in this server",
            f"`{CONFIG['prefix']}poll quick \"Question?\"` - Create a quick yes/no poll"
        ]
        
        embed.add_field(
            name="Available Commands",
            value="\n".join(commands),
            inline=False
        )
        
        embed.add_field(
            name="How to Vote",
            value="React to the poll message with the corresponding emoji.",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @poll.command(name="create")
    @commands.has_permissions(manage_messages=True)
    async def create_poll(self, ctx, question: str, *options):
        """Create a new poll
        
        Args:
            question: The poll question
            options: The poll options (min 2, max 10)
        """
        # Validate options
        if len(options) < 2:
            embed = discord.Embed(
                title="❌ Not Enough Options",
                description="You need to provide at least 2 options for a poll.",
                color=CONFIG['colors']['error']
            )
            await ctx.send(embed=embed)
            return
            
        if len(options) > 10:
            embed = discord.Embed(
                title="❌ Too Many Options",
                description="You can only have up to 10 options in a poll.",
                color=CONFIG['colors']['error']
            )
            await ctx.send(embed=embed)
            return
        
        # Create poll embed
        embed = discord.Embed(
            title=f"📊 {question}",
            description="React with the corresponding emoji to vote!",
            color=CONFIG['colors']['info'],
            timestamp=datetime.datetime.utcnow()
        )
        
        # Number emojis for options
        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        # Add options to embed
        for i, option in enumerate(options):
            embed.add_field(
                name=f"Option {i+1}",
                value=f"{number_emojis[i]} {option}",
                inline=False
            )
        
        # Add footer
        embed.set_footer(text=f"Poll ID: {ctx.message.id} | Created by {ctx.author}")
        
        # Send poll and add reactions
        poll_message = await ctx.send(embed=embed)
        
        for i in range(len(options)):
            await poll_message.add_reaction(number_emojis[i])
        
        # Store poll in active polls
        guild_id = str(ctx.guild.id)
        if guild_id not in self.active_polls:
            self.active_polls[guild_id] = {}
            
        self.active_polls[guild_id][str(poll_message.id)] = {
            "question": question,
            "options": options,
            "emojis": number_emojis[:len(options)],
            "channel_id": str(ctx.channel.id),
            "author_id": str(ctx.author.id),
            "created_at": datetime.datetime.utcnow().isoformat(),
            "timed": False,
            "end_time": None
        }
        
        self.save_polls()
    
    @poll.command(name="timed")
    @commands.has_permissions(manage_messages=True)
    async def timed_poll(self, ctx, question: str, duration: str, *options):
        """Create a timed poll that automatically ends
        
        Args:
            question: The poll question
            duration: How long the poll should last (e.g. 30m, 1h, 1d)
            options: The poll options (min 2, max 10)
        """
        # Validate options
        if len(options) < 2:
            embed = discord.Embed(
                title="❌ Not Enough Options",
                description="You need to provide at least 2 options for a poll.",
                color=CONFIG['colors']['error']
            )
            await ctx.send(embed=embed)
            return
            
        if len(options) > 10:
            embed = discord.Embed(
                title="❌ Too Many Options",
                description="You can only have up to 10 options in a poll.",
                color=CONFIG['colors']['error']
            )
            await ctx.send(embed=embed)
            return
        
        # Parse duration
        seconds = 0
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
                
            if seconds < 30 or seconds > 86400 * 7:  # Between 30 seconds and 7 days
                embed = discord.Embed(
                    title="❌ Invalid Duration",
                    description="Poll duration must be between 30 seconds and 7 days.",
                    color=CONFIG['colors']['error']
                )
                await ctx.send(embed=embed)
                return
                
        except:
            embed = discord.Embed(
                title="❌ Invalid Duration",
                description="Please specify a valid duration (e.g. 30s, 5m, 1h, 1d).",
                color=CONFIG['colors']['error']
            )
            await ctx.send(embed=embed)
            return
        
        # Calculate end time
        end_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds)
        time_str = end_time.strftime("%Y-%m-%d %H:%M UTC")
        
        # Create poll embed
        embed = discord.Embed(
            title=f"📊 {question}",
            description="React with the corresponding emoji to vote!",
            color=CONFIG['colors']['info'],
            timestamp=datetime.datetime.utcnow()
        )
        
        # Number emojis for options
        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        # Add options to embed
        for i, option in enumerate(options):
            embed.add_field(
                name=f"Option {i+1}",
                value=f"{number_emojis[i]} {option}",
                inline=False
            )
        
        # Add end time
        embed.add_field(
            name="Poll Ends",
            value=f"📆 {time_str}",
            inline=False
        )
        
        # Add footer
        embed.set_footer(text=f"Poll ID: {ctx.message.id} | Created by {ctx.author}")
        
        # Send poll and add reactions
        poll_message = await ctx.send(embed=embed)
        
        for i in range(len(options)):
            await poll_message.add_reaction(number_emojis[i])
        
        # Store poll in active polls
        guild_id = str(ctx.guild.id)
        if guild_id not in self.active_polls:
            self.active_polls[guild_id] = {}
            
        self.active_polls[guild_id][str(poll_message.id)] = {
            "question": question,
            "options": options,
            "emojis": number_emojis[:len(options)],
            "channel_id": str(ctx.channel.id),
            "author_id": str(ctx.author.id),
            "created_at": datetime.datetime.utcnow().isoformat(),
            "timed": True,
            "end_time": end_time.isoformat()
        }
        
        self.save_polls()
        
        # Schedule poll end
        self.bot.loop.create_task(self.end_poll_after(ctx.guild.id, poll_message.id, seconds))
    
    @poll.command(name="quick")
    async def quick_poll(self, ctx, *, question: str):
        """Create a quick yes/no poll
        
        Args:
            question: The poll question
        """
        # Create poll embed
        embed = discord.Embed(
            title=f"📊 {question}",
            description="React with 👍 for Yes or 👎 for No",
            color=CONFIG['colors']['info'],
            timestamp=datetime.datetime.utcnow()
        )
        
        # Add footer
        embed.set_footer(text=f"Quick poll by {ctx.author}")
        
        # Send poll and add reactions
        poll_message = await ctx.send(embed=embed)
        await poll_message.add_reaction("👍")
        await poll_message.add_reaction("👎")
    
    @poll.command(name="end")
    @commands.has_permissions(manage_messages=True)
    async def end_poll(self, ctx, poll_id: int):
        """End a poll early and show results
        
        Args:
            poll_id: The ID of the poll to end
        """
        guild_id = str(ctx.guild.id)
        
        # Check if poll exists
        if (guild_id not in self.active_polls or
            str(poll_id) not in self.active_polls[guild_id]):
            
            embed = discord.Embed(
                title="❌ Poll Not Found",
                description=f"Could not find an active poll with ID {poll_id}.",
                color=CONFIG['colors']['error']
            )
            await ctx.send(embed=embed)
            return
        
        # Get poll data
        poll_data = self.active_polls[guild_id][str(poll_id)]
        
        # Check if user is authorized to end the poll
        if (str(ctx.author.id) != poll_data["author_id"] and
            not ctx.author.guild_permissions.administrator):
            
            embed = discord.Embed(
                title="❌ Not Authorized",
                description="Only the poll creator or an administrator can end this poll.",
                color=CONFIG['colors']['error']
            )
            await ctx.send(embed=embed)
            return
        
        # Get the poll message
        try:
            channel = ctx.guild.get_channel(int(poll_data["channel_id"]))
            if not channel:
                raise ValueError("Channel not found")
                
            message = await channel.fetch_message(poll_id)
            
            # End the poll
            await self.end_poll_message(ctx.guild.id, poll_id, message)
            
        except Exception as e:
            logger.error(f"Error ending poll: {e}")
            
            # Remove from active polls anyway
            del self.active_polls[guild_id][str(poll_id)]
            self.save_polls()
            
            embed = discord.Embed(
                title="❌ Error",
                description=f"Could not find the poll message. The poll has been removed from active polls.",
                color=CONFIG['colors']['error']
            )
            await ctx.send(embed=embed)
    
    @poll.command(name="list")
    async def list_polls(self, ctx):
        """List all active polls in the server"""
        guild_id = str(ctx.guild.id)
        
        # Check if there are any active polls
        if (guild_id not in self.active_polls or
            not self.active_polls[guild_id]):
            
            embed = discord.Embed(
                title="📊 Active Polls",
                description="There are no active polls in this server.",
                color=CONFIG['colors']['info']
            )
            await ctx.send(embed=embed)
            return
        
        # Create polls embed
        embed = discord.Embed(
            title="📊 Active Polls",
            description=f"There are {len(self.active_polls[guild_id])} active polls in this server.",
            color=CONFIG['colors']['info']
        )
        
        # Add each poll
        for poll_id, poll_data in self.active_polls[guild_id].items():
            # Get channel
            channel = ctx.guild.get_channel(int(poll_data["channel_id"]))
            channel_mention = channel.mention if channel else "Unknown Channel"
            
            # Get end time if timed
            if poll_data["timed"] and poll_data["end_time"]:
                try:
                    end_time = datetime.datetime.fromisoformat(poll_data["end_time"])
                    time_str = end_time.strftime("%Y-%m-%d %H:%M UTC")
                    time_info = f"Ends: {time_str}"
                except:
                    time_info = "Timed poll"
            else:
                time_info = "No end time"
                
            # Create field for this poll
            question = poll_data["question"]
            if len(question) > 100:
                question = question[:97] + "..."
                
            embed.add_field(
                name=f"Poll {poll_id}",
                value=f"**Question:** {question}\n**Channel:** {channel_mention}\n**Status:** {time_info}\n**Options:** {len(poll_data['options'])}\n`{CONFIG['prefix']}poll end {poll_id}` to end",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    async def end_poll_message(self, guild_id, poll_id, message):
        """End a poll and show results"""
        guild_id = str(guild_id)
        poll_id = str(poll_id)
        
        # Get poll data
        poll_data = self.active_polls[guild_id][poll_id]
        
        # Get the poll results
        results = []
        for i, emoji in enumerate(poll_data["emojis"]):
            # Get reaction count
            reaction = discord.utils.get(message.reactions, emoji=emoji)
            count = reaction.count - 1 if reaction else 0  # Subtract bot's reaction
            
            results.append((poll_data["options"][i], count))
        
        # Sort results by vote count (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Calculate total votes
        total_votes = sum(count for _, count in results)
        
        # Create results embed
        embed = discord.Embed(
            title=f"📊 Poll Results: {poll_data['question']}",
            description=f"The poll has ended with {total_votes} total votes.",
            color=CONFIG['colors']['success'],
            timestamp=datetime.datetime.utcnow()
        )
        
        # Add results
        for i, (option, count) in enumerate(results):
            # Calculate percentage
            percentage = (count / total_votes * 100) if total_votes > 0 else 0
            
            # Create progress bar
            bar_length = 20
            filled_length = int(bar_length * percentage / 100) if percentage > 0 else 0
            bar = "█" * filled_length + "░" * (bar_length - filled_length)
            
            embed.add_field(
                name=f"{i+1}. {option}",
                value=f"{bar} {count} votes ({percentage:.1f}%)",
                inline=False
            )
        
        # Add footer
        embed.set_footer(text=f"Poll ID: {poll_id}")
        
        # Send results
        await message.channel.send(embed=embed)
        
        # Remove from active polls
        del self.active_polls[guild_id][poll_id]
        self.save_polls()
    
    async def end_poll_after(self, guild_id, poll_id, seconds):
        """End a poll after a specified duration"""
        await asyncio.sleep(seconds)
        
        guild_id = str(guild_id)
        poll_id = str(poll_id)
        
        # Check if poll still exists
        if (guild_id not in self.active_polls or
            poll_id not in self.active_polls[guild_id]):
            return
        
        # Get poll data
        poll_data = self.active_polls[guild_id][poll_id]
        
        # Get the poll message
        try:
            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                raise ValueError("Guild not found")
                
            channel = guild.get_channel(int(poll_data["channel_id"]))
            if not channel:
                raise ValueError("Channel not found")
                
            message = await channel.fetch_message(int(poll_id))
            
            # End the poll
            await self.end_poll_message(guild_id, poll_id, message)
            
        except Exception as e:
            logger.error(f"Error ending timed poll: {e}")
            
            # Remove from active polls anyway
            if guild_id in self.active_polls and poll_id in self.active_polls[guild_id]:
                del self.active_polls[guild_id][poll_id]
                self.save_polls()

async def setup(bot):
    await bot.add_cog(Polls(bot))