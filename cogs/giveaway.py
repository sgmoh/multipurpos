import discord
from discord.ext import commands, tasks
import asyncio
import random
import logging
import re
from datetime import datetime, timedelta

from utils.database import db
from utils.embed_creator import EmbedCreator
from config import CONFIG

logger = logging.getLogger('discord_bot')

# Time conversion constants
TIME_REGEX = re.compile(r"(\d+)([smhdw])")
TIME_DICT = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400,
    "w": 604800
}

class Giveaway(commands.Cog):
    """Giveaway system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.check_giveaways.start()
        logger.info("Giveaway cog initialized")
    
    def cog_unload(self):
        self.check_giveaways.cancel()
    
    @tasks.loop(seconds=60)
    async def check_giveaways(self):
        """Check for ended giveaways and announce winners"""
        active_giveaways = db.get_active_giveaways()
        now = datetime.now()
        
        for giveaway in active_giveaways:
            if giveaway['end_time'] <= now:
                # Giveaway has ended
                await self.end_giveaway(giveaway)
    
    @check_giveaways.before_loop
    async def before_check_giveaways(self):
        """Wait until the bot is ready before starting the giveaway checker"""
        await self.bot.wait_until_ready()
    
    async def end_giveaway(self, giveaway):
        """End a giveaway and announce winners"""
        guild_id = int(giveaway['guild_id'])
        channel_id = int(giveaway['channel_id'])
        message_id = int(giveaway['message_id'])
        
        guild = self.bot.get_guild(guild_id)
        if not guild:
            logger.error(f"Guild {guild_id} not found for giveaway {message_id}")
            return
        
        channel = guild.get_channel(channel_id)
        if not channel:
            logger.error(f"Channel {channel_id} not found for giveaway {message_id}")
            return
        
        try:
            message = await channel.fetch_message(message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
            logger.error(f"Could not fetch message {message_id} for giveaway: {e}")
            return
        
        # Mark giveaway as ended
        db.end_giveaway(guild_id, message_id)
        
        # Get giveaway data
        giveaway_data = giveaway['data']
        winners_count = giveaway_data['winners']
        participants = giveaway_data['participants']
        prize = giveaway_data['prize']
        
        # Select winners
        winners = []
        if participants:
            # Make sure we don't try to select more winners than participants
            winners_count = min(winners_count, len(participants))
            winner_ids = random.sample(participants, winners_count)
            
            for winner_id in winner_ids:
                winner = guild.get_member(int(winner_id))
                if winner:
                    winners.append(winner)
        
        # Update the giveaway embed
        if winners:
            winners_text = ", ".join(winner.mention for winner in winners)
            embed = discord.Embed(
                title=f"{CONFIG['emojis']['giveaway']} GIVEAWAY ENDED: {prize}",
                description=f"Winners: {winners_text}",
                color=CONFIG['colors']['success']
            )
            
            host = guild.get_member(int(giveaway_data['host_id']))
            host_text = host.mention if host else "Unknown"
            
            embed.add_field(name="Hosted by:", value=host_text)
            embed.add_field(name="Participants:", value=str(len(participants)))
            embed.set_footer(text="Giveaway ended")
            
            await message.edit(embed=embed)
            
            # Send winner announcement
            await channel.send(
                f"🎉 Congratulations {winners_text}! You won the giveaway for **{prize}**!",
                allowed_mentions=discord.AllowedMentions(users=True)
            )
        else:
            embed = discord.Embed(
                title=f"{CONFIG['emojis']['giveaway']} GIVEAWAY ENDED: {prize}",
                description="No valid participants.",
                color=CONFIG['colors']['error']
            )
            
            host = guild.get_member(int(giveaway_data['host_id']))
            host_text = host.mention if host else "Unknown"
            
            embed.add_field(name="Hosted by:", value=host_text)
            embed.set_footer(text="Giveaway ended")
            
            await message.edit(embed=embed)
            await channel.send(f"No valid winners for the giveaway: **{prize}**.")
    
    def convert_time_to_seconds(self, time_str):
        """Convert a time string (e.g. '1h30m') to seconds"""
        matches = TIME_REGEX.findall(time_str)
        if not matches:
            return None
        
        total_seconds = 0
        for value, unit in matches:
            total_seconds += int(value) * TIME_DICT[unit]
        
        return total_seconds
    
    @commands.hybrid_command(name="gstart", description="Start a giveaway")
    @commands.has_permissions(manage_guild=True)
    async def gstart(self, ctx, duration: str, winners: int, *, prize: str):
        """Start a giveaway
        
        Args:
            duration: Duration of the giveaway (e.g. 1h, 30m, 1d)
            winners: Number of winners
            prize: The prize to give away
        """
        # Check duration format
        seconds = self.convert_time_to_seconds(duration)
        if not seconds:
            embed = EmbedCreator.create_error_embed(
                "Invalid Duration",
                "Please provide a valid duration (e.g. 1h, 30m, 1d)."
            )
            await ctx.send(embed=embed)
            return
        
        # Check winners
        if winners < 1:
            embed = EmbedCreator.create_error_embed(
                "Invalid Winner Count",
                "The number of winners must be at least 1."
            )
            await ctx.send(embed=embed)
            return
        
        # Calculate end time
        end_time = datetime.now() + timedelta(seconds=seconds)
        
        # Create embed
        embed = EmbedCreator.create_giveaway_embed(prize, ctx.author, end_time, winners)
        
        # Send message
        message = await ctx.send(embed=embed)
        
        # Add reaction
        await message.add_reaction(CONFIG['emojis']['giveaway'])
        
        # Store giveaway in database
        db.create_giveaway(
            ctx.guild.id,
            ctx.channel.id,
            message.id,
            prize,
            ctx.author.id,
            end_time,
            winners
        )
        
        # Send confirmation to command user if different from giveaway channel
        if ctx.channel.id != message.channel.id:
            confirm_embed = EmbedCreator.create_success_embed(
                "Giveaway Started",
                f"Giveaway for **{prize}** has been started in {message.channel.mention}."
            )
            await ctx.send(embed=confirm_embed)
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Handle reactions for giveaways"""
        # Ignore bot reactions
        if payload.user_id == self.bot.user.id:
            return
        
        # Check if this is a giveaway reaction
        if str(payload.emoji) != CONFIG['emojis']['giveaway']:
            return
        
        # Get the giveaway data
        giveaway = db.get_giveaway(payload.guild_id, payload.message_id)
        if not giveaway:
            return
        
        # Add participant
        db.add_giveaway_participant(payload.guild_id, payload.message_id, payload.user_id)
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Handle reaction removals for giveaways"""
        # Check if this is a giveaway reaction
        if str(payload.emoji) != CONFIG['emojis']['giveaway']:
            return
        
        # Get the giveaway data
        giveaway = db.get_giveaway(payload.guild_id, payload.message_id)
        if not giveaway:
            return
        
        # Remove participant
        db.remove_giveaway_participant(payload.guild_id, payload.message_id, payload.user_id)
    
    @commands.hybrid_command(name="gend", description="End a giveaway early")
    @commands.has_permissions(manage_guild=True)
    async def gend(self, ctx, message_id: str):
        """End a giveaway early
        
        Args:
            message_id: The ID of the giveaway message
        """
        # Get the giveaway
        giveaway = db.get_giveaway(ctx.guild.id, message_id)
        if not giveaway:
            embed = EmbedCreator.create_error_embed(
                "Giveaway Not Found",
                "Could not find an active giveaway with that message ID."
            )
            await ctx.send(embed=embed)
            return
        
        # End the giveaway
        channel_id = int(giveaway['channel_id'])
        channel = ctx.guild.get_channel(channel_id)
        
        if not channel:
            embed = EmbedCreator.create_error_embed(
                "Channel Not Found",
                "The channel containing this giveaway no longer exists."
            )
            await ctx.send(embed=embed)
            return
        
        embed = EmbedCreator.create_info_embed(
            "Ending Giveaway",
            f"Ending the giveaway for **{giveaway['prize']}**..."
        )
        await ctx.send(embed=embed)
        
        # Force end time to now
        giveaway_data = {
            'guild_id': str(ctx.guild.id),
            'channel_id': str(channel_id),
            'message_id': message_id,
            'end_time': datetime.now(),
            'data': giveaway
        }
        
        await self.end_giveaway(giveaway_data)
    
    @commands.hybrid_command(name="greroll", description="Reroll a giveaway")
    @commands.has_permissions(manage_guild=True)
    async def greroll(self, ctx, message_id: str):
        """Reroll a giveaway to select new winners
        
        Args:
            message_id: The ID of the giveaway message
        """
        # Get the giveaway
        giveaway = db.get_giveaway(ctx.guild.id, message_id)
        if not giveaway:
            embed = EmbedCreator.create_error_embed(
                "Giveaway Not Found",
                "Could not find a giveaway with that message ID."
            )
            await ctx.send(embed=embed)
            return
        
        # Check if giveaway has participants
        if not giveaway.get('participants'):
            embed = EmbedCreator.create_error_embed(
                "No Participants",
                "This giveaway doesn't have any participants to reroll."
            )
            await ctx.send(embed=embed)
            return
        
        # Select new winners
        winners_count = min(giveaway['winners'], len(giveaway['participants']))
        winner_ids = random.sample(giveaway['participants'], winners_count)
        
        winners = []
        for winner_id in winner_ids:
            winner = ctx.guild.get_member(int(winner_id))
            if winner:
                winners.append(winner)
        
        if not winners:
            embed = EmbedCreator.create_error_embed(
                "No Valid Winners",
                "Could not find any valid members to select as winners."
            )
            await ctx.send(embed=embed)
            return
        
        # Announce new winners
        winners_text = ", ".join(winner.mention for winner in winners)
        
        embed = EmbedCreator.create_success_embed(
            "Giveaway Rerolled",
            f"New winners for **{giveaway['prize']}**: {winners_text}"
        )
        
        await ctx.send(embed=embed)
        
        # Send notification in the original channel
        channel = ctx.guild.get_channel(int(giveaway['channel_id']))
        if channel:
            await channel.send(
                f"🎉 The giveaway for **{giveaway['prize']}** has been rerolled!\n"
                f"New winners: {winners_text}",
                allowed_mentions=discord.AllowedMentions(users=True)
            )

async def setup(bot):
    await bot.add_cog(Giveaway(bot))
