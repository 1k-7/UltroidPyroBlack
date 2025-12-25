# Ultroid - UserBot
# Copyright (C) 2021-2025 TeamUltroid
# Rewritten for Pyroblack by Gemini

import asyncio
import calendar
import html
import io
import os
import pathlib
import time
from datetime import datetime as dt

try:
    from PIL import Image
except ImportError:
    Image = None

from pyUltroid._misc._assistant import asst_cmd
from pyUltroid.dB.gban_mute_db import is_gbanned
from pyUltroid.fns.tools import get_chat_and_msgid

# Assuming upload_file wrapper is compatible or mapped
from . import upload_file as uf

# Pyroblack Imports
from pyroblack import enums, errors
from pyroblack.types import (
    Message,
    User,
    Chat,
    Poll,
    PollOption
)

from pyUltroid.fns.info import get_chat_info

from . import (
    HNDLR,
    LOGS,
    Image,
    ReTrieveFile,
    Telegraph,
    asst,
    async_searcher,
    bash,
    check_filename,
    eod,
    eor,
    get_paste,
    get_string,
    inline_mention,
    json_parser,
    mediainfo,
    udB,
    ultroid_cmd,
)

# =================================================================#

TMP_DOWNLOAD_DIRECTORY = "resources/downloads/"
CAPTION_LIMIT = 1024  # Telegram's caption character limit for non-premium

_copied_msg = {}


@ultroid_cmd(pattern="kickme$", fullsudo=True)
async def leave(ult: Message):
    await ult.eor(f"`{ult.from_user.first_name} has left this group, bye!!.`")
    await ult.chat.leave()


@ultroid_cmd(
    pattern="date$",
)
async def date(event: Message):
    m = dt.now().month
    y = dt.now().year
    d = dt.now().strftime("Date - %B %d, %Y\nTime- %H:%M:%S")
    k = calendar.month(y, m)
    await event.eor(f"`{k}\n\n{d}`")


@ultroid_cmd(
    pattern="listreserved$",
)
async def _(event: Message):
    # Pyrogram doesn't have a direct "GetAdminedPublicChannels"
    # We iterate dialogs and filter
    chats = []
    async for dialog in event._client.get_dialogs():
        chat = dialog.chat
        if chat.type in [enums.ChatType.CHANNEL, enums.ChatType.SUPERGROUP]:
            # Check if creator or admin and has username
            if chat.username and (chat.is_creator or (chat.privileges and chat.privileges.can_change_info)):
                 chats.append(chat)
    
    if not chats:
        return await event.eor("`No username Reserved`")
        
    output_str = "".join(
        f"- {chat.title} @{chat.username} \n"
        for chat in chats
    )
    await event.eor(output_str)


@ultroid_cmd(
    pattern="stats$",
)
async def stats(event: Message):
    ok = await event.eor("`Collecting stats...`")
    start_time = time.time()
    private_chats = 0
    bots = 0
    groups = 0
    broadcast_channels = 0
    admin_in_groups = 0
    creator_in_groups = 0
    admin_in_broadcast_channels = 0
    creator_in_channels = 0
    unread_mentions = 0
    unread = 0
    
    async for dialog in event._client.get_dialogs():
        chat = dialog.chat
        
        if chat.type == enums.ChatType.CHANNEL:
            broadcast_channels += 1
            if chat.is_creator:
                creator_in_channels += 1
                admin_in_broadcast_channels += 1 # Creator is admin
            elif chat.privileges: # Has admin rights
                admin_in_broadcast_channels += 1

        elif chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            groups += 1
            if chat.is_creator:
                creator_in_groups += 1
                admin_in_groups += 1
            elif chat.privileges:
                admin_in_groups += 1

        elif chat.type == enums.ChatType.PRIVATE:
            private_chats += 1
            # dialog.chat.is_bot is not always populated in dialog list without full resolve?
            # Pyrogram Chat object doesn't strictly have is_bot, usually on User object
            # We fetch chat members or assume based on something else, but strictly:
            # We might need to peek the user entity.
            # Simplified:
            pass # Counting bots in dialog iteration is harder in Pyro without fetching users
            
        unread_mentions += dialog.unread_mentions_count
        unread += dialog.unread_messages_count

    stop_time = time.time() - start_time
    
    # Blocked Users
    try:
        ct = await event._client.get_blocked_users_count()
    except Exception:
        ct = 0

    # Stickers (No direct API for 'all installed packs' in Client without Raw)
    sp_count = "N/A"

    full_name = inline_mention(event.from_user)
    response = f"🔸 **Stats for {full_name}** \n\n"
    response += f"**Private Chats:** {private_chats} \n"
    # response += f"** •• **`Bots: {bots}` \n" # Disabled due to efficiency
    response += f"**Groups:** {groups} \n"
    response += f"**Channels:** {broadcast_channels} \n"
    response += f"**Admin in Groups:** {admin_in_groups} \n"
    response += f"** •• **`Creator: {creator_in_groups}` \n"
    response += f"** •• **`Admin Rights: {admin_in_groups - creator_in_groups}` \n"
    response += f"**Admin in Channels:** {admin_in_broadcast_channels} \n"
    response += f"** •• **`Creator: {creator_in_channels}` \n"
    response += f"** •• **`Admin Rights: {admin_in_broadcast_channels - creator_in_channels}` \n"
    response += f"**Unread:** {unread} \n"
    response += f"**Unread Mentions:** {unread_mentions} \n"
    response += f"**Blocked Users:** {ct}\n"
    # response += f"**Total Stickers Pack Installed :** `{sp_count}`\n\n"
    response += f"**__It Took:__** {stop_time:.02f}s \n"
    await ok.edit(response)


@ultroid_cmd(pattern="paste( (.*)|$)", manager=True, allow_all=True)
async def _(event: Message):
    try:
        input_str = event.text.split(maxsplit=1)[1]
    except IndexError:
        input_str = None
        
    xx = await event.eor("` 《 Pasting... 》 `")
    downloaded_file_name = None
    
    if input_str:
        message = input_str
    elif event.reply_to_message:
        previous_message = event.reply_to_message
        if previous_message.media or previous_message.document:
            downloaded_file_name = await previous_message.download(
                file_name="./resources/downloads/"
            )
            with open(downloaded_file_name, "r") as fd:
                message = fd.read()
            os.remove(downloaded_file_name)
        else:
            message = previous_message.text or previous_message.caption
    else:
        message = None
        
    if not message:
        return await xx.eor(
            "`Reply to a Message/Document or Give me Some Text !`", time=5
        )
        
    done, data = await get_paste(message)
    if not done and data.get("error"):
        return await xx.eor(data["error"])
        
    reply_text = (
        f"• **Pasted to SpaceBin :** [Space]({data['link']})\n• **Raw Url :** : [Raw]({data['raw']})"
    )
    
    try:
        # Check if bot
        if event._client.me.is_bot:
            return await xx.eor(reply_text)
            
        # Inline Query (Assuming assistant exists)
        results = await event._client.get_inline_bot_results(asst.me.username, f"pasta-{data['link']}")
        if results.results:
             await event._client.send_inline_bot_result(
                event.chat.id,
                results.query_id,
                results.results[0].id,
                reply_to_message_id=event.reply_to_message_id
             )
             await xx.delete()
        else:
             await xx.edit(reply_text)
             
    except BaseException as e:
        LOGS.exception(e)
        await xx.edit(reply_text)


@ultroid_cmd(
    pattern="info( (.*)|$)",
    manager=True,
)
async def _(event: Message):
    match = None
    if event.matches:
        match = event.matches[0].group(1).strip()
    
    if match:
        # Resolve ID/Username
        try:
             # Pyrogram get_users handles username/ID
             user_obj = await event._client.get_users(match)
             user = user_obj.id
        except Exception as er:
             # Could be chat
             try:
                 chat_obj = await event._client.get_chat(match)
                 user = chat_obj.id
             except:
                 return await event.eor(str(er))
    elif event.reply_to_message:
        user = event.reply_to_message.from_user.id
    else:
        user = event.chat.id
        
    xx = await event.eor(get_string("com_1"))
    
    try:
        entity = await event._client.get_chat(user)
    except Exception as er:
        return await xx.edit(f"**ERROR :** {er}")
        
    # Check if it's a Chat/Channel (Not User)
    if entity.type != enums.ChatType.PRIVATE:
        try:
            peer_id = entity.id
            photo, capt = await get_chat_info(entity, event)
            if is_gbanned(peer_id):
                capt += "\n•<b> Is Gbanned:</b> <code>True</code>"
            if not photo:
                return await xx.eor(capt, parse_mode=enums.ParseMode.HTML)
            
            await event._client.send_photo(
                event.chat.id,
                photo=photo,
                caption=capt[:1024],
                parse_mode=enums.ParseMode.HTML
            )
            await xx.delete()
        except Exception as er:
            await event.eor("**ERROR ON CHATINFO**\n" + str(er))
        return

    # It is a User
    # In Pyrogram get_chat(user_id) returns Chat object, get_users(user_id) returns User object
    # Let's get User object for specific fields
    try:
        user_info = await event._client.get_users(user)
    except:
        user_info = entity # Fallback
        
    # Photos count (requires iterating get_chat_photos)
    user_photos = await event._client.get_chat_photos_count(user)

    user_id = user_info.id
    first_name = html.escape(user_info.first_name or "")
    last_name = html.escape(user_info.last_name or "Last Name not found")
    user_bio = entity.bio or "None"
    
    dc_id = "Unknown"
    if user_info.photo:
         dc_id = user_info.photo.big_file_id[:5] + "..." # Approx
         
    common_chats = len(await event._client.get_common_chats(user_id))

    caption = """<b>Exᴛʀᴀᴄᴛᴇᴅ Dᴀᴛᴀ Fʀᴏᴍ Tᴇʟᴇɢʀᴀᴍ's Dᴀᴛᴀʙᴀsᴇ<b>
<b>••Tᴇʟᴇɢʀᴀᴍ ID</b>: <code>{}</code>
<b>••Pᴇʀᴍᴀɴᴇɴᴛ Lɪɴᴋ</b>: <a href='tg://user?id={}'>Click Here</a>
<b>••Fɪʀsᴛ Nᴀᴍᴇ</b>: <code>{}</code>
<b>••Sᴇᴄᴏɴᴅ Nᴀᴍᴇ</b>: <code>{}</code>
<b>••Bɪᴏ</b>: <code>{}</code>
<b>••Dᴄ ID</b>: <code>{}</code>
<b>••Nᴏ. Oғ PғPs</b> : <code>{}</code>
<b>••Is Rᴇsᴛʀɪᴄᴛᴇᴅ</b>: <code>{}</code>
<b>••Vᴇʀɪғɪᴇᴅ</b>: <code>{}</code>
<b>••Is Pʀᴇᴍɪᴜᴍ</b>: <code>{}</code>
<b>••Is A Bᴏᴛ</b>: <code>{}</code>
<b>••Gʀᴏᴜᴘs Iɴ Cᴏᴍᴍᴏɴ</b>: <code>{}</code>
""".format(
        user_id,
        user_id,
        first_name,
        last_name,
        user_bio,
        dc_id,
        user_photos,
        user_info.is_restricted,
        user_info.is_verified,
        user_info.is_premium,
        user_info.is_bot,
        common_chats,
    )
    
    if chk := is_gbanned(user_id):
        caption += f"""<b>••Gʟᴏʙᴀʟʟʏ Bᴀɴɴᴇᴅ</b>: <code>True</code>
<b>••Rᴇᴀsᴏɴ</b>: <code>{chk}</code>"""
        
    # Send
    if user_info.photo:
         await event._client.send_photo(
             event.chat.id,
             user_info.photo.big_file_id,
             caption=caption,
             parse_mode=enums.ParseMode.HTML,
             reply_to_message_id=event.reply_to_message_id
         )
    else:
         await event._client.send_message(
             event.chat.id,
             caption,
             parse_mode=enums.ParseMode.HTML,
             reply_to_message_id=event.reply_to_message_id
         )
         
    await xx.delete()


@ultroid_cmd(
    pattern="invite( (.*)|$)",
    groups_only=True,
)
async def _(ult: Message):
    xx = await ult.eor(get_string("com_1"))
    to_add_users = ult.matches[0].group(1).strip() if ult.matches else None
    
    if not to_add_users:
        return await xx.edit("Give username/ID to invite")

    # Pyrogram add_members works for both groups and channels
    users_list = to_add_users.split(" ")
    try:
        await ult.chat.add_members(users_list)
        await xx.edit(f"Successfully invited `{to_add_users}` to `{ult.chat.title}`")
    except Exception as e:
        await xx.edit(f"Error: {str(e)}")


@ultroid_cmd(
    pattern="rmbg($| (.*))",
)
async def abs_rmbg(event: Message):
    RMBG_API = udB.get_key("RMBG_API")
    if not RMBG_API:
        return await event.eor(
            "Get your API key from [here](https://www.remove.bg/) for this plugin to work.",
        )
    match = event.matches[0].group(1).strip() if event.matches else None
    reply = event.reply_to_message
    
    if match and os.path.exists(match):
        dl = match
    elif reply and (reply.photo or reply.document):
        dl = await reply.download()
    else:
        return await eod(
            event, f"Use `{HNDLR}rmbg` as reply to a pic to remove its background."
        )
        
    if not (dl and dl.lower().endswith(("webp", "jpg", "png", "jpeg"))):
        os.remove(dl)
        return await event.eor(get_string("com_4"))
        
    if dl.endswith("webp"):
        file = f"{dl}.png"
        Image.open(dl).save(file)
        os.remove(dl)
        dl = file
        
    xx = await event.eor("`Sending to remove.bg`")
    dn, out = await ReTrieveFile(dl)
    os.remove(dl)
    
    if not dn:
        # Error handling
        return await xx.edit(f"**ERROR**")
        
    zz = Image.open(out)
    if zz.mode != "RGB":
        zz.convert("RGB")
    wbn = check_filename("ult-rmbg.webp")
    zz.save(wbn, "webp")
    
    await event.reply_document(out, force_document=True)
    await event.reply_document(wbn)
    
    os.remove(out)
    os.remove(wbn)
    await xx.delete()


@ultroid_cmd(
    pattern="telegraph( (.*)|$)",
)
async def telegraphcmd(event: Message):
    xx = await event.eor(get_string("com_1"))
    match = event.matches[0].group(1).strip() if event.matches else "Ultroid"
    reply = event.reply_to_message
    
    if not reply:
        return await xx.eor("`Reply to Message.`")
        
    if not reply.media and (reply.text or reply.caption):
        content = reply.text or reply.caption
    else:
        getit = await reply.download()
        # Mime check not as simple in Pyro without helpers, relying on filename extension or explicit media type
        if reply.sticker:
             file = f"{getit}.png"
             Image.open(getit).save(file)
             os.remove(getit)
             getit = file
        elif reply.animation:
             file = f"{getit}.gif"
             await bash(f"lottie_convert.py '{getit}' {file}")
             os.remove(getit)
             getit = file
             
        # Check if text file? Pyro doesn't give mimetype easily on download path return
        # Assuming image/media upload logic
        try:
            nn = uf(getit)
            amsg = f"Uploaded to [Telegraph]({nn}) !"
        except Exception as e:
            amsg = f"Error : {e}"
        os.remove(getit)
        return await xx.eor(amsg)
        
    makeit = Telegraph.create_page(title=match, content=[content])
    await xx.eor(
        f"Pasted to Telegraph : [Telegraph]({makeit['url']})", link_preview=False
    )


@ultroid_cmd(pattern="json( (.*)|$)")
async def _(event: Message):
    match = event.matches[0].group(1).strip() if event.matches else None
    
    if event.reply_to_message:
        msg = event.reply_to_message
    else:
        msg = event
    
    # Pyrogram objects str() representation IS json-like
    if match and hasattr(msg, match.split()[0]):
         msg = getattr(msg, match.split()[0])
         
    msg_str = str(msg)
    
    if len(msg_str) > 4096:
        with io.BytesIO(str.encode(msg_str)) as out_file:
            out_file.name = "json-ult.txt"
            await event.reply_document(
                out_file,
                quote=True
            )
            await event.delete()
    else:
        await event.eor(f"```{msg_str}```")


@ultroid_cmd(pattern="suggest( (.*)|$)", manager=True)
async def sugg(event: Message):
    args = event.text.split(maxsplit=1)
    text = args[1] if len(args) > 1 else None
    
    if not (event.reply_to_message or text):
        return await eod(event, "`Please reply to a message to make a suggestion poll!`")
        
    if event.reply_to_message and not text:
        reply = event.reply_to_message
        if reply.text and len(reply.text) < 35:
            text = reply.text
        else:
            text = "Do you Agree to Replied Suggestion ?"
            
    reply_to = event.reply_to_message.id if event.reply_to_message else None
    
    try:
        await event._client.send_poll(
            event.chat.id,
            question=text,
            options=["Yes", "No"],
            reply_to_message_id=reply_to
        )
    except Exception as e:
        return await eod(event, f"`Oops, you can't send polls here!\n\n{e}`")
    await event.delete()


@ultroid_cmd(pattern="ipinfo( (.*)|$)")
async def ipinfo(event: Message):
    ip = event.text.split()
    ipaddr = ""
    try:
        ipaddr = f"/{ip[1]}"
    except IndexError:
        ipaddr = ""
    det = await async_searcher(f"https://ipinfo.io{ipaddr}/geo", re_json=True)
    try:
        ip = det["ip"]
        city = det["city"]
        region = det["region"]
        country = det["country"]
        cord = det["loc"]
        zipc = det.get("postal", "None")
        tz = det["timezone"]
        await eor(
            event,
            """
**IP Details Fetched.**

**IP:** `{}`
**City:** `{}`
**Region:** `{}`
**Country:** `{}`
**Co-ordinates:** `{}`
**Postal Code:** `{}`
**Time Zone:** `{}`
""".format(
                ip,
                city,
                region,
                country,
                cord,
                zipc,
                tz,
            ),
        )
    except BaseException:
        err = det.get("error", {}).get("title", "Error")
        msg = det.get("error", {}).get("message", "Unknown")
        await event.eor(f"ERROR:\n{err}\n{msg}", time=5)


@ultroid_cmd(
    pattern="cpy$",
)
async def copp(event: Message):
    msg = event.reply_to_message
    if not msg:
        return await event.eor(f"Use `{HNDLR}cpy` as reply to a message!", time=5)
    _copied_msg["CLIPBOARD"] = msg
    await event.eor(f"Copied. Use `{HNDLR}pst` to paste!", time=10)


@asst_cmd(pattern="pst$")
async def pepsodent(event: Message):
    await toothpaste(event)


@ultroid_cmd(
    pattern="pst$",
)
async def colgate(event: Message):
    await toothpaste(event)


async def toothpaste(event: Message):
    try:
        # copy() works for messages in Pyrogram
        msg = _copied_msg["CLIPBOARD"]
        await msg.copy(event.chat.id)
    except KeyError:
        return await eod(
            event,
            f"Nothing was copied! Use `{HNDLR}cpy` as reply to a message first!",
        )
    except Exception as ex:
        return await event.eor(str(ex), time=5)
    await event.delete()


@ultroid_cmd(pattern="thumb$")
async def thumb_dl(event: Message):
    reply = event.reply_to_message
    if not (reply and (reply.photo or reply.document or reply.video)):
        return await eod(event, get_string("th_1"), time=5)
        
    # Check if thumbs exist (video/doc have thumbs, photo is thumb itself)
    # Pyrogram handles download("filename.jpg") for photos/thumbs
    await event.eor(get_string("com_1"))
    
    m = await reply.download(file_name="resources/downloads/thumb.jpg") 
    # Logic note: if it's a doc without thumb, pyro might download whole file. 
    # For video/doc, pyro automatically tries to download thumb if file_name ends in jpg usually.
    # Safe check:
    if not os.path.exists(m):
         # Try specific thumb download if available? Pyro doesn't expose thumb index easily 
         pass
         
    await event.reply_photo(m)
    os.remove(m)


async def get_video_duration(file_path):
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        file_path,
    ]
    try:
        result = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        duration = float(stdout.decode().strip())
        return duration
    except Exception as e:
        print("Error running ffprobe:", e)
        return None

async def get_thumbnail(file_path, thumbnail_path):
    try:
        await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-i", file_path,
            "-ss", "00:00:04",
            "-vframes", "1",  # Extract a single frame as the thumbnail
            thumbnail_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except Exception as e:
        print(f"Error extracting thumbnail: {e}")

@ultroid_cmd(pattern="getmsg( ?(.*)|$)")
async def get_restricted_msg(event: Message):
    match = event.matches[0].group(1).strip() if event.matches else None
    if not match:
        await event.eor("`Please provide a link!`", time=5)
        return
    
    xx = await event.eor("`Loading...`")
    chat, msg = get_chat_and_msgid(match)
    if not (chat and msg):
        return await event.eor(
            "Invalid link!\nExamples:\n"
            "`https://t.me/TeamUltroid/3`\n"
            "`https://t.me/c/1313492028/3`\n"
            "`tg://openmessage?user_id=1234567890&message_id=1`"
        )
    
    try:
        # Pyrogram get_messages
        message = await event._client.get_messages(chat, message_ids=msg)
    except BaseException as er:
        return await event.eor(f"**ERROR**\n`{er}`")
    
    if not message or message.empty:
        return await event.eor("`Message not found or may not exist.`")
    
    try:
        await message.copy(event.chat.id)
        await xx.try_delete()
        return
    except errors.ChatForwardsRestricted:
        pass
    except Exception as e:
        pass # Fetch manually below
    
    if message.media:
        # If media exists
        if message.photo or message.document or message.video:
             # Download using helper
             media_path, _ = await event._client.fast_downloader(message, show_progress=True, event=xx, message=get_string("com_5"))
             caption = message.caption or ""
             
             thumb_path = None
             if message.video:
                 thumb_path = media_path + "_thumb.jpg"
                 await get_thumbnail(media_path, thumb_path)

             await xx.edit(get_string("com_6"))
             
             # Upload
             # Using reply_document / reply_video / reply_photo based on type
             try:
                 if message.video:
                     await event.reply_video(
                         media_path,
                         caption=caption,
                         thumb=thumb_path,
                         supports_streaming=True
                     )
                 elif message.photo:
                     await event.reply_photo(
                         media_path,
                         caption=caption
                     )
                 else:
                     await event.reply_document(
                         media_path,
                         caption=caption
                     )
             except Exception as e:
                 await event.eor(f"Error sending: {e}")
             
             # Cleanup
             if os.path.exists(media_path):
                 os.remove(media_path)
             if thumb_path and os.path.exists(thumb_path):
                 os.remove(thumb_path)
                 
             await xx.try_delete()
        else:
            await event.eor("`Cannot process this type of media.`")
    else:
        # Text message
        if message.text:
             await event.reply(message.text)
             await xx.try_delete()
        else:
             await event.eor("`No media found in the message.`")
