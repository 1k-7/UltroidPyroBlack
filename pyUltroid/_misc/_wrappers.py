# Ultroid - UserBot
# Copyright (C) 2021-2025 TeamUltroid
# Rewritten for Pyroblack by Gemini

from asyncio import sleep
from pyroblack.types import Message
from pyroblack import errors

async def eor(self, text=None, time=None, link_preview=None, edit_time=None, **args):
    """
    Edit or Reply wrapper for Pyrogram.
    If message is outgoing (from me), edit it.
    If message is incoming, reply to it.
    """
    
    disable_web_page_preview = not link_preview if link_preview is not None else None
    
    if edit_time:
        await sleep(edit_time)
        
    is_outgoing = self.outgoing or (self.from_user and self.from_user.is_self)
    
    ok = None
    try:
        if is_outgoing:
            if args.get("file"):
                # If wanting to send a file, we can't edit a text message into a file in TG
                await self.delete()
                # Remove file/text from args to avoid duplication if passed
                file_to_send = args.pop("file")
                caption = text
                # We need to guess the method based on file type or use send_document as generic
                # For simplicity, using reply_document (Pyrogram handles file paths smart)
                ok = await self.reply_document(document=file_to_send, caption=caption, **args)
            else:
                ok = await self.edit_text(
                    text, 
                    disable_web_page_preview=disable_web_page_preview,
                    **args
                )
        else:
            ok = await self.reply_text(
                text, 
                disable_web_page_preview=disable_web_page_preview, 
                quote=True, 
                **args
            )
    except errors.MessageNotModified:
        ok = self
    except Exception as e:
        # Fallback if edit fails (e.g. too old), reply instead
        try:
             ok = await self.reply_text(text, disable_web_page_preview=disable_web_page_preview, **args)
        except:
             pass

    if time and ok:
        await sleep(time)
        await ok.delete()
        
    return ok

async def eod(self, text=None, **kwargs):
    kwargs["time"] = kwargs.get("time", 8)
    return await self.eor(text, **kwargs)

async def _try_delete(self):
    try:
        await self.delete()
    except:
        pass

# Monkey Patch Pyrogram Message
Message.eor = eor
Message.eod = eod
Message.try_delete = _try_delete
