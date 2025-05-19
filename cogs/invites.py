import discord
from discord.ext import commands
import logging
from datetime import datetime, timedelta

from utils.database import db
from utils.embed_creator import EmbedCreator
from config import CONFIG

logger = logging.getLogger('discord_bot')

class Invites(commands.Cog):
    """Invite tracking system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.invite_cache = {}
        logger.info("Invites cog initialized")
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Cache all invites when the bot starts"""
        await self.cache_invites()
    
    async def cache_invites(self):
        """Cache all invites from all guilds"""
        for guild in self.bot.guilds:
            try:
                # Skip guilds where the bot doesn't have permission to manage guild
                if not guild.me.guild_permissions.manage_guild:
                    continue
                
                self.invite_cache[guild.id] = {}
                
                # Fetch and cache invites
                invites = await guild.invites()
                for invite in invites:
                    self.invite_cache[guild.id][invite.code] = {
                        'uses': invite.uses,
                        'inviter': invite.inviter.id if invite.inviter else None
                    }
                
                logger.info(f"Cached {len(invites)} invites for guild {guild.name}")
            except discord.Forbidden:
                logger.warning(f"No permission to fetch invites in guild {guild.name}")
            except Exception as e:
                logger.error(f"Error caching invites for guild {guild.name}: {e}")
    
    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        """Cache new invites when they are created"""
        if invite.guild.id not in self.invite_cache:
            self.invite_cache[invite.guild.id] = {}
        
        self.invite_cache[invite.guild.id][invite.code] = {
            'uses': invite.uses,
            'inviter': invite.inviter.id if invite.inviter else None
        }
        
        logger.info(f"Cached new invite {invite.code} for guild {invite.guild.name}")
    
    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        """Remove deleted invites from the cache"""
        if invite.guild.id in self.invite_cache and invite.code in self.invite_cache[invite.guild.id]:
            del self.invite_cache[invite.guild.id][invite.code]
            logger.info(f"Removed invite {invite.code} from cache for guild {invite.guild.name}")
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Cache invites when the bot joins a new guild"""
        if not guild.me.guild_permissions.manage_guild:
            return
        
        try:
            self.invite_cache[guild.id] = {}
            
            invites = await guild.invites()
            for invite in invites:
                self.invite_cache[guild.id][invite.code] = {
                    'uses': invite.uses,
                    'inviter': invite.inviter.id if invite.inviter else None
                }
            
            logger.info(f"Cached {len(invites)} invites for new guild {guild.name}")
        except discord.Forbidden:
            logger.warning(f"No permission to fetch invites in guild {guild.name}")
        except Exception as e:
            logger.error(f"Error caching invites for guild {guild.name}: {e}")
    
    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """Remove guild from cache when the bot leaves a guild"""
        if guild.id in self.invite_cache:
            del self.invite_cache[guild.id]
            logger.info(f"Removed guild {guild.name} from invite cache")
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Track which invite was used when a member joins"""
        # Skip bots
        if member.bot:
            return
        
        # Skip if guild is not in cache or bot doesn't have required permissions
        if member.guild.id not in self.invite_cache or not member.guild.me.guild_permissions.manage_guild:
            return
        
        # Get current invites
        try:
            invite_used = None
            inviter_id = None
            is_vanity = False
            is_fake = False
            is_rejoin = False
            
            # Check if the member had joined the server before (rejoin)
            # This is a basic check; a more robust implementation would require storing join/leave history
            member_age = (datetime.now() - member.created_at).days
            if member_age < 7:  # If account is less than 7 days old
                is_fake = True
            
            try:
                # Get previous join/leave entries for this user from database
                guild_invites = db.data.get('invites', {}).get(str(member.guild.id), {})
                for inviter_id_str, inviter_data in guild_invites.items():
                    for invitee in inviter_data.get('invitees', []):
                        if invitee.get('user_id') == str(member.id):
                            is_rejoin = True
                            break
                    if is_rejoin:
                        break
            except Exception as e:
                logger.error(f"Error checking rejoin status: {e}")
                is_rejoin = False
            
            # Get new invites
            current_invites = {}
            guild_invites = await member.guild.invites()
            
            for invite in guild_invites:
                current_invites[invite.code] = {
                    'uses': invite.uses,
                    'inviter': invite.inviter.id if invite.inviter else None
                }
            
            # Check for vanity URL
            if hasattr(member.guild, 'vanity_url_code') and member.guild.vanity_url_code:
                # Guild has a vanity URL, check if it was used
                try:
                    vanity = await member.guild.vanity_invite()
                    old_uses = self.invite_cache[member.guild.id].get(member.guild.vanity_url_code, {}).get('uses', 0)
                    
                    if vanity.uses > old_uses:
                        # Vanity URL was used
                        invite_used = member.guild.vanity_url_code
                        is_vanity = True
                        
                        # Update the cache
                        self.invite_cache[member.guild.id][member.guild.vanity_url_code] = {
                            'uses': vanity.uses,
                            'inviter': None
                        }
                except:
                    pass
            
            # If not vanity URL, find which invite was used by comparing with cache
            if not is_vanity:
                for invite_code, invite_data in current_invites.items():
                    # If this invite is new or has more uses than cached
                    if (invite_code not in self.invite_cache[member.guild.id] or 
                        invite_data['uses'] > self.invite_cache[member.guild.id][invite_code]['uses']):
                        invite_used = invite_code
                        inviter_id = invite_data['inviter']
                        break
            
            # Update the invite cache
            self.invite_cache[member.guild.id] = current_invites
            
            # If we found which invite was used
            if invite_used and inviter_id:
                # Track the invite in the database
                db.track_invite(member.guild.id, inviter_id, member.id, is_fake, is_rejoin)
                
                # Log the invite
                inviter = member.guild.get_member(inviter_id)
                inviter_name = inviter.name if inviter else f"Unknown ({inviter_id})"
                
                logger.info(
                    f"Member {member.name} joined {member.guild.name} "
                    f"using invite {invite_used} from {inviter_name}. "
                    f"Fake: {is_fake}, Rejoin: {is_rejoin}"
                )
            elif is_vanity:
                logger.info(f"Member {member.name} joined {member.guild.name} using the vanity URL.")
            else:
                logger.warning(f"Could not determine which invite {member.name} used to join {member.guild.name}")
            
        except discord.Forbidden:
            logger.warning(f"No permission to fetch invites in guild {member.guild.name}")
        except Exception as e:
            logger.error(f"Error tracking invite for {member.name} in {member.guild.name}: {e}")
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Track when a member leaves"""
        # Skip bots
        if member.bot:
            return
        
        # Track the leave
        db.track_leave(member.guild.id, member.id)
        
        logger.info(f"Member {member.name} left {member.guild.name}")
    
    @commands.hybrid_command(name="invites", aliases=["i"], description="Check your invite stats or someone else's")
    async def invites(self, ctx, member: discord.Member = None):
        """Check invite statistics for a user
        
        Args:
            member: The member to check. If None, checks the command user.
        """
        # Default to command author if no member specified
        if member is None:
            member = ctx.author
        
        # Get invite stats
        stats = db.get_invite_stats(ctx.guild.id, member.id)
        
        # Create embed
        embed = EmbedCreator.create_invite_stats_embed(member, stats)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Invites(bot))
