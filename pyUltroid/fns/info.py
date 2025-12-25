# Ultroid - UserBot
# Copyright (C) 2021-2025 TeamUltroid
# Rewritten for Pyroblack by Gemini

import math
from pyroblack import enums, types
from .. import LOGS

async def get_uinfo(e):
    """
    Get (User, Data) from a message (Reply or Args).
    """
    user, data = None, None
    
    # Check Reply
    if e.reply_to_message:
        user = e.reply_to_message.from_user
        # Pattern match group 1 equivalent in Pyrogram (regex match)
        if e.matches:
             try:
                 data = e.matches[0].group(1)
             except:
                 pass
    else:
        # Check arguments from command
        # e.command is available if filters.command used, but we use regex mostly in Ultroid
        # So we split e.text
        text = e.text or e.caption or ""
        args = text.split(maxsplit=1)
        if len(args) > 1:
            input_str = args[1]
            parts = input_str.split(maxsplit=1)
            user_str = parts[0]
            data = parts[1] if len(parts) > 1 else None
            
            try:
                # Try getting user
                user = await e._client.get_users(user_str)
            except Exception as er:
                await e.eor(f"User not found: {er}")
                return None, None
                
    return user, data


async def get_chat_info(chat, event):
    try:
        full_chat = await event._client.get_chat(chat.id)
    except Exception as er:
        return None, f"Error: {er}"

    chat_type = full_chat.type
    chat_title = full_chat.title
    
    members = full_chat.members_count
    
    # Data gathering
    dc_id = full_chat.photo.dc_id if full_chat.photo else "Null"
    
    # Description
    description = full_chat.description or ""
    
    caption = "ℹ️ <b>[<u>CHAT INFO</u>]</b>\n"
    caption += f"🆔 <b>ID:</b> <code>{full_chat.id}</code>\n"
    caption += f"📛 <b>Name:</b> <code>{chat_title}</code>\n"
    
    if full_chat.username:
        caption += f"🔗 <b>Link:</b> @{full_chat.username}\n"
    
    if full_chat.type == enums.ChatType.PRIVATE:
        caption += f"🗳 <b>Type:</b> Private\n"
    else:
        caption += f"🗳 <b>Type:</b> {full_chat.type.name}\n"

    if full_chat.type != enums.ChatType.PRIVATE:
        if members:
            caption += f"👥 <b>Members:</b> <code>{members}</code>\n"
        
        # Only available in full chat object sometimes
        if full_chat.is_verified:
            caption += f"✅ <b>Verified:</b> <code>Yes</code>\n"
        if full_chat.is_scam:
             caption += "⚠ <b>Scam:</b> <b>Yes</b>\n"
             
    if description:
        caption += f"🗒 <b>Description:</b> \n<code>{description}</code>\n"
        
    return full_chat.photo, caption
