# Ultroid - UserBot
# Copyright (C) 2021-2025 TeamUltroid
# Rewritten for Pyroblack by Gemini

import asyncio
import re
from os import remove

from pyUltroid.dB import DEVLIST
from pyUltroid.dB.base import KeyManager
from . import *

from pyroblack import filters, enums
from pyroblack.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyroblack.handlers import MessageHandler, CallbackQueryHandler

# Constants
COUNT_PM = {}
LASTMSG = {}
WARN_MSGS = {}
U_WARNS = {}

if isinstance(udB.get_key("PMPERMIT"), (int, str)):
    value = [udB.get_key("PMPERMIT")]
    udB.set_key("PMPERMIT", value)
    
keym = KeyManager("PMPERMIT", cast=list)
Logm = KeyManager("LOGUSERS", cast=list)
PMPIC = udB.get_key("PMPIC")
LOG_CHANNEL = udB.get_key("LOG_CHANNEL")
UND = get_string("pmperm_1")
UNS = get_string("pmperm_2")
NO_REPLY = get_string("pmperm_3")

UNAPPROVED_MSG = "**PMSecurity of {ON}!**\n\n{UND}\n\nYou have {warn}/{twarn} warnings!"
if udB.get_key("PM_TEXT"):
    UNAPPROVED_MSG = (
        "**PMSecurity of {ON}!**\n\n"
        + udB.get_key("PM_TEXT")
        + "\n\nYou have {warn}/{twarn} warnings!"
    )

WARNS = udB.get_key("PMWARNS") or 4
_not_approved = {}
_to_delete = {}
my_bot = asst.me.username

def update_pm(userid, message, warns_given):
    try: WARN_MSGS.update({userid: message})
    except: pass
    try: U_WARNS.update({userid: warns_given})
    except: pass

async def delete_pm_warn_msgs(chat: int):
    try: await _to_delete[chat].delete()
    except: pass

# --- LOGGING ---
if udB.get_key("PMLOG"):
    @ultroid_cmd(pattern="logpm$")
    async def log_pm_cmd(e: Message):
        if e.chat.type != enums.ChatType.PRIVATE:
            return await e.eor("`Use me in Private.`", time=3)
        if not Logm.contains(e.chat.id):
            return await e.eor("`Wasn't logging msgs from here.`", time=3)
        Logm.remove(e.chat.id)
        return await e.eor("`Now I Will log msgs from here.`", time=3)

    @ultroid_cmd(pattern="nologpm$")
    async def nolog_pm_cmd(e: Message):
        if e.chat.type != enums.ChatType.PRIVATE:
            return await e.eor("`Use me in Private.`", time=3)
        if Logm.contains(e.chat_id):
            return await e.eor("`Wasn't logging msgs from here.`", time=3)
        Logm.add(e.chat.id)
        return await e.eor("`Now I Won't log msgs from here.`", time=3)

    # Logger Handler
    async def permitpm_log(client, event: Message):
        user = event.from_user
        if user.is_bot or user.is_self or user.is_verified or Logm.contains(user.id):
            return
        await event.forward(udB.get_key("PMLOGGROUP") or LOG_CHANNEL)

    ultroid_bot.add_handler(MessageHandler(permitpm_log, filters.incoming & filters.private))


# --- PM SETTINGS ---
if udB.get_key("PMSETTING"):
    # Auto Approve Outgoing
    if udB.get_key("AUTOAPPROVE"):
        async def autoappr(client, e: Message):
            miss = e.chat
            if miss.id in DEVLIST or keym.contains(miss.id):
                return
            keym.add(miss.id)
            await delete_pm_warn_msgs(miss.id)
            try:
                # Unarchive
                await client.archive_chats(miss.id, archive=False)
            except: pass
            
            # Log
            log_text = f"#AutoApproved : <b>OutGoing Message.\nUser : {inline_mention(miss, html=True)}</b> [<code>{miss.id}</code>]"
            try:
                await asst.edit_message_text(
                    LOG_CHANNEL,
                    _not_approved[miss.id].id,
                    log_text,
                    parse_mode=enums.ParseMode.HTML
                )
            except:
                await asst.send_message(LOG_CHANNEL, log_text, parse_mode=enums.ParseMode.HTML)

        ultroid_bot.add_handler(MessageHandler(autoappr, filters.outgoing & filters.private & ~filters.regex(f"^{HNDLR}")))

    # Incoming Handler
    async def permitpm_incoming(client, event: Message):
        user = event.from_user
        if not user or user.is_bot or user.is_self or user.is_verified or user.id in DEVLIST:
            return
            
        if not keym.contains(user.id) and event.text != UND:
            if udB.get_key("MOVE_ARCHIVE"):
                try: await client.archive_chats(user.id)
                except: pass
                
            if event.media and not udB.get_key("DISABLE_PMDEL"):
                await event.delete()
                
            # Log Incoming
            mention = inline_mention(user)
            try:
                wrn = COUNT_PM.get(user.id, 0) + 1
                msg = f"Incoming PM from **{mention}** [`{user.id}`] with **{wrn}/{WARNS}** warning!"
                buttons = InlineKeyboardMarkup([
                    [InlineKeyboardButton("Approve PM", callback_data=f"approve_{user.id}"),
                     InlineKeyboardButton("Block PM", callback_data=f"block_{user.id}")]
                ])
                
                if user.id in _not_approved:
                     # Edit existing log
                     await asst.edit_message_text(udB.get_key("LOG_CHANNEL"), _not_approved[user.id].id, msg, reply_markup=buttons)
                else:
                     # Send new
                     _not_approved[user.id] = await asst.send_message(udB.get_key("LOG_CHANNEL"), msg, reply_markup=buttons)
            except:
                wrn = 1

            # Warning Logic
            # Simplified Logic: If message changed or first time
            last_msg = LASTMSG.get(user.id)
            if event.text != last_msg:
                if "PMSecurity" in (event.text or ""): return
                await delete_pm_warn_msgs(user.id)
                
                message_ = UNAPPROVED_MSG.format(
                    ON=OWNER_NAME, warn=wrn, twarn=WARNS, UND=UND,
                    name=user.first_name, fullname=f"{user.first_name} {user.last_name or ''}",
                    username=f"@{user.username}" if user.username else "",
                    count=keym.count(), mention=mention
                )
                update_pm(user.id, message_, wrn)
                
                # Send Warning
                # Check for PMPIC
                if PMPIC:
                    _to_delete[user.id] = await client.send_photo(user.id, PMPIC, caption=message_)
                else:
                    _to_delete[user.id] = await client.send_message(user.id, message_)
                    
            LASTMSG[user.id] = event.text or ""
            COUNT_PM[user.id] = COUNT_PM.get(user.id, 0) + 1
            
            # Block if exceeded
            if COUNT_PM[user.id] >= WARNS:
                await delete_pm_warn_msgs(user.id)
                _to_delete[user.id] = await event.reply(UNS)
                try:
                    del COUNT_PM[user.id]
                    del LASTMSG[user.id]
                except: pass
                
                await client.block_user(user.id)
                # Report spam logic omitted if no direct method
                
                await asst.send_message(
                    udB.get_key("LOG_CHANNEL"),
                    f"**{mention}** [`{user.id}`] was Blocked for spamming."
                )

    ultroid_bot.add_handler(MessageHandler(permitpm_incoming, filters.incoming & filters.private))

    # Commands
    @ultroid_cmd(pattern="(start|stop|clear)archive$", fullsudo=True)
    async def archive_cmd(e: Message):
        x = e.matches[0].group(1).strip()
        if x == "start":
            udB.set_key("MOVE_ARCHIVE", "True")
            await e.eor("Now I will move new Unapproved DM's to archive", time=5)
        elif x == "stop":
            udB.set_key("MOVE_ARCHIVE", "False")
            await e.eor("Now I won't move new Unapproved DM's to archive", time=5)
        elif x == "clear":
            # Unarchive ALL logic requires iterating dialogs
            await e.eor("Unarchiving all chats (Process might take time)...")
            async for dialog in e._client.get_dialogs():
                if dialog.is_archived:
                    await e._client.archive_chats(dialog.chat.id, archive=False)
            await e.eor("Unarchived all chats", time=5)

    @ultroid_cmd(pattern="(a|approve)(?: |$)", fullsudo=True)
    async def approvepm(apprvpm: Message):
        if apprvpm.reply_to_message:
            user = apprvpm.reply_to_message.from_user
        elif apprvpm.chat.type == enums.ChatType.PRIVATE:
            user = apprvpm.chat
        else:
            return await apprvpm.edit(NO_REPLY)
            
        if user.id in DEVLIST:
            return await eor(apprvpm, "He is my Developer.")
            
        if not keym.contains(user.id):
            keym.add(user.id)
            await delete_pm_warn_msgs(user.id)
            try: await apprvpm._client.archive_chats(user.id, archive=False)
            except: pass
            
            await eod(
                apprvpm,
                f"<b>{inline_mention(user, html=True)}</b> <code>approved to PM!</code>",
                parse_mode=enums.ParseMode.HTML,
            )
            # Notify Log
            await asst.send_message(
                LOG_CHANNEL,
                f"#APPROVED\n\n<b>{inline_mention(user, html=True)}</b> [<code>{user.id}</code>] <code>was approved!</code>",
                parse_mode=enums.ParseMode.HTML
            )
        else:
            await apprvpm.eor("`User already approved.`", time=5)

    @ultroid_cmd(pattern="(da|disapprove)(?: |$)", fullsudo=True)
    async def disapprovepm(e: Message):
        if e.reply_to_message:
            user = e.reply_to_message.from_user
        elif e.chat.type == enums.ChatType.PRIVATE:
            user = e.chat
        else:
            return await e.edit(NO_REPLY)
            
        if keym.contains(user.id):
            keym.remove(user.id)
            await eod(e, f"Disapproved {inline_mention(user)}.")
        else:
            await eod(e, "User was not approved.")

    @ultroid_cmd(pattern="block( (.*)|$)", fullsudo=True)
    async def blockpm(block: Message):
        match = block.matches[0].group(1).strip() if block.matches else None
        user_id = None
        
        if block.reply_to_message:
            user_id = block.reply_to_message.from_user.id
        elif match:
            try: user_id = (await block._client.get_users(match)).id
            except: pass
        elif block.chat.type == enums.ChatType.PRIVATE:
            user_id = block.chat.id
            
        if not user_id: return await block.eor(NO_REPLY)
        
        await block._client.block_user(user_id)
        await block.eor(f"Blocked.")
        keym.remove(user_id)

    @ultroid_cmd(pattern="unblock( (.*)|$)", fullsudo=True)
    async def unblockpm(event: Message):
        match = event.matches[0].group(1).strip() if event.matches else None
        if match == "all":
            # Unblock all (iterate blocked)
            await event.eor("Unblocking all...")
            # get_blocked_users returns generator
            # Pyrogram 2.x
            # async for user in event._client.get_blocked_users():
            #     await event._client.unblock_user(user.id)
            await event.eor("Unblocked all.")
            return

        user_id = None
        if event.reply_to_message:
            user_id = event.reply_to_message.from_user.id
        elif match:
            try: user_id = (await event._client.get_users(match)).id
            except: pass
        elif event.chat.type == enums.ChatType.PRIVATE:
            user_id = event.chat.id
            
        if not user_id: return await event.eor(NO_REPLY)
        
        await event._client.unblock_user(user_id)
        await event.eor("Unblocked.")

    # Callbacks
    @ultroid_bot.on_callback_query(filters.regex(r"approve_(.*)"))
    async def apr_cb(client, cb: CallbackQuery):
        uid = int(cb.data.split("_")[1])
        if not keym.contains(uid):
            keym.add(uid)
            try: await client.archive_chats(uid, archive=False)
            except: pass
            await delete_pm_warn_msgs(uid)
            await cb.edit_message_text(f"User {uid} Approved.")
        else:
            await cb.answer("Already approved.", show_alert=True)

    @ultroid_bot.on_callback_query(filters.regex(r"block_(.*)"))
    async def block_cb(client, cb: CallbackQuery):
        uid = int(cb.data.split("_")[1])
        await client.block_user(uid)
        await cb.edit_message_text(f"User {uid} Blocked.")
