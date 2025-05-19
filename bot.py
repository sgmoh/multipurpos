import discord
from discord.ext import commands
import os
import logging
import asyncio
from config import PREFIX

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('discord_bot')

def initialize_bot():
    # Set intents - we need all of them for the features we're implementing
    intents = discord.Intents.all()
    
    # Initialize the bot with prefix and intents
    bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)
    
    @bot.event
    async def on_ready():
        """Event triggered when the bot is ready and connected to Discord."""
        logger.info(f'Logged in as {bot.user.name} ({bot.user.id})')
        await bot.change_presence(activity=discord.Activity(
            type=discord.ActivityType.watching, 
            name=f"for {PREFIX}help"
        ))
        logger.info("Bot is ready!")
    
    # Load all cogs
    async def load_cogs():
        """Load all cogs from the cogs directory."""
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await bot.load_extension(f'cogs.{filename[:-3]}')
                    logger.info(f'Loaded cog: {filename[:-3]}')
                except Exception as e:
                    logger.error(f'Failed to load cog {filename[:-3]}: {e}')
    
    @bot.event
    async def on_connect():
        """Event triggered when the bot connects to Discord."""
        await load_cogs()
    
    @bot.event
    async def on_command_error(ctx, error):
        """Global error handler for command errors."""
        if isinstance(error, commands.CommandNotFound):
            return
        
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: {error.param.name}")
            return
        
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command.")
            return
            
        if isinstance(error, commands.BotMissingPermissions):
            await ctx.send(f"I need the following permission(s) to execute this command: {', '.join(error.missing_permissions)}")
            return
        
        # Log the error for debugging
        logger.error(f"Command error in {ctx.command}: {error}")
        await ctx.send(f"An error occurred: {error}")
    
    return bot
