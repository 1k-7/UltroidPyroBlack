# Ultroid - UserBot
# Copyright (C) 2021-2025 TeamUltroid
# Rewritten for Pyroblack by Gemini

import json
import math
import os
import random
import re, subprocess
import secrets
import ssl, html
from io import BytesIO
from json.decoder import JSONDecodeError
from traceback import format_exc

import requests

from .. import *
from ..exceptions import DependencyMissingError
from . import some_random_headers
from .helper import async_searcher, bash, run_async

try:
    import certifi
except ImportError:
    certifi = None

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image, ImageDraw, ImageFont = None, None, None
    LOGS.info("PIL not installed!")

from urllib.parse import quote, unquote

# Replaced Telethon Types
from pyroblack.types import InlineKeyboardButton, InlineKeyboardMarkup

if run_as_module:
    from ..dB.filestore_db import get_stored_msg, store_msg

try:
    import numpy as np
except ImportError:
    np = None

try:
    from telegraph import Telegraph
except ImportError:
    Telegraph = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

# ~~~~~~~~~~~~~~~~~~~~OFOX API~~~~~~~~~~~~~~~~~~~~
async def get_ofox(codename):
    ofox_baseurl = "https://api.orangefox.download/v3/"
    releases = await async_searcher(
        ofox_baseurl + "releases?codename=" + codename, re_json=True
    )
    device = await async_searcher(
        ofox_baseurl + "devices/get?codename=" + codename, re_json=True
    )
    return device, releases

# ~~~~~~~~~~~~~~~JSON Parser~~~~~~~~~~~~~~~
def _unquote_text(text):
    return text.replace("'", unquote("%5C%27")).replace('"', unquote("%5C%22"))

def json_parser(data, indent=None, ascii=False):
    parsed = {}
    try:
        if isinstance(data, str):
            parsed = json.loads(str(data))
            if indent:
                parsed = json.dumps(
                    json.loads(str(data)), indent=indent, ensure_ascii=ascii
                )
        elif isinstance(data, dict):
            parsed = data
            if indent:
                parsed = json.dumps(data, indent=indent, ensure_ascii=ascii)
    except JSONDecodeError:
        parsed = eval(data)
    return parsed

# ~~~~~~~~~~~~~~~~Link Checker~~~~~~~~~~~~~~~~~
async def is_url_ok(url: str):
    try:
        return await async_searcher(url, head=True)
    except BaseException as er:
        LOGS.debug(er)
        return False

# ~~~~~~~~~~~~~~~~ Metadata ~~~~~~~~~~~~~~~~~~~~
async def metadata(file):
    out, _ = await bash(f'mediainfo "{_unquote_text(file)}" --Output=JSON')
    if _ and _.endswith("NOT_FOUND"):
        raise DependencyMissingError(
            f"'{_}' is not installed!\nInstall it to use this command."
        )
    
    data = {}
    try:
        _info = json.loads(out)["media"]
    except:
        return {}
        
    if not _info:
        return {}
    _info = _info["track"]
    info = _info[0]
    if info.get("Format") in ["GIF", "PNG"]:
        return {
            "height": _info[1]["Height"],
            "width": _info[1]["Width"],
            "bitrate": _info[1].get("BitRate", 320),
        }
    if info.get("AudioCount"):
        data["title"] = info.get("Title", file)
        data["performer"] = info.get("Performer") or udB.get_key("artist") or ""
    if info.get("VideoCount"):
        data["height"] = int(float(_info[1].get("Height", 720)))
        data["width"] = int(float(_info[1].get("Width", 1280)))
        data["bitrate"] = int(_info[1].get("BitRate", 320))
    data["duration"] = int(float(info.get("Duration", 0)))
    return data

# ~~~~~~~~~~~~~~~~ Attributes ~~~~~~~~~~~~~~~~
async def set_attributes(file):
    # Pyrogram detects attributes automatically.
    # Returns dictionary of attributes if needed to be unpacked into send_video etc.
    data = await metadata(file)
    if not data:
        return {}
    
    attributes = {}
    if "duration" in data:
        attributes["duration"] = data["duration"]
    if "width" in data:
        attributes["width"] = data["width"]
    if "height" in data:
        attributes["height"] = data["height"]
    if "title" in data:
        attributes["file_name"] = data["title"] # Pyrogram uses file_name often
        # Note: Pyrogram send_audio takes performer/title as kwargs
    if "performer" in data:
        attributes["performer"] = data["performer"]
        
    return attributes

# ~~~~~~~~~~~~~~~~ Button stuffs ~~~~~~~~~~~~~~~
def get_msg_button(texts: str):
    # Extracts text and button structure, returns InlineKeyboardMarkup compatible list
    btn_list = []
    # Regex to find [Button Text|Url]
    for z in re.findall("\\[(.*?)\\|(.*?)\\]", texts):
        text, url = z
        urls = url.split("|")
        url = urls[0].strip()
        # Only taking first url for simplicity, Pyrogram buttons are (text, url/callback)
        btn_list.append([InlineKeyboardButton(text, url=url)])

    txt = texts
    for z in re.findall("\\[.+?\\|.+?\\]", texts):
        txt = txt.replace(z, "")

    return txt.strip(), InlineKeyboardMarkup(btn_list) if btn_list else None

def create_tl_btn(button: list):
    # Convert list of lists to InlineKeyboardMarkup
    # Input format: [[('Text', 'url')], ...]
    keyboard = []
    for row in button:
        k_row = []
        if isinstance(row, list):
            for btn in row:
                if isinstance(btn, list) or isinstance(btn, tuple):
                     k_row.append(InlineKeyboardButton(text=btn[0], url=btn[1].strip()))
                elif isinstance(btn, InlineKeyboardButton):
                     k_row.append(btn)
        keyboard.append(k_row)
    return InlineKeyboardMarkup(keyboard)

def format_btn(buttons: list):
    # Reverse format: InlineKeyboardMarkup -> String representation
    txt = ""
    # This logic assumes buttons is a list of lists of InlineKeyboardButton
    if hasattr(buttons, 'inline_keyboard'):
        buttons = buttons.inline_keyboard
        
    for row in buttons:
        a = 0
        for btn in row:
            if hasattr(btn, "url") and btn.url:
                a += 1
                if a > 1:
                    txt += f"[{btn.text} | {btn.url} | same]"
                else:
                    txt += f"[{btn.text} | {btn.url}]"
            elif hasattr(btn, "callback_data") and btn.callback_data:
                 txt += f"[{btn.text} | {btn.callback_data}]" # Approx representation
    
    # Return extracted text and recreated markup (for consistency)
    text_out, markup_out = get_msg_button(txt)
    return markup_out

# ~~~~~~~~~~~~~~~Saavn Downloader~~~~~~~~~~~~~~~
async def saavn_search(query: str):
    try:
        data = await async_searcher(
            url=f"https://saavn-api.vercel.app/search/{query.replace(' ', '%20')}",
            re_json=True,
        )
    except BaseException:
        data = None
    return data

# --- webupload ------#
_webupload_cache = {}

async def webuploader(chat_id: int, msg_id: int, uploader: str):
    LOGS.info("webuploader function called with uploader: %s", uploader)
    if chat_id in _webupload_cache and msg_id in _webupload_cache[chat_id]:
        file = _webupload_cache[chat_id][msg_id]
    else:
        return "File not found in cache."

    sites = {
        "siasky": {"url": "https://siasky.net/skynet/skyfile", "json": True},
        "file.io": {"url": "https://file.io/", "json": True},
        "0x0.st": {"url": "https://0x0.st", "json": False},
        "transfer": {"url": "https://transfer.sh", "json": False},
        "catbox": {"url": "https://catbox.moe/user/api.php", "json": False},
        "filebin": {"url": "https://filebin.net", "json": False},
    }

    if uploader and uploader in sites:
        url = sites[uploader]["url"]
        json_format = sites[uploader]["json"]
    else:
        return "Uploader not supported or invalid."

    files = {"file": open(file, "rb")}

    try:
        if uploader == "filebin":
            cmd = f"curl -X POST --data-binary '@{file}' -H 'filename: \"{file}\"' \"{url}\""
            response = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if response.returncode == 0:
                try:
                    response_json = json.loads(response.stdout)
                    bin_id = response_json.get("bin", {}).get("id")
                    if bin_id:
                        return f"https://filebin.net/{bin_id}"
                except:
                    pass
                return "Failed to extract bin ID"
            else:
                return f"Failed to upload file to Filebin: {response.stderr.strip()}"
        elif uploader == "catbox":
            cmd = f"curl -F reqtype=fileupload -F time=24h -F 'fileToUpload=@{file}' {url}"
        elif uploader == "0x0.st":
            cmd = f"curl -F 'file=@{file}' {url}"
        elif uploader == "file.io" or uploader == "siasky":
            try:
                status = await async_searcher(
                    url, data=files, post=True, re_json=json_format
                )
            except Exception as e:
                return f"Failed to upload file: {e}"
            if isinstance(status, dict):
                if "skylink" in status:
                    return f"https://siasky.net/{status['skylink']}"
                if status.get("status") == 200:
                    return status.get("link")
        else:
            raise ValueError("Uploader not supported")

        response = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if response.returncode == 0:
            return response.stdout.strip()
        else:
            return f"Failed to upload file: {response.stderr.strip()}"
    except Exception as e:
        return f"Failed to upload file: {e}"

    del _webupload_cache.get(chat_id, {})[msg_id]
    return "Failed to get valid URL for the uploaded file."

def get_all_files(path, extension=None):
    filelist = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if not (extension and not file.endswith(extension)):
                filelist.append(os.path.join(root, file))
    return sorted(filelist)

def text_set(text):
    lines = []
    if len(text) <= 55:
        lines.append(text)
    else:
        all_lines = text.split("\n")
        for line in all_lines:
            if len(line) <= 55:
                lines.append(line)
            else:
                k = len(line) // 55
                for z in range(1, k + 2):
                    lines.append(line[((z - 1) * 55) : (z * 55)])
    return lines[:25]

class LogoHelper:
    @staticmethod
    def get_text_size(text, image, font):
        im = Image.new("RGB", (image.width, image.height))
        draw = ImageDraw.Draw(im)
        return draw.textlength(text, font)

    @staticmethod
    def find_font_size(text, font, image, target_width_ratio):
        tested_font_size = 100
        tested_font = ImageFont.truetype(font, tested_font_size)
        observed_width = LogoHelper.get_text_size(text, image, tested_font)
        estimated_font_size = (
            tested_font_size / (observed_width / image.width) * target_width_ratio
        )
        return round(estimated_font_size)

    @staticmethod
    def make_logo(imgpath, text, funt, **args):
        fill = args.get("fill")
        width_ratio = args.get("width_ratio") or 0.7
        stroke_width = int(args.get("stroke_width"))
        stroke_fill = args.get("stroke_fill")

        img = Image.open(imgpath)
        width, height = img.size
        fct = min(height, width)
        if height != width:
            img = img.crop((0, 0, fct, fct))
        if img.height < 1000:
            img = img.resize((1020, 1020))
        width, height = img.size
        draw = ImageDraw.Draw(img)
        font_size = LogoHelper.find_font_size(text, funt, img, width_ratio)
        font = ImageFont.truetype(funt, font_size)
        l, t, r, b = font.getbbox(text)
        w, h = r - l, (b - t) * 1.5
        draw.text(
            ((width - w) / 2, ((height - h) / 2)),
            text,
            font=font,
            fill=fill,
            stroke_width=stroke_width,
            stroke_fill=stroke_fill,
        )
        file_name = check_filename("logo.png")
        img.save(file_name, "PNG")
        return file_name

async def get_paste(data: str, extension: str = "txt"):
    try:
        url = "https://spaceb.in/api/"
        res = await async_searcher(url, json={"content": data, "extension": extension}, post=True, re_json=True)
        return True, {
            "link": f"https://spaceb.in/{res['payload']['id']}",
            "raw": f"https://spaceb.in/{res['payload']['id']}/raw"
        }
    except Exception:
        try:
            url = "https://dpaste.org/api/"
            data = {
                'format': 'json',
                'content': data.encode('utf-8'),
                'lexer': extension,
                'expires': '604800', 
            }
            res = await async_searcher(url, data=data, post=True, re_json=True)
            return True, {
                "link": res["url"],
                "raw": f'{res["url"]}/raw'
            }
        except Exception as e:
            LOGS.info(e)
            return None, {
                "link": None,
                "raw": None,
                "error": str(e)
            }

async def get_google_images(query):
    LOGS.info(f"Searching Google Images for: {query}")
    google_keys = [
        {"key": "AIzaSyAj75v6vHWLJdJaYcj44tLz7bdsrh2g7Y0", "cx": "712a54749d99a449e"},
        {"key": "AIzaSyDFQQwPLCzcJ9FDao-B7zDusBxk8GoZ0HY", "cx": "001bbd139705f44a6"},
        {"key": "AIzaSyD0sRNZUa8-0kq9LAREDAFKLNO1HPmikRU", "cx": "4717c609c54e24250"}
    ]
    key_index = random.randint(0, len(google_keys) - 1)
    GOOGLE_API_KEY = google_keys[key_index]["key"]
    GOOGLE_CX = google_keys[key_index]["cx"]
    try:
        url = (
            "https://www.googleapis.com/customsearch/v1"
            f"?q={quote(query)}"
            f"&cx={GOOGLE_CX}"
            f"&key={GOOGLE_API_KEY}"
            "&searchType=image"
            "&num=10"
        )
        response = await async_searcher(url, re_json=True)
        if not response or "items" not in response:
            LOGS.error("No results from Google Custom Search API")
            return []
            
        google_images = []
        for item in response["items"]:
            try:
                google_images.append({
                    "title": item.get("title", ""),
                    "link": item.get("contextLink", ""),
                    "source": item.get("displayLink", ""),
                    "thumbnail": item.get("image", {}).get("thumbnailLink", item["link"]),
                    "original": item["link"]
                })
            except Exception as e:
                LOGS.warning(f"Failed to process image result: {str(e)}")
                continue
                
        random.shuffle(google_images)
        return google_images
    except Exception as e:
        LOGS.exception(f"Error in get_google_images: {str(e)}")
        return []

async def get_chatbot_reply(message):
    chatbot_base = "https://api.safone.dev/chatbot?query={}"
    req_link = chatbot_base.format(message)
    try:
        return (await async_searcher(req_link, re_json=True)).get("response")
    except Exception:
        LOGS.info(f"**ERROR:**`{format_exc()}`")

def check_filename(filroid):
    if os.path.exists(filroid):
        no = 1
        while True:
            ult = "{0}_{2}{1}".format(*os.path.splitext(filroid) + (no,))
            if os.path.exists(ult):
                no += 1
            else:
                return ult
    return filroid

async def genss(file):
    return (await metadata(file)).get("duration", 0)

async def duration_s(file, stime):
    tsec = await genss(file)
    x = round(tsec / 5)
    y = round(tsec / 5 + int(stime))
    pin = stdr(x)
    pon = stdr(y) if y < tsec else stdr(tsec)
    return pin, pon

def stdr(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if len(str(minutes)) == 1:
        minutes = "0" + str(minutes)
    if len(str(hours)) == 1:
        hours = "0" + str(hours)
    if len(str(seconds)) == 1:
        seconds = "0" + str(seconds)
    return (
        ((str(hours) + ":") if hours else "00:")
        + ((str(minutes) + ":") if minutes else "00:")
        + ((str(seconds)) if seconds else "")
    )

def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

def four_point_transform(image, pts):
    try:
        import cv2
    except ImportError:
        raise DependencyMissingError("This function needs 'cv2' to be installed.")
    rect = order_points(pts)
    (tl, tr, br, bl) = rect
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))
    dst = np.array(
        [[0, 0], [maxWidth - 1, 0], [maxWidth - 1, maxHeight - 1], [0, maxHeight - 1]],
        dtype="float32",
    )
    M = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, M, (maxWidth, maxHeight))

TELEGRAPH = []

def telegraph_client():
    if not Telegraph:
        LOGS.info("'Telegraph' is not Installed!")
        return
    if TELEGRAPH:
        return TELEGRAPH[0]

    from .. import udB, ultroid_bot

    token = udB.get_key("_TELEGRAPH_TOKEN")
    TELEGRAPH_DOMAIN = udB.get_key("GRAPH_DOMAIN")
    TelegraphClient = Telegraph(token, domain=TELEGRAPH_DOMAIN or "graph.org")
    if token:
        TELEGRAPH.append(TelegraphClient)
        return TelegraphClient
    gd_name = ultroid_bot.full_name
    short_name = gd_name[:30]
    profile_url = (
        f"https://t.me/{ultroid_bot.me.username}"
        if ultroid_bot.me.username
        else "https://t.me/TeamUltroid"
    )
    try:
        TelegraphClient.create_account(
            short_name=short_name, author_name=gd_name, author_url=profile_url
        )
    except Exception as er:
        if "SHORT_NAME_TOO_LONG" in str(er):
            TelegraphClient.create_account(
                short_name="ultroiduser", author_name=gd_name, author_url=profile_url
            )
        else:
            LOGS.exception(er)
            return
    udB.set_key("_TELEGRAPH_TOKEN", TelegraphClient.get_access_token())
    TELEGRAPH.append(TelegraphClient)
    return TelegraphClient

@run_async
def make_html_telegraph(title, html=""):
    telegraph = telegraph_client()
    page = telegraph.create_page(
        title=title,
        html_content=html,
    )
    return page["url"]

async def Carbon(
    code,
    base_url="https://carbonara.solopov.dev/api/cook",
    file_name="ultroid",
    download=False,
    rayso=False,
    **kwargs,
):
    if rayso:
        base_url = "https://rayso-api-desvhu-33.koyeb.app/generate"
        kwargs["text"] = code
        kwargs["theme"] = kwargs.get("theme", "breeze")
        kwargs["darkMode"] = kwargs.get("darkMode", True)
        kwargs["title"] = kwargs.get("title", "Ultroid")
    else:
        kwargs["code"] = code
    con = await async_searcher(base_url, post=True, json=kwargs, re_content=True)
    if not download:
        file = BytesIO(con)
        file.name = file_name + ".jpg"
    else:
        try:
            return json_parser(con.decode())
        except Exception:
            pass
        file = file_name + ".jpg"
        with open(file, "wb") as f:
            f.write(con)
    return file

async def get_file_link(msg):
    # Adapted for Pyrogram
    from .. import udB
    
    # Forward the message to the log channel
    forwarded = await msg.forward(udB.get_key("LOG_CHANNEL"))
    await forwarded.reply_text(
        "**Message has been stored to generate a shareable link. Do not delete it.**"
    )
    
    msg_id = forwarded.id
    msg_hash = secrets.token_hex(nbytes=8)
    store_msg(msg_hash, msg_id)
    return msg_hash

async def get_stored_file(event, hash):
    from .. import udB, asst

    msg_id = get_stored_msg(hash)
    if not msg_id:
        return
    try:
        # Pyrogram: get_messages returns a list if list of IDs, or single if single ID
        msg = await asst.get_messages(udB.get_key("LOG_CHANNEL"), message_ids=msg_id)
    except Exception as er:
        LOGS.warning(f"FileStore, Error: {er}")
        return
    if not msg or msg.empty:
        return await event.reply(
            "__Message was deleted by owner!__"
        )
    
    # Copy message logic (Pyrogram copy_message)
    await msg.copy(event.chat.id, reply_to_message_id=event.id)

def translate(text, lang_tgt="en", lang_src="auto", timeout=60, detect=False):
    pattern = r'(?s)class="(?:t0|result-container)">(.*?)<'
    escaped_text = quote(text.encode("utf8"))
    url = "https://translate.google.com/m?tl=%s&sl=%s&q=%s" % (
        lang_tgt,
        lang_src,
        escaped_text,
    )
    response = requests.get(url, timeout=timeout).content
    result = response.decode("utf8")
    result = re.findall(pattern, result)
    if not result:
        return ""
    text = html.unescape(result[0])
    return (text, None) if detect else text

def cmd_regex_replace(cmd):
    return (
        cmd.replace("$", "")
        .replace("?(.*)", "")
        .replace("(.*)", "")
        .replace("(?: |)", "")
        .replace("| ", "")
        .replace("( |)", "")
        .replace("?((.|//)*)", "")
        .replace("?P<shortname>\\w+", "")
        .replace("(", "")
        .replace(")", "")
        .replace("?(\\d+)", "")
    )

class LottieException(Exception):
    ...

class TgConverter:
    # ... (TgConverter logic is largely file manipulation, mostly preserved)
    # ... (Just Ensure that attributes/types aren't Telethon specific)
    
    @staticmethod
    async def animated_sticker(file, out_path="sticker.tgs", throw=False, remove=False):
        # ... (Preserve logic)
        LOGS.info(f"Converting animated sticker: {file} -> {out_path}")
        try:
            if out_path.endswith("webp"):
                er, out = await bash(
                    f"lottie_convert.py --webp-quality 100 --webp-skip-frames 100 '{file}' '{out_path}'"
                )
            else:
                er, out = await bash(f"lottie_convert.py '{file}' '{out_path}'")
            
            if er:
                LOGS.error(f"Error in animated_sticker conversion: {er}")
                if throw:
                    raise LottieException(er)
            if remove and os.path.exists(file):
                os.remove(file)
            if os.path.exists(out_path):
                return out_path
            return None
        except Exception as e:
            if throw: raise
            return None

    @staticmethod
    async def animated_to_gif(file, out_path="gif.gif"):
        # ... (Preserve logic)
        try:
            er, out = await bash(
                f"lottie_convert.py '{_unquote_text(file)}' '{_unquote_text(out_path)}'"
            )
            if os.path.exists(out_path):
                return out_path
            return None
        except:
            return None

    @staticmethod
    def resize_photo_sticker(photo):
        # ... (Preserve PIL logic)
        try:
            image = Image.open(photo)
            if (image.width and image.height) < 512:
                size1 = image.width
                size2 = image.height
                if image.width > image.height:
                    scale = 512 / size1
                    size1new = 512
                    size2new = size2 * scale
                else:
                    scale = 512 / size2
                    size1new = size1 * scale
                    size2new = 512
                size1new = math.floor(size1new)
                size2new = math.floor(size2new)
                sizenew = (size1new, size2new)
                image = image.resize(sizenew)
            else:
                maxsize = (512, 512)
                image.thumbnail(maxsize)
            return image
        except:
            raise

    @staticmethod
    async def ffmpeg_convert(input_, output, remove=False):
        # ... (Preserve bash ffmpeg logic)
        if output.endswith(".webm"):
            return await TgConverter.create_webm(
                input_, name=output[:-5], remove=remove
            )
        if output.endswith(".gif"):
            out, er = await bash(f"ffmpeg -i '{input_}' -an -sn -c:v copy '{output}.mp4' -y")
        else:
            out, er = await bash(f"ffmpeg -i '{input_}' '{output}' -y")
        if remove and os.path.exists(input_):
            os.remove(input_)
        if os.path.exists(output):
            return output

    @staticmethod
    async def create_webm(file, name="video", remove=False):
        # ... (Preserve logic)
        try:
            _ = await metadata(file)
            name += ".webm"
            h, w = _["height"], _["width"]
            if h == w and h != 512:
                h, w = 512, 512
            if h != 512 or w != 512:
                if h > w:
                    h, w = 512, -1
                if w > h:
                    h, w = -1, 512
            await bash(
                f'ffmpeg -i "{file}" -preset fast -an -to 00:00:03 -crf 30 -bufsize 256k -b:v {_["bitrate"]} -vf "scale={w}:{h},fps=30" -c:v libvpx-vp9 "{name}" -y'
            )
            if remove and os.path.exists(file):
                os.remove(file)
            if os.path.exists(name):
                return name
            return None
        except:
            return None

    @staticmethod
    def to_image(input_, name, remove=False):
        # ... (Preserve logic)
        try:
            import cv2
            img = cv2.VideoCapture(input_)
            success, frame = img.read()
            if not success: return None
            cv2.imwrite(name, frame)
            img.release()
            if remove and os.path.exists(input_):
                os.remove(input_)
            return name
        except:
            return None

    @staticmethod
    async def convert(input_file, outname="converted", convert_to=None, allowed_formats=[], remove_old=True):
        # ... (Preserve logic, largely file type detection)
        if not input_file or not os.path.exists(input_file): return None
        if "." in input_file:
            ext = input_file.split(".")[-1].lower()
        else:
            return input_file

        if (ext in allowed_formats or ext == convert_to or not (convert_to or allowed_formats)):
            return input_file

        def recycle_type(exte):
            return convert_to == exte or exte in allowed_formats

        try:
            if ext == "tgs":
                for extn in ["webp", "json", "png", "mp4", "gif"]:
                    if recycle_type(extn):
                        name = outname + "." + extn
                        result = await TgConverter.animated_sticker(input_file, name, remove=remove_old)
                        if result: return result
                if recycle_type("webm"):
                    gif_file = await TgConverter.convert(input_file, convert_to="gif", remove_old=remove_old)
                    if gif_file:
                         return await TgConverter.create_webm(gif_file, outname, remove=True)
            elif ext == "json":
                if recycle_type("tgs"):
                    name = outname + ".tgs"
                    return await TgConverter.animated_sticker(input_file, name, remove=remove_old)
            elif ext in ["webm", "mp4", "gif"]:
                for exte in ["webm", "mp4", "gif"]:
                    if recycle_type(exte):
                        name = outname + "." + exte
                        result = await TgConverter.ffmpeg_convert(input_file, name, remove=remove_old)
                        if result: return result
                for exte in ["png", "jpg", "jpeg", "webp"]:
                    if recycle_type(exte):
                        name = outname + "." + exte
                        result = TgConverter.to_image(input_file, name, remove=remove_old)
                        if result: return result
            elif ext in ["jpg", "jpeg", "png", "webp"]:
                 for extn in ["png", "webp", "ico"]:
                    if recycle_type(extn):
                        img = Image.open(input_file)
                        name = outname + "." + extn
                        img.save(name, extn.upper())
                        if remove_old: os.remove(input_file)
                        return name
                 for extn in ["webm", "gif", "mp4"]:
                    if recycle_type(extn):
                        name = outname + "." + extn
                        if extn == "webm":
                            png_file = await TgConverter.convert(input_file, convert_to="png", remove_old=remove_old)
                            if png_file: return await TgConverter.ffmpeg_convert(png_file, name, remove=True)
                        else:
                            return await TgConverter.ffmpeg_convert(input_file, name, remove=remove_old)
        except Exception as e:
            LOGS.error(str(e))
            return None

def _get_value(stri):
    try:
        value = eval(stri.strip())
    except Exception as er:
        from .. import LOGS
        LOGS.debug(er)
        value = stri.strip()
    return value

def safe_load(file, *args, **kwargs):
    if isinstance(file, str):
        read = file.split("\n")
    else:
        read = file.readlines()
    out = {}
    for line in read:
        if ":" in line:
            spli = line.split(":", maxsplit=1)
            key = spli[0].strip()
            value = _get_value(spli[1])
            out.update({key: value or []})
        elif "-" in line:
            spli = line.split("-", maxsplit=1)
            where = out[list(out.keys())[-1]]
            if isinstance(where, list):
                value = _get_value(spli[1])
                if value:
                    where.append(value)
    return out

def get_chat_and_msgid(link):
    m = re.findall(r"t\.me\/(c\/)?([^\/]+)\/(\d+)", link)
    if m:
        is_channel, chat, msg_id = m[0]
        if is_channel:
            chat = int("-100" + chat)
        return chat, int(msg_id)

    m = re.findall(r"user_id=(\d+)&message_id=(\d+)", link)
    if m:
        return int(m[0][0]), int(m[0][1])

    return None, None
