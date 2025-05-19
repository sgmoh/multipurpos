import discord
from discord.ext import commands
import random
import logging
import asyncio

from utils.database import db
from utils.embed_creator import EmbedCreator
from config import CONFIG

logger = logging.getLogger('discord_bot')

# XP gain settings
XP_MIN = 15
XP_MAX = 25
XP_COOLDOWN = 60  # Seconds between XP gains

class Levels(commands.Cog):
    """Level tracking system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.xp_cooldown = commands.CooldownMapping.from_cooldown(1, XP_COOLDOWN, commands.BucketType.member)
        logger.info("Levels cog initialized")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Award XP for messages"""
        # Skip if message is from a bot or in DMs
        if message.author.bot or not message.guild:
            return
        
        # Check cooldown
        bucket = self.xp_cooldown.get_bucket(message)
        if bucket.update_rate_limit():
            return
        
        # Award XP
        xp_to_add = random.randint(XP_MIN, XP_MAX)
        level_up = db.add_user_xp(message.guild.id, message.author.id, xp_to_add)
        
        # Handle level up
        if level_up:
            user_data = db.get_user_level(message.guild.id, message.author.id)
            
            # Create level up embed
            embed = EmbedCreator.create_level_up_embed(message.author, user_data['level'])
            
            # Send level up message
            try:
                await message.channel.send(embed=embed)
            except discord.HTTPException:
                logger.error(f"Could not send level up message in {message.guild.name}")
    
    @commands.hybrid_command(name="level", description="Check your or someone else's level")
    async def level(self, ctx, member: discord.Member = None):
        """Check level and XP for a user
        
        Args:
            member: The member to check. If None, checks the command user.
        """
        # Default to command author if no member specified
        if member is None:
            member = ctx.author
        
        # Get level data
        level_data = db.get_user_level(ctx.guild.id, member.id)
        
        # Create embed
        embed = discord.Embed(
            title=f"{CONFIG['emojis']['level']} Level Stats for {member.display_name}",
            color=CONFIG['colors']['default']
        )
        
        embed.add_field(name="Level", value=level_data['level'], inline=True)
        embed.add_field(name="XP", value=level_data['xp'], inline=True)
        
        # Calculate XP needed for next level
        next_level = level_data['level'] + 1
        xp_needed = next_level * 100
        xp_progress = level_data['xp'] % 100
        
        embed.add_field(
            name="Progress to Next Level",
            value=f"{xp_progress}/{100} XP ({xp_progress}%)",
            inline=False
        )
        
        # Set thumbnail to user's avatar
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Set footer
        embed.set_footer(
            text=f"Requested by {ctx.author}",
            icon_url=ctx.author.display_avatar.url
        )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="leaderboard", description="View the server's leaderboard")
    async def leaderboard(self, ctx, type: str = "levels"):
        """Show the server leaderboard
        
        Args:
            type: The type of leaderboard to show (levels, messages, invites)
        """
        valid_types = ["levels", "messages", "invites"]
        if type.lower() not in valid_types:
            embed = EmbedCreator.create_error_embed(
                "Invalid Type",
                f"Valid leaderboard types are: {', '.join(valid_types)}"
            )
            await ctx.send(embed=embed)
            return
        
        if type.lower() == "levels":
            # Get level leaderboard
            leaderboard_data = db.get_level_leaderboard(ctx.guild.id, 10)
            
            entries = []
            for i, (user_id, data) in enumerate(leaderboard_data, 1):
                member = ctx.guild.get_member(int(user_id))
                name = member.display_name if member else f"Unknown User ({user_id})"
                entries.append({
                    "name": name,
                    "value": data['level']
                })
            
            if not entries:
                embed = EmbedCreator.create_info_embed(
                    "Empty Leaderboard",
                    "No one has gained any levels yet."
                )
                await ctx.send(embed=embed)
                return
            
            # Create embed
            embed = EmbedCreator.create_leaderboard_embed("levels", entries)
            
        elif type.lower() == "messages":
            # Get message leaderboard
            leaderboard_data = db.get_message_leaderboard(ctx.guild.id, 10)
            
            entries = []
            for i, entry in enumerate(leaderboard_data, 1):
                member = ctx.guild.get_member(int(entry['user_id']))
                name = member.display_name if member else f"Unknown User ({entry['user_id']})"
                entries.append({
                    "name": name,
                    "value": entry['count']
                })
            
            if not entries:
                embed = EmbedCreator.create_info_embed(
                    "Empty Leaderboard",
                    "No message data has been tracked yet."
                )
                await ctx.send(embed=embed)
                return
            
            # Create embed
            embed = EmbedCreator.create_leaderboard_embed("messages", entries)
            
        elif type.lower() == "invites":
            # Get invite leaderboard
            leaderboard_data = db.get_invite_leaderboard(ctx.guild.id, 10)
            
            entries = []
            for i, entry in enumerate(leaderboard_data, 1):
                member = ctx.guild.get_member(int(entry['user_id']))
                name = member.display_name if member else f"Unknown User ({entry['user_id']})"
                entries.append({
                    "name": name,
                    "value": entry['total']
                })
            
            if not entries:
                embed = EmbedCreator.create_info_embed(
                    "Empty Leaderboard",
                    "No invite data has been tracked yet."
                )
                await ctx.send(embed=embed)
                return
            
            # Create embed
            embed = EmbedCreator.create_leaderboard_embed("invites", entries)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Levels(bot))
