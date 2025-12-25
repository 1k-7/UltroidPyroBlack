# Ultroid - UserBot
# Copyright (C) 2021-2025 TeamUltroid
# Rewritten for Pyroblack by Gemini

from . import get_help

__doc__ = get_help("help_downloadupload")

import asyncio
import glob
import os
import time
from datetime import datetime as dt

from pyUltroid.fns.helper import time_formatter
from pyUltroid.fns.tools import get_chat_and_msgid, set_attributes

from . import (
    LOGS,
    ULTConfig,
    eor,
    fast_download,
    get_all_files,
    get_string,
    progress,
    ultroid_cmd,
)

@ultroid_cmd(
    pattern="download( (.*)|$)",
)
async def down(event):
    match = event.matches[0].group(1).strip() if event.matches else None
    msg = await event.eor(get_string("udl_4"))
    
    if not match:
        return await eor(msg, get_string("udl_5"), time=5)
    
    try:
        splited = match.split(" | ")
        link = splited[0]
        filename = splited[1] if len(splited) > 1 else None
    except IndexError:
        filename = None
        
    s_time = time.time()
    try:
        filename, d = await fast_download(
            link,
            filename,
            progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                progress(d, t, msg, s_time, f"Downloading from {link}")
            ),
        )
    except Exception as e:
        return await msg.eor(f"`Error: {e}`", time=5)
        
    await msg.eor(f"`{filename}` `downloaded in {time_formatter(d*1000)}.`")


@ultroid_cmd(
    pattern="dl( (.*)|$)",
)
async def download(event):
    match = event.matches[0].group(1).strip() if event.matches else None
    ok = event.reply_to_message
    
    if match and ("t.me/" in match or "telegram.me/" in match):
        chat, msg_id = get_chat_and_msgid(match)
        if chat and msg_id:
            try:
                ok = await event._client.get_messages(chat, message_ids=msg_id)
            except Exception as e:
                return await event.eor(f"Error getting message: {e}")
        else:
            return await event.eor(get_string("gms_1"))
        match = None # Reset match so it doesn't interfere with filename
    elif not ok:
        return await event.eor(get_string("cvt_3"), time=8)
        
    xx = await event.eor(get_string("com_1"))
    
    # Check media
    if not (ok and (ok.media or ok.photo or ok.video or ok.document or ok.audio or ok.voice or ok.sticker)):
        return await xx.eor(get_string("udl_1"), time=5)
        
    s = dt.now()
    k = time.time()
    
    # Determine Filename
    filename = match
    if not filename:
        if ok.document:
            filename = ok.document.file_name
        elif ok.video:
            filename = ok.video.file_name or f"video_{dt.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        elif ok.audio:
            filename = ok.audio.file_name or f"audio_{dt.now().strftime('%Y%m%d_%H%M%S')}.ogg"
        elif ok.photo:
            filename = f"jpg_{dt.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        elif ok.sticker:
            filename = f"sticker_{dt.now().strftime('%Y%m%d_%H%M%S')}.webp"
            
    if not filename:
        filename = f"download_{dt.now().strftime('%Y%m%d_%H%M%S')}"

    path = os.path.join("resources/downloads", filename)
    
    try:
        # Native Pyrogram Download
        file_path = await ok.download(
            file_name=path,
            progress=progress,
            progress_args=(xx, k, get_string("com_5"))
        )
    except Exception as err:
        return await xx.edit(f"Download Failed: {err}")
        
    e = dt.now()
    t = time_formatter(((e - s).seconds) * 1000)
    
    final_name = os.path.basename(file_path) if file_path else filename
    await xx.eor(get_string("udl_2").format(final_name, t))


@ultroid_cmd(
    pattern="ul( (.*)|$)",
)
async def upload_cmd(event):
    msg = await event.eor(get_string("com_1"))
    match = event.matches[0].group(1).strip() if event.matches else None
    
    if not event.outgoing and match == ".env":
        return await event.reply("`You can't do this...`")
        
    stream, force_doc, delete, thumb = False, True, False, ULTConfig.thumb
    
    if match:
        if "--stream" in match:
            stream = True
            force_doc = False
        if "--delete" in match:
            delete = True
        if "--no-thumb" in match:
            thumb = None
            
        for item in ["--stream", "--delete", "--no-thumb"]:
            match = match.replace(item, "")
        match = match.strip()
        
        if match.endswith("/"):
            match += "*"
            
    results = glob.glob(match) if match else []
    if not results and match and os.path.exists(match):
        results = [match]
        
    if not results:
        try:
            await event.reply_document(match)
            return await event.try_delete()
        except:
            pass
        return await msg.eor(get_string("ls1"))
        
    for result in results:
        if os.path.isdir(result):
            for files in get_all_files(result):
                await upload_process(event, msg, files, stream, force_doc, delete, thumb)
        else:
            await upload_process(event, msg, result, stream, force_doc, delete, thumb)
            
    await msg.try_delete()

async def upload_process(event, msg, file_path, stream, force_doc, delete, thumb):
    s_time = time.time()
    caption = f"`Uploaded` `{os.path.basename(file_path)}`"
    
    try:
        if force_doc:
            await event._client.send_document(
                event.chat.id,
                document=file_path,
                thumb=thumb,
                caption=caption,
                progress=progress,
                progress_args=(msg, s_time, f"Uploading {os.path.basename(file_path)}"),
                reply_to_message_id=event.reply_to_message_id
            )
        elif stream:
             # Guess type
             ext = os.path.splitext(file_path)[1].lower()
             if ext in [".mp4", ".mkv", ".webm"]:
                 await event._client.send_video(
                     event.chat.id,
                     video=file_path,
                     thumb=thumb,
                     caption=caption,
                     supports_streaming=True,
                     progress=progress,
                     progress_args=(msg, s_time, f"Uploading {os.path.basename(file_path)}"),
                     reply_to_message_id=event.reply_to_message_id
                 )
             elif ext in [".mp3", ".ogg", ".wav"]:
                 await event._client.send_audio(
                     event.chat.id,
                     audio=file_path,
                     thumb=thumb,
                     caption=caption,
                     progress=progress,
                     progress_args=(msg, s_time, f"Uploading {os.path.basename(file_path)}"),
                     reply_to_message_id=event.reply_to_message_id
                 )
             else:
                 await event._client.send_document(
                    event.chat.id,
                    document=file_path,
                    thumb=thumb,
                    caption=caption,
                    progress=progress,
                    progress_args=(msg, s_time, f"Uploading {os.path.basename(file_path)}"),
                    reply_to_message_id=event.reply_to_message_id
                )
        else:
             await event._client.send_document(
                event.chat.id,
                document=file_path,
                thumb=thumb,
                caption=caption,
                progress=progress,
                progress_args=(msg, s_time, f"Uploading {os.path.basename(file_path)}"),
                reply_to_message_id=event.reply_to_message_id
            )
            
        if delete:
            os.remove(file_path)
            
    except Exception as e:
        LOGS.exception(e)
        await msg.edit(f"Error uploading: {e}")
