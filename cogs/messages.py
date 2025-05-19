import discord
from discord.ext import commands
import logging

from utils.database import db
from utils.embed_creator import EmbedCreator
from config import CONFIG

logger = logging.getLogger('discord_bot')

class Messages(commands.Cog):
    """Message tracking system"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("Messages cog initialized")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Track messages from users"""
        # Skip if message is from a bot or in DMs
        if message.author.bot or not message.guild:
            return
        
        # Track the message
        db.increment_message_count(message.guild.id, message.author.id)
    
    @commands.hybrid_command(name="messages", aliases=["m"], description="Check your message stats or someone else's")
    async def messages(self, ctx, member: discord.Member = None):
        """Check message statistics for a user
        
        Args:
            member: The member to check. If None, checks the command user.
        """
        # Default to command author if no member specified
        if member is None:
            member = ctx.author
        
        # Get message stats
        stats = db.get_message_stats(ctx.guild.id, member.id)
        
        # Create embed
        embed = EmbedCreator.create_message_stats_embed(member, stats)
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="resetmessages", description="Reset message stats for a user")
    @commands.has_permissions(manage_guild=True)
    async def resetmessages(self, ctx, member: discord.Member):
        """Reset message statistics for a user
        
        Args:
            member: The member whose stats to reset.
        """
        # Reset the stats in the database
        guild_id, user_id = str(ctx.guild.id), str(member.id)
        
        if 'message_counts' in db.data and guild_id in db.data['message_counts'] and user_id in db.data['message_counts'][guild_id]:
            db.data['message_counts'][guild_id][user_id] = {
                'all_time': 0,
                'daily': {}
            }
            db._save_data()
            
            embed = EmbedCreator.create_success_embed(
                "Stats Reset",
                f"Message statistics for {member.mention} have been reset."
            )
        else:
            embed = EmbedCreator.create_info_embed(
                "No Stats Found",
                f"No message statistics found for {member.mention}."
            )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="topmessages", description="Show top message senders in the server")
    async def topmessages(self, ctx, period: str = "all_time"):
        """Show the top message senders
        
        Args:
            period: The time period to show (all_time or today)
        """
        if period.lower() not in ["all_time", "today"]:
            embed = EmbedCreator.create_error_embed(
                "Invalid Period",
                "Valid periods are: all_time, today"
            )
            await ctx.send(embed=embed)
            return
        
        # Get the leaderboard
        leaderboard = db.get_message_leaderboard(ctx.guild.id, 10, period.lower())
        
        if not leaderboard:
            embed = EmbedCreator.create_info_embed(
                "Empty Leaderboard",
                f"No message data for {period.replace('_', ' ')} has been tracked yet."
            )
            await ctx.send(embed=embed)
            return
        
        # Format the leaderboard entries
        entries = []
        for entry in leaderboard:
            member = ctx.guild.get_member(int(entry['user_id']))
            name = member.display_name if member else f"Unknown User ({entry['user_id']})"
            entries.append({
                "name": name,
                "value": entry['count']
            })
        
        # Create embed
        embed = EmbedCreator.create_leaderboard_embed("messages", entries)
        embed.title = f"📊 Message Leaderboard ({period.replace('_', ' ')})"
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Messages(bot))
