# Ultroid - UserBot
# Copyright (C) 2021-2025 TeamUltroid
# Rewritten for Pyroblack by Gemini

import base64
import os
import random
import re
import string
from random import choice, randrange, shuffle
from catbox import CatboxUploader

from pyUltroid.exceptions import DependencyMissingError
from pyroblack import enums, types

from .. import *
from .._misc._wrappers import eor

if run_as_module:
    from ..dB import DEVLIST
    from ..dB._core import LIST

from . import some_random_headers
from .helper import async_searcher
from .tools import check_filename, json_parser

try:
    import aiohttp
except ImportError:
    aiohttp = None

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    import cv2
except ImportError:
    cv2 = None
try:
    import numpy as np
except ImportError:
    np = None

uploader = CatboxUploader()

async def randomchannel(tochat, channel, range1, range2, caption=None, client=ultroid_bot):
    do = randrange(range1, range2)
    # Pyrogram get_chat_history iteration
    try:
        # We assume offset works as skip count
        async for x in client.get_chat_history(channel, limit=1, offset=do):
             caption = caption or x.text or x.caption
             if x.media:
                 await x.copy(tochat, caption=caption)
             elif caption:
                 await client.send_message(tochat, caption)
    except BaseException:
        pass


async def YtDataScraper(url: str):
    to_return = {}
    data = json_parser(
        BeautifulSoup(
            await async_searcher(url),
            "html.parser",
        )
        .find_all("script")[41]
        .text[20:-1]
    )["contents"]
    _common_data = data["twoColumnWatchNextResults"]["results"]["results"]["contents"]
    common_data = _common_data[0]["videoPrimaryInfoRenderer"]
    try:
        description_data = _common_data[1]["videoSecondaryInfoRenderer"]["description"][
            "runs"
        ]
    except (KeyError, IndexError):
        description_data = [{"text": "No Description"}]
    description = "".join(
        description_datum["text"] for description_datum in description_data
    )
    to_return["title"] = common_data["title"]["runs"][0]["text"]
    to_return["views"] = (
        common_data["viewCount"]["videoViewCountRenderer"]["shortViewCount"][
            "simpleText"
        ]
        or common_data["viewCount"]["videoViewCountRenderer"]["viewCount"]["simpleText"]
    )
    to_return["publish_date"] = common_data["dateText"]["simpleText"]
    to_return["likes"] = (
        common_data["videoActions"]["menuRenderer"]["topLevelButtons"][0][
            "toggleButtonRenderer"
        ]["defaultText"]["simpleText"]
    )
    to_return["description"] = description
    return to_return


async def google_search(query):
    query = query.replace(" ", "+")
    _base = "https://google.com"
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "User-Agent": choice(some_random_headers),
    }
    con = await async_searcher(_base + "/search?q=" + query, headers=headers)
    soup = BeautifulSoup(con, "html.parser")
    result = []
    pdata = soup.find_all("a", href=re.compile("url="))
    for data in pdata:
        if not data.find("div"):
            continue
        try:
            result.append(
                {
                    "title": data.find("div").text,
                    "link": data["href"].split("&url=")[1].split("&ved=")[0],
                    "description": data.find_all("div")[-1].text,
                }
            )
        except BaseException as er:
            LOGS.exception(er)
    return result


async def allcmds(event, telegraph):
    txt = ""
    for z in LIST.keys():
        txt += f"PLUGIN NAME: {z}\n"
        for zz in LIST[z]:
            txt += HNDLR + zz + "\n"
        txt += "\n\n"
    t = telegraph.create_page(title="Ultroid All Cmds", content=[txt])
    await eor(event, f"All Ultroid Cmds : [Click Here]({t['url']})", link_preview=False)


async def ReTrieveFile(input_file_name):
    if not aiohttp:
        raise DependencyMissingError("This function needs 'aiohttp' to be installed.")
    RMBG_API = udB.get_key("RMBG_API")
    headers = {"X-API-Key": RMBG_API}
    files = {"image_file": open(input_file_name, "rb").read()}
    async with aiohttp.ClientSession() as ses:
        async with ses.post(
            "https://api.remove.bg/v1.0/removebg", headers=headers, data=files
        ) as out:
            contentType = out.headers.get("content-type")
            if "image" not in contentType:
                return False, (await out.json())

            name = check_filename("ult-rmbg.png")
            with open(name, "wb") as file:
                file.write(await out.read())
            return True, name


async def unsplashsearch(query, limit=None, shuf=True):
    query = query.replace(" ", "-")
    link = "https://unsplash.com/s/photos/" + query
    extra = await async_searcher(link, re_content=True)
    res = BeautifulSoup(extra, "html.parser", from_encoding="utf-8")
    all_ = res.find_all("img", srcset=re.compile("images.unsplash.com/photo"))
    if shuf:
        shuffle(all_)
    return list(map(lambda e: e['src'], all_[:limit]))


async def get_random_user_data():
    base_url = "https://randomuser.me/api/"
    cc = await async_searcher(
        "https://random-data-api.com/api/business_credit_card/random_card", re_json=True
    )
    card = (
        "**CARD_ID:** "
        + str(cc["credit_card_number"])
        + f" {cc['credit_card_expiry_date']}\n"
        + f"**C-ID :** {cc['id']}"
    )
    data_ = (await async_searcher(base_url, re_json=True))["results"][0]
    _g = data_["gender"]
    gender = "🤵🏻‍♂" if _g == "male" else "🤵🏻‍♀"
    name = data_["name"]
    loc = data_["location"]
    dob = data_["dob"]
    msg = """
{} **Name:** {}.{} {}
**Street:** {} {}
**City:** {}
**State:** {}
**Country:** {}
**Postal Code:** {}
**Email:** {}
**Phone:** {}
**Card:** {}
**Birthday:** {}
""".format(
        gender,
        name["title"],
        name["first"],
        name["last"],
        loc["street"]["number"],
        loc["street"]["name"],
        loc["city"],
        loc["state"],
        loc["country"],
        loc["postcode"],
        data_["email"],
        data_["phone"],
        card,
        dob["date"][:10],
    )
    pic = data_["picture"]["large"]
    return msg, pic


async def get_synonyms_or_antonyms(word, type_of_words):
    if type_of_words not in ["synonyms", "antonyms"]:
        return "Dude! Please give a corrent type of words you want."
    s = await async_searcher(
        f"https://tuna.thesaurus.com/pageData/{word}", re_json=True
    )
    li_1 = [
        y
        for x in [
            s["data"]["definitionData"]["definitions"][0][type_of_words],
            s["data"]["definitionData"]["definitions"][1][type_of_words],
        ]
        for y in x
    ]
    return [y["term"] for y in li_1]


class Quotly:
    _API = "https://quoteampi.onrender.com/generate"
    _entities = {
        enums.MessageEntityType.BOLD: "bold",
        enums.MessageEntityType.ITALIC: "italic",
        enums.MessageEntityType.UNDERLINE: "underline",
        enums.MessageEntityType.STRIKETHROUGH: "strikethrough",
        enums.MessageEntityType.SPOILER: "spoiler",
        enums.MessageEntityType.CODE: "code",
        enums.MessageEntityType.PRE: "pre",
        enums.MessageEntityType.TEXT_LINK: "text_link",
        enums.MessageEntityType.URL: "url",
        enums.MessageEntityType.MENTION: "mention",
        enums.MessageEntityType.HASHTAG: "hashtag",
        enums.MessageEntityType.CASHTAG: "cashtag",
        enums.MessageEntityType.BOT_COMMAND: "bot_command",
        enums.MessageEntityType.EMAIL: "email",
        enums.MessageEntityType.PHONE_NUMBER: "phone_number",
    }

    async def _format_quote(self, message: types.Message, reply=None, sender=None, type_="private"):
        user_id = message.from_user.id if message.from_user else 0
        name = message.from_user.first_name if message.from_user else "Deleted Account"
        last_name = message.from_user.last_name if message.from_user else None
        username = message.from_user.username if message.from_user else None
        title = name
        
        if message.sender_chat:
             user_id = message.sender_chat.id
             name = message.sender_chat.title
             title = name

        entities = []
        if message.entities:
            for entity in message.entities:
                if entity.type in self._entities:
                    entities.append({
                        "type": self._entities[entity.type],
                        "offset": entity.offset,
                        "length": entity.length,
                        "url": entity.url if entity.type == enums.MessageEntityType.TEXT_LINK else None
                    })

        text = message.text or message.caption or ""
        
        if message.service:
             text = f"Service Message: {message.service}"

        msg_json = {
            "entities": entities,
            "chatId": user_id,
            "avatar": True,
            "from": {
                "id": user_id,
                "first_name": name,
                "last_name": last_name,
                "username": username,
                "language_code": "en",
                "title": title,
                "name": name,
                "type": type_,
            },
            "text": text,
            "replyMessage": reply or {},
        }
        
        return msg_json

    async def create_quotly(
        self,
        event,
        url="https://bot.lyo.su/quote/generate",
        reply={},
        bg=None,
        sender=None,
        file_name="quote.webp",
    ):
        if not isinstance(event, list):
            event = [event]
            
        from .. import udB
        if udB.get_key("OQAPI"):
            url = Quotly._API
        if not bg:
            bg = "#1b1429"
            
        msgs = []
        for msg in event:
            formatted = await self._format_quote(msg, reply=reply, sender=sender)
            msgs.append(formatted)

        content = {
            "type": "quote",
            "format": "webp",
            "backgroundColor": bg,
            "width": 512,
            "height": 768,
            "scale": 2,
            "messages": msgs,
        }
        
        try:
            request = await async_searcher(url, post=True, json=content, re_json=True)
        except Exception as er:
            raise er
            
        if request.get("ok"):
            with open(file_name, "wb") as file:
                image = base64.decodebytes(request["result"]["image"].encode("utf-8"))
                file.write(image)
            return file_name
        raise Exception(str(request))


def split_list(List, index):
    new_ = []
    while List:
        new_.extend([List[:index]])
        List = List[index:]
    return new_


def rotate_image(image, angle):
    if not cv2:
        raise DependencyMissingError("This function needs 'cv2' to be installed!")
    image_center = tuple(np.array(image.shape[1::-1]) / 2)
    rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
    return cv2.warpAffine(image, rot_mat, image.shape[1::-1], flags=cv2.INTER_LINEAR)


def random_string(length=3):
    """Generate random string of 'n' Length"""
    return "".join(random.choices(string.ascii_uppercase, k=length))


setattr(random, "random_string", random_string)
