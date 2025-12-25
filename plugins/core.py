# Ultroid - UserBot
# Copyright (C) 2021-2025 TeamUltroid
# Rewritten for Pyroblack by Gemini

from . import get_help

__doc__ = get_help("help_core")

import os
from pyUltroid.startup.loader import load_addons
from . import LOGS, async_searcher, eod, get_string, safeinstall, ultroid_cmd, un_plug
from pyroblack.types import Message

@ultroid_cmd(pattern="install", fullsudo=True)
async def install(event: Message):
    # safeinstall must be adapted in helper.py to handle Pyrogram messages
    await safeinstall(event)


@ultroid_cmd(
    pattern=r"unload( (.*)|$)",
)
async def unload(event: Message):
    # In Pyrogram regex filters, matches are in event.matches
    try:
        shortname = event.matches[0].group(1).strip()
    except (IndexError, AttributeError):
        shortname = None
        
    if not shortname:
        await event.eor(get_string("core_9"))
        return
        
    lsd = os.listdir("addons")
    zym = f"{shortname}.py"
    
    if zym in lsd:
        try:
            un_plug(shortname)
            await event.eor(f"**Uɴʟᴏᴀᴅᴇᴅ** `{shortname}` **Sᴜᴄᴄᴇssғᴜʟʟʏ.**", time=3)
        except Exception as ex:
            LOGS.exception(ex)
            return await event.eor(str(ex))
    elif zym in os.listdir("plugins"):
        return await event.eor(get_string("core_11"), time=3)
    else:
        await event.eor(f"**Nᴏ Pʟᴜɢɪɴ Nᴀᴍᴇᴅ** `{shortname}`", time=3)


@ultroid_cmd(
    pattern=r"uninstall( (.*)|$)",
)
async def uninstall(event: Message):
    try:
        shortname = event.matches[0].group(1).strip()
    except (IndexError, AttributeError):
        shortname = None

    if not shortname:
        await event.eor(get_string("core_13"))
        return
        
    lsd = os.listdir("addons")
    zym = f"{shortname}.py"
    
    if zym in lsd:
        try:
            un_plug(shortname)
            await event.eor(f"**Uɴɪɴsᴛᴀʟʟᴇᴅ** `{shortname}` **Sᴜᴄᴄᴇssғᴜʟʟʏ.**", time=3)
            os.remove(f"addons/{shortname}.py")
        except Exception as ex:
            return await event.eor(str(ex))
    elif zym in os.listdir("plugins"):
        return await event.eor(get_string("core_15"), time=3)
    else:
        return await event.eor(f"**Nᴏ Pʟᴜɢɪɴ Nᴀᴍᴇᴅ** `{shortname}`", time=3)


@ultroid_cmd(
    pattern=r"load( (.*)|$)",
    fullsudo=True,
)
async def load(event: Message):
    try:
        shortname = event.matches[0].group(1).strip()
    except (IndexError, AttributeError):
        shortname = None

    if not shortname:
        await event.eor(get_string("core_16"))
        return
    try:
        try:
            un_plug(shortname)
        except BaseException:
            pass
        load_addons(f"addons/{shortname}.py")
        await event.eor(get_string("core_17").format(shortname), time=3)
    except Exception as e:
        LOGS.exception(e)
        await eod(
            event,
            get_string("core_18").format(shortname, e),
            time=3,
        )


@ultroid_cmd(pattern="getaddons( (.*)|$)", fullsudo=True)
async def get_the_addons_lol(event: Message):
    try:
        thelink = event.matches[0].group(1).strip()
    except (IndexError, AttributeError):
        thelink = None

    xx = await event.eor(get_string("com_1"))
    fool = get_string("gas_1")
    
    if thelink is None:
        return await xx.eor(fool, time=10)
        
    split_thelink = thelink.split("/")
    if not ("raw" in thelink and thelink.endswith(".py")):
        return await xx.eor(fool, time=10)
        
    name_of_it = split_thelink[-1]
    plug = await async_searcher(thelink)
    fil = f"addons/{name_of_it}"
    
    await xx.edit("Packing the codes...")
    with open(fil, "w", encoding="utf-8") as uult:
        uult.write(plug)
        
    await xx.edit("Packed. Now loading the plugin..")
    shortname = name_of_it.split(".")[0]
    
    try:
        load_addons(fil)
        await xx.eor(get_string("core_17").format(shortname), time=15)
    except Exception as e:
        LOGS.exception(e)
        await eod(
            xx,
            get_string("core_18").format(shortname, e),
            time=3,
        )
