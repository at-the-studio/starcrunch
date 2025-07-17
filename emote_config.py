# 🔹---💠---🔹•EMOTE CONFIGURATION•🔹---💠---🔹
# Maps emoji to Discord custom emote codes

EMOTE_MAP = {
    # Main Character/Theme
    '🦕': '<:starcrunch:1392407227394035814>',  # dinosaur - Starcrunch
    '🚀': '<:starcrunch2:>',  # rocket - space theme (needs emote code)
    
    # Task Categories
    '📅': '<:appntmt:1392405806481145906>',  # calendar - appointments
    '🧹': '<:clean:1392405840790683698>',  # broom - cleaning tasks
    '🛍️': '<:shopping:1392407207626408026>',  # shopping bags - errands
    '💼': '<:worktask:>',  # briefcase - work tasks (from worktask.png)
    '👤': '<:personal:>',  # person - personal tasks (from personal.png)
    '📋': '<:general:1392406970325274636>',  # clipboard - generic tasks
    
    # Priority Levels
    '🔥': '<:highP:1392407013564219392>',  # fire - high priority
    '⚡': '<:mediumP:1392407045210243072>',  # lightning - medium priority
    '💤': '<:lowP:1392407030584574172>',  # sleeping - low priority
    
    # Status & Actions
    '✅': '✅',  # Use regular emoji for now
    '📡': '<:connected:1392406868458082414>',  # satellite - connected/online
    '⏰': '<:peakfocus:1392407141289164921>',  # alarm clock - time/duration
    '🎯': '<:goals:1392406997143519242>',  # target - goals/tasks
    '🏆': '🏆',  # Use regular emoji for now
    '💡': '💡',  # Use regular emoji for now
    
    # Time of Day Tasks
    '🌅': '<:morningtask:>',  # sunrise - morning tasks (from morningtask.png)
    '☀️': '<:afternoontask:1392405316737564762>',  # sun - afternoon tasks
    '🌙': '<:nighttask:1392407123417239552>',  # moon - night tasks
    
    # UI & Feedback  
    '🏪': '<:store:>',  # convenience store - errands (from store.png)
    '📁': '<:data:1392406884795027526>',  # folder - data/files
    '⚠️': '<:error:1392406934401056788>',  # warning - alerts
    '❌': '<:cancel:1392405831684980776>',  # X - errors/cancel
    '🔍': '<:search:1392407193294475264>',  # magnifying glass - search/check
    
    # Task Types
    '🛒': '<:errand:1392406920505327719>',  # shopping cart - errands
    '🎮': '<:gamingtask:1392406957469601793>',  # game controller - gaming tasks
    '💻': '<:worktask2:1392405403916173393>',  # computer - work tasks
    '🎯': '<:personaltask:1392407168120258560>',  # target - personal tasks
    
    # Stars
    '⭐': '<:4ptstar:1392405561110433802>',  # 4-point star
    '🌟': '<:5ptstar:1392405575056232478>',  # 5-point star  
    '✨': '<:8ptstar:1392405584963174431>',  # 8-point star
    
    # Days of Week
    'monday': '<:monday:1392407080782135336>',
    'tuesday': '<:tuesday:>',  # from tuesday.png
    'wednesday': '<:wednesday:>',  # from wednesday.png  
    'thursday': '<:thursday:>',  # from thursday.png
    'friday': '<:friday:>',  # from friday.png
    'saturday': '<:saturday:1392407182292684820>',
    'sunday': '<:sunday:>',  # from sunday.png
    
    # Special
    '🦶': '<:dinopaw:1392406904613113868>',  # dinosaur paw
    '📝': '<:todo:>',  # todo list (from todo.png)
    '❌': '<:missed:>',  # missed task (from missed.png)
    '🧹': '<:clean2:1392405854535286836>',  # alternate clean icon
    '📦': '<:batcherrands:1392405821627043870>',  # batch errands
    
    # Animated banners and special emotes
    'info_banner': '<a:info_banner:1393082430218436788>',
    'banner': '<a:banner:1393084917839171624>',
    '8ptstar': '<:8ptstar:1392834331906539590>',
}

def get_emote(emoji_or_name):
    """Get Discord emote code for an emoji or name"""
    # Direct emoji lookup
    if emoji_or_name in EMOTE_MAP:
        emote = EMOTE_MAP[emoji_or_name]
        # If custom emote code is incomplete, return original emoji
        if emote and ':>' in emote and not emote.endswith('>'):
            return emoji_or_name
        return emote
    
    # Try lowercase name lookup for days
    if emoji_or_name.lower() in EMOTE_MAP:
        emote = EMOTE_MAP[emoji_or_name.lower()]
        if emote and ':>' in emote and not emote.endswith('>'):
            return emoji_or_name
        return emote
    
    # Return original if no mapping found
    return emoji_or_name

def replace_emojis(text):
    """Replace all emojis in text with Discord emote codes"""
    result = text
    for emoji, emote_code in EMOTE_MAP.items():
        if emote_code and ':>' in emote_code:  # Only replace if we have a valid emote code
            result = result.replace(emoji, emote_code)
    return result