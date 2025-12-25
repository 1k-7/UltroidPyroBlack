# Ultroid - UserBot
# Copyright (C) 2021-2025 TeamUltroid
# Rewritten for Pyroblack by Gemini

from . import get_help

__doc__ = get_help("help_afk")

import asyncio
from pyroblack import filters
from pyroblack.handlers import MessageHandler
from pyroblack.types import Message

from pyUltroid.dB.afk_db import add_afk, del_afk, is_afk
from pyUltroid.dB.base import KeyManager

from . import (
    LOG_CHANNEL,
    NOSPAM_CHAT,
    asst,
    get_string,
    mediainfo,
    udB,
    ultroid_bot,
    ultroid_cmd,
    upload_file # Wrapper assumed available
)

old_afk_msg = []
is_approved = KeyManager("PMPERMIT", cast=list).contains

@ultroid_cmd(pattern="afk( (.*)|$)", owner_only=True)
async def set_afk(event: Message):
    if event._client.me.is_bot or is_afk():
        return
        
    text, media, media_type = None, None, None
    
    match = event.matches[0].group(1).strip() if event.matches else None
    if match:
        text = match
        
    reply = event.reply_to_message
    if reply:
        if reply.text and not text:
            text = reply.text
        if reply.media:
            media_type = mediainfo(reply) # Adapted mediainfo
            if media_type.startswith(("pic", "gif")):
                # Download and upload to get file_id/url if needed or just cache
                file = await reply.download()
                media = file # Simplified, usually we store file_id
            else:
                # Store file_id
                media = reply.document.file_id if reply.document else None # Logic simplified
                
    await event.eor("`Done`", time=2)
    
    add_afk(text, media_type, media)
    
    # Add Handlers dynamically
    ultroid_bot.add_handler(MessageHandler(remove_afk, filters.outgoing))
    ultroid_bot.add_handler(
        MessageHandler(
            on_afk,
            filters.incoming & (filters.mentioned | filters.private)
        )
    )
    
    msg1, msg2 = None, None
    
    # Send confirmation logic
    if text and media:
        # Assuming media is a file path or ID
        if media and os.path.exists(media):
             msg1 = await ultroid_bot.send_document(event.chat.id, document=media)
        msg2 = await ultroid_bot.send_message(
            event.chat_id, get_string("afk_5").format(text)
        )
    elif text:
        msg1 = await event.reply(get_string("afk_5").format(text))
    else:
        msg1 = await event.reply(get_string("afk_6"))
        
    old_afk_msg.append(msg1)
    if msg2:
        old_afk_msg.append(msg2)
        await asst.send_message(LOG_CHANNEL, msg2.text)
    else:
        await asst.send_message(LOG_CHANNEL, msg1.text)


async def remove_afk(client, event: Message):
    if event.chat.type == enums.ChatType.PRIVATE and udB.get_key("PMSETTING") and not is_approved(event.chat.id):
        return
    elif event.text and "afk" in event.text.lower():
        return
    elif event.chat.id in NOSPAM_CHAT:
        return
        
    if is_afk():
        _, _, _, afk_time = is_afk()
        del_afk()
        
        # Remove Handlers (Pyrogram remove_handler is tricky if you don't have the group/instance, 
        # usually we just keep them and check is_afk() which returns False now)
        # But to be clean:
        # ultroid_bot.remove_handler(...) - Skipping for stability, boolean check is enough
        
        off = await event.reply(get_string("afk_1").format(afk_time))
        await asst.send_message(LOG_CHANNEL, get_string("afk_2").format(afk_time))
        
        for x in old_afk_msg:
            try:
                await x.delete()
            except:
                pass
        await asyncio.sleep(10)
        await off.delete()


async def on_afk(client, event: Message):
    if event.chat.type == enums.ChatType.PRIVATE and udB.get_key("PMSETTING") and not is_approved(event.chat.id):
        return
    elif event.text and "afk" in event.text.lower():
        return
    elif not is_afk():
        return
    if event.chat.id in NOSPAM_CHAT:
        return
        
    sender = event.from_user
    if sender.is_bot or sender.is_verified:
        return
        
    text, media_type, media, afk_time = is_afk()
    msg1, msg2 = None, None
    
    response_text = get_string("afk_3").format(afk_time, text) if text else get_string("afk_4").format(afk_time)
    
    if media and os.path.exists(media):
        msg1 = await event.reply_document(media, caption=response_text)
    else:
        msg1 = await event.reply(response_text)
        
    for x in old_afk_msg:
        try:
            await x.delete()
        except:
            pass
            
    old_afk_msg.append(msg1)

# On Startup Load
if udB.get_key("AFK_DB"):
    ultroid_bot.add_handler(MessageHandler(remove_afk, filters.outgoing))
    ultroid_bot.add_handler(
        MessageHandler(
            on_afk,
            filters.incoming & (filters.mentioned | filters.private)
        )
    )
