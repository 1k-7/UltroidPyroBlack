# Ultroid - UserBot
# Copyright (C) 2021-2025 TeamUltroid
# Rewritten for Pyroblack by Gemini

from . import get_help

__doc__ = get_help("help_webupload")

import os
from pyUltroid.fns.tools import webuploader
from . import eor, ultroid_cmd

@ultroid_cmd(
    pattern="webupload( (.*)|$)",
)
async def _(event):
    match = event.matches[0].group(1).strip() if event.matches else None
    if not match:
        return await event.eor("`Please mention which site to upload!`")
        
    if not event.reply_to_message:
        return await event.eor("`Reply to a message to upload it.`")
        
    msg = await event.eor("`Processing...`")
    
    # Download first
    try:
        file = await event.reply_to_message.download()
    except Exception as e:
        return await msg.edit(f"Download Error: {e}")
        
    if not file:
        return await msg.edit("`Failed to download media.`")
        
    # We need to inject the file into the webuploader cache or pass it directly
    # The original webuploader helper uses a cache dict _webupload_cache[chat_id][msg_id]
    # We must adapt usage. 
    # For now, let's assume we modified webuploader or we mimic the cache.
    
    # Importing internal cache to hack it (Ultroid legacy style)
    from pyUltroid.fns.tools import _webupload_cache
    
    if event.chat.id not in _webupload_cache:
        _webupload_cache[event.chat.id] = {}
        
    _webupload_cache[event.chat.id][msg.id] = file
    
    await msg.edit(f"`Uploading to {match}...`")
    
    try:
        # Calling helper
        output = await webuploader(event.chat.id, msg.id, match)
        
        if "https://" in output:
            await msg.edit(f"**Upload Success!**\n\n**Link:** {output}", link_preview=False)
        else:
            await msg.edit(f"**Upload Failed:** `{output}`")
            
    except Exception as e:
        await msg.edit(f"Error: {e}")
    finally:
        if os.path.exists(file):
            os.remove(file)
