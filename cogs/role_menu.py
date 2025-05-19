import discord
from discord.ext import commands
import logging
import json
import os
from discord import ui, SelectOption
from config import CONFIG
from utils.embed_creator import EmbedCreator

logger = logging.getLogger('discord_bot')

class RoleDropdown(ui.Select):
    """Dropdown menu for role selection"""
    
    def __init__(self, roles_data):
        self.roles_data = roles_data
        
        # Create options for the dropdown
        options = []
        for role_id, role_info in roles_data.items():
            options.append(
                SelectOption(
                    label=role_info["name"],
                    description=role_info["description"],
                    emoji=role_info["emoji"] if "emoji" in role_info else None,
                    value=role_id
                )
            )
        
        # Initialize the select with options
        super().__init__(
            placeholder="Select roles to add/remove...",
            min_values=0,
            max_values=len(options),
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Handle dropdown selection"""
        await interaction.response.defer(ephemeral=True)
        
        # Get the member
        member = interaction.user
        guild = interaction.guild
        
        # Track added and removed roles
        added_roles = []
        removed_roles = []
        
        for role_id, role_info in self.roles_data.items():
            role = guild.get_role(int(role_id))
            if not role:
                continue
                
            # Check if role was selected
            if role_id in self.values:
                # Add role if user doesn't have it
                if role not in member.roles:
                    try:
                        await member.add_roles(role)
                        added_roles.append(role.name)
                    except:
                        pass
            else:
                # Remove role if user has it
                if role in member.roles:
                    try:
                        await member.remove_roles(role)
                        removed_roles.append(role.name)
                    except:
                        pass
        
        # Create response message
        response = ""
        if added_roles:
            response += f"✅ Added roles: {', '.join(added_roles)}\n"
        if removed_roles:
            response += f"❌ Removed roles: {', '.join(removed_roles)}\n"
        if not added_roles and not removed_roles:
            response = "No role changes were made."
            
        await interaction.followup.send(response, ephemeral=True)


class RoleMenuView(ui.View):
    """View containing role dropdown menu"""
    
    def __init__(self, roles_data):
        super().__init__(timeout=None)  # Make the view persistent
        
        # Add the dropdown to the view
        self.add_item(RoleDropdown(roles_data))


class RoleMenu(commands.Cog):
    """Role menu system with dropdowns for easy role assignment"""
    
    def __init__(self, bot):
        self.bot = bot
        self.role_menus = {}
        self.data_file = 'data/role_menus.json'
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        
        # Load settings
        self.load_settings()
        
        logger.info("RoleMenu cog initialized")
        
    def load_settings(self):
        """Load role menu settings from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    self.role_menus = json.load(f)
            else:
                self.role_menus = {}
                self.save_settings()
        except Exception as e:
            logger.error(f"Error loading role menu settings: {e}")
            self.role_menus = {}
            
    def save_settings(self):
        """Save role menu settings to file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.role_menus, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving role menu settings: {e}")
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Re-create active role menus when the bot starts"""
        for guild_id, menus in self.role_menus.items():
            for message_id, menu_data in menus.items():
                # Try to get the message
                try:
                    channel = self.bot.get_channel(int(menu_data["channel_id"]))
                    if not channel:
                        continue
                        
                    message = await channel.fetch_message(int(message_id))
                    if not message:
                        continue
                        
                    # Create a new view for the message
                    view = RoleMenuView(menu_data["roles"])
                    
                    # Update the message with the new view
                    await message.edit(view=view)
                    
                    logger.info(f"Restored role menu for message {message_id} in guild {guild_id}")
                except Exception as e:
                    logger.error(f"Error restoring role menu: {e}")
    
    @commands.group(name="rolemenu", invoke_without_command=True)
    @commands.has_permissions(manage_roles=True)
    async def rolemenu(self, ctx):
        """Role menu commands with dropdowns"""
        embed = discord.Embed(
            title="🔽 Role Menu Commands",
            description="Create and manage role menus with dropdowns",
            color=CONFIG['colors']['default']
        )
        
        commands = [
            f"`{CONFIG['prefix']}rolemenu create` - Create a new role menu",
            f"`{CONFIG['prefix']}rolemenu delete <message_id>` - Delete a role menu",
            f"`{CONFIG['prefix']}rolemenu list` - List all role menus in this server"
        ]
        
        embed.add_field(
            name="Available Commands",
            value="\n".join(commands),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @rolemenu.command(name="create")
    @commands.has_permissions(manage_roles=True)
    async def create_menu(self, ctx):
        """Create a new role menu with dropdown"""
        # Start the role menu creation process
        embed = EmbedCreator.create_info_embed(
            "Role Menu Setup (1/3)",
            "Please enter a title for your role menu, or type 'cancel' to abort."
        )
        
        await ctx.send(embed=embed)
        
        # Wait for the title
        try:
            title_message = await self.bot.wait_for(
                "message",
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel,
                timeout=60.0
            )
            
            title = title_message.content
            
            if title.lower() == "cancel":
                await ctx.send(embed=EmbedCreator.create_error_embed("Setup Cancelled", "Role menu creation has been cancelled."))
                return
                
            # Ask for description
            embed = EmbedCreator.create_info_embed(
                "Role Menu Setup (2/3)",
                "Please enter a description for your role menu, or type 'cancel' to abort."
            )
            
            await ctx.send(embed=embed)
            
            # Wait for the description
            description_message = await self.bot.wait_for(
                "message",
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel,
                timeout=60.0
            )
            
            description = description_message.content
            
            if description.lower() == "cancel":
                await ctx.send(embed=EmbedCreator.create_error_embed("Setup Cancelled", "Role menu creation has been cancelled."))
                return
                
            # Ask for roles
            embed = EmbedCreator.create_info_embed(
                "Role Menu Setup (3/3)",
                "Now let's add some roles. For each role, send a message in this format:\n"
                "@Role Description of the role\n\n"
                "You can optionally include an emoji after the role mention:\n"
                "@Role 🎮 Gamers role\n\n"
                "Send 'done' when you're finished, or 'cancel' to abort."
            )
            
            await ctx.send(embed=embed)
            
            # Collect roles
            roles_data = {}
            
            while True:
                role_message = await self.bot.wait_for(
                    "message",
                    check=lambda m: m.author == ctx.author and m.channel == ctx.channel,
                    timeout=120.0
                )
                
                content = role_message.content
                
                if content.lower() == "cancel":
                    await ctx.send(embed=EmbedCreator.create_error_embed("Setup Cancelled", "Role menu creation has been cancelled."))
                    return
                    
                if content.lower() == "done":
                    if not roles_data:
                        await ctx.send(embed=EmbedCreator.create_error_embed("No Roles Added", "You need to add at least one role. Try again or type 'cancel' to abort."))
                        continue
                    else:
                        break
                
                # Parse role from the message
                if not role_message.role_mentions:
                    await ctx.send("Please mention a role with @Role.")
                    continue
                
                role = role_message.role_mentions[0]
                
                # Check bot permissions for the role
                if role >= ctx.guild.me.top_role:
                    await ctx.send(f"I cannot assign the role {role.mention} because it's higher than or equal to my highest role.")
                    continue
                    
                # Get description (everything after the role mention)
                parts = content.split(' ', 1)
                if len(parts) < 2:
                    await ctx.send("Please include a description for the role.")
                    continue
                    
                role_content = parts[1].strip()
                
                # Check if there's an emoji at the start of the description
                emoji = None
                description = role_content
                
                # Try to parse emoji from the start of the description
                for i, char in enumerate(role_content):
                    if char.isalpha() or char.isspace():
                        if i > 0:
                            emoji = role_content[:i].strip()
                            description = role_content[i:].strip()
                        break
                
                # Store role information
                roles_data[str(role.id)] = {
                    "name": role.name,
                    "description": description,
                }
                
                if emoji:
                    roles_data[str(role.id)]["emoji"] = emoji
                
                await ctx.send(f"Added role {role.mention}.")
            
            # Create the role menu embed
            menu_embed = discord.Embed(
                title=title,
                description=description,
                color=CONFIG['colors']['default']
            )
            
            menu_embed.add_field(
                name="Available Roles",
                value="Use the dropdown menu below to add or remove roles.",
                inline=False
            )
            
            # Create the view with the dropdown
            view = RoleMenuView(roles_data)
            
            # Send the menu
            menu_message = await ctx.send(embed=menu_embed, view=view)
            
            # Save the menu to settings
            guild_id = str(ctx.guild.id)
            
            if guild_id not in self.role_menus:
                self.role_menus[guild_id] = {}
                
            self.role_menus[guild_id][str(menu_message.id)] = {
                "title": title,
                "description": description,
                "roles": roles_data,
                "channel_id": str(ctx.channel.id),
                "author_id": str(ctx.author.id)
            }
            
            self.save_settings()
            
            # Send confirmation
            await ctx.send(embed=EmbedCreator.create_success_embed(
                "Role Menu Created",
                "Your role menu has been created! Users can now select roles from the dropdown menu."
            ))
            
        except asyncio.TimeoutError:
            await ctx.send(embed=EmbedCreator.create_error_embed("Setup Timed Out", "You took too long to respond. Please try again."))
            return
        except Exception as e:
            logger.error(f"Error creating role menu: {e}")
            await ctx.send(embed=EmbedCreator.create_error_embed("Error", f"An error occurred while creating the role menu: {str(e)}"))
            return
    
    @rolemenu.command(name="delete")
    @commands.has_permissions(manage_roles=True)
    async def delete_menu(self, ctx, message_id: str):
        """Delete a role menu
        
        Args:
            message_id: The ID of the role menu message to delete
        """
        guild_id = str(ctx.guild.id)
        
        # Check if the menu exists
        if (guild_id not in self.role_menus or
            message_id not in self.role_menus[guild_id]):
            
            await ctx.send(embed=EmbedCreator.create_error_embed(
                "Menu Not Found",
                f"Could not find a role menu with ID {message_id}."
            ))
            return
        
        # Get the menu data
        menu_data = self.role_menus[guild_id][message_id]
        
        # Check permissions to delete
        if (str(ctx.author.id) != menu_data["author_id"] and
            not ctx.author.guild_permissions.administrator):
            
            await ctx.send(embed=EmbedCreator.create_error_embed(
                "Permission Denied",
                "You can only delete role menus that you created, unless you are an administrator."
            ))
            return
        
        # Try to delete the message
        try:
            channel = ctx.guild.get_channel(int(menu_data["channel_id"]))
            if channel:
                try:
                    message = await channel.fetch_message(int(message_id))
                    if message:
                        await message.delete()
                except:
                    pass
        except Exception as e:
            logger.error(f"Error deleting role menu message: {e}")
        
        # Remove the menu from settings
        del self.role_menus[guild_id][message_id]
        if not self.role_menus[guild_id]:
            del self.role_menus[guild_id]
            
        self.save_settings()
        
        # Send confirmation
        await ctx.send(embed=EmbedCreator.create_success_embed(
            "Role Menu Deleted",
            f"The role menu with ID {message_id} has been deleted."
        ))
    
    @rolemenu.command(name="list")
    @commands.has_permissions(manage_roles=True)
    async def list_menus(self, ctx):
        """List all role menus in the server"""
        guild_id = str(ctx.guild.id)
        
        # Check if there are any menus
        if guild_id not in self.role_menus or not self.role_menus[guild_id]:
            await ctx.send(embed=EmbedCreator.create_info_embed(
                "No Role Menus",
                "There are no role menus in this server."
            ))
            return
        
        # Create embed
        embed = discord.Embed(
            title="🔽 Role Menus",
            description=f"There are {len(self.role_menus[guild_id])} role menus in this server.",
            color=CONFIG['colors']['info']
        )
        
        # Add each menu
        for message_id, menu_data in self.role_menus[guild_id].items():
            # Get channel
            channel = ctx.guild.get_channel(int(menu_data["channel_id"]))
            channel_mention = channel.mention if channel else "Unknown Channel"
            
            # Get author
            author_id = menu_data["author_id"]
            author = ctx.guild.get_member(int(author_id))
            author_name = author.display_name if author else "Unknown User"
            
            # Get role count
            role_count = len(menu_data["roles"])
            
            # Create field
            embed.add_field(
                name=f"Menu: {menu_data['title']}",
                value=f"**ID:** {message_id}\n"
                      f"**Channel:** {channel_mention}\n"
                      f"**Roles:** {role_count}\n"
                      f"**Created by:** {author_name}\n"
                      f"`{CONFIG['prefix']}rolemenu delete {message_id}` to delete",
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(RoleMenu(bot))