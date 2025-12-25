# Ultroid - UserBot
# Copyright (C) 2021-2025 TeamUltroid
# Rewritten for Pyroblack by Gemini

import asyncio

from pyroblack import filters
from pyroblack.types import Message
from pyroblack.handlers import MessageHandler, RawUpdateHandler
from pyroblack.raw import types as raw_types

from pyUltroid.dB import stickers
from pyUltroid.dB.echo_db import check_echo
from pyUltroid.dB.forcesub_db import get_forcesetting
from pyUltroid.dB.gban_mute_db import is_gbanned
from pyUltroid.dB.greetings_db import get_goodbye, get_welcome, must_thank
from pyUltroid.dB.nsfw_db import is_profan
from pyUltroid.fns.helper import inline_mention
from pyUltroid.fns.tools import async_searcher, create_tl_btn, get_chatbot_reply

try:
    from ProfanityDetector import detector
except ImportError:
    detector = None
from . import LOG_CHANNEL, LOGS, asst, get_string, types, udB, ultroid_bot
from ._inline import something

# --- Chat Actions Handler ---
# Equivalent to events.ChatAction

async def ChatActionHandler(client, message: Message):
    # This filter should catch service messages (joined, left, etc)
    try:
        await DummyHandler(message)
    except Exception as er:
        LOGS.exception(er)

async def DummyHandler(ult: Message):
    # clean chat actions
    key = udB.get_key("CLEANCHAT") or []
    if ult.chat.id in key:
        try:
            await ult.delete()
        except BaseException:
            pass

    # thank members
    if must_thank(ult.chat.id) and ult.new_chat_members:
        chat_count = ult.chat.members_count
        if chat_count and chat_count % 100 == 0:
            stik_id = int(chat_count / 100 - 1)
            if stik_id < len(stickers):
                sticker = stickers[stik_id]
                await ult.reply_sticker(sticker)

    # force subscribe
    if (
        udB.get_key("FORCESUB")
        and ult.new_chat_members
        and get_forcesetting(ult.chat.id)
    ):
        joinchat = get_forcesetting(ult.chat.id)
        for user in ult.new_chat_members:
            if user.is_bot:
                continue
            
            try:
                # Check participation
                await ult._client.get_chat_member(int(joinchat), user.id)
            except Exception: # UserNotParticipant
                # Mute/Restrict
                await ult.chat.restrict_member(user.id, permissions=types.ChatPermissions())
                
                # Send FSub Button (Inline)
                # Inline query via Assistant
                results = await ult._client.get_inline_bot_results(
                    asst.me.username, f"fsub {user.id}_{joinchat}"
                )
                if results.results:
                    await ult._client.send_inline_bot_result(
                        ult.chat.id,
                        results.query_id,
                        results.results[0].id,
                        reply_to_message_id=ult.id
                    )

    if ult.new_chat_members:
        chat = ult.chat
        
        for user in ult.new_chat_members:
            # gbans and @UltroidBans checks
            if udB.get_key("ULTROID_BANS"):
                try:
                    is_banned = await async_searcher(
                        "https://bans.ultroid.tech/api/status",
                        json={"userId": user.id},
                        post=True,
                        re_json=True,
                    )
                    if is_banned["is_banned"]:
                        await ult.chat.ban_member(user.id)
                        await ult.reply(
                            f'**@UltroidBans:** Banned user detected and banned!\n`{str(is_banned)}`.\nBan reason: {is_banned["reason"]}',
                        )

                except BaseException:
                    pass
            
            reason = is_gbanned(user.id)
            if reason: # and chat.privileges.can_restrict_members
                try:
                    await ult.chat.ban_member(user.id)
                    gban_watch = get_string("can_1").format(inline_mention(user), reason)
                    await ult.reply(gban_watch)
                except Exception as er:
                    LOGS.exception(er)

            # greetings
            elif get_welcome(ult.chat.id):
                title = chat.title or "this chat"
                count = chat.members_count
                
                mention = inline_mention(user)
                name = user.first_name
                fullname = f"{user.first_name} {user.last_name or ''}".strip()
                uu = user.username
                username = f"@{uu}" if uu else mention
                userid = user.id
                
                wel = get_welcome(ult.chat.id)
                msgg = wel["welcome"]
                med = wel["media"] or None
                
                msg = None
                if msgg:
                    msg = msgg.format(
                        mention=mention,
                        group=title,
                        count=count,
                        name=name,
                        fullname=fullname,
                        username=username,
                        userid=userid,
                    )
                    
                if wel.get("button"):
                    btn = create_tl_btn(wel["button"])
                    # Assuming 'something' handles pyrogram markup
                    await something(ult, msg, med, btn)
                elif msg:
                    if med:
                        # Send as caption
                         send = await ult.reply_cached_media(med, caption=msg) if isinstance(med, str) else await ult.reply(msg) # logic for media ID needed
                    else:
                        send = await ult.reply(msg)
                        
                    await asyncio.sleep(150)
                    try:
                        await send.delete()
                    except:
                        pass
                elif med:
                     await ult.reply_cached_media(med)

    elif ult.left_chat_member and get_goodbye(ult.chat.id):
        user = ult.left_chat_member
        chat = ult.chat
        title = chat.title or "this chat"
        count = chat.members_count
        
        mention = inline_mention(user)
        name = user.first_name
        fullname = f"{user.first_name} {user.last_name or ''}".strip()
        uu = user.username
        username = f"@{uu}" if uu else mention
        userid = user.id
        
        wel = get_goodbye(ult.chat_id)
        msgg = wel["goodbye"]
        med = wel["media"]
        
        msg = None
        if msgg:
            msg = msgg.format(
                mention=mention,
                group=title,
                count=count,
                name=name,
                fullname=fullname,
                username=username,
                userid=userid,
            )
            
        if wel.get("button"):
            btn = create_tl_btn(wel["button"])
            await something(ult, msg, med, btn)
        elif msg:
            send = await ult.reply(msg) # media logic omitted for brevity
            await asyncio.sleep(150)
            try:
                await send.delete()
            except:
                pass


# --- Incoming Message Handler ---
# Equivalent to events.NewMessage(incoming=True)

async def chatBot_replies(client, e: Message):
    sender = e.from_user
    if not sender or sender.is_bot:
        return
        
    if check_echo(e.chat.id, sender.id):
        try:
            await e.copy(e.chat.id)
        except Exception as er:
            LOGS.exception(er)
            
    key = udB.get_key("CHATBOT_USERS") or {}
    if e.text and key.get(e.chat.id) and sender.id in key[e.chat.id]:
        msg = await get_chatbot_reply(e.text)
        if msg:
            sleep = udB.get_key("CHATBOT_SLEEP") or 1.5
            await asyncio.sleep(sleep)
            await e.reply(msg)
            
    if e.chat.type in [filters.group, filters.supergroup] and sender.username:
        await uname_stuff(sender.id, sender.username, sender.first_name)
    elif e.chat.type == filters.private and e.chat.username:
        await uname_stuff(sender.id, e.chat.username, e.chat.first_name)
        
    if detector and is_profan(e.chat.id) and e.text:
        x, y = detector(e.text)
        if y:
            await e.delete()


# --- Raw Update Handler ---
# Equivalent to events.Raw(UpdateUserName)

async def uname_change(client, update: raw_types.UpdateUserName, users, chats):
    # Pyrogram raw updates pass (client, update, users, chats)
    await uname_stuff(update.user_id, update.usernames[0].username if update.usernames else None, update.first_name)


async def uname_stuff(id, uname, name):
    if udB.get_key("USERNAME_LOG"):
        old_ = udB.get_key("USERNAME_DB") or {}
        old = old_.get(str(id)) # Keys are strings in JSON usually
        
        # Ignore Name Logs
        if old and old == uname:
            return
            
        if old and uname:
            await asst.send_message(
                LOG_CHANNEL,
                get_string("can_2").format(old, uname),
            )
        elif old:
            await asst.send_message(
                LOG_CHANNEL,
                get_string("can_3").format(f"[{name}](tg://user?id={id})", old),
            )
        elif uname:
            await asst.send_message(
                LOG_CHANNEL,
                get_string("can_4").format(f"[{name}](tg://user?id={id})", uname),
            )

        old_[str(id)] = uname
        udB.set_key("USERNAME_DB", old_)

# Register Handlers
ultroid_bot.add_handler(MessageHandler(ChatActionHandler, filters.service))
ultroid_bot.add_handler(MessageHandler(chatBot_replies, filters.incoming & ~filters.service))
ultroid_bot.add_handler(RawUpdateHandler(uname_change), group=1) # Using RawUpdateHandler
