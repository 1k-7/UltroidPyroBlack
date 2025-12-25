# Ultroid - UserBot
# Copyright (C) 2021-2025 TeamUltroid
# Rewritten for Pyroblack by Gemini

from pyroblack.errors import (
    BotMethodInvalid,
    ChatSendInlineForbidden,
    ChatSendMediaForbidden,
)
from pyroblack.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from . import LOG_CHANNEL, LOGS, asst, eor, get_string, ultroid_cmd

REPOMSG = """
• **ULTROID USERBOT** •\n
• Repo - [Click Here](https://github.com/TeamUltroid/Ultroid)
• Addons - [Click Here](https://github.com/TeamUltroid/UltroidAddons)
• Support - @UltroidSupportChat
"""

RP_BUTTONS = InlineKeyboardMarkup([
    [
        InlineKeyboardButton(get_string("bot_3"), url="https://github.com/TeamUltroid/Ultroid"),
        InlineKeyboardButton("Addons", url="https://github.com/TeamUltroid/UltroidAddons"),
    ],
    [InlineKeyboardButton("Support Group", url="t.me/UltroidSupportChat")],
])

ULTSTRING = """🎇 **Thanks for Deploying Ultroid Userbot!**

• Here, are the Some Basic stuff from, where you can Know, about its Usage."""


@ultroid_cmd(
    pattern="repo$",
    manager=True,
)
async def repify(e: Message):
    try:
        # get_inline_bot_results(bot_username, query)
        q = await e._client.get_inline_bot_results(asst.me.username, "")
        # send_inline_bot_result(chat_id, query_id, result_id)
        if q and q.results:
             await e._client.send_inline_bot_result(
                 e.chat.id, 
                 q.query_id, 
                 q.results[0].id
             )
             return await e.delete()
    except (
        ChatSendInlineForbidden,
        ChatSendMediaForbidden,
        BotMethodInvalid,
    ):
        pass
    except Exception as er:
        LOGS.info(f"Error while repo command : {str(er)}")
    
    await eor(e, REPOMSG)


@ultroid_cmd(pattern="ultroid$")
async def useUltroid(rs: Message):
    button = InlineKeyboardMarkup([[InlineKeyboardButton("Start >>", callback_data="initft_2")]])
    
    # send_message returns Message
    msg = await asst.send_photo(
        LOG_CHANNEL,
        photo="https://graph.org/file/54a917cc9dbb94733ea5f.jpg",
        caption=ULTSTRING,
        reply_markup=button,
    )
    
    # Check if executed in Log Channel
    if not (rs.chat.id == LOG_CHANNEL and rs.from_user.is_self):
        await eor(rs, f"**[Click Here]({msg.link})**")
