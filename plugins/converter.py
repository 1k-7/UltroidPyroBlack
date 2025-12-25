# Ultroid - UserBot
# Copyright (C) 2021-2025 TeamUltroid
# Rewritten for Pyroblack by Gemini

from . import get_help

__doc__ = get_help("help_converter")

import os
import time

from . import LOGS, ULTConfig, bash
from . import eor, get_paste, get_string, udB, ultroid_cmd
from pyUltroid.fns.tools import TgConverter as con
from pyUltroid.fns.FastTelethon import upload_file as uf 

@ultroid_cmd(
    pattern="thumbnail$",
)
async def _(e):
    r = e.reply_to_message
    if not r:
        return await e.eor("`Reply to Photo or media with thumb...`")
        
    if r.photo or (r.document and r.document.thumbs):
        dl = await r.download(file_name="resources/downloads/thumb_dl.jpg")
    else:
        return await e.eor("`Reply to Photo or media with thumb...`")
        
    # uf is FastTelethon wrapper, likely compatible if rewrote
    # But for thumb, we just set path
    udB.set_key("CUSTOM_THUMBNAIL", str(dl))
    # Backup to resources
    await bash(f"cp {dl} resources/extras/ultroid.jpg")
    await e.eor(f"Thumbnail Saved.", link_preview=False)


@ultroid_cmd(
    pattern="rename( (.*)|$)",
)
async def imak(event):
    reply = event.reply_to_message
    if not reply:
        return await event.eor(get_string("cvt_1"))
        
    inp = event.matches[0].group(1).strip() if event.matches else None
    if not inp:
        return await event.eor(get_string("cvt_2"))
        
    xx = await event.eor(get_string("com_1"))
    
    # Download
    try:
        file = await reply.download(file_name=f"resources/downloads/{inp}")
    except Exception as er:
        return await xx.edit(f"Download Error: {er}")
        
    if not file:
        return await xx.edit("Download Failed.")

    # Upload
    try:
        await event.reply_document(
            document=file,
            force_document=True,
            thumb=ULTConfig.thumb,
            caption=f"`{inp}`"
        )
    except Exception as er:
        await xx.edit(f"Upload Error: {er}")
    
    if os.path.exists(file):
        os.remove(file)
    await xx.delete()


conv_keys = {
    "img": "png",
    "sticker": "webp",
    "webp": "webp",
    "image": "png",
    "webm": "webm",
    "gif": "gif",
    "json": "json",
    "tgs": "tgs",
}


@ultroid_cmd(
    pattern="convert( (.*)|$)",
)
async def uconverter(event):
    xx = await event.eor(get_string("com_1"))
    a = event.reply_to_message
    if a is None:
        return await event.eor("`Reply to Photo or media...`")
        
    input_ = event.matches[0].group(1).strip() if event.matches else None
    
    b = await a.download(file_name="resources/downloads/")
    
    if not b:
        return await xx.edit(get_string("cvt_3"))
        
    try:
        convert = conv_keys.get(input_, "png") # Default png
    except KeyError:
        return await xx.edit(get_string("sts_3").format("gif/img/sticker/webm"))
        
    # Using TgConverter (con)
    file = await con.convert(b, outname="resources/downloads/ultroid", convert_to=convert)

    if file and os.path.exists(file):
        await event.reply_document(
            document=file,
            quote=True
        )
        os.remove(file)
    else:
        await xx.edit("`Failed to convert`")
        return
        
    if os.path.exists(b):
        os.remove(b)
    await xx.delete()

@ultroid_cmd(
    pattern="doc( (.*)|$)",
)
async def _(event):
    input_str = event.matches[0].group(1).strip() if event.matches else "message.txt"
    if not event.reply_to_message:
        return await event.eor(get_string("cvt_1"), time=5)
        
    xx = await event.eor(get_string("com_1"))
    a = event.reply_to_message
    
    content = a.text or a.caption or str(a)
    
    with open(input_str, "w", encoding="utf-8") as b:
        b.write(content)
        
    await xx.edit(f"**Packing into** `{input_str}`")
    await event.reply_document(
        document=input_str, 
        thumb=ULTConfig.thumb
    )
    await xx.delete()
    os.remove(input_str)


@ultroid_cmd(
    pattern="open( (.*)|$)",
)
async def _(event):
    a = event.reply_to_message
    b = event.matches[0].group(1).strip() if event.matches else None
    
    if not ((a and (a.document or a.photo)) or (b and os.path.exists(b))):
        return await event.eor(get_string("cvt_7"), time=5)
        
    xx = await event.eor(get_string("com_1"))
    rem = False
    
    if not b and a:
        b = await a.download()
        rem = True
        
    try:
        with open(b, "r", encoding="utf-8", errors="ignore") as c:
            d = c.read()
    except Exception:
        return await xx.eor(get_string("cvt_8"), time=5)
        
    if len(d) > 4000:
        what, data = await get_paste(d)
        await xx.edit(
            f"**MESSAGE EXCEEDS TELEGRAM LIMITS**\n\nSo Pasted It On [SPACEBIN]({data['link']})"
        )
    else:
        await xx.edit(f"```{d}```")
        
    if rem and os.path.exists(b):
        os.remove(b)
