# Ultroid - UserBot
# Copyright (C) 2021-2025 TeamUltroid
# Rewritten for Pyroblack by Gemini

import asyncio
import time
import uuid
from datetime import datetime

from pyroblack import enums, types, errors

try:
    from .. import _ult_cache
    from .._misc import SUDO_M
except ImportError:
    _ult_cache = {}
    SUDO_M = None


def ban_time(time_str):
    """Simplify ban time from text"""
    if not any(time_str.endswith(unit) for unit in ("s", "m", "h", "d")):
        time_str += "s"
    unit = time_str[-1]
    time_int = time_str[:-1].strip()
    if not time_int.isdigit():
        raise Exception("Invalid time amount specified.")
        
    now = time.time()
    seconds = 0
    
    if unit == "s":
        seconds = int(time_int)
    elif unit == "m":
        seconds = int(time_int) * 60
    elif unit == "h":
        seconds = int(time_int) * 60 * 60
    elif unit == "d":
        seconds = int(time_int) * 24 * 60 * 60
        
    # Pyrogram expects a datetime object or timestamp for until_date
    return datetime.fromtimestamp(now + seconds)


# ------------------Admin Check--------------- #

async def _callback_check(event):
    # This was a button verification logic for Telethon.
    # Pyrogram callback handling is different.
    # For now, we return None to fail verification or require strict admin rights.
    # Implementing inline button wait logic in Pyrogram requires a conversation manager
    # which is not built-in like Telethon's conversation.
    return None


async def get_update_linked_chat(event):
    if _ult_cache.get("LINKED_CHATS") and _ult_cache["LINKED_CHATS"].get(event.chat.id):
        _ignore = _ult_cache["LINKED_CHATS"][event.chat.id]["linked_chat"]
    else:
        full_chat = await event._client.get_chat(event.chat.id)
        _ignore = full_chat.linked_chat.id if full_chat.linked_chat else None
        
        if _ult_cache.get("LINKED_CHATS"):
            _ult_cache["LINKED_CHATS"].update({event.chat.id: {"linked_chat": _ignore}})
        else:
            _ult_cache.update(
                {"LINKED_CHATS": {event.chat.id: {"linked_chat": _ignore}}}
            )
    return _ignore


async def admin_check(event, require=None, silent: bool = False):
    user_id = event.from_user.id
    chat_id = event.chat.id
    
    if SUDO_M and user_id in SUDO_M.owner_and_sudos():
        return True

    # Anonymous Admin / Channel Logic
    if event.sender_chat and event.sender_chat.id == chat_id:
        if not require:
            return True
        # If requiring specific rights, anonymous admins usually have them all
        return True

    try:
        member = await event.chat.get_member(user_id)
    except errors.UserNotParticipant:
        if not silent:
            await event.eor("You need to join this chat First!")
        return False
    except Exception:
        return False

    if member.status not in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
        if not silent:
            await event.eor("Only Admins can use this command!", time=8)
        return False

    if require:
        # Mapping common Ultroid/Telethon keys to Pyrogram
        req_map = {
            "ban_users": "can_restrict_members",
            "delete_messages": "can_delete_messages",
            "pin_messages": "can_pin_messages",
            "invite_users": "can_invite_users",
            "add_admins": "can_promote_members",
            "change_info": "can_change_info"
        }
        
        pyro_req = req_map.get(require, require)
        
        # If Owner, they have all rights
        if member.status == enums.ChatMemberStatus.OWNER:
            return True

        if not getattr(member.privileges, pyro_req, False):
            if not silent:
                await event.eor(f"You are missing the right of `{require}`", time=8)
            return False
            
    return True


# ------------------Lock Unlock----------------

def lock_unlock(query, lock=True):
    """
    Used in locks plugin. 
    Returns ChatPermissions object.
    """
    # Pyrogram ChatPermissions: True = Allowed, False = Restricted
    # "Lock" means setting permission to False.
    
    _allow = not lock
    
    # Default everything to None (No change)
    # Pyrogram restrictive permissions need to be constructed fully or used with set_chat_permissions
    
    permissions = types.ChatPermissions()
    
    if query == "msgs":
        permissions.can_send_messages = _allow
    elif query == "media":
        permissions.can_send_media_messages = _allow
    elif query == "sticker":
        permissions.can_send_other_messages = _allow # Stickers/GIFs usually here
    elif query == "gif":
        permissions.can_send_other_messages = _allow
    elif query == "games":
        permissions.can_send_other_messages = _allow
    elif query == "inline":
        permissions.can_send_other_messages = _allow
    elif query == "polls":
        permissions.can_send_polls = _allow
    elif query == "invites":
        permissions.can_invite_users = _allow
    elif query == "pin":
        permissions.can_pin_messages = _allow
    elif query == "changeinfo":
        permissions.can_change_info = _allow
    else:
        return None
        
    return permissions
