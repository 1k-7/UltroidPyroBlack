# Ultroid - UserBot
# Copyright (C) 2021-2025 TeamUltroid
# Rewritten for Pyroblack by Gemini

from . import get_help

__doc__ = get_help("help_admintools")

import asyncio
from pyroblack import enums, errors
from pyroblack.types import ChatPrivileges

from pyUltroid.dB import DEVLIST
from pyUltroid.fns.admins import ban_time
from pyUltroid.fns.info import get_uinfo

from . import HNDLR, LOGS, eod, eor, get_string, inline_mention, ultroid_cmd

FULL_RIGHTS = ChatPrivileges(
    can_change_info=True,
    can_invite_users=True,
    can_delete_messages=True,
    can_restrict_members=True,
    can_pin_messages=True,
    can_promote_members=True,
    can_manage_chat=True,
    can_manage_video_chats=True,
)

@ultroid_cmd(
    pattern="promote( (.*)|$)",
    admins_only=True,
    manager=True,
    require="add_admins",
    fullsudo=True,
)
async def prmte(ult):
    xx = await eor(ult, get_string("com_1"))
    user, rank = await get_uinfo(ult)
    rank = rank or "Admin"
    
    rights = ChatPrivileges(
        can_change_info=False,
        can_invite_users=True,
        can_delete_messages=True,
        can_restrict_members=True,
        can_pin_messages=True,
        can_promote_members=False,
        can_manage_chat=True,
        can_manage_video_chats=True,
    )
    
    if rank.startswith("-f"):
        rights = FULL_RIGHTS
        rank = rank.replace("-f", "").strip() or "Admin"

    if not user:
        return await xx.edit(get_string("pro_1"))

    try:
        await ult.chat.promote_member(user.id, privileges=rights)
        try:
            await ult.chat.set_administrator_title(user.id, rank)
        except: pass
        
        await eod(
            xx, get_string("pro_2").format(inline_mention(user), ult.chat.title, rank)
        )
    except Exception as ex:
        return await xx.edit(f"`{ex}`")


@ultroid_cmd(
    pattern="demote( (.*)|$)",
    admins_only=True,
    manager=True,
    require="add_admins",
    fullsudo=True,
)
async def dmote(ult):
    xx = await eor(ult, get_string("com_1"))
    user, _ = await get_uinfo(ult)
    
    if not user:
        return await xx.edit(get_string("de_1"))
        
    try:
        # Demote by promoting with all False
        await ult.chat.promote_member(
            user.id,
            privileges=ChatPrivileges(
                can_manage_chat=False,
                can_change_info=False,
                can_post_messages=False,
                can_edit_messages=False,
                can_delete_messages=False,
                can_invite_users=False,
                can_restrict_members=False,
                can_pin_messages=False,
                can_promote_members=False,
                can_manage_video_chats=False,
                is_anonymous=False
            )
        )
        await eod(xx, get_string("de_2").format(inline_mention(user), ult.chat.title))
    except Exception as ex:
        return await xx.edit(f"`{ex}`")


@ultroid_cmd(
    pattern="ban( (.*)|$)",
    admins_only=True,
    manager=True,
    require="ban_users",
    fullsudo=True,
)
async def bban(ult):
    user, reason = await get_uinfo(ult)
    if not user:
        return await eod(ult, get_string("ban_1"))
    if user.id in DEVLIST:
        return await eod(ult, get_string("ban_2"))
        
    try:
        await ult.chat.ban_member(user.id)
    except Exception as e:
        return await eod(ult, f"Error: {e}")
        
    text = get_string("ban_4").format(inline_mention(user), inline_mention(ult.from_user), ult.chat.title)
    if reason:
        text += get_string("ban_5").format(reason)
    await eod(ult, text)


@ultroid_cmd(
    pattern="unban( (.*)|$)",
    admins_only=True,
    manager=True,
    require="ban_users",
    fullsudo=True,
)
async def uunban(ult):
    user, reason = await get_uinfo(ult)
    if not user:
        return await eor(ult, get_string("unban_1"))
        
    try:
        await ult.chat.unban_member(user.id)
    except Exception as e:
        return await eor(ult, f"Error: {e}")
        
    text = get_string("unban_3").format(inline_mention(user), inline_mention(ult.from_user), ult.chat.title)
    if reason:
        text += get_string("ban_5").format(reason)
    await eor(ult, text)


@ultroid_cmd(pattern="purge( (.*)|$)", manager=True, require="delete_messages")
async def fastpurger(purg):
    match = purg.matches[0].group(1).strip() if purg.matches else None
    reply = purg.reply_to_message
    
    if not reply:
        return await eor(purg, get_string("purge_1"), time=10)
        
    # Purge from Reply to Current
    try:
        message_ids = []
        # In Pyrogram, get_history is reverse (newest first).
        # We want everything from 'reply' to 'purg'
        
        # Simple ID range generation (works for basic groups/supergroups usually)
        start = reply.id
        end = purg.id
        
        message_ids = list(range(start, end + 1))
        
        # Batch delete (Pyrogram handles chunking 100 internally mostly, but safe to chunk)
        chunk_size = 100
        for i in range(0, len(message_ids), chunk_size):
            chunk = message_ids[i:i + chunk_size]
            await purg.chat.delete_messages(chunk)
            
    except Exception as er:
        LOGS.error(er)
        return await eor(purg, f"Error: {er}")
        
    await eor(purg, "__Fast purge complete!__", time=5)


@ultroid_cmd(pattern="pin$", manager=True, require="pin_messages", fullsudo=True)
async def pin(msg):
    if not msg.reply_to_message:
        return await eor(msg, get_string("pin_1"))
    
    try:
        await msg.reply_to_message.pin(disable_notification=True)
        await eor(msg, "Pinned.", time=5)
    except Exception as e:
        await eor(msg, f"Error: {e}")


@ultroid_cmd(pattern="unpin($| (.*))", manager=True, require="pin_messages", fullsudo=True)
async def unp(ult):
    match = ult.matches[0].group(1).strip() if ult.matches else None
    
    try:
        if match == "all":
            await ult.chat.unpin_all_messages()
            await eor(ult, "Unpinned all messages.")
        else:
            # Unpin reply or last pinned? Pyrogram unpin_message unpins specific
            if ult.reply_to_message:
                await ult.reply_to_message.unpin()
                await eor(ult, "Unpinned.")
            elif ult.chat.pinned_message:
                await ult.chat.pinned_message.unpin() # might need fetching chat first
                await eor(ult, "Unpinned latest.")
            else:
                await eor(ult, "Reply to a message or use `unpin all`.")
    except Exception as e:
        await eor(ult, f"Error: {e}")
