# Ultroid - UserBot
# Copyright (C) 2021-2025 TeamUltroid
# Rewritten for Pyroblack by Gemini

from . import get_help

__doc__ = get_help("help_search")

import os
from pyUltroid.fns.misc import google_search
from pyUltroid.fns.tools import get_google_images
from . import LOGS, ultroid_cmd

# Pyrogram
from pyroblack import enums
from pyroblack.types import InputMediaPhoto

@ultroid_cmd(pattern="google( (.*)|$)")
async def _(event):
    match = event.matches[0].group(1).strip() if event.matches else None
    if not match:
        return await event.eor("`Give me a query to search!`")
        
    msg = await event.eor("`Searching...`")
    
    try:
        results = await google_search(match)
    except Exception as e:
        return await msg.edit(f"Error: {e}")
        
    if not results:
        return await msg.edit("`No results found.`")
        
    output = f"**Google Search:** `{match}`\n\n"
    for i in results[:5]: # Top 5
        output += f"• [{i['title']}]({i['link']})\n`{i['description']}`\n\n"
        
    await msg.edit(output, disable_web_page_preview=True)


@ultroid_cmd(pattern="img( (.*)|$)")
async def _(event):
    match = event.matches[0].group(1).strip() if event.matches else None
    if not match:
        return await event.eor("`Give me a query to search images!`")
        
    msg = await event.eor("`Searching Images...`")
    
    try:
        results = await get_google_images(match)
    except Exception as e:
        return await msg.edit(f"Error: {e}")
        
    if not results:
        return await msg.edit("`No images found.`")
        
    # Send as album if possible (Pyrogram send_media_group)
    # results is list of dicts with 'link'
    
    media_group = []
    count = 0
    for res in results:
        if count >= 5: break
        if res.get("link"):
            # Pyrogram 2.x InputMediaPhoto
            media_group.append(InputMediaPhoto(res["link"], caption=res.get("title", "")))
            count += 1
            
    if media_group:
        await msg.delete()
        try:
            await event._client.send_media_group(
                event.chat.id,
                media=media_group,
                reply_to_message_id=event.reply_to_message_id
            )
        except Exception as e:
            # Fallback single
            await event.reply_photo(results[0]["link"], caption=results[0]["title"])
    else:
        await msg.edit("`Could not process images.`")
