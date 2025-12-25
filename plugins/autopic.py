# Ultroid - UserBot
# Copyright (C) 2021-2025 TeamUltroid
# Rewritten for Pyroblack by Gemini

import asyncio
import os
import random
from random import shuffle
import aiohttp
import re
from PIL import Image

from pyUltroid.fns.helper import fast_download
from . import LOGS, get_help, get_string, udB, ultroid_bot, ultroid_cmd

__doc__ = get_help("help_autopic")

async def get_google_images(query: str):
    # (Keep existing google images logic, it's generic python)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    search_url = f"https://www.google.com/search?q={query}&tbm=isch"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(search_url, headers=headers) as response:
                html = await response.text()
        img_urls = re.findall(r"https://[^\"]*?\.(?:jpg|jpeg|png|webp)", html)
        return list(set(img_urls))
    except Exception:
        return []

@ultroid_cmd(pattern="autopic( (.*)|$)")
async def autopic(e):
    search = e.matches[0].group(1).strip() if e.matches else None
    
    if udB.get_key("AUTOPIC") and not search:
        udB.del_key("AUTOPIC")
        return await e.eor(get_string("autopic_5"))
        
    if not search:
        return await e.eor(get_string("autopic_1"), time=5)
        
    e = await e.eor(get_string("com_1"))
    images = await get_google_images(search)
    
    if not images:
        return await e.eor(get_string("autopic_2").format(search), time=5)
        
    await e.eor(get_string("autopic_3").format(search))
    udB.set_key("AUTOPIC", search)
    
    SLEEP_TIME = udB.get_key("SLEEP_TIME") or 1221
    
    while True:
        # Check if stopped
        if udB.get_key("AUTOPIC") != search:
            break
            
        for lie in images:
            if udB.get_key("AUTOPIC") != search:
                return
                
            try:
                download_path, stime = await fast_download(lie, "resources/downloads/autopic.jpg")
                if not os.path.exists(download_path): continue
                
                # Pyrogram Set Profile Photo
                # set_profile_photo takes video or photo
                await e._client.set_profile_photo(photo=download_path)
                
                os.remove(download_path)
                await asyncio.sleep(SLEEP_TIME)
            except Exception as er:
                LOGS.error(er)
                await asyncio.sleep(60)

        shuffle(images)
