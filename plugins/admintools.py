# Ultroid - UserBot
# Copyright (C) 2021-2025 TeamUltroid
# Rewritten for Pyroblack by Gemini

from . import get_help

__doc__ = get_help("help_admintools")

import asyncio
import time
from datetime import datetime, timedelta

from pyroblack import Client, enums, errors
from pyroblack.types import ChatPrivileges, ChatPermissions, Message

from pyUltroid.dB import DEVLIST
from pyUltroid.fns.admins import ban_time
from pyUltroid.fns.info import get_uinfo

from . import HNDLR, LOGS, eod, eor, get_string, inline_mention, ultroid_cmd

# Permissions Helpers
FULL_PROMOTE_POWERS = ChatPrivileges(
    can_change_info=True,
    can_invite_users=True,
    can_delete_messages=True,
    can_restrict_members=True,
    can_pin_messages=True,
    can_promote_members=True,
    can_manage_chat=True,
    can_manage_video_chats=True,
)

BASIC_PROMOTE_POWERS = ChatPrivileges(
    can_change_info=False,
    can_invite_users=True,
    can_delete_messages=True,
    can_restrict_members=True,
    can_pin_messages=True,
    can_promote_members=False,
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
async def prmte(ult: Message):
    xx = await eor(ult, get_string("com_1"))
    user, rank = await get_uinfo(ult)
    rank = rank or "Admin"
    
    privileges = BASIC_PROMOTE_POWERS
    if rank.split()[0] == "-f":
        try:
            rank = rank.split(maxsplit=1)[1]
        except IndexError:
            rank = "Admin"
        privileges = FULL_PROMOTE_POWERS

    if not user:
        return await xx.edit(get_string("pro_1"))

    try:
        # Promote
        await ult.chat.promote_member(
            user.id,
            privileges=privileges
        )
        # Set Title (Rank) - Pyroblack separate call
        try:
            await ult.chat.set_administrator_title(user.id, rank)
        except Exception:
            pass # Some chats don't support custom titles or bot lacks permission

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
async def dmote(ult: Message):
    xx = await eor(ult, get_string("com_1"))
    user, rank = await get_uinfo(ult)
    if not rank:
        rank = "Not Admin"
    if not user:
        return await xx.edit(get_string("de_1"))
    try:
        # Pass empty privileges to demote
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
                can_manage_video_chats=False
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
async def bban(ult: Message):
    something = await get_uinfo(ult)
    if not something:
        return
    user, reason = something
    if not user:
        return await eod(ult, get_string("ban_1"))
    if user.id in DEVLIST:
        return await eod(ult, get_string("ban_2"))
    try:
        # Ban user
        await ult.chat.ban_member(user.id)
    except errors.UserAdminInvalid:
        return await eod(ult, get_string("adm_1"))
    except errors.BadRequest:
        return await eod(ult, get_string("ban_3"))
        
    senderme = inline_mention(ult.from_user)
    userme = inline_mention(user)
    text = get_string("ban_4").format(userme, senderme, ult.chat.title)
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
async def uunban(ult: Message):
    xx = await eor(ult, get_string("com_1"))
    # Assuming text property exists or using ult.text if converted
    text_content = ult.text or ult.caption or ""
    
    if text_content[1:].startswith("unbanall"):
        return
        
    something = await get_uinfo(ult)
    if not something:
        return
    user, reason = something
    if not user:
        return await xx.edit(get_string("unban_1"))
    try:
        await ult.chat.unban_member(user.id)
    except errors.UserAdminInvalid:
        return await eod(ult, get_string("adm_1"))
    except errors.BadRequest:
        return await xx.edit(get_string("adm_2"))
        
    sender = inline_mention(ult.from_user)
    text = get_string("unban_3").format(inline_mention(user), sender, ult.chat.title)
    if reason:
        text += get_string("ban_5").format(reason)
    await xx.edit(text)


@ultroid_cmd(
    pattern="kick( (.*)|$)",
    manager=True,
    require="ban_users",
    fullsudo=True,
)
async def kck(ult: Message):
    if "kickme" in ult.text:
        return
    if ult.chat.type == enums.ChatType.PRIVATE:
        return await eor(ult, "`Use this in Group/Channel.`", time=5)
    
    xx = await eor(ult, get_string("com_1"))
    something = await get_uinfo(ult)
    if not something:
        return
    user, reason = something
    if not user:
        return await xx.edit(get_string("adm_1"))
    if user.id in DEVLIST:
        return await xx.edit(get_string("kick_2"))
    if user.is_self:
        return await xx.edit(get_string("kick_3"))
        
    try:
        # Kick in Pyrogram is usually Ban then Unban
        await ult.chat.ban_member(user.id)
        await asyncio.sleep(1)
        await ult.chat.unban_member(user.id)
    except errors.BadRequest as er:
        LOGS.info(er)
        return await xx.edit(get_string("kick_1"))
    except Exception as e:
        LOGS.exception(e)
        return
        
    text = get_string("kick_4").format(
        inline_mention(user), inline_mention(ult.from_user), ult.chat.title
    )
    if reason:
        text += get_string("ban_5").format(reason)
    await xx.edit(text)


@ultroid_cmd(
    pattern="tban( (.*)|$)",
    admins_only=True,
    manager=True,
    require="ban_users",
    fullsudo=True,
)
async def tkicki(e: Message):
    huh = e.text.split()
    inputt = None
    try:
        tme = huh[1]
    except IndexError:
        return await eor(e, get_string("adm_3"), time=15)
    try:
        inputt = huh[2]
    except IndexError:
        if e.reply_to_message:
            inputt = e.reply_to_message.from_user.id
            
    if not inputt:
        return await eor(e, get_string("tban_1"))
    
    try:
        # Assuming parse_id is available in client wrapper
        userid = await e._client.parse_id(inputt)
        user = await e._client.get_users(userid)
    except Exception as ex:
        return await eor(e, f"`{ex}`")
        
    try:
        bun = ban_time(tme) # returns datetime or timestamp
        # Pyrogram expects datetime for until_date
        await e.chat.ban_member(user.id, until_date=bun)
        
        await eod(
            e,
            get_string("tban_2").format(inline_mention(user), e.chat.title, tme),
            time=15,
        )
    except Exception as m:
        return await eor(e, str(m))


@ultroid_cmd(pattern="pin$", manager=True, require="pin_messages", fullsudo=True)
async def pin(msg: Message):
    if not msg.reply_to_message:
        return await eor(msg, get_string("pin_1"))
    
    me = msg.reply_to_message
    if me.chat.type == enums.ChatType.PRIVATE:
        text = "`Pinned.`"
    else:
        text = f"Pinned [This Message]({me.link}) !"
    try:
        # disable_notification=True -> notify=False
        await me.pin(disable_notification=True)
    except errors.BadRequest:
        return await eor(msg, get_string("adm_2"))
    except Exception as e:
        return await eor(msg, f"**ERROR:**`{e}`")
    await eor(msg, text)


@ultroid_cmd(
    pattern="unpin($| (.*))",
    manager=True,
    require="pin_messages",
    fullsudo=True,
)
async def unp(ult: Message):
    xx = await eor(ult, get_string("com_1"))
    # Argument handling needs to be adapted to how your decorators pass args
    # Fallback to basic text splitting
    args = ult.text.split(maxsplit=1)
    ch = args[1].strip() if len(args) > 1 else ""
    
    msg_id = None
    if ult.reply_to_message:
        msg_id = ult.reply_to_message.id
    elif ch != "all":
        return await xx.edit(get_string("unpin_1").format(HNDLR))
        
    try:
        if ch == "all":
            await ult.chat.unpin_all_messages()
        else:
            await ult.chat.unpin_message(msg_id)
    except errors.BadRequest:
        return await xx.edit(get_string("adm_2"))
    except Exception as e:
        return await xx.edit(f"**ERROR:**`{e}`")
    await xx.edit("`Unpinned!`")


@ultroid_cmd(
    pattern="tpin( (.*)|$)",
    admins_only=True,
    manager=True,
    require="pin_messages",
    fullsudo=True,
)
async def pin_message(ult: Message):
    args = ult.text.split(maxsplit=1)
    match = args[1].strip() if len(args) > 1 else ""
    
    if not ult.reply_to_message:
        return await eor(ult, "`Reply to message..`", time=6)
    if not match:
        return await eor(ult, "`Please provide time..`", time=8)
        
    msg = await eor(ult, get_string("com_1"))
    r_msg = ult.reply_to_message
    
    try:
        # ban_time usually returns datetime, convert to seconds for sleep
        # or calculate diff
        until_dt = ban_time(match)
        sleep_seconds = (until_dt - datetime.now()).total_seconds()
        
        await r_msg.pin(disable_notification=True)
        await msg.edit(f"`pinned for time` `{match}`")
    except Exception as er:
        return await msg.edit(str(er))
        
    await asyncio.sleep(sleep_seconds)
    try:
        await r_msg.unpin()
    except Exception as er:
        LOGS.exception(er)


@ultroid_cmd(pattern="purge( (.*)|$)", manager=True, require="delete_messages")
async def fastpurger(purg: Message):
    args = purg.text.split(maxsplit=1)
    match = args[1].strip() if len(args) > 1 else ""
    
    # Check flags like -m or -a (Assuming text[6] logic was for specific flags)
    # Pyrogram adaptation:
    
    reply_msg = purg.reply_to_message
    
    if not purg.from_user.is_self and (
        (match) or (reply_msg and purg.chat.type == enums.ChatType.PRIVATE)
    ):
        # Delete last N messages logic
        try:
            count = int(match)
            # Pyrogram doesn't have a simple "delete last N". 
            # We must fetch history IDs.
            msgs_to_delete = []
            async for m in purg.chat.get_history(limit=count):
                msgs_to_delete.append(m.id)
            
            # chunking 100 is handled by pyrogram usually
            await purg._client.delete_messages(purg.chat.id, msgs_to_delete)
            return await eor(purg, f"Purged {len(msgs_to_delete)} Messages! ", time=5)
        except ValueError:
            pass

    if not reply_msg:
        return await eor(purg, get_string("purge_1"), time=10)

    # Purge from Reply to Current
    try:
        message_ids = []
        # get_history is reverse chronological (newest first)
        # We need messages between reply_id and current_id
        # Pyrogram doesn't support 'min_id'/'max_id' in get_history effectively for range deletion
        # without iterating.
        
        # Iterating from reply_msg.id to purg.id
        # In Pyrogram, usually easier to iterate history with offset
        # But for 'purge', we usually want everything AFTER the reply.
        
        # Telethon: list(range(reply.id, current.id)) works because IDs are sequential-ish
        # Pyrogram can accept list of IDs.
        
        start_id = reply_msg.id
        end_id = purg.id
        
        # Ideally, we should fetch actual existing IDs to avoid errors, 
        # but delete_messages ignores non-existent IDs mostly.
        # Generating range is risky if IDs are huge gaps, but standard for Userbots.
        
        # Safety cap
        if end_id - start_id > 1000:
             # Logic to batch delete
             chunk = list(range(start_id, end_id + 1))
             # You might need to split this into chunks of 100 if Pyrogram doesn't auto-chunk
             for i in range(0, len(chunk), 100):
                 await purg._client.delete_messages(purg.chat.id, chunk[i:i+100])
        else:
             await purg._client.delete_messages(purg.chat.id, list(range(start_id, end_id + 1)))

    except Exception as er:
        LOGS.info(er)
        
    await eor(purg, "__Fast purge complete!__", time=5)


@ultroid_cmd(
    pattern="purgeme( (.*)|$)",
)
async def fastpurgerme(purg: Message):
    args = purg.text.split(maxsplit=1)
    num = args[1].strip() if len(args) > 1 else ""
    
    if num:
        try:
            nnt = int(num)
        except BaseException:
            await eor(purg, get_string("com_3"), time=5)
            return
        mp = 0
        msgs = []
        # get_history limit=nnt, then filter
        # Note: Pyrogram search_messages(from_user="me") is better
        async for mm in purg._client.search_messages(purg.chat.id, query="", from_user="me", limit=nnt):
            msgs.append(mm.id)
            mp += 1
        
        if msgs:
            await purg._client.delete_messages(purg.chat.id, msgs)
        await eor(purg, f"Purged {mp} Messages!", time=5)
        return
        
    elif not purg.reply_to_message:
        return await eod(
            purg,
            "`Reply to a message to purge from or use it like ``purgeme <num>`",
            time=10,
        )
        
    msgs = []
    # Search messages from me starting from the reply
    # Note: Complex to do range search with search_messages. 
    # Fallback to history iteration
    async for msg in purg.chat.get_history():
        if msg.id < purg.reply_to_message.id:
            break
        if msg.from_user and msg.from_user.is_self:
            msgs.append(msg.id)
            
    if msgs:
        await purg._client.delete_messages(purg.chat.id, msgs)
        
    await eor(purg,
        "__Fast purge complete!__\n**Purged** `" + str(len(msgs)) + "` **messages.**",
        time=5,
    )


@ultroid_cmd(
    pattern="purgeall$",
)
async def _(e: Message):
    if not e.reply_to_message:
        return await eod(e, get_string("purgeall_1"))

    msg = e.reply_to_message
    user_id = msg.from_user.id
    name = msg.from_user.first_name
    
    try:
        # delete_user_history is available for supergroups
        await e.chat.delete_user_history(user_id)
        await eor(e, get_string("purgeall_2").format(name), time=5)
    except Exception as er:
        return await eor(e, str(er), time=5)

@ultroid_cmd(pattern="pinned", manager=True, groups_only=True)
async def djshsh(event: Message):
    # Pyrogram stores pinned_message in Chat object
    chat = await event.chat.get() # Refresh chat info
    if not chat.pinned_message:
        return await eor(event, get_string("pinned_1"))
        
    await eor(event, get_string("pinned_2").format(chat.pinned_message.link))


@ultroid_cmd(
    pattern="listpinned$",
)
async def get_all_pinned(event: Message):
    x = await eor(event, get_string("com_1"))
    chat_name = event.chat.title
    a = ""
    c = 1
    
    # search_messages filter=PINNED
    async for i in event._client.search_messages(event.chat.id, filter=enums.MessagesFilter.PINNED):
        if i.text or i.caption:
            # First 4 words
            text_content = i.text or i.caption
            t = " ".join(text_content.split()[:4])
            txt = f"{t}...."
        else:
            txt = "Go to message."
            
        a += f"{c}. <a href={i.link}>{txt}</a>\n"
        c += 1

    if c == 1:
        m = f"<b>The pinned message in {chat_name}:</b>\n\n"
    else:
        m = f"<b>List of pinned message(s) in {chat_name}:</b>\n\n"

    if not a:
        return await eor(x, get_string("listpin_1"), time=5)

    await x.edit(m + a, parse_mode=enums.ParseMode.HTML)


@ultroid_cmd(
    pattern="autodelete( (.*)|$)",
    admins_only=True,
)
async def autodelte(ult: Message):
    args = ult.text.split(maxsplit=1)
    match = args[1].strip() if len(args) > 1 else ""
    
    if not match or match not in ["24h", "7d", "1m", "off"]:
        return await eor(ult, "`Please Use in Proper Format..`", time=5)
        
    # Pyrogram set_chat_ttl takes seconds
    if match == "24h":
        tt = 3600 * 24
    elif match == "7d":
        tt = 3600 * 24 * 7
    elif match == "1m":
        tt = 3600 * 24 * 31
    else:
        tt = 0
        
    try:
        await ult.chat.set_ttl(tt)
    except Exception as e:
        # ChatNotModified not strictly in Pyro exceptions similarly, catch generic
        return await eor(ult, f"Error: {e}", time=5)
        
    await eor(ult, f"Auto Delete Status Changed to `{match}` !")
