#
# Copyright (C) 2021-2023 by ArchBots@Github, < https://github.com/ArchBots >.
#
# This file is part of < https://github.com/ArchBots/ArchMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/ArchBots/ArchMusic/blob/master/LICENSE >
#
# All rights reserved.
#

import asyncio
import os
import re
import shlex
from typing import Union

import aiofiles
import aiohttp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from yt_dlp import YoutubeDL
from youtubesearchpython.__future__ import VideosSearch

from ArchMusic.utils.formatters import time_to_seconds

_COOKIES_FILE = "assets/cookies.txt"

_COMMON_OPTS = {
    "geo_bypass": True,
    "nocheckcertificate": True,
    "quiet": True,
    "no_warnings": True,
    "extractor_retries": 1,
    "socket_timeout": 5,
}

_THUMB_RESOLUTIONS = ["maxresdefault", "sddefault", "hqdefault", "mqdefault", "default"]


def _cookies_opts() -> dict:
    if os.path.isfile(_COOKIES_FILE):
        return {"cookiefile": _COOKIES_FILE}
    return {}


async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    if errorz:
        if "unavailable videos are hidden" in errorz.decode("utf-8").lower():
            return out.decode("utf-8")
        else:
            return errorz.decode("utf-8")
    return out.decode("utf-8")


async def _cdn_url(link: str, fmt: str) -> str | None:
    args = [
        "yt-dlp", "-g",
        "-f", fmt,
        "--format-sort", "res,fps,tbr",
        "--no-playlist",
    ]
    if os.path.isfile(_COOKIES_FILE):
        args += ["--cookies", _COOKIES_FILE]
    args.append(link)
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    if stdout:
        url = stdout.decode().strip().split("\n")[0]
        if url:
            return url
    return None


async def _fetch_thumbnail(videoid: str) -> str:
    path = f"cache/thumb{videoid}.jpg"
    if os.path.isfile(path):
        return path
    async with aiohttp.ClientSession() as session:
        for res in _THUMB_RESOLUTIONS:
            url = f"https://img.youtube.com/vi/{videoid}/{res}.jpg"
            async with session.get(url) as resp:
                if resp.status == 200:
                    content = await resp.read()
                    if len(content) > 2000:
                        async with aiofiles.open(path, "wb") as f:
                            await f.write(content)
                        return path
    return ""


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if re.search(self.regex, link):
            return True
        else:
            return False

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        text = ""
        offset = None
        length = None
        for message in messages:
            if offset:
                break
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        offset, length = entity.offset, entity.length
                        break
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        if offset in (None,):
            return None
        return text[offset : offset + length]

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
            if str(duration_min) == "None":
                duration_sec = 0
            else:
                duration_sec = int(time_to_seconds(duration_min))
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
        return title

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            duration = result["duration"]
        return duration

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        return thumbnail

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            vidid = result["id"]
            yturl = result["link"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        track_details = {
            "title": title,
            "link": yturl,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }
        return track_details, vidid

    async def slider(
        self,
        link: str,
        query_type: int,
        videoid: Union[bool, str] = None,
    ):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        a = VideosSearch(link, limit=10)
        result = (await a.next()).get("result")
        title = result[query_type]["title"]
        duration_min = result[query_type]["duration"]
        vidid = result[query_type]["id"]
        thumbnail = result[query_type]["thumbnails"][0]["url"].split("?")[0]
        return title, duration_min, thumbnail, vidid

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        cookies_part = f"--cookies {shlex.quote(_COOKIES_FILE)}" if os.path.isfile(_COOKIES_FILE) else ""
        playlist = await shell_cmd(
            f"yt-dlp -i --get-id --flat-playlist --playlist-end {limit} --skip-download {cookies_part} {shlex.quote(link)}"
        )
        try:
            result = playlist.split("\n")
            result = [x for x in result if x != ""]
        except Exception:
            result = []
        return result

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        url = await _cdn_url(link, "bestvideo+bestaudio/bestvideo/best")
        return (1, url) if url else (0, "Failed to fetch video URL")

    async def audio_stream(self, link: str, videoid: Union[bool, str] = None) -> str | None:
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        return await _cdn_url(link, "bestaudio/best")

    async def thumbnail_download(self, videoid: str) -> str:
        return await _fetch_thumbnail(videoid)

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        ydl_opts = {**_COMMON_OPTS, **_cookies_opts()}
        ydl = YoutubeDL(ydl_opts)
        with ydl:
            r = ydl.extract_info(link, download=False)
        is_live = bool(r.get("is_live") or r.get("was_live"))
        audio_formats = []
        video_formats = []
        for fmt in r.get("formats", []):
            if not fmt.get("format_id") or not fmt.get("ext"):
                continue
            if fmt.get("ext") == "mhtml":
                continue
            format_note = fmt.get("format_note") or ""
            if "storyboard" in format_note:
                continue
            format_str = fmt.get("format") or ""
            if not is_live and ("dash" in format_str.lower() or "dash" in format_note.lower()):
                continue
            vcodec = fmt.get("vcodec") or "none"
            acodec = fmt.get("acodec") or "none"
            has_v = vcodec != "none"
            has_a = acodec != "none"
            if has_a and not has_v:
                stream_type = "audio"
            elif has_v and not has_a:
                stream_type = "video"
            elif has_v and has_a:
                stream_type = "audio+video"
            else:
                continue
            filesize = fmt.get("filesize") or fmt.get("filesize_approx")
            entry = {
                "format": format_str,
                "filesize": filesize,
                "format_id": fmt["format_id"],
                "ext": fmt["ext"],
                "format_note": format_note,
                "stream_type": stream_type,
                "is_live": is_live,
                "yturl": link,
            }
            if stream_type == "audio":
                audio_formats.append(entry)
            else:
                video_formats.append(entry)
        if not audio_formats and video_formats:
            audio_formats = [video_formats[0]]
        return audio_formats + video_formats, link
