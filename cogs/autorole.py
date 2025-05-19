import discord
from discord.ext import commands
import logging

from utils.database import db
from utils.embed_creator import EmbedCreator
from config import CONFIG

logger = logging.getLogger('discord_bot')

class Autorole(commands.Cog):
    """Automatically assigns a role to new members"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("Autorole cog initialized")
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Assign role to new members"""
        # Skip bots
        if member.bot:
            return
        
        # Get the autorole from database
        role_id = db.get_autorole(member.guild.id)
        if not role_id:
            return
        
        # Get the role
        role = member.guild.get_role(int(role_id))
        if not role:
            logger.warning(f"Autorole {role_id} not found in guild {member.guild.id}")
            return
        
        # Add the role
        try:
            await member.add_roles(role, reason="Autorole")
            logger.info(f"Added autorole {role.name} to {member.name} in {member.guild.name}")
        except discord.Forbidden:
            logger.error(f"No permission to add autorole to {member.name} in {member.guild.name}")
        except discord.HTTPException as e:
            logger.error(f"Failed to add autorole to {member.name} in {member.guild.name}: {e}")
    
    @commands.hybrid_command(name="autorole", description="Set a role to be automatically assigned to new members")
    @commands.has_permissions(manage_roles=True)
    async def autorole(self, ctx, role: discord.Role = None):
        """Set the autorole for the server
        
        Args:
            role: The role to assign to new members. If None, displays current autorole.
        """
        if role is None:
            # Display current autorole
            role_id = db.get_autorole(ctx.guild.id)
            if not role_id:
                embed = EmbedCreator.create_info_embed(
                    "Autorole",
                    f"No autorole is currently set. Use `{CONFIG['prefix']}autorole @role` to set one."
                )
            else:
                role = ctx.guild.get_role(int(role_id))
                if role:
                    embed = EmbedCreator.create_info_embed(
                        "Autorole",
                        f"Current autorole: {role.mention}"
                    )
                else:
                    embed = EmbedCreator.create_warning_embed(
                        "Autorole",
                        "The configured autorole no longer exists."
                    )
            
            await ctx.send(embed=embed)
            return
        
        # Check if bot has permission to assign this role
        if ctx.guild.me.top_role <= role:
            embed = EmbedCreator.create_error_embed(
                "Permission Error",
                "I can't assign a role that is higher than or equal to my highest role.\n"
                "Please move my role above the target role in the server settings."
            )
            await ctx.send(embed=embed)
            return
        
        # Set the autorole
        success = db.set_autorole(ctx.guild.id, role.id)
        
        if success:
            embed = EmbedCreator.create_success_embed(
                "Autorole Set",
                f"New members will now automatically receive the {role.mention} role."
            )
        else:
            embed = EmbedCreator.create_error_embed(
                "Database Error",
                "Failed to set autorole. Please try again later."
            )
        
        await ctx.send(embed=embed)
    
    @autorole.error
    async def autorole_error(self, ctx, error):
        """Error handler for autorole command"""
        if isinstance(error, commands.MissingPermissions):
            embed = EmbedCreator.create_error_embed(
                "Permission Error",
                "You need the 'Manage Roles' permission to use this command."
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = EmbedCreator.create_error_embed(
                "Invalid Role",
                "Could not find that role. Please mention a valid role."
            )
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="clearautorole", description="Clear the autorole setting")
    @commands.has_permissions(manage_roles=True)
    async def clearautorole(self, ctx):
        """Clear the autorole setting"""
        success = db.remove_autorole(ctx.guild.id)
        
        if success:
            embed = EmbedCreator.create_success_embed(
                "Autorole Cleared",
                "New members will no longer automatically receive a role."
            )
        else:
            embed = EmbedCreator.create_info_embed(
                "Autorole",
                "No autorole was set."
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Autorole(bot))
