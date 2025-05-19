import discord
from discord.ext import commands
import logging
import json
import os
import asyncio
import datetime
import random
import platform
import time
from config import CONFIG

logger = logging.getLogger('discord_bot')

class Utility(commands.Cog):
    """Utility commands for server management and information"""
    
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.datetime.utcnow()
        logger.info("Utility cog initialized")
    
    @commands.command(name="serverinfo")
    async def server_info(self, ctx):
        """Show information about the server"""
        guild = ctx.guild
        
        # Get member counts
        total_members = guild.member_count
        online_members = len([m for m in guild.members if m.status != discord.Status.offline])
        bot_count = len([m for m in guild.members if m.bot])
        human_count = total_members - bot_count
        
        # Get channel counts
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        # Create embed
        embed = discord.Embed(
            title=f"{guild.name} Server Information",
            description=guild.description or "No description set",
            color=CONFIG['colors']['info']
        )
        
        # Set server icon as thumbnail
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Add fields - General information
        embed.add_field(
            name="📊 Server ID",
            value=guild.id,
            inline=True
        )
        
        embed.add_field(
            name="👑 Owner",
            value=guild.owner.mention if guild.owner else "Unknown",
            inline=True
        )
        
        embed.add_field(
            name="🌍 Region",
            value=str(guild.region).title() if hasattr(guild, 'region') else "Unknown",
            inline=True
        )
        
        # Add boost status
        boost_level = guild.premium_tier
        boost_count = guild.premium_subscription_count
        boost_info = f"Level {boost_level} ({boost_count} boosts)"
        
        embed.add_field(
            name="🚀 Boost Status",
            value=boost_info,
            inline=True
        )
        
        # Add created date
        created_timestamp = int(guild.created_at.timestamp())
        created_date = f"<t:{created_timestamp}:F>\n<t:{created_timestamp}:R>"
        
        embed.add_field(
            name="📅 Created",
            value=created_date,
            inline=True
        )
        
        # Add verification level
        verification_levels = {
            discord.VerificationLevel.none: "None",
            discord.VerificationLevel.low: "Low",
            discord.VerificationLevel.medium: "Medium",
            discord.VerificationLevel.high: "High",
            discord.VerificationLevel.highest: "Highest"
        }
        
        embed.add_field(
            name="🔒 Verification",
            value=verification_levels.get(guild.verification_level, "Unknown"),
            inline=True
        )
        
        # Add members section
        embed.add_field(
            name="👥 Members",
            value=f"Total: {total_members}\nHumans: {human_count}\nBots: {bot_count}\nOnline: {online_members}",
            inline=True
        )
        
        # Add channels section
        embed.add_field(
            name="💬 Channels",
            value=f"Text: {text_channels}\nVoice: {voice_channels}\nCategories: {categories}",
            inline=True
        )
        
        # Add roles count
        embed.add_field(
            name="👑 Roles",
            value=len(guild.roles) - 1,  # -1 to exclude @everyone
            inline=True
        )
        
        # Add emoji count
        emoji_count = len(guild.emojis)
        emoji_limit = guild.emoji_limit
        
        embed.add_field(
            name="😀 Emojis",
            value=f"{emoji_count}/{emoji_limit}",
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="userinfo")
    async def user_info(self, ctx, member: discord.Member = None):
        """Show information about a user
        
        Args:
            member: The member to show info for (defaults to yourself)
        """
        # Default to the command invoker if no member specified
        member = member or ctx.author
        
        # Get join position
        join_position = sorted(ctx.guild.members, key=lambda m: m.joined_at or datetime.datetime.utcnow()).index(member) + 1
        
        # Create embed
        embed = discord.Embed(
            title=f"{member.name} User Information",
            color=member.color or CONFIG['colors']['info']
        )
        
        # Set user avatar as thumbnail
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Add user ID
        embed.add_field(
            name="🆔 User ID",
            value=member.id,
            inline=True
        )
        
        # Add nickname if exists
        if member.nick:
            embed.add_field(
                name="📝 Nickname",
                value=member.nick,
                inline=True
            )
        
        # Add account created date
        created_timestamp = int(member.created_at.timestamp())
        created_date = f"<t:{created_timestamp}:F>\n<t:{created_timestamp}:R>"
        
        embed.add_field(
            name="🔰 Account Created",
            value=created_date,
            inline=True
        )
        
        # Add server join date
        if member.joined_at:
            joined_timestamp = int(member.joined_at.timestamp())
            joined_date = f"<t:{joined_timestamp}:F>\n<t:{joined_timestamp}:R>"
            
            embed.add_field(
                name="📥 Joined Server",
                value=f"{joined_date}\n(#{join_position} to join)",
                inline=True
            )
        
        # Add status
        status_emojis = {
            discord.Status.online: "🟢 Online",
            discord.Status.idle: "🟡 Idle",
            discord.Status.dnd: "🔴 Do Not Disturb",
            discord.Status.offline: "⚫ Offline"
        }
        
        embed.add_field(
            name="📶 Status",
            value=status_emojis.get(member.status, "Unknown"),
            inline=True
        )
        
        # Add activity if available
        if member.activity:
            activity_type = {
                discord.ActivityType.playing: "Playing",
                discord.ActivityType.streaming: "Streaming",
                discord.ActivityType.listening: "Listening to",
                discord.ActivityType.watching: "Watching",
                discord.ActivityType.custom: "Custom Status",
                discord.ActivityType.competing: "Competing in"
            }
            
            activity_name = f"{activity_type.get(member.activity.type, 'Unknown')} {member.activity.name}"
            
            embed.add_field(
                name="🎮 Activity",
                value=activity_name,
                inline=True
            )
        
        # Add roles
        roles = [role.mention for role in reversed(member.roles) if role.name != "@everyone"]
        if roles:
            embed.add_field(
                name=f"👑 Roles ({len(roles)})",
                value=" ".join(roles) if len(" ".join(roles)) < 1024 else f"{len(roles)} roles",
                inline=False
            )
        
        # Add permissions if available
        key_permissions = {
            "administrator": "Administrator",
            "manage_guild": "Manage Server",
            "manage_roles": "Manage Roles",
            "manage_channels": "Manage Channels",
            "manage_messages": "Manage Messages",
            "manage_webhooks": "Manage Webhooks",
            "manage_nicknames": "Manage Nicknames",
            "manage_emojis": "Manage Emojis",
            "kick_members": "Kick Members",
            "ban_members": "Ban Members",
            "mention_everyone": "Mention Everyone"
        }
        
        permissions = []
        for perm, name in key_permissions.items():
            if getattr(member.guild_permissions, perm):
                permissions.append(name)
        
        if permissions:
            embed.add_field(
                name="🔑 Key Permissions",
                value=", ".join(permissions),
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="avatar")
    async def avatar(self, ctx, member: discord.Member = None):
        """Show a user's avatar
        
        Args:
            member: The member to show avatar for (defaults to yourself)
        """
        # Default to the command invoker if no member specified
        member = member or ctx.author
        
        # Create embed
        embed = discord.Embed(
            title=f"{member.name}'s Avatar",
            color=member.color or CONFIG['colors']['info']
        )
        
        # Set avatar image
        embed.set_image(url=member.display_avatar.url)
        
        # Add links to different formats
        formats = ["png", "jpg", "webp"]
        if member.display_avatar.is_animated():
            formats.append("gif")
            
        links = [f"[{fmt.upper()}]({member.display_avatar.with_format(fmt).url})" for fmt in formats]
        
        embed.add_field(
            name="Download",
            value=" | ".join(links),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="ping")
    async def ping(self, ctx):
        """Check the bot's latency"""
        start_time = time.time()
        message = await ctx.send("Pinging...")
        end_time = time.time()
        
        # Calculate latencies
        api_latency = round(self.bot.latency * 1000)
        message_latency = round((end_time - start_time) * 1000)
        
        # Create embed
        embed = discord.Embed(
            title="🏓 Pong!",
            color=CONFIG['colors']['info']
        )
        
        embed.add_field(
            name="API Latency",
            value=f"{api_latency}ms",
            inline=True
        )
        
        embed.add_field(
            name="Message Latency",
            value=f"{message_latency}ms",
            inline=True
        )
        
        await message.edit(content=None, embed=embed)
    
    @commands.command(name="botinfo")
    async def bot_info(self, ctx):
        """Show information about the bot"""
        # Calculate uptime
        uptime_delta = datetime.datetime.utcnow() - self.start_time
        days = uptime_delta.days
        hours, remainder = divmod(uptime_delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
        
        # Get server count
        server_count = len(self.bot.guilds)
        
        # Get user count (excluding bots)
        user_count = sum(1 for m in self.bot.get_all_members() if not m.bot)
        
        # Get channel count
        channel_count = sum(1 for _ in self.bot.get_all_channels())
        
        # Create embed
        embed = discord.Embed(
            title=f"{self.bot.user.name} Bot Information",
            description="A multipurpose Discord bot with moderation, welcome messages, tickets, and more!",
            color=CONFIG['colors']['default']
        )
        
        # Set bot avatar as thumbnail
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        # Add general information
        embed.add_field(
            name="📊 Bot ID",
            value=self.bot.user.id,
            inline=True
        )
        
        embed.add_field(
            name="📅 Created",
            value=discord.utils.format_dt(self.bot.user.created_at, "F"),
            inline=True
        )
        
        embed.add_field(
            name="⏱️ Uptime",
            value=uptime_str,
            inline=True
        )
        
        # Add statistics
        embed.add_field(
            name="🖥️ Servers",
            value=server_count,
            inline=True
        )
        
        embed.add_field(
            name="👥 Users",
            value=user_count,
            inline=True
        )
        
        embed.add_field(
            name="📝 Channels",
            value=channel_count,
            inline=True
        )
        
        # Add commands count
        command_count = len(self.bot.commands)
        cog_count = len(self.bot.cogs)
        
        embed.add_field(
            name="⚙️ Commands",
            value=f"{command_count} commands in {cog_count} modules",
            inline=True
        )
        
        # Add prefix info
        embed.add_field(
            name="📌 Prefix",
            value=f"`{CONFIG['prefix']}`",
            inline=True
        )
        
        # Add version info
        embed.add_field(
            name="🔧 Version",
            value=f"Discord.py {discord.__version__}\nPython {platform.python_version()}",
            inline=True
        )
        
        # Add a link to invite the bot
        embed.add_field(
            name="📲 Links",
            value="[Invite Bot](https://discord.com/oauth2/authorize) | [Support Server](https://discord.gg/)",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="roleinfo")
    async def role_info(self, ctx, *, role: discord.Role):
        """Show information about a role
        
        Args:
            role: The role to show info for
        """
        # Get member count with this role
        member_count = len(role.members)
        
        # Create embed
        embed = discord.Embed(
            title=f"{role.name} Role Information",
            color=role.color
        )
        
        # Add role ID
        embed.add_field(
            name="🆔 Role ID",
            value=role.id,
            inline=True
        )
        
        # Add color
        hex_color = str(role.color).upper()
        embed.add_field(
            name="🎨 Color",
            value=hex_color,
            inline=True
        )
        
        # Add creation date
        created_timestamp = int(role.created_at.timestamp())
        created_date = f"<t:{created_timestamp}:F>\n<t:{created_timestamp}:R>"
        
        embed.add_field(
            name="📅 Created",
            value=created_date,
            inline=True
        )
        
        # Add position
        position = ctx.guild.roles.index(role)
        total_roles = len(ctx.guild.roles)
        
        embed.add_field(
            name="📊 Position",
            value=f"{total_roles - position}/{total_roles}",
            inline=True
        )
        
        # Add mentionable info
        embed.add_field(
            name="💬 Mentionable",
            value="Yes" if role.mentionable else "No",
            inline=True
        )
        
        # Add hoisting info (displayed separately)
        embed.add_field(
            name="👁️ Displayed Separately",
            value="Yes" if role.hoist else "No",
            inline=True
        )
        
        # Add managed info
        embed.add_field(
            name="🤖 Managed by Integration",
            value="Yes" if role.managed else "No",
            inline=True
        )
        
        # Add members with role
        embed.add_field(
            name="👥 Members",
            value=member_count,
            inline=True
        )
        
        # Add role mention
        embed.add_field(
            name="📝 Mention",
            value=role.mention,
            inline=True
        )
        
        # Add permissions
        if role.permissions.value > 0:
            permissions = []
            for perm, value in role.permissions:
                if value:
                    # Format permission name (convert manage_guild to Manage Guild)
                    formatted_perm = perm.replace("_", " ").title()
                    permissions.append(formatted_perm)
                    
            if permissions:
                embed.add_field(
                    name="🔑 Permissions",
                    value=", ".join(permissions) if len(", ".join(permissions)) < 1024 else f"{len(permissions)} permissions",
                    inline=False
                )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="channelinfo")
    async def channel_info(self, ctx, channel: discord.TextChannel = None):
        """Show information about a channel
        
        Args:
            channel: The channel to show info for (defaults to current channel)
        """
        # Default to the current channel if none specified
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
        
        # Add position
        embed.add_field(
            name="📊 Position",
            value=channel.position,
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
        if hasattr(channel, 'permissions_synced'):
            synced = await channel.permissions_synced() if callable(channel.permissions_synced) else channel.permissions_synced
            embed.add_field(
                name="🔄 Synced Permissions",
                value="Yes" if synced else "No",
                inline=True
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="emojis")
    async def emojis(self, ctx):
        """Show all emojis in the server"""
        guild = ctx.guild
        
        # Check if server has emojis
        if not guild.emojis:
            embed = discord.Embed(
                title="😕 No Emojis",
                description="This server doesn't have any custom emojis.",
                color=CONFIG['colors']['error']
            )
            
            await ctx.send(embed=embed)
            return
        
        # Sort emojis by name
        emojis = sorted(guild.emojis, key=lambda e: e.name)
        
        # Create emoji pages (20 emojis per page)
        emoji_pages = []
        page_size = 20
        
        for i in range(0, len(emojis), page_size):
            page_emojis = emojis[i:i+page_size]
            
            embed = discord.Embed(
                title=f"Server Emojis ({len(guild.emojis)})",
                color=CONFIG['colors']['info']
            )
            
            # Add static and animated emoji counts
            static_emojis = len([e for e in guild.emojis if not e.animated])
            animated_emojis = len([e for e in guild.emojis if e.animated])
            
            embed.set_footer(text=f"Page {i//page_size + 1}/{len(guild.emojis)//page_size + 1} • {static_emojis} static • {animated_emojis} animated")
            
            # Add emoji fields
            for emoji in page_emojis:
                emoji_type = "Animated" if emoji.animated else "Static"
                emoji_info = f"{emoji} • `:{emoji.name}:`\nID: {emoji.id}\nType: {emoji_type}"
                
                embed.add_field(
                    name=emoji.name,
                    value=emoji_info,
                    inline=True
                )
            
            emoji_pages.append(embed)
        
        # Only one page
        if len(emoji_pages) == 1:
            await ctx.send(embed=emoji_pages[0])
            return
        
        # Multiple pages - add reaction controls
        current_page = 0
        message = await ctx.send(embed=emoji_pages[current_page])
        
        # Add reactions
        controls = ["⬅️", "➡️", "❌"]
        for control in controls:
            await message.add_reaction(control)
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in controls and reaction.message.id == message.id
        
        # Handle reaction navigation
        try:
            while True:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                
                if str(reaction.emoji) == "⬅️":
                    # Go to previous page
                    if current_page > 0:
                        current_page -= 1
                        await message.edit(embed=emoji_pages[current_page])
                    
                elif str(reaction.emoji) == "➡️":
                    # Go to next page
                    if current_page < len(emoji_pages) - 1:
                        current_page += 1
                        await message.edit(embed=emoji_pages[current_page])
                    
                elif str(reaction.emoji) == "❌":
                    # Stop pagination
                    await message.clear_reactions()
                    break
                
                # Remove user reaction
                try:
                    await message.remove_reaction(reaction.emoji, user)
                except:
                    pass
                
        except asyncio.TimeoutError:
            # Timeout - remove all reactions
            try:
                await message.clear_reactions()
            except:
                pass
    
    @commands.command(name="roll")
    async def roll_dice(self, ctx, dice: str = "1d6"):
        """Roll dice using NdN format
        
        Args:
            dice: Dice to roll in NdN format (default: 1d6)
        """
        try:
            # Parse dice format
            if 'd' not in dice:
                # Assume it's just the number of sides
                num_dice = 1
                num_sides = int(dice)
            else:
                num_dice, num_sides = map(int, dice.split('d'))
            
            # Validate inputs
            if num_dice <= 0 or num_sides <= 0:
                raise ValueError("Number of dice and sides must be positive")
                
            if num_dice > 100:
                raise ValueError("Cannot roll more than 100 dice at once")
                
            if num_sides > 1000:
                raise ValueError("Cannot roll dice with more than 1000 sides")
            
            # Roll the dice
            rolls = [random.randint(1, num_sides) for _ in range(num_dice)]
            total = sum(rolls)
            
            # Create embed
            embed = discord.Embed(
                title="🎲 Dice Roll",
                description=f"Rolled {dice}",
                color=CONFIG['colors']['info']
            )
            
            # Add rolls
            if num_dice > 1:
                embed.add_field(
                    name="Rolls",
                    value=", ".join(str(r) for r in rolls),
                    inline=False
                )
                
                embed.add_field(
                    name="Total",
                    value=total,
                    inline=False
                )
            else:
                embed.add_field(
                    name="Result",
                    value=total,
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except ValueError as e:
            # Invalid format
            embed = discord.Embed(
                title="❌ Invalid Dice Format",
                description=f"Error: {str(e)}\nUse format 'NdN' like '1d6', '2d20', etc.",
                color=CONFIG['colors']['error']
            )
            
            await ctx.send(embed=embed)
    
    @commands.command(name="choose")
    async def choose(self, ctx, *options):
        """Choose between multiple options
        
        Args:
            options: Options to choose from (separate with spaces, or use quotes for options with spaces)
        """
        # Check if enough options were provided
        if len(options) < 2:
            embed = discord.Embed(
                title="❌ Not Enough Options",
                description="Please provide at least 2 options to choose from.",
                color=CONFIG['colors']['error']
            )
            
            await ctx.send(embed=embed)
            return
        
        # Choose a random option
        choice = random.choice(options)
        
        # Create embed
        embed = discord.Embed(
            title="🤔 Choice Made",
            description=f"I choose: **{choice}**",
            color=CONFIG['colors']['success']
        )
        
        embed.add_field(
            name="Options",
            value="\n".join(f"• {option}" for option in options),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="remind")
    async def remind(self, ctx, time: str, *, reminder: str):
        """Set a reminder
        
        Args:
            time: When to remind you (e.g. 10s, 5m, 1h, 1d)
            reminder: What to remind you about
        """
        # Parse time
        seconds = 0
        time_units = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400
        }
        
        try:
            unit = time[-1].lower()
            value = int(time[:-1])
            
            if unit in time_units:
                seconds = value * time_units[unit]
            else:
                seconds = int(time)  # Try to parse as seconds
                
            if seconds < 1 or seconds > 86400 * 7:  # Between 1 second and 7 days
                raise ValueError("Invalid time")
                
        except:
            embed = discord.Embed(
                title="❌ Invalid Time",
                description="Please specify a valid time (e.g. 10s, 5m, 1h, 1d).",
                color=CONFIG['colors']['error']
            )
            await ctx.send(embed=embed)
            return
        
        # Calculate when the reminder will be triggered
        now = datetime.datetime.utcnow()
        remind_time = now + datetime.timedelta(seconds=seconds)
        
        # Format times
        timestamp = int(remind_time.timestamp())
        remind_time_str = f"<t:{timestamp}:F>"
        relative_time = f"<t:{timestamp}:R>"
        
        # Create confirmation embed
        embed = discord.Embed(
            title="⏰ Reminder Set",
            description=f"I'll remind you about: **{reminder}**",
            color=CONFIG['colors']['success']
        )
        
        embed.add_field(
            name="When",
            value=f"{remind_time_str}\n{relative_time}",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
        # Wait for the specified time
        await asyncio.sleep(seconds)
        
        # Create reminder embed
        reminder_embed = discord.Embed(
            title="⏰ Reminder",
            description=reminder,
            color=CONFIG['colors']['info'],
            timestamp=now  # When the reminder was set
        )
        
        reminder_embed.add_field(
            name="Reminder Set",
            value=f"{seconds_to_time_string(seconds)} ago",
            inline=False
        )
        
        # Send the reminder
        try:
            await ctx.author.send(f"{ctx.author.mention} Here's your reminder!", embed=reminder_embed)
            
            # If the reminder was set in a guild, also send a message there
            if ctx.guild:
                await ctx.send(f"{ctx.author.mention} I've sent your reminder to your DMs!")
                
        except discord.Forbidden:
            # Can't DM the user
            if ctx.guild:
                await ctx.send(f"{ctx.author.mention} Here's your reminder!", embed=reminder_embed)
            
        except Exception as e:
            logger.error(f"Error sending reminder: {e}")
            if ctx.guild:
                await ctx.send(f"{ctx.author.mention} I tried to send your reminder, but something went wrong.")

def seconds_to_time_string(seconds):
    """Convert seconds to a human-readable time string"""
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds > 0:
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
    
    return ", ".join(parts)

async def setup(bot):
    await bot.add_cog(Utility(bot))