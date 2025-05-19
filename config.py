# Bot configuration settings

CONFIG = {
    'prefix': '.',  # Bot command prefix
    'cogs': [
        'fixed_help_menu',  # Only use this help menu
        'autorole',
        'giveaway',
        'simple_levels',
        'tickets',
        'invites',
        'messages',
        'reaction_roles',
        'welcome',
        'polls',
        'utility',
        'role_menu',
        'timeout',
        'channel_management',
        'direct_moderation'
    ],
    'colors': {
        'default': 0x5865F2,  # Discord Blurple
        'success': 0x57F287,  # Green
        'error': 0xED4245,    # Red
        'warning': 0xFEE75C,  # Yellow
        'info': 0x3498DB      # Blue
    },
    'emojis': {
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️',
        'loading': '⏳',
        'ticket': '🎫',
        'giveaway': '🎉',
        'level': '⬆️',
        'invite': '📨',
        'message': '💬',
        'role': '👑'
    },
    'cooldowns': {
        'default': 3,  # Default cooldown in seconds
        'giveaway': 30,
        'ticket': 60
    },
    'placeholders': {
        'thumbnail_url': 'https://cdn.discordapp.com/emojis/964566755781476473.png'
    },
    'custom_gifs': {
        'welcome': 'assets/images/welcome.gif'
    },
    'levels': {
        'xp_per_message': 15,      # Base XP for each message
        'xp_randomizer': 5,        # Random bonus XP (0 to this value)
        'xp_cooldown': 60,         # Seconds between XP awards
        'level_up_channel_id': None,  # Set to a specific channel ID to send all level up notifications
                                      # If None, uses guild-specific settings from the database
        'level_roles': {}           # Roles awarded at specific levels - format: {level: role_id}
    }
}
