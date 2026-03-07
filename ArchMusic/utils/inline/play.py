import random

from pyrogram.types import InlineKeyboardButton

selection = [
    "▁▄▂▇▄▅▄▅▃",
    "▁▃▇▂▅▇▄▅▃",
    "▃▁▇▂▅▃▄▃▅",
    "▃▄▂▄▇▅▃▅▁",
    "▁▃▄▂▇▃▄▅▃",
    "▃▁▄▂▅▃▇▃▅",
    "▁▇▄▂▅▄▅▃▄",
    "▁▃▅▇▂▅▄▃▇",
    "▃▅▂▅▇▁▄▃▁",
    "▇▅▂▅▃▄▃▁▃",
    "▃▇▂▅▁▅▄▃▁",
    "▅▄▇▂▅▂▄▇▁",
    "▃▅▂▅▃▇▄▅▃",
]

BAR_LENGTH = 15
FILLED = "█"
HALF = "▓"
EMPTY = "░"


def time_to_sec(time: str):
    x = time.split(":")
    if len(x) == 2:
        min = int(x[0])
        sec = int(x[1])
        total_sec = (min * 60) + sec
    elif len(x) == 3:
        hour = int(x[0])
        min = int(x[1])
        sec = int(x[2])
        total_sec = (hour * 60 * 60) + (min * 60) + sec
    else:
        total_sec = 0
    return total_sec


def build_progress_bar(played_sec, total_sec, length=BAR_LENGTH):
    if total_sec == 0:
        return EMPTY * length
    ratio = played_sec / total_sec
    filled_len = int(ratio * length)
    remainder = (ratio * length) - filled_len
    bar = FILLED * filled_len
    if filled_len < length:
        bar += HALF if remainder >= 0.5 else "⬤"
        bar += EMPTY * (length - filled_len - 1)
    return bar


def stream_markup_timer(_, videoid, chat_id, played, dur):
    played_sec = time_to_sec(played)
    total_sec = time_to_sec(dur)
    bar = build_progress_bar(played_sec, total_sec)
    percent = int((played_sec / total_sec) * 100) if total_sec else 0

    buttons = [
        [
            InlineKeyboardButton(
                text=f"⏱ {played} / {dur}",
                callback_data="GetTimer",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{bar} {percent}%",
                callback_data="GetTimer",
            )
        ],
        [
            InlineKeyboardButton(text="⏮", callback_data=f"ADMIN 3|{chat_id}"),
            InlineKeyboardButton(text="⏪", callback_data=f"ADMIN 1|{chat_id}"),
            InlineKeyboardButton(text="⏸", callback_data=f"ADMIN Pause|{chat_id}"),
            InlineKeyboardButton(text="⏩", callback_data=f"ADMIN 2|{chat_id}"),
            InlineKeyboardButton(text="⏭", callback_data=f"ADMIN Skip|{chat_id}"),
        ],
        [
            InlineKeyboardButton(text="▶️ Resume", callback_data=f"ADMIN Resume|{chat_id}"),
            InlineKeyboardButton(text="⏹ Stop", callback_data=f"ADMIN Stop|{chat_id}"),
        ],
        [
            InlineKeyboardButton(text="➕ Save", callback_data=f"add_playlist {videoid}"),
            InlineKeyboardButton(text="🎛 CPanel", callback_data=f"PanelMarkup None|{chat_id}"),
        ],
    ]
    return buttons


def telegram_markup_timer(_, chat_id, played, dur):
    played_sec = time_to_sec(played)
    total_sec = time_to_sec(dur)
    bar = build_progress_bar(played_sec, total_sec)
    percent = int((played_sec / total_sec) * 100) if total_sec else 0

    buttons = [
        [
            InlineKeyboardButton(
                text=f"⏱ {played} / {dur}",
                callback_data="GetTimer",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{bar} {percent}%",
                callback_data="GetTimer",
            )
        ],
        [
            InlineKeyboardButton(text="⏮", callback_data=f"ADMIN 3|{chat_id}"),
            InlineKeyboardButton(text="⏪", callback_data=f"ADMIN 1|{chat_id}"),
            InlineKeyboardButton(text="⏸", callback_data=f"ADMIN Pause|{chat_id}"),
            InlineKeyboardButton(text="⏩", callback_data=f"ADMIN 2|{chat_id}"),
            InlineKeyboardButton(text="⏭", callback_data=f"ADMIN Skip|{chat_id}"),
        ],
        [
            InlineKeyboardButton(text="▶️ Resume", callback_data=f"ADMIN Resume|{chat_id}"),
            InlineKeyboardButton(text="⏹ Stop", callback_data=f"ADMIN Stop|{chat_id}"),
        ],
        [
            InlineKeyboardButton(text="🎛 CPanel", callback_data=f"PanelMarkup None|{chat_id}"),
        ],
    ]
    return buttons


def stream_markup(_, videoid, chat_id):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["PL_B_2"],
                callback_data=f"add_playlist {videoid}",
            ),
            InlineKeyboardButton(
                text=_["PL_B_3"],
                callback_data=f"PanelMarkup None|{chat_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSEMENU_BUTTON"], callback_data="close"
            )
        ],
    ]
    return buttons


def telegram_markup(_, chat_id):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["PL_B_3"],
                callback_data=f"PanelMarkup None|{chat_id}",
            ),
            InlineKeyboardButton(
                text=_["CLOSEMENU_BUTTON"], callback_data="close"
            ),
        ],
    ]
    return buttons


def track_markup(_, videoid, user_id, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            )
        ],
    ]
    return buttons


def playlist_markup(_, videoid, user_id, ptype, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"ArchMusicPlaylists {videoid}|{user_id}|{ptype}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"ArchMusicPlaylists {videoid}|{user_id}|{ptype}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            ),
        ],
    ]
    return buttons


def livestream_markup(_, videoid, user_id, mode, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_3"],
                callback_data=f"LiveStream {videoid}|{user_id}|{mode}|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["CLOSEMENU_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            ),
        ],
    ]
    return buttons


def slider_markup(_, videoid, user_id, query, query_type, channel, fplay):
    query = f"{query[:20]}"
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="❮",
                callback_data=f"slider B|{query_type}|{query}|{user_id}|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {query}|{user_id}",
            ),
            InlineKeyboardButton(
                text="❯",
                callback_data=f"slider F|{query_type}|{query}|{user_id}|{channel}|{fplay}",
            ),
        ],
    ]
    return buttons


def panel_markup_1(_, videoid, chat_id):
    buttons = [
        [
            InlineKeyboardButton(
                text="⏸ Pause", callback_data=f"ADMIN Pause|{chat_id}"
            ),
            InlineKeyboardButton(
                text="▶️ Resume",
                callback_data=f"ADMIN Resume|{chat_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="⏯ Skip", callback_data=f"ADMIN Skip|{chat_id}"
            ),
            InlineKeyboardButton(
                text="⏹ Stop", callback_data=f"ADMIN Stop|{chat_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="◀️",
                callback_data=f"Pages Back|0|{videoid}|{chat_id}",
            ),
            InlineKeyboardButton(
                text="🔙 Back",
                callback_data=f"MainMarkup {videoid}|{chat_id}",
            ),
            InlineKeyboardButton(
                text="▶️",
                callback_data=f"Pages Forw|0|{videoid}|{chat_id}",
            ),
        ],
    ]
    return buttons


def panel_markup_2(_, videoid, chat_id):
    buttons = [
        [
            InlineKeyboardButton(
                text="🔇 Mute", callback_data=f"ADMIN Mute|{chat_id}"
            ),
            InlineKeyboardButton(
                text="🔊 Unmute",
                callback_data=f"ADMIN Unmute|{chat_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔀 Shuffle",
                callback_data=f"ADMIN Shuffle|{chat_id}",
            ),
            InlineKeyboardButton(
                text="🔁 Loop", callback_data=f"ADMIN Loop|{chat_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="◀️",
                callback_data=f"Pages Back|1|{videoid}|{chat_id}",
            ),
            InlineKeyboardButton(
                text="🔙 Back",
                callback_data=f"MainMarkup {videoid}|{chat_id}",
            ),
            InlineKeyboardButton(
                text="▶️",
                callback_data=f"Pages Forw|1|{videoid}|{chat_id}",
            ),
        ],
    ]
    return buttons


def panel_markup_3(_, videoid, chat_id):
    buttons = [
        [
            InlineKeyboardButton(
                text="⏮ 10 Seconds",
                callback_data=f"ADMIN 1|{chat_id}",
            ),
            InlineKeyboardButton(
                text="⏭ 10 Seconds",
                callback_data=f"ADMIN 2|{chat_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="⏮ 30 Seconds",
                callback_data=f"ADMIN 3|{chat_id}",
            ),
            InlineKeyboardButton(
                text="⏭ 30 Seconds",
                callback_data=f"ADMIN 4|{chat_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="◀️",
                callback_data=f"Pages Back|2|{videoid}|{chat_id}",
            ),
            InlineKeyboardButton(
                text="🔙 Back",
                callback_data=f"MainMarkup {videoid}|{chat_id}",
            ),
            InlineKeyboardButton(
                text="▶️",
                callback_data=f"Pages Forw|2|{videoid}|{chat_id}",
            ),
        ],
    ]
    return buttons
