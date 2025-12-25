# Ultroid - UserBot
# Copyright (C) 2021-2025 TeamUltroid
# Rewritten for Pyroblack by Gemini

import asyncio
import inspect
import sys
import re
from io import BytesIO
from pathlib import Path
from time import gmtime, strftime
from traceback import format_exc

from pyroblack import Client, filters, errors, enums
from pyroblack.types import Message
from pyroblack.handlers import MessageHandler

from strings import get_string
from .. import *
from ..dB import DEVLIST
from ..dB._core import LIST, LOADED
from ..fns.admins import admin_check
from ..fns.helper import bash
from ..fns.helper import time_formatter as tf
from ..version import __version__ as pyver
from ..version import ultroid_version as ult_ver
from . import SUDO_M, owner_and_sudos
from ._wrappers import eod, eor

# Configs
MANAGER = udB.get_key("MANAGER")
TAKE_EDITS = udB.get_key("TAKE_EDITS")
black_list_chats = udB.get_key("BLACKLIST_CHATS") or []
allow_sudo = SUDO_M.should_allow_sudo

def compile_pattern(data, hndlr):
    if data.startswith("^"):
        data = data[1:]
    if data.startswith("."):
        data = data[1:]
    if hndlr in [" ", "NO_HNDLR"]:
        return re.compile("^" + data)
    return re.compile("\\" + re.escape(hndlr) + data)

def ultroid_cmd(
    pattern=None, 
    manager=False, 
    ultroid_bot=ultroid_bot, 
    asst=asst, 
    **kwargs
):
    owner_only = kwargs.get("owner_only", False)
    groups_only = kwargs.get("groups_only", False)
    admins_only = kwargs.get("admins_only", False)
    fullsudo = kwargs.get("fullsudo", False)
    only_devs = kwargs.get("only_devs", False)
    # Filter function replacement (default allow unless specified)
    custom_filter = kwargs.get("func", None) 

    def decor(func):
        async def wrapp(client: Client, message: Message):
            # Command Logging
            if udB.get_key("COMMAND_LOGGER"):
                try:
                    user_id = message.from_user.id
                    chat_id = message.chat.id
                    command_name = pattern if pattern else (message.text.split()[0] if message.text else "Unknown")
                    chat_name = message.chat.title or message.chat.first_name or "Private"
                    
                    log_msg = f"Command '{command_name}' executed by user ID {user_id} in chat {chat_id} ({chat_name})"
                    LOGS.info(log_msg)
                    
                    log_channel = udB.get_key("LOG_CHANNEL")
                    if log_channel:
                         await asst.send_message(log_channel, log_msg)
                except Exception as e:
                    LOGS.warning(f"Logger Error: {e}")

            # Permissions Check
            sender_id = message.from_user.id if message.from_user else 0
            is_outgoing = message.outgoing or (message.from_user and message.from_user.is_self)

            if not is_outgoing:
                if owner_only:
                    return
                if sender_id not in owner_and_sudos():
                    return
                if sender_id in _ignore_eval:
                    return await eod(message, get_string("py_d1"))
                if fullsudo and sender_id not in SUDO_M.fullsudos:
                    return await eod(message, get_string("py_d2"), time=15)

            # Chat blacklists and logic
            if message.chat.title: 
                if "#noub" in message.chat.title.lower() and not (sender_id in DEVLIST):
                    # Skip execution if chat title contains #noub and user is not dev
                    return

            if (message.chat.type == enums.ChatType.PRIVATE) and (groups_only or admins_only):
                return await eod(message, get_string("py_d3"))
            
            # Admin check 
            if admins_only:
                 # Check if user is admin in the chat
                 is_admin = await admin_check(message, silent=True)
                 if not is_admin:
                     return await eod(message, get_string("py_d5"))

            if only_devs and not udB.get_key("I_DEV"):
                return await eod(message, get_string("py_d4").format(HNDLR), time=10)

            try:
                await func(message)
            except errors.FloodWait as fwerr:
                await asst.send_message(
                    udB.get_key("LOG_CHANNEL"),
                    f"`FloodWaitError:\n{str(fwerr)}\n\nSleeping for {tf((fwerr.value + 10)*1000)}`",
                )
                await asyncio.sleep(fwerr.value + 10)
                return
            except errors.Forbidden:
                 return await eod(message, get_string("py_d8"))
            except (errors.BotMethodInvalid, errors.UserIsBot):
                return await eod(message, get_string("py_d6"))
            except (errors.MessageIdInvalid, errors.MessageNotModified):
                pass
            except events.StopPropagation:
                 pass 
            except Exception as e:
                LOGS.exception(e)
                # Error Reporting Logic
                date = strftime("%Y-%m-%d %H:%M:%S", gmtime())
                ftext = "**Ultroid Client Error:** `Forward this to` @UltroidSupportChat\n\n"
                ftext += "**Py-Ultroid Version:** `" + str(pyver)
                ftext += "`\n**Ultroid Version:** `" + str(ult_ver)
                ftext += "`\n**Pyrogram Version:** `2.x`\n" 
                ftext += f"**Hosted At:** `{HOSTED_ON}`\n\n"
                ftext += "--------START ULTROID CRASH LOG--------\n"
                ftext += f"**Date:** `{date}`\n"
                ftext += f"**Chat:** `{message.chat.id}`\n"
                ftext += f"**Sender:** `{sender_id}`\n"
                ftext += f"**Command:** `{message.text or message.caption}`\n\n"
                ftext += f"**Traceback:**\n`{format_exc()}`\n"
                ftext += "--------END ULTROID CRASH LOG--------\n"

                if len(ftext) > 4096:
                    with BytesIO(ftext.encode()) as file:
                        file.name = "logs.txt"
                        await asst.send_document(
                            udB.get_key("LOG_CHANNEL"),
                            file,
                            caption="**Ultroid Client Error**",
                        )
                else:
                    await asst.send_message(udB.get_key("LOG_CHANNEL"), ftext)
                
                if is_outgoing:
                    await message.edit(f"<b>An error occurred. check logs.</b>")

        # --- Filter Construction ---
        final_filter = filters.all
        
        # 1. Incoming/Outgoing
        if allow_sudo and HNDLR != SUDO_HNDLR:
            # Sudo users with different handler
            user_filter = filters.me | filters.user(SUDO_M.sudos if SUDO_M else [])
        else:
            user_filter = filters.me
            
        if manager:
            # Managers can trigger assistant
            final_filter = filters.incoming
        else:
            final_filter = user_filter & ~filters.edited if not TAKE_EDITS else user_filter

        # 2. Pattern (Regex or Command)
        if pattern:
            # Compile regex similar to Telethon's logic
            regex_pattern = compile_pattern(pattern, HNDLR if not manager else "/")
            final_filter &= filters.regex(regex_pattern)
        
        # 3. Custom Function Filter
        if custom_filter:
             final_filter &= filters.create(lambda _, __, m: custom_filter(m))

        # 4. Blacklist
        if black_list_chats:
            final_filter &= ~filters.chat(black_list_chats)

        # --- Register Handler ---
        if manager and MANAGER:
            # Assistant Handler
            asst.add_handler(MessageHandler(wrapp, final_filter))
        else:
            # Userbot Handler
            ultroid_bot.add_handler(MessageHandler(wrapp, final_filter))
            
        # --- Metadata Storage (For Help Menu) ---
        file = Path(inspect.stack()[1].filename)
        plugin_name = file.stem
        if "addons" in str(file):
             plugin_name = file.stem 
        
        if plugin_name not in LOADED:
            LOADED[plugin_name] = []
        LOADED[plugin_name].append(wrapp)

        if pattern:
             if plugin_name not in LIST:
                 LIST[plugin_name] = []
             LIST[plugin_name].append(pattern)

        return wrapp

    return decor
