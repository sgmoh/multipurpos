import discord
from discord.ext import commands
import logging
import asyncio

from utils.database import db
from utils.embed_creator import EmbedCreator
from config import CONFIG

logger = logging.getLogger('discord_bot')

class TicketButton(discord.ui.Button):
    """Button for creating tickets"""
    
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label="Create Ticket",
            emoji=CONFIG['emojis']['ticket'],
            custom_id="create_ticket"
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Handle button click"""
        # Check if user already has an open ticket
        guild_tickets = db.data.get('tickets', {}).get(str(interaction.guild.id), {})
        for channel_id, ticket_data in guild_tickets.items():
            if ticket_data.get('user_id') == str(interaction.user.id) and ticket_data.get('status') == 'open':
                # User already has an open ticket
                channel = interaction.guild.get_channel(int(channel_id))
                if channel:
                    await interaction.response.send_message(
                        f"You already have an open ticket: {channel.mention}",
                        ephemeral=True
                    )
                    return
        
        # Create new ticket channel
        try:
            # Get or create ticket category
            category = None
            for cat in interaction.guild.categories:
                if cat.name.lower() == "tickets":
                    category = cat
                    break
            
            if not category:
                # Create category
                category = await interaction.guild.create_category("Tickets")
                # Set permissions for the category
                await category.set_permissions(interaction.guild.default_role, read_messages=False)
                await category.set_permissions(interaction.guild.me, read_messages=True, send_messages=True)
            
            # Create ticket channel
            channel_name = f"ticket-{interaction.user.name.lower()}"
            channel = await interaction.guild.create_text_channel(
                channel_name,
                category=category,
                topic=f"Ticket for {interaction.user.name} | ID: {interaction.user.id}"
            )
            
            # Set permissions for the ticket channel
            await channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
            
            # Save ticket to database
            db.create_ticket(interaction.guild.id, channel.id, interaction.user.id)
            
            # Create ticket welcome message
            embed = discord.Embed(
                title=f"{CONFIG['emojis']['ticket']} Ticket Created",
                description=f"Thank you for creating a ticket, {interaction.user.mention}!\nSupport will be with you shortly.",
                color=CONFIG['colors']['success']
            )
            
            embed.add_field(
                name="Closing the Ticket",
                value=f"Use the `{CONFIG['prefix']}close` command when your issue is resolved.",
                inline=False
            )
            
            # Create close button
            close_button = discord.ui.Button(
                style=discord.ButtonStyle.danger,
                label="Close Ticket",
                emoji="🔒",
                custom_id="close_ticket"
            )
            
            view = discord.ui.View()
            view.add_item(close_button)
            
            # Send welcome message
            await channel.send(
                content=f"{interaction.user.mention} Support team will be with you shortly!",
                embed=embed,
                view=view
            )
            
            # Notify user
            await interaction.response.send_message(
                f"Ticket created! Head over to {channel.mention}",
                ephemeral=True
            )
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "I don't have permission to create ticket channels. Please contact an administrator.",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            await interaction.response.send_message(
                "An error occurred while creating your ticket. Please try again later.",
                ephemeral=True
            )

class TicketView(discord.ui.View):
    """View for ticket buttons"""
    
    def __init__(self):
        super().__init__(timeout=None)  # Persistent view
        self.add_item(TicketButton())

class Tickets(commands.Cog):
    """Ticket system for support requests"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("Tickets cog initialized")
        
        # Register persistent view
        self.bot.add_view(TicketView())
    
    @commands.hybrid_command(name="ticket", description="Set up the ticket system")
    @commands.has_permissions(manage_channels=True)
    async def ticket(self, ctx, option: str = "setup"):
        """Set up the ticket system
        
        Args:
            option: The option to use (setup)
        """
        if option.lower() == "setup":
            # Create ticket embed and button
            embed = EmbedCreator.create_ticket_embed()
            view = TicketView()
            
            # Send the ticket message
            await ctx.send(embed=embed, view=view)
    
    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        """Handle interactions for ticket buttons"""
        if not interaction.type == discord.InteractionType.component:
            return
        
        # Handle close ticket button
        if interaction.data.get('custom_id') == 'close_ticket':
            # Check if this is a ticket channel
            ticket_data = db.get_ticket(interaction.guild.id, interaction.channel.id)
            if not ticket_data:
                await interaction.response.send_message(
                    "This is not a ticket channel.",
                    ephemeral=True
                )
                return
            
            # Check permissions
            if not interaction.user.guild_permissions.manage_channels and \
               str(interaction.user.id) != ticket_data.get('user_id'):
                await interaction.response.send_message(
                    "You don't have permission to close this ticket.",
                    ephemeral=True
                )
                return
            
            # Update database
            db.close_ticket(interaction.guild.id, interaction.channel.id)
            
            # Send closing message
            await interaction.response.send_message(
                f"🔒 Ticket closed by {interaction.user.mention}. This channel will be deleted in 5 seconds.",
                ephemeral=False
            )
            
            # Wait and delete the channel
            await asyncio.sleep(5)
            try:
                await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")
            except discord.Forbidden:
                await interaction.channel.send("I don't have permission to delete this channel.")
            except discord.HTTPException as e:
                logger.error(f"Error deleting ticket channel: {e}")
    
    @commands.hybrid_command(name="close", description="Close a ticket")
    async def close(self, ctx):
        """Close a ticket channel"""
        # Check if this is a ticket channel
        ticket_data = db.get_ticket(ctx.guild.id, ctx.channel.id)
        if not ticket_data:
            embed = EmbedCreator.create_error_embed(
                "Not a Ticket",
                "This command can only be used in ticket channels."
            )
            await ctx.send(embed=embed)
            return
        
        # Check permissions
        if not ctx.author.guild_permissions.manage_channels and \
           str(ctx.author.id) != ticket_data.get('user_id'):
            embed = EmbedCreator.create_error_embed(
                "Permission Denied",
                "You don't have permission to close this ticket."
            )
            await ctx.send(embed=embed)
            return
        
        # Update database
        db.close_ticket(ctx.guild.id, ctx.channel.id)
        
        # Send closing message
        embed = EmbedCreator.create_success_embed(
            "Ticket Closing",
            f"Ticket closed by {ctx.author.mention}. This channel will be deleted in 5 seconds."
        )
        await ctx.send(embed=embed)
        
        # Wait and delete the channel
        await asyncio.sleep(5)
        try:
            await ctx.channel.delete(reason=f"Ticket closed by {ctx.author}")
        except discord.Forbidden:
            await ctx.send("I don't have permission to delete this channel.")
        except discord.HTTPException as e:
            logger.error(f"Error deleting ticket channel: {e}")

async def setup(bot):
    await bot.add_cog(Tickets(bot))
