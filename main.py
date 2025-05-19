from flask import Flask, render_template
import threading
import subprocess
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('main')

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bot')
def bot_info():
    return "The Discord bot is configured and running in the background."

def start_discord_bot():
    """Start the Discord bot in a separate process"""
    logger.info("Starting Discord bot...")
    try:
        subprocess.Popen(["python", "start_discord_bot.py"], 
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
        logger.info("Discord bot process started")
    except Exception as e:
        logger.error(f"Failed to start Discord bot: {e}")

# Start the Discord bot when the server starts
start_discord_bot()