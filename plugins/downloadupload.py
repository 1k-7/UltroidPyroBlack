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
    fast_download, # Assuming this helper still exists or adapted
    get_all_files,
    get_string,
    progress,
    ultroid_cmd,
)

# Pyrogram imports
from pyroblack import enums
from pyroblack.errors import MessageNotModified

@ultroid_cmd(
    pattern="download( (.*)|$)",
)
async def down(event):
    # Pyrogram match handling
    try:
        matched = event.matches[0].group(1).strip()
    except (IndexError, AttributeError):
        matched = None
        
    msg = await event.eor(get_string("udl_4"))
    
    if not matched:
        return await eor(msg, get_string("udl_5"), time=5)
        
    try:
        splited = matched.split(" | ")
        link = splited[0]
        filename = splited[1] if len(splited) > 1 else None
    except IndexError:
        filename = None
        
    s_time = time.time()
    try:
        # Using helper fast_download
        filename, d = await fast_download(
            link,
            filename,
            progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                progress(
                    d,
                    t,
                    msg,
                    s_time,
                    f"Downloading from {link}",
                )
            ),
        )
    except Exception as e: # InvalidURL catch generic
        return await msg.eor(f"`Error: {e}`", time=5)
        
    await msg.eor(f"`{filename}` `downloaded in {time_formatter(d*1000)}.`")


@ultroid_cmd(
    pattern="dl( (.*)|$)",
)
async def download(event):
    match = event.matches[0].group(1).strip() if event.matches else None
    
    ok = None
    if match and "t.me/" in match:
        chat, msg_id = get_chat_and_msgid(match)
        if not (chat and msg_id):
            return await event.eor(get_string("gms_1"))
        match = ""
        try:
            # Pyrogram get_messages takes chat_id and list of message_ids or single int
            ok = await event._client.get_messages(chat, message_ids=msg_id)
        except Exception as e:
            return await event.eor(f"Error fetching message: {e}")
    elif event.reply_to_message:
        ok = event.reply_to_message
    else:
        return await event.eor(get_string("cvt_3"), time=8)
        
    xx = await event.eor(get_string("com_1"))
    
    if not (ok and (ok.media or ok.document or ok.photo or ok.video or ok.audio or ok.voice)):
        return await xx.eor(get_string("udl_1"), time=5)
        
    s = dt.now()
    k = time.time()
    
    # Determine filename
    filename = match
    if not filename:
        if ok.document:
            filename = ok.document.file_name
        elif ok.audio:
            filename = ok.audio.file_name or f"audio_{dt.now().isoformat('_', 'seconds')}.ogg"
        elif ok.video:
            filename = ok.video.file_name or f"video_{dt.now().isoformat('_', 'seconds')}.mp4"
        elif ok.photo:
            filename = f"jpg_{dt.now().isoformat('_', 'seconds')}.jpg"
            
    if not filename:
         filename = f"file_{dt.now().isoformat('_', 'seconds')}"

    # Path
    path = f"resources/downloads/{filename}"
    
    try:
        # Pyrogram download_media
        file_path = await event._client.download_media(
            message=ok,
            file_name=path,
            progress=progress,
            progress_args=(xx, k, get_string("com_5"))
        )
    except Exception as err:
        return await xx.edit(f"Download Failed: {str(err)}")
        
    e = dt.now()
    t = time_formatter(((e - s).seconds) * 1000)
    
    # Extract just the name from path
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
        
    stream, force_doc, delete, thumb = (
        False,
        True,
        False,
        ULTConfig.thumb,
    )
    
    if match:
        if "--stream" in match:
            stream = True
            force_doc = False
        if "--delete" in match:
            delete = True
        if "--no-thumb" in match:
            thumb = None
            
        arguments = ["--stream", "--delete", "--no-thumb"]
        for item in arguments:
            match = match.replace(item, "")
        match = match.strip()
        
        if match.endswith("/"):
            match += "*"
            
    results = glob.glob(match) if match else []
    if not results and match and os.path.exists(match):
        results = [match]
        
    if not results:
        # Maybe text message or invalid path
        return await msg.eor(get_string("ls1"))
        
    for result in results:
        if os.path.isdir(result):
            for files in get_all_files(result):
                await upload_process(
                    event, msg, files, stream, force_doc, delete, thumb
                )
        else:
            await upload_process(
                event, msg, result, stream, force_doc, delete, thumb
            )
            
    await msg.try_delete()

async def upload_process(event, msg, file_path, stream, force_doc, delete, thumb):
    s_time = time.time()
    attributes = []
    
    # In Pyrogram, send_video/audio handles attributes mostly automatically
    # but we can pass duration/width/height if known
    if stream:
        try:
            # set_attributes helper returns dict, need to adapt for Pyrogram
            # Pyrogram send methods take kwargs
            attrs = await set_attributes(file_path)
            # We'll use these attrs in send_file logic
        except Exception as er:
            LOGS.exception(er)

    # Fast Upload (returns InputFile)
    # Using client.save_file or just passing path to send method? 
    # Passing path to send method allows Pyrogram to handle parallel upload.
    # But if we want progress on the 'upload' specifically before 'sending':
    
    # We will simply use send_document/video with progress
    
    caption = f"`Uploaded` `{os.path.basename(file_path)}`"
    
    try:
        # Determine method
        # Force doc overrides everything
        if force_doc:
            await event._client.send_document(
                event.chat.id,
                document=file_path,
                thumb=thumb,
                caption=caption,
                progress=progress,
                progress_args=(msg, s_time, f"Uploading {os.path.basename(file_path)}"),
                reply_to_message_id=event.reply_to_message_id or event.id
            )
        elif stream:
             # Try to guess video/audio
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
                     reply_to_message_id=event.reply_to_message_id or event.id
                 )
             elif ext in [".mp3", ".ogg", ".wav"]:
                 await event._client.send_audio(
                     event.chat.id,
                     audio=file_path,
                     thumb=thumb,
                     caption=caption,
                     progress=progress,
                     progress_args=(msg, s_time, f"Uploading {os.path.basename(file_path)}"),
                     reply_to_message_id=event.reply_to_message_id or event.id
                 )
             else:
                 # Fallback
                 await event._client.send_document(
                    event.chat.id,
                    document=file_path,
                    thumb=thumb,
                    caption=caption,
                    progress=progress,
                    progress_args=(msg, s_time, f"Uploading {os.path.basename(file_path)}"),
                    reply_to_message_id=event.reply_to_message_id or event.id
                )
        else:
             # Default generic send
             await event._client.send_document(
                event.chat.id,
                document=file_path,
                thumb=thumb,
                caption=caption,
                progress=progress,
                progress_args=(msg, s_time, f"Uploading {os.path.basename(file_path)}"),
                reply_to_message_id=event.reply_to_message_id or event.id
            )
            
        if delete:
            os.remove(file_path)
            
    except Exception as e:
        LOGS.exception(e)
        await msg.edit(f"Error uploading {os.path.basename(file_path)}: {e}")
