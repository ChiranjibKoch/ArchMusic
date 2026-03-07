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
from random import randint
from typing import Union

from pyrogram.types import InlineKeyboardMarkup

import config
from ArchMusic import Carbon, YouTube, app
from ArchMusic.core.call import ArchMusic
from ArchMusic.misc import db
from ArchMusic.utils.database import (
    add_active_video_chat,
    is_active_chat,
    is_video_allowed,
    music_on,
)
from ArchMusic.utils.exceptions import AssistantErr
from ArchMusic.utils.formatters import time_to_seconds
from ArchMusic.utils.inline.play import stream_markup, telegram_markup
from ArchMusic.utils.inline.playlist import close_markup
from ArchMusic.utils.pastebin import ArchMusicbin
from ArchMusic.utils.stream.queue import put_queue, put_queue_index
from ArchMusic.utils.thumbnails import gen_thumb, gen_qthumb

_AUTO_QUEUE_LIMIT = 4


async def _auto_queue(chat_id, original_chat_id, title, user_id, video):
    try:
        for query_type in range(1, _AUTO_QUEUE_LIMIT + 1):
            try:
                aq_title, aq_dur, _, aq_vidid = await YouTube.slider(title, query_type)
            except Exception:
                continue
            if not aq_dur:
                continue
            try:
                if int(time_to_seconds(aq_dur)) > config.DURATION_LIMIT:
                    continue
            except Exception:
                continue
            await put_queue(
                chat_id,
                original_chat_id,
                f"vid_{aq_vidid}",
                aq_title,
                aq_dur,
                "AutoQueue",
                aq_vidid,
                user_id,
                "video" if video else "audio",
            )
    except Exception:
        pass


def _video_status(video):
    return True if video else None


async def stream(
    _,
    mystic,
    user_id,
    result,
    chat_id,
    user_name,
    original_chat_id,
    video: Union[bool, str] = None,
    streamtype: Union[bool, str] = None,
    spotify: Union[bool, str] = None,
    forceplay: Union[bool, str] = None,
):
    if not result:
        return
    if video:
        if not await is_video_allowed(chat_id):
            raise AssistantErr(_["play_7"])
    if forceplay:
        await ArchMusic.force_stop_stream(chat_id)

    if streamtype == "playlist":
        msg = f"{_['playlist_16']}\n\n"
        count = 0
        position = 0
        for search in result:
            if count == config.PLAYLIST_FETCH_LIMIT:
                continue
            try:
                title, duration_min, duration_sec, thumbnail, vidid = (
                    await YouTube.details(search, False if spotify else True)
                )
            except Exception:
                continue
            if str(duration_min) == "None":
                continue
            if duration_sec > config.DURATION_LIMIT:
                continue
            if await is_active_chat(chat_id):
                await put_queue(
                    chat_id,
                    original_chat_id,
                    f"vid_{vidid}",
                    title,
                    duration_min,
                    user_name,
                    vidid,
                    user_id,
                    "video" if video else "audio",
                )
                position = len(db.get(chat_id)) - 1
                count += 1
                msg += f"{count}- {title[:70]}\n"
                msg += f"{_['playlist_17']} {position}\n\n"
            else:
                if not forceplay:
                    db[chat_id] = []
                try:
                    if bool(video):
                        n, file_path = await YouTube.video(vidid, videoid=True)
                        if n == 0:
                            raise AssistantErr(_["play_16"])
                    else:
                        file_path = await YouTube.audio_stream(vidid, videoid=True)
                        if not file_path:
                            raise AssistantErr(_["play_16"])
                except AssistantErr:
                    raise
                except Exception:
                    raise AssistantErr(_["play_16"])
                await ArchMusic.join_call(
                    chat_id, original_chat_id, file_path, video=_video_status(video)
                )
                await put_queue(
                    chat_id,
                    original_chat_id,
                    file_path,
                    title,
                    duration_min,
                    user_name,
                    vidid,
                    user_id,
                    "video" if video else "audio",
                    forceplay=forceplay,
                )
                img = await gen_thumb(vidid)
                button = stream_markup(_, vidid, chat_id)
                run = await app.send_photo(
                    original_chat_id,
                    photo=img,
                    caption=_["stream_1"].format(
                        user_name,
                        f"https://t.me/{app.username}?start=info_{vidid}",
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"
                count += 1
                msg += f"{count}- {title[:70]}\n"
                msg += f"{_['playlist_17']} 0\n\n"
        if count == 0:
            return
        link = await ArchMusicbin(msg)
        lines = msg.count("\n")
        car = os.linesep.join(msg.split(os.linesep)[:17]) if lines >= 17 else msg
        carbon = await Carbon.generate(car, randint(100, 10000000))
        return await app.send_photo(
            original_chat_id,
            photo=carbon,
            caption=_["playlist_18"].format(link, position),
            reply_markup=close_markup(_),
        )

    elif streamtype == "youtube":
        vidid = result["vidid"]
        title = result["title"].title()
        duration_min = result["duration_min"]
        try:
            if bool(video):
                n, file_path = await YouTube.video(vidid, videoid=True)
                if n == 0:
                    raise AssistantErr(_["play_16"])
            else:
                file_path = await YouTube.audio_stream(vidid, videoid=True)
                if not file_path:
                    raise AssistantErr(_["play_16"])
        except AssistantErr:
            raise
        except Exception:
            raise AssistantErr(_["play_16"])
        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            img = await gen_qthumb(vidid)
            await app.send_photo(
                original_chat_id,
                photo=img,
                caption=_["queue_4"].format(position, title[:30], duration_min, user_name),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            await ArchMusic.join_call(
                chat_id, original_chat_id, file_path, video=_video_status(video)
            )
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
                forceplay=forceplay,
            )
            img = await gen_thumb(vidid)
            button = stream_markup(_, vidid, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=img,
                caption=_["stream_1"].format(
                    user_name,
                    f"https://t.me/{app.username}?start=info_{vidid}",
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"
            asyncio.create_task(
                _auto_queue(chat_id, original_chat_id, title, user_id, video)
            )

    elif streamtype == "soundcloud":
        file_path = result["filepath"]
        title = result["title"]
        duration_min = result["duration_min"]
        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "audio",
            )
            position = len(db.get(chat_id)) - 1
            await app.send_message(
                original_chat_id,
                _["queue_4"].format(position, title[:30], duration_min, user_name),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            await ArchMusic.join_call(chat_id, original_chat_id, file_path, video=None)
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "audio",
                forceplay=forceplay,
            )
            button = telegram_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=config.SOUNCLOUD_IMG_URL,
                caption=_["stream_3"].format(title, duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"

    elif streamtype == "telegram":
        file_path = result["path"]
        link = result["link"]
        title = result["title"].title()
        duration_min = result["dur"]
        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            await app.send_message(
                original_chat_id,
                _["queue_4"].format(position, title[:30], duration_min, user_name),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            await ArchMusic.join_call(
                chat_id, original_chat_id, file_path, video=_video_status(video)
            )
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "video" if video else "audio",
                forceplay=forceplay,
            )
            if video:
                await add_active_video_chat(chat_id)
            button = telegram_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=config.TELEGRAM_VIDEO_URL if video else config.TELEGRAM_AUDIO_URL,
                caption=_["stream_4"].format(title, link, duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"

    elif streamtype == "live":
        link = result["link"]
        vidid = result["vidid"]
        title = result["title"].title()
        duration_min = "Live Track"
        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                f"live_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            await app.send_message(
                original_chat_id,
                _["queue_4"].format(position, title[:30], duration_min, user_name),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            n, file_path = await YouTube.video(link)
            if n == 0:
                raise AssistantErr(_["str_3"])
            await ArchMusic.join_call(
                chat_id, original_chat_id, file_path, video=_video_status(video)
            )
            await put_queue(
                chat_id,
                original_chat_id,
                f"live_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
                forceplay=forceplay,
            )
            img = await gen_thumb(vidid)
            button = telegram_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=img,
                caption=_["stream_1"].format(
                    user_name,
                    f"https://t.me/{app.username}?start=info_{vidid}",
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"

    elif streamtype == "index":
        link = result
        title = "Index or M3u8 Link"
        duration_min = "URL stream"
        if await is_active_chat(chat_id):
            await put_queue_index(
                chat_id,
                original_chat_id,
                "index_url",
                title,
                duration_min,
                user_name,
                link,
                "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            await mystic.edit_text(
                _["queue_4"].format(position, title[:30], duration_min, user_name)
            )
        else:
            if not forceplay:
                db[chat_id] = []
            await ArchMusic.join_call(
                chat_id, original_chat_id, link, video=_video_status(video)
            )
            await put_queue_index(
                chat_id,
                original_chat_id,
                "index_url",
                title,
                duration_min,
                user_name,
                link,
                "video" if video else "audio",
                forceplay=forceplay,
            )
            button = telegram_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=config.STREAM_IMG_URL,
                caption=_["stream_2"].format(user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            await mystic.delete()
