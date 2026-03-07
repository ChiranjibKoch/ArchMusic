#
# Copyright (C) 2021-2026 by ArchBots@Github, < https://github.com/ArchBots >.
#
# This file is part of < https://github.com/ArchBots/ArchMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/ArchBots/ArchMusic/blob/master/LICENSE >
#
# All rights reserved.

import httpx
from youtubesearchpython.core.requests import RequestCore
from youtubesearchpython.core.constants import userAgent


def _init_no_proxy(self):
    self.url = None
    self.data = None
    self.timeout = 2


def _sync_post(self) -> httpx.Response:
    return httpx.post(
        self.url,
        headers={"User-Agent": userAgent},
        json=self.data,
        timeout=self.timeout,
    )


async def _async_post(self) -> httpx.Response:
    async with httpx.AsyncClient() as client:
        return await client.post(
            self.url,
            headers={"User-Agent": userAgent},
            json=self.data,
            timeout=self.timeout,
        )


def _sync_get(self) -> httpx.Response:
    return httpx.get(
        self.url,
        headers={"User-Agent": userAgent},
        timeout=self.timeout,
        cookies={"CONSENT": "YES+1"},
    )


async def _async_get(self) -> httpx.Response:
    async with httpx.AsyncClient() as client:
        return await client.get(
            self.url,
            headers={"User-Agent": userAgent},
            timeout=self.timeout,
            cookies={"CONSENT": "YES+1"},
        )


RequestCore.__init__ = _init_no_proxy
RequestCore.syncPostRequest = _sync_post
RequestCore.asyncPostRequest = _async_post
RequestCore.syncGetRequest = _sync_get
RequestCore.asyncGetRequest = _async_get

from ArchMusic.core.bot import ArchMusic
from ArchMusic.core.dir import dirr
from ArchMusic.core.git import git
from ArchMusic.core.userbot import Userbot
from ArchMusic.misc import dbb, heroku, sudo

from .logging import LOGGER

dirr()
git()
dbb()
heroku()
sudo()

app = ArchMusic()
userbot = Userbot()

from .platforms import *

YouTube = YouTubeAPI()
Carbon = CarbonAPI()
Spotify = SpotifyAPI()
Apple = AppleAPI()
Resso = RessoAPI()
SoundCloud = SoundAPI()
Telegram = TeleAPI()
