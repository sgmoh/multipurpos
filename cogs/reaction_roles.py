import discord
from discord.ext import commands
import logging
import asyncio

from utils.database import db
from utils.embed_creator import EmbedCreator
from config import CONFIG

logger = logging.getLogger('discord_bot')

class RoleSelect(discord.ui.Select):
    """Dropdown for selecting roles"""
    
    def __init__(self, roles):
        # Create options for each role
        options = []
        for role_info in roles:
            options.append(
                discord.SelectOption(
                    label=role_info['name'],
                    description=role_info['description'],
                    emoji=role_info['emoji'],
                    value=str(role_info['id'])
                )
            )
        
        super().__init__(
            placeholder="Select roles...",
            min_values=0,
            max_values=min(len(options), 25),  # Max 25 options in a select
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Handle role selection"""
        # Get selected role IDs
        selected_role_ids = [int(value) for value in self.values]
        
        try:
            # Get the member
            member = interaction.user
            
            # Get all selectable roles
            selectable_roles = [int(option.value) for option in self.options]
            
            # Get member's current roles
            current_role_ids = [role.id for role in member.roles]
            
            # Determine roles to add and remove
            roles_to_add = [
                interaction.guild.get_role(role_id) 
                for role_id in selected_role_ids 
                if role_id not in current_role_ids
            ]
            
            roles_to_remove = [
                interaction.guild.get_role(role_id) 
                for role_id in selectable_roles 
                if role_id not in selected_role_ids and role_id in current_role_ids
            ]
            
            # Remove roles that are None (not found in the guild)
            roles_to_add = [role for role in roles_to_add if role is not None]
            roles_to_remove = [role for role in roles_to_remove if role is not None]
            
            # Apply role changes
            if roles_to_add:
                await member.add_roles(*roles_to_add, reason="Reaction role selection")
            
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason="Reaction role selection")
            
            # Create response message
            response = []
            if roles_to_add:
                role_names = [role.name for role in roles_to_add]
                response.append(f"Added roles: {', '.join(role_names)}")
            
            if roles_to_remove:
                role_names = [role.name for role in roles_to_remove]
                response.append(f"Removed roles: {', '.join(role_names)}")
            
            if not response:
                response.append("No role changes were made.")
            
            await interaction.response.send_message(
                "\n".join(response),
                ephemeral=True
            )
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "I don't have permission to manage your roles.",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error updating roles: {e}")
            await interaction.response.send_message(
                "An error occurred while updating your roles.",
                ephemeral=True
            )

class RoleView(discord.ui.View):
    """View containing the role selection dropdown"""
    
    def __init__(self, roles):
        super().__init__(timeout=None)  # Persistent view
        self.add_item(RoleSelect(roles))

class ReactionRoles(commands.Cog):
    """Reaction roles system"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("ReactionRoles cog initialized")
        
        # Register persistent view
        # This will be populated when the bot starts
        self.register_views()
    
    def register_views(self):
        """Register persistent views for reaction roles"""
        # This will be called on bot startup to register all existing reaction role messages
        # We'll actually do this in the on_ready event to ensure the bot is fully ready
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Register all existing reaction role views when the bot starts"""
        # Get all reaction role messages from the database
        all_reaction_roles = db.data.get('reaction_roles', {})
        
        for guild_id, guild_data in all_reaction_roles.items():
            for message_id, roles_data in guild_data.items():
                # Format roles data for the view
                roles = []
                
                for role_data in roles_data:
                    role_id = int(role_data['role_id'])
                    emoji = role_data['emoji']
                    
                    # Try to get the guild to find role information
                    guild = self.bot.get_guild(int(guild_id))
                    if guild:
                        role = guild.get_role(role_id)
                        if role:
                            roles.append({
                                'id': role_id,
                                'name': role.name,
                                'description': f"Click to get the {role.name} role",
                                'emoji': emoji
                            })
                
                # Register the view if we have roles
                if roles:
                    view = RoleView(roles)
                    self.bot.add_view(view, message_id=int(message_id))
                    logger.info(f"Registered reaction role view for message {message_id} in guild {guild_id}")
    
    @commands.hybrid_group(name="reactionrole", description="Manage reaction roles")
    @commands.has_permissions(manage_roles=True)
    async def reactionrole(self, ctx):
        """Base command for managing reaction roles"""
        if ctx.invoked_subcommand is None:
            embed = EmbedCreator.create_info_embed(
                "Reaction Roles",
                f"Use `{CONFIG['prefix']}reactionrole create` to create a new reaction role message."
            )
            await ctx.send(embed=embed)
    
    @reactionrole.command(name="create", description="Create a new reaction role message")
    @commands.has_permissions(manage_roles=True)
    async def create(self, ctx):
        """Interactive command to create a reaction role message"""
        # Initialize empty data
        title = "Role Selection"
        description = "Select roles from the dropdown below"
        roles = []
        
        # Ask for title
        embed = EmbedCreator.create_info_embed(
            "Reaction Role Setup (1/3)",
            "Please enter a title for your reaction role message, or type 'cancel' to abort."
        )
        await ctx.send(embed=embed)
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        
        try:
            # Get title
            msg = await self.bot.wait_for('message', check=check, timeout=60)
            
            if msg.content.lower() == 'cancel':
                await ctx.send("Setup cancelled.")
                return
            
            title = msg.content
            
            # Ask for description
            embed = EmbedCreator.create_info_embed(
                "Reaction Role Setup (2/3)",
                "Please enter a description for your reaction role message, or type 'cancel' to abort."
            )
            await ctx.send(embed=embed)
            
            # Get description
            msg = await self.bot.wait_for('message', check=check, timeout=60)
            
            if msg.content.lower() == 'cancel':
                await ctx.send("Setup cancelled.")
                return
            
            description = msg.content
            
            # Ask for roles
            embed = EmbedCreator.create_info_embed(
                "Reaction Role Setup (3/3)",
                "Now let's add some roles. For each role, send a message in this format:\n"
                "`@Role :emoji: Description of the role`\n\n"
                "Send 'done' when you're finished, or 'cancel' to abort."
            )
            await ctx.send(embed=embed)
            
            # Collect roles
            while True:
                msg = await self.bot.wait_for('message', check=check, timeout=60)
                
                if msg.content.lower() == 'done':
                    break
                
                if msg.content.lower() == 'cancel':
                    await ctx.send("Setup cancelled.")
                    return
                
                # Parse the role, emoji, and description
                if not msg.role_mentions:
                    await ctx.send("Please mention a role with @Role.")
                    continue
                
                role = msg.role_mentions[0]
                
                # Extract emoji and description
                content = msg.content
                role_mention = f"<@&{role.id}>"
                content = content.replace(role_mention, "", 1).strip()
                
                # Find emoji in content
                emoji = None
                description = None
                
                # Check for custom emoji
                custom_emoji_match = discord.utils.get(self.bot.emojis, name=content.split(':')[1]) if ':' in content else None
                
                if custom_emoji_match:
                    emoji = str(custom_emoji_match)
                    description = content.split(':', 2)[2].strip() if len(content.split(':', 2)) > 2 else f"Get the {role.name} role"
                else:
                    # Check for unicode emoji
                    for char in content:
                        if char.isalnum() or char.isspace():
                            if emoji is not None:
                                description = content[content.find(char):]
                                break
                        else:
                            if emoji is None:
                                emoji = char
                            else:
                                emoji += char
                
                if not emoji:
                    await ctx.send("Could not find an emoji in your message. Please include an emoji.")
                    continue
                
                if not description:
                    description = f"Get the {role.name} role"
                
                # Add role to the list
                roles.append({
                    'id': role.id,
                    'name': role.name,
                    'description': description,
                    'emoji': emoji
                })
                
                await ctx.send(f"Added role {role.name} with emoji {emoji}.")
            
            # Check if we have any roles
            if not roles:
                await ctx.send("You didn't add any roles. Setup cancelled.")
                return
            
            # Create the embed and view
            embed = EmbedCreator.create_reaction_roles_embed(title, description, roles)
            view = RoleView(roles)
            
            # Send the reaction role message
            reaction_message = await ctx.send(embed=embed, view=view)
            
            # Store in database
            for role in roles:
                db.set_reaction_role(
                    ctx.guild.id,
                    reaction_message.id,
                    role['id'],
                    role['emoji']
                )
            
            # Confirm
            await ctx.send("Reaction role message created successfully!")
            
        except asyncio.TimeoutError:
            await ctx.send("Setup timed out. Please try again.")
        except Exception as e:
            logger.error(f"Error in reaction role setup: {e}")
            await ctx.send(f"An error occurred during setup: {e}")
    
    @reactionrole.command(name="delete", description="Delete a reaction role message")
    @commands.has_permissions(manage_roles=True)
    async def delete(self, ctx, message_id: str):
        """Delete a reaction role message
        
        Args:
            message_id: The ID of the message to delete
        """
        try:
            # Check if message exists in the database
            reaction_roles = db.data.get('reaction_roles', {}).get(str(ctx.guild.id), {}).get(message_id)
            
            if not reaction_roles:
                embed = EmbedCreator.create_error_embed(
                    "Not Found",
                    "Could not find a reaction role message with that ID."
                )
                await ctx.send(embed=embed)
                return
            
            # Try to delete the message
            try:
                for channel in ctx.guild.text_channels:
                    try:
                        message = await channel.fetch_message(int(message_id))
                        await message.delete()
                        break
                    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                        continue
            except Exception as e:
                logger.error(f"Error deleting message: {e}")
                await ctx.send("Could not delete the message, but will remove it from the database.")
            
            # Remove from database
            if str(ctx.guild.id) in db.data.get('reaction_roles', {}) and message_id in db.data['reaction_roles'][str(ctx.guild.id)]:
                del db.data['reaction_roles'][str(ctx.guild.id)][message_id]
                db._save_data()
            
            embed = EmbedCreator.create_success_embed(
                "Deleted",
                "Reaction role message has been deleted."
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in reaction role delete: {e}")
            embed = EmbedCreator.create_error_embed(
                "Error",
                f"An error occurred: {e}"
            )
            await ctx.send(embed=embed)
    
    @reactionrole.command(name="list", description="List all reaction role messages")
    @commands.has_permissions(manage_roles=True)
    async def list(self, ctx):
        """List all reaction role messages in the server"""
        reaction_roles = db.data.get('reaction_roles', {}).get(str(ctx.guild.id), {})
        
        if not reaction_roles:
            embed = EmbedCreator.create_info_embed(
                "No Reaction Roles",
                "This server has no reaction role messages."
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="Reaction Role Messages",
            description="Here are all the reaction role messages in this server:",
            color=CONFIG['colors']['default']
        )
        
        for message_id, roles in reaction_roles.items():
            role_count = len(roles)
            
            # Try to get the channel
            channel_id = None
            for channel in ctx.guild.text_channels:
                try:
                    message = await channel.fetch_message(int(message_id))
                    channel_id = channel.id
                    break
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    continue
            
            channel_text = f"<#{channel_id}>" if channel_id else "Unknown channel"
            
            embed.add_field(
                name=f"Message ID: {message_id}",
                value=f"Channel: {channel_text}\nRoles: {role_count}",
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))
