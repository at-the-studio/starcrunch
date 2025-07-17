// 🔹---💠---🔹•DISCORD EMOTE HANDLER•🔹---💠---🔹

const EMOTE_MAP = {
    // Main Character/Theme
    '🦕': '<:starcrunch:1392407227394035814>',
    '🚀': '<:starcrunch2:>',
    
    // Task Categories
    '📅': '<:appntmt:1392405806481145906>',
    '🧹': '<:clean:1392405840790683698>',
    '🛍️': '<:shopping:1392407207626408026>',
    '💼': '<:worktask:>',
    '👤': '<:personal:>',
    '📋': '<:general:1392406970325274636>',
    
    // Priority Levels
    '🔥': '<:highP:1392407013564219392>',
    '⚡': '<:mediumP:1392407045210243072>',
    '💤': '<:lowP:1392407030584574172>',
    
    // Status & Actions
    '✅': '<:complete:>',
    '📡': '<:connected:1392406868458082414>',
    '⏰': '<:peakfocus:1392407141289164921>',
    '🎯': '<:goals:1392406997143519242>',
    '🏆': '<:achievements:>',
    '💡': '<:suggestions:>',
    
    // Time of Day Tasks
    '🌅': '<:morningtask:>',
    '☀️': '<:afternoontask:1392405316737564762>',
    '🌙': '<:nighttask:1392407123417239552>',
    
    // UI & Feedback  
    '🏪': '<:store:>',
    '📁': '<:data:1392406884795027526>',
    '⚠️': '<:error:1392406934401056788>',
    '❌': '<:cancel:1392405831684980776>',
    '🔍': '<:search:1392407193294475264>',
    
    // Task Types
    '🛒': '<:errand:1392406920505327719>',
    '🎮': '<:gamingtask:1392406957469601793>',
    '💻': '<:worktask2:1392405403916173393>',
    
    // Stars
    '⭐': '<:4ptstar:1392405561110433802>',
    '🌟': '<:5ptstar:1392405575056232478>',
    '✨': '<:8ptstar:1392405584963174431>',
    
    // Days of Week
    'monday': '<:monday:1392407080782135336>',
    'tuesday': '<:tuesday:>',
    'wednesday': '<:wednesday:>',
    'thursday': '<:thursday:>',
    'friday': '<:friday:>',
    'saturday': '<:saturday:1392407182292684820>',
    'sunday': '<:sunday:>',
    
    // Special
    '🦶': '<:dinopaw:1392406904613113868>',
    '📝': '<:todo:>',
    '🧹': '<:clean2:1392405854535286836>',
    '📦': '<:batcherrands:1392405821627043870>'
};

// Function to convert emote code to image
function emoteToImage(emoteCode) {
    // Extract emote name from code like <:starcrunch:1392407227394035814>
    const match = emoteCode.match(/<:(\w+):(\d*)>/);
    if (match) {
        const emoteName = match[1];
        const emoteId = match[2];
        
        // If we have an ID, return Discord CDN URL
        if (emoteId) {
            return `<img src="https://cdn.discordapp.com/emojis/${emoteId}.png" alt="${emoteName}" class="discord-emote" />`;
        }
        
        // Otherwise try to use local image
        return `<img src="starcrunchemotes/${emoteName}.png" alt="${emoteName}" class="discord-emote" />`;
    }
    return emoteCode;
}

// Function to replace emojis with Discord emotes in text
function replaceEmojis(text) {
    let result = text;
    
    // Replace each emoji with its emote code
    for (const [emoji, emoteCode] of Object.entries(EMOTE_MAP)) {
        if (emoteCode && emoteCode.includes(':>')) {
            // For display in web, convert to image
            const imageTag = emoteToImage(emoteCode);
            result = result.replace(new RegExp(emoji, 'g'), imageTag);
        }
    }
    
    return result;
}

// Function to get emote code (for Discord messages)
function getEmoteCode(emoji) {
    return EMOTE_MAP[emoji] || emoji;
}

// Function to update all emotes on page
function updatePageEmotes() {
    // Update widget icons
    document.querySelectorAll('.widget-icon').forEach(element => {
        const originalText = element.textContent;
        const emoteCode = getEmoteCode(originalText);
        if (emoteCode !== originalText && emoteCode.includes(':')) {
            element.innerHTML = emoteToImage(emoteCode);
        }
    });
    
    // Update any other emoji text on the page
    document.querySelectorAll('.action-btn, .task-item, .daily-tip').forEach(element => {
        if (element.innerHTML) {
            element.innerHTML = replaceEmojis(element.innerHTML);
        }
    });
}

// Add CSS for Discord emotes
const style = document.createElement('style');
style.textContent = `
    .discord-emote {
        width: 20px;
        height: 20px;
        vertical-align: middle;
        margin: 0 2px;
    }
    
    .widget-icon .discord-emote {
        width: 24px;
        height: 24px;
    }
    
    .action-btn .discord-emote {
        width: 18px;
        height: 18px;
    }
`;
document.head.appendChild(style);

// Auto-update emotes when page loads
document.addEventListener('DOMContentLoaded', updatePageEmotes);