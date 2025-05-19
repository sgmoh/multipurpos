# Bot configuration settings

CONFIG = {
    'prefix': '.',  # Bot command prefix
    'cogs': [
        'fixed_help_menu',
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
        'gif_url': 'https://i.imgur.com/qlOthc3.gif',
        'thumbnail_url': 'https://cdn.discordapp.com/emojis/964566755781476473.png'
    }
}
