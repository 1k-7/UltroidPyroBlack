# Ultroid - UserBot
# Copyright (C) 2021-2025 TeamUltroid
# Rewritten for Pyroblack by Gemini

from pyroblack.types import Message
from pyUltroid.fns.admins import lock_unlock
from . import ultroid_cmd

@ultroid_cmd(
    pattern="(un|)lock( (.*)|$)", admins_only=True, manager=True, require="change_info"
)
async def un_lock(e: Message):
    # Matches: Group 1 is "un" or "", Group 2 is " type" or "", Group 3 is type
    # Regex pattern "(un|)lock( (.*)|$)"
    # Pyrogram regex groups in matches
    
    # match object structure depends on regex engine, but typically:
    # matches[0] is full match? No, filters.regex returns match object list
    
    prefix = e.matches[0].group(1) # "un" or ""
    mat = e.matches[0].group(3).strip() # "msgs", "media" etc
    
    if not mat:
        return await e.eor("`Give some Proper Input..`", time=5)
        
    is_lock = (prefix == "")
    
    permissions = lock_unlock(mat, is_lock)
    
    if not permissions:
        return await e.eor("`Incorrect Input`", time=5)
        
    msg = "Locked" if is_lock else "Unlocked"
    
    try:
        # Pyrogram set_chat_permissions
        await e.chat.set_permissions(permissions)
    except Exception as er:
        return await e.eor(f"Error: {str(er)}")
        
    await e.eor(f"**{msg}** - `{mat}` ! ")
