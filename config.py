# Bot configuration settings

CONFIG = {
    'prefix': '.',  # Bot command prefix
    'cogs': [
        'help_commands',
        'autorole',
        'giveaway',
        'levels',
        'tickets',
        'invites',
        'messages',
        'reaction_roles'
    ],
    'colors': {
        'default': 0x5865F2,  # Discord Blurple
        'success': 0x57F287,  # Green
        'error': 0xED4245,    # Red
        'warning': 0xFEE75C   # Yellow
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
        'gif_url': 'https://cdn.discordapp.com/attachments/1234567890/1234567890/help_banner.gif',
        'thumbnail_url': 'https://cdn.discordapp.com/attachments/1234567890/1234567890/category_icon.png'
    }
}
