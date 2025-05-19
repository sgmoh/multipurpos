import os
import subprocess
import threading
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('bot_runner')

def run_discord_bot():
    """Run the Discord bot in a separate process"""
    logger.info("Starting Discord bot...")
    try:
        subprocess.run(["python", "discord_bot.py"])
    except Exception as e:
        logger.error(f"Error running Discord bot: {e}")

if __name__ == "__main__":
    # Start the Discord bot in a separate thread
    bot_thread = threading.Thread(target=run_discord_bot)
    bot_thread.daemon = True  # This makes the thread exit when the main program exits
    bot_thread.start()
    
    logger.info("Discord bot thread started.")
    logger.info("The web server is running in the main process.")
    
    # Keep the script running to keep the bot thread alive
    try:
        while True:
            time.sleep(10)  # Sleep to prevent CPU usage
    except KeyboardInterrupt:
        logger.info("Shutting down...")