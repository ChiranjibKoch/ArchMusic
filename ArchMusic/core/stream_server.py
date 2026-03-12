#
# Copyright (C) 2021-2023 by ArchBots@Github, < https://github.com/ArchBots >.
#
# This file is part of < https://github.com/ArchBots/ArchMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/ArchBots/ArchMusic/blob/master/LICENSE >
#
# All rights reserved.
#

import math

from aiohttp import web

import config

CHUNK_SIZE = 1024 * 1024


async def stream_handler(request):
    from ArchMusic import app

    chat_id = int(request.match_info["chat_id"])
    message_id = int(request.match_info["message_id"])

    message = await app.get_messages(chat_id, message_id)
    if not message:
        return web.Response(status=404)

    media = (
        message.audio
        or message.video
        or message.voice
        or message.document
        or message.video_note
    )
    if not media:
        return web.Response(status=404)

    file_size = media.file_size
    mime_type = getattr(media, "mime_type", None) or "application/octet-stream"

    range_header = request.headers.get("Range")

    if range_header:
        range_val = range_header.replace("bytes=", "")
        parts = range_val.split("-")
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if parts[1] else file_size - 1
        end = min(end, file_size - 1)
        length = end - start + 1

        offset = start // CHUNK_SIZE
        first_skip = start % CHUNK_SIZE
        chunks_needed = math.ceil((first_skip + length) / CHUNK_SIZE)

        async def ranged_body():
            sent = 0
            async for chunk in app.stream_media(message, offset=offset, limit=chunks_needed):
                if first_skip and sent == 0:
                    chunk = chunk[first_skip:]
                remaining = length - sent
                if len(chunk) > remaining:
                    chunk = chunk[:remaining]
                yield chunk
                sent += len(chunk)
                if sent >= length:
                    break

        return web.Response(
            body=ranged_body(),
            status=206,
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Content-Length": str(length),
                "Content-Type": mime_type,
                "Accept-Ranges": "bytes",
            },
        )

    async def full_body():
        async for chunk in app.stream_media(message):
            yield chunk

    return web.Response(
        body=full_body(),
        headers={
            "Content-Length": str(file_size),
            "Content-Type": mime_type,
            "Accept-Ranges": "bytes",
        },
    )


async def start_stream_server():
    try:
        server_app = web.Application()
        server_app.router.add_get("/stream/{chat_id}/{message_id}", stream_handler)
        runner = web.AppRunner(server_app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", config.PORT)
        await site.start()
    except Exception as e:
        from ArchMusic import LOGGER
        LOGGER("ArchMusic.stream_server").error(f"Failed to start stream server: {e}")
