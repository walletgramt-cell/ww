from aiogram.fsm.context import FSMContext
import asyncio
import logging
logging.getLogger("aiogram.dispatcher").setLevel(logging.WARNING)
logging.getLogger("aiogram.event").setLevel(logging.WARNING)
import os
import sqlite3
import socket
import time
import aiohttp
import html
import hashlib
import secrets
import re
import subprocess
from pathlib import Path as FsPath
from datetime import datetime, timezone

from aiogram import Bot, Dispatcher, F
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    LabeledPrice, PreCheckoutQuery, ErrorEvent, ReactionTypeEmoji,
    KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, ChatMemberUpdated, FSInputFile
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
try:
    from aiogram.types import KeyboardButtonRequestManagedBot
except ImportError:
    KeyboardButtonRequestManagedBot = None
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError, TelegramNetworkError

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = 7544486326  # основной администратор
ADMIN_IDS = {ADMIN_ID} | {int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()}

DB_PATH = os.getenv("DB_PATH", "gifts_bot.sqlite3")
MAIN_DB_PATH = os.getenv("WINESWORK_MAIN_DB_PATH", DB_PATH)
CHILD_MODE = os.getenv("WINESWORK_CHILD", "0") == "1"
CHILD_BOT_NAME = os.getenv("WINESWORK_CHILD_NAME", "")
PARTNER_DIR = FsPath(os.getenv("WINESWORK_PARTNER_DIR", ".wineswork_partners"))
WELCOME_PHOTO = FsPath(os.getenv("WINESWORK_WELCOME_PHOTO", str(FsPath(__file__).with_name("welcome.jpg"))))

REQUIRED_CHANNELS = [
    ("@wwlobby", "wwlobby"),
    ("@LonixGram", "LonixGram"),
    ("@ListStudio", "ListStudio"),
]
SUPPORT_URL = "https://t.me/mevance"

# Premium/Custom Emoji IDs для оформления WinesWork.
# Название набора в исходнике намеренно не указывается.
PREMIUM_EMOJI_IDS = {
    "plane": "6028346797368283073",
    "apple": "5775870512127283512",
    "star1": "6028338546736107668",
    "star2": "5767199127775481841",
    "gift": "5773677501825945508",
    "symbols": "6035162669948867129",
    "desktop": "5942734685976138521",
    "gear1": "5904258298764334001",
    "gear2": "6032742198179532882",
    "gear3": "5850309953293653168",
    "gear4": "5850332476102153487",
    "gear5": "5850392884817172292",
    "gear6": "5850224242926295392",
    "gear7": "5924722061288150929",
    "controls1": "5776424837786374634",
    "controls2": "5771449289972650710",
    "news1": "5895519358871932592",
    "news2": "5893444447286334441",
    "news3": "5886437972647088483",
    "news4": "5893236738372932548",
    "news5": "5893057118545646106",
    "note1": "5920046907782074235",
    "note2": "5922693616953725714",
    "folder1": "5766994197705921104",
    "swap1": "5893316448670978477",
    "swap2": "5895534923833413814",
    "left1": "5960671702059848143",
    "repeat": "6030657343744644592",
    "up_double": "5938437708635443119",
    "pencil1": "6039779802741739617",
    "pencil2": "6039614175917903752",
    "cross1": "6030757850274336631",
    "keyboard": "6039404727542747508",
    "paperclip": "6039451237743595514",
    "wrench": "5962952497197748583",
    "hammer": "5940433880585605708",
    "door": "6035130900075777681",
    "search": "6032850693348399258",
    "tag1": "5888620056551625531",
    "tag2": "5886285355279193209",
    "tag3": "5884050696679986441",
    "tag4": "5884090188904272855",
    "tag5": "5886473311637999700",
    "tag6": "5888880224195581055",
    "tag7": "5884491244360438851",
    "return": "5895507195524550741",
    "left2": "6039539366177541657",
    "right1": "5895383238473421210",
    "right2": "6037622221625626773",
    "tv": "6039391078136681499",
    "link1": "6028171274939797252",
    "link2": "6030864215139422409",
    "link3": "5776078972659962594",
    "link4": "5778455936410588193",
    "link5": "5895364284782743985",
    "link6": "5769289093221454192",
    "link7": "5766902139376898645",
    "plus": "6032924188828767321",
    "info": "6028435952299413210",
    "question": "6030848053177486888",
    "warning": "6030563507299160824",
    "play1": "5773626993010546707",
    "play2": "5850346984501680054",
    "cross2": "5774077015388852135",
    "check": "5774022692642492953",
    "up1": "6028205772117118673",
    "unlock": "6037496202990194718",
    "lock": "6037249452824072506",
    "image1": "6030466823290360017",
    "image2": "6035128606563241721",
    "robot": "6030400221232501136",
    "star3": "6030425896546996257",
    "star4": "6030680867280522811",
    "folder2": "6037475557082403885",
    "folder3": "5904219717073114606",
    "document": "6034969813032374911",
    "trash": "6039522349517115015",
    "music1": "6037364759811068375",
    "music2": "6037460610596212193",
    "eye1": "6037397706505195857",
    "eye2": "6037243349675544634",
    "eye3": "5884097155341226387",
    "eye4": "5935757052042285202",
    "down1": "6037157012242960559",
    "down2": "5884218166044791498",
    "down3": "6039802767931871481",
    "cloud": "6028115612163641653",
    "down4": "6032745346390560408",
    "up2": "5963103826075456248",
    "down5": "5963087934696459905",
    "up3": "6039391666547201160",
    "upload": "6039573425268201570",
    "up4": "5776288820467077551",
    "shield1": "6030537007350944596",
    "shield2": "6032636795387121097",
    "shield3": "6030445631921721471",
    "folder4": "6039630677182254664",
    "folder5": "6039800856671424701",
    "folder6": "6037373985400819577",
    "folder7": "6039348811363520645",
}

def method(name: str, **kwargs):
    """Small Telegram API method helper; keeps direct API calls uniform."""
    return api_call(name, **kwargs)


def pe(name: str, fallback: str = "✨") -> str:
    """Telegram Custom Emoji в HTML-разметке."""
    emoji_id = PREMIUM_EMOJI_IDS.get(name)
    if emoji_id:
        return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'
    return fallback


if not BOT_TOKEN:
    raise RuntimeError("Установи переменную окружения BOT_TOKEN перед запуском.")

logging.basicConfig(level=logging.INFO)
logging.getLogger("aiogram.event").setLevel(logging.ERROR)
logging.getLogger("aiogram.dispatcher").setLevel(logging.WARNING)
class WinesWorkAiohttpSession(AiohttpSession):
    """Сессия Telegram API с принудительным IPv4.

    На серверах без рабочего IPv6 попытка подключения к api.telegram.org
    может завершаться Errno 101 (Network is unreachable).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._connector_init["family"] = socket.AF_INET


bot_session = WinesWorkAiohttpSession(timeout=45)
bot = Bot(BOT_TOKEN, session=bot_session, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                joined_at TEXT
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                gift_id TEXT NOT NULL,
                gift_name TEXT NOT NULL,
                price INTEGER NOT NULL,
                recipient_id INTEGER,
                status TEXT NOT NULL DEFAULT 'pending',
                payload TEXT UNIQUE NOT NULL,
                charge_id TEXT,
                created_at TEXT NOT NULL,
                delivery_mode TEXT NOT NULL DEFAULT 'direct'
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                rating INTEGER NOT NULL,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS partner_bots (
                owner_id INTEGER NOT NULL,
                bot_id INTEGER PRIMARY KEY,
                bot_username TEXT NOT NULL,
                bot_name TEXT NOT NULL,
                token_file TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS admin_topups (
                payload TEXT PRIMARY KEY,
                admin_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                charge_id TEXT,
                created_at TEXT NOT NULL
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS gift_links (
                token TEXT PRIMARY KEY,
                order_id INTEGER NOT NULL,
                gift_id TEXT NOT NULL,
                password_hash TEXT,
                claimed_by INTEGER,
                claimed_at TEXT,
                created_at TEXT NOT NULL
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS bans (
                user_id INTEGER PRIMARY KEY,
                reason TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                admin_id INTEGER NOT NULL
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS subscription_cache (
                user_id INTEGER NOT NULL,
                channel TEXT NOT NULL,
                verified_at TEXT NOT NULL,
                PRIMARY KEY(user_id, channel)
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS partner_subscription_exemptions (
                user_id INTEGER PRIMARY KEY,
                verified_at TEXT NOT NULL
            )
        """)
        # Миграция старой БД: комментарий покупателя к подарку.
        cols = {row[1] for row in con.execute("PRAGMA table_info(orders)").fetchall()}
        if "gift_message" not in cols:
            con.execute("ALTER TABLE orders ADD COLUMN gift_message TEXT NOT NULL DEFAULT ''")
        if "delivery_mode" not in cols:
            con.execute("ALTER TABLE orders ADD COLUMN delivery_mode TEXT NOT NULL DEFAULT 'direct'")
        if "recipient_username" not in cols:
            con.execute("ALTER TABLE orders ADD COLUMN recipient_username TEXT NOT NULL DEFAULT ''")
        con.execute("""
            INSERT OR IGNORE INTO bot_settings(key, value) VALUES
                ('welcome_photo_url', 'https://display.wjwj.top/2026/10/30/5a5731eab953a1828e0afd2ff9eb0fb1.jpg?x-oss-process=image%2Fresize%2Cm_lfit%2Cw_1280%2Ch_1280%2Climit_1%2Fformat%2Cwebp%2Fquality%2Cq_80')
        """)


def get_setting(key: str, default=""):
    with db() as con:
        row = con.execute("SELECT value FROM bot_settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default

def set_setting(key: str, value: str):
    with db() as con:
        con.execute("INSERT INTO bot_settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))

def is_admin(message: Message) -> bool:
    return bool(message.from_user and message.from_user.id in ADMIN_IDS)

def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")



def is_banned(user_id: int) -> bool:
    with db() as con:
        row = con.execute("SELECT 1 FROM bans WHERE user_id=?", (int(user_id),)).fetchone()
    return bool(row)

def ban_user(user_id: int, reason: str, admin_id: int):
    with db() as con:
        con.execute(
            "INSERT INTO bans(user_id,reason,created_at,admin_id) VALUES(?,?,?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET reason=excluded.reason, created_at=excluded.created_at, admin_id=excluded.admin_id",
            (int(user_id), reason[:500], now(), int(admin_id))
        )

def unban_user(user_id: int):
    with db() as con:
        con.execute("DELETE FROM bans WHERE user_id=?", (int(user_id),))

def user_blocked(user_id: int) -> bool:
    return user_id not in ADMIN_IDS and is_banned(user_id)

def premium_prefix(fallback="✨", name="star1"):
    return pe(name, fallback)

def html_text(text: str, emoji_name: str = "star1", fallback: str = "✨") -> str:
    # Экранируем пользовательский текст, чтобы спецсимволы не ломали HTML parse_mode.
    return f"{pe(emoji_name, fallback)} {html.escape(str(text))}"

def tg_html(text: str) -> str:
    """Convert simple Markdown markers to Telegram HTML."""
    text = str(text)
    parts = text.split("**")
    text = "".join(("<b>" if i % 2 == 1 else "") + part + ("</b>" if i % 2 == 1 else "") for i, part in enumerate(parts))
    parts = text.split("`")
    text = "".join(("<code>" if i % 2 == 1 else "") + part + ("</code>" if i % 2 == 1 else "") for i, part in enumerate(parts))
    return text

def button(text: str, callback_data=None, url=None, emoji_name=None, custom_emoji_id=None, style=None):
    """Создаёт inline-кнопку в нативном цветном стиле Telegram.

    style: primary (синий), success (зелёный), danger (красный).
    """
    kwargs = {"text": text}
    if callback_data is not None:
        kwargs["callback_data"] = callback_data
    if url is not None:
        kwargs["url"] = url
    if style in {"primary", "success", "danger"}:
        kwargs["style"] = style
    if custom_emoji_id:
        kwargs["icon_custom_emoji_id"] = str(custom_emoji_id)
    elif emoji_name and PREMIUM_EMOJI_IDS.get(emoji_name):
        kwargs["icon_custom_emoji_id"] = PREMIUM_EMOJI_IDS[emoji_name]
    return InlineKeyboardButton(**kwargs)


def main_menu(user_id=None):
    b = InlineKeyboardBuilder()
    # Главное меню — цветное: красный/зелёный.
    b.row(button("Профиль", callback_data="profile", emoji_name="eye1", style="success"),
          button("Подарки", callback_data="gifts", emoji_name="gift", style="success"))
    b.row(button("Чеки-подарки", callback_data="vouchers", emoji_name="check", style="success"))
    b.row(button("Отзывы", callback_data="reviews", emoji_name="note1", style="success"))
    b.row(button("Наш канал", url="https://t.me/wwlobby", emoji_name="link1", style="danger"))
    if user_id and ADMIN_ID and user_id in ADMIN_IDS:
        b.row(button("Панель", callback_data="admin:panel", emoji_name="gear1", style="danger"))
    return b.as_markup()


def managed_bot_keyboard():
    if CHILD_MODE or KeyboardButtonRequestManagedBot is None:
        return None
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(
            text="🤖 Создать своего бота",
            style="success",
            request_managed_bot=KeyboardButtonRequestManagedBot(
                request_id=abs(hash((os.getpid(), time.time_ns()))) % 2147483647,
                suggested_name="Мой WinesWork бот",
            )
        )]],
        resize_keyboard=True,
        is_persistent=True,
    )


def gifts_menu():
    b = InlineKeyboardBuilder()
    b.row(button("Обычные подарки", callback_data="catalog:regular", emoji_name="gift"))
    b.row(button("Удалённые Подарки", callback_data="catalog:rare", emoji_name="star4"))
    b.row(button("Назад", callback_data="home", emoji_name="left1"))
    return b.as_markup()

def back_menu(target="gifts", emoji_name="left1"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [button("Назад", callback_data=target, emoji_name=emoji_name)]
    ])


SAFE_API_METHODS = {"getMe", "getAvailableGifts", "getMyStarBalance", "sendGift"}
API_RETRY_DELAYS = (0.5, 1.5, 3.0)

async def api_call(method: str, **kwargs):
    """Надёжный прямой вызов Bot API с принудительным IPv4.

    Важно: aiogram-сессия уже использует IPv4, а прежний прямой aiohttp-вызов
    создавал отдельную сессию без family=AF_INET. Из-за этого getMyStarBalance
    и getAvailableGifts могли падать на серверах без рабочего IPv6.
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    # На Android/Pydroid сетевое соединение с Telegram может кратковременно
    # сбрасываться. Повторяем безопасные запросы и отправку подарка, но не
    # повторяем платежные операции, чтобы не создать двойную оплату.
    timeout = aiohttp.ClientTimeout(total=40, connect=15, sock_connect=15, sock_read=30)
    retries = API_RETRY_DELAYS if method in SAFE_API_METHODS else (0,)

    last_error = None
    for attempt, delay in enumerate(retries):
        if delay:
            await asyncio.sleep(delay)
        try:
            connector = aiohttp.TCPConnector(
                family=socket.AF_INET,
                ttl_dns_cache=300,
                limit=8,
                force_close=True,
                enable_cleanup_closed=True,
            )
            async with aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={"Connection": "close"},
            ) as session:
                async with session.post(url, json=kwargs) as response:
                    data = await response.json(content_type=None)

            if not data.get("ok"):
                raise RuntimeError(
                    data.get("description", f"Telegram API error: {method}")
                )
            return data.get("result")
        except (aiohttp.ClientError, asyncio.TimeoutError, ConnectionError, OSError) as exc:
            last_error = exc
            if attempt < len(retries) - 1:
                continue
            raise
        except Exception as exc:
            last_error = exc
            raise
    raise last_error or RuntimeError(f"Telegram API error: {method}")


_gifts_cache = []
_gifts_cache_at = 0.0
GIFT_CACHE_TTL = 120.0
SUBSCRIPTION_CACHE_TTL = 7 * 24 * 60 * 60


async def get_available_gifts(force_refresh: bool = False):
    """Получает каталог доступных для бота подарков и держит короткий кеш."""
    global _gifts_cache, _gifts_cache_at

    now_mono = time.monotonic()
    if not force_refresh and _gifts_cache and now_mono - _gifts_cache_at < GIFT_CACHE_TTL:
        return _gifts_cache

    try:
        result = await api_call("getAvailableGifts")
        raw_gifts = result.get("gifts", []) if isinstance(result, dict) else []
        gifts = [
            g for g in raw_gifts
            if g.get("personal_remaining_count") != 0
            and g.get("remaining_count") != 0
        ]
        if gifts:
            _gifts_cache = gifts
            _gifts_cache_at = time.monotonic()
            return gifts
    except Exception:
        # Не показываем техническую ошибку пользователю.
        pass

    return _gifts_cache



def partner_subscription_exempt(user_id: int) -> bool:
    """Не требуем подписки в партнёрской копии, если пользователь уже
    подтвердил все обязательные каналы в основном WinesWork.

    Проверяем и отдельное исключение, и старый кеш subscription_cache,
    чтобы пользователи, подтвердившие подписку до этой функции, тоже
    не получили повторное требование.
    """
    if not CHILD_MODE:
        return False
    try:
        main_db = FsPath(MAIN_DB_PATH)
        if not main_db.exists():
            return False
        with sqlite3.connect(str(main_db)) as con:
            row = con.execute(
                "SELECT 1 FROM partner_subscription_exemptions WHERE user_id=? LIMIT 1",
                (int(user_id),)
            ).fetchone()
            if row is not None:
                return True

            rows = con.execute(
                "SELECT channel FROM subscription_cache WHERE user_id=?",
                (int(user_id),)
            ).fetchall()
            verified_channels = {str(r[0]) for r in rows}
            required_channels = {str(channel) for channel, _ in REQUIRED_CHANNELS}
            if required_channels and required_channels.issubset(verified_channels):
                con.execute(
                    "INSERT INTO partner_subscription_exemptions(user_id, verified_at) VALUES(?, ?) "
                    "ON CONFLICT(user_id) DO UPDATE SET verified_at=excluded.verified_at",
                    (int(user_id), now())
                )
                return True
    except Exception:
        logging.getLogger("WinesWork").exception(
            "Не удалось проверить подтверждение подписок в основной БД"
        )
    return False


async def check_required_subscriptions(user_id: int):
    # В партнёрской копии повторная обязательная подписка не нужна,
    # если пользователь уже подтвердил все каналы в основном WinesWork.
    if partner_subscription_exempt(user_id):
        return []

    """Проверяет обязательные подписки, не заставляя уже проверенных
    пользователей повторно проходить проверку при временных сбоях Telegram API.

    Если Telegram отвечает корректно — актуальный статус имеет приоритет.
    Если API временно недоступен, подтверждённая ранее подписка сохраняется
    на 30 дней, чтобы бот не зацикливался на повторной подписке.
    """
    not_subscribed = []
    now_ts = time.time()

    # Быстрый путь: если пользователь уже недавно успешно проходил проверку,
    # не делаем 3 сетевых запроса на каждый /start и каждое нажатие кнопки.
    # Это также предотвращает повторное требование подписки у давних подписчиков.
    with db() as con:
        cached_rows = con.execute(
            "SELECT channel, verified_at FROM subscription_cache WHERE user_id=?",
            (int(user_id),)
        ).fetchall()
    cached = {}
    for row in cached_rows:
        try:
            cached[row["channel"]] = datetime.fromisoformat(row["verified_at"]).timestamp()
        except Exception:
            pass
    if all(channel in cached and now_ts - cached[channel] <= SUBSCRIPTION_CACHE_TTL
           for channel, _ in REQUIRED_CHANNELS):
        if not CHILD_MODE:
            with db() as con:
                con.execute(
                    "INSERT INTO partner_subscription_exemptions(user_id, verified_at) VALUES(?, ?) "
                    "ON CONFLICT(user_id) DO UPDATE SET verified_at=excluded.verified_at",
                    (int(user_id), now())
                )
        return []

    for channel, title in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            status = getattr(member, "status", "left")
            # administrator/creator/member/restricted считаем подписанными.
            is_member = status not in ("left", "kicked")
            if is_member:
                with db() as con:
                    con.execute(
                        "INSERT INTO subscription_cache(user_id,channel,verified_at) VALUES(?,?,?) "
                        "ON CONFLICT(user_id,channel) DO UPDATE SET verified_at=excluded.verified_at",
                        (int(user_id), channel, now())
                    )
                continue

            not_subscribed.append((channel, title))
        except TelegramAPIError:
            # Временный сбой проверки не должен бесконечно требовать подписку.
            with db() as con:
                row = con.execute(
                    "SELECT verified_at FROM subscription_cache WHERE user_id=? AND channel=?",
                    (int(user_id), channel)
                ).fetchone()
            if row:
                try:
                    verified_ts = datetime.fromisoformat(row["verified_at"]).timestamp()
                    if now_ts - verified_ts <= SUBSCRIPTION_CACHE_TTL:
                        continue
                except Exception:
                    pass
            not_subscribed.append((channel, title))

    if not not_subscribed and not CHILD_MODE:
        with db() as con:
            con.execute(
                "INSERT INTO partner_subscription_exemptions(user_id, verified_at) VALUES(?, ?) "
                "ON CONFLICT(user_id) DO UPDATE SET verified_at=excluded.verified_at",
                (int(user_id), now())
            )

    return not_subscribed


def subscriptions_keyboard():
    b = InlineKeyboardBuilder()
    for channel, title in REQUIRED_CHANNELS:
        b.button(text=f"Подписаться на {title}", url=f"https://t.me/{channel.lstrip('@')}", style="success")
    b.button(text="Проверить подписки", callback_data="check_subs", style="primary")
    b.adjust(1)
    return b.as_markup()


async def require_subscriptions_message(message: Message):
    if user_blocked(message.from_user.id):
        await message.answer("🚫 Доступ к боту заблокирован.")
        return False
    missing = await check_required_subscriptions(message.from_user.id)
    if not missing:
        return True

    names = "\n".join(f"• {title}" for _, title in missing)
    await message.answer(
        f"{pe('lock', '🔒')} Для использования бота нужно подписаться на все обязательные каналы:\n\n"
        f"{names}\n\n"
        "После подписки нажми «Проверить подписки».",
        reply_markup=subscriptions_keyboard()
    )
    return False


async def require_subscriptions_callback(call: CallbackQuery):
    if user_blocked(call.from_user.id):
        await call.answer("🚫 Доступ к боту заблокирован.", show_alert=True)
        return False
    missing = await check_required_subscriptions(call.from_user.id)
    if not missing:
        return True

    names = "\n".join(f"• {title}" for _, title in missing)
    await call.message.edit_text(
        f"{pe('lock', '🔒')} Сначала подпишись на все обязательные каналы:\n\n"
        f"{names}\n\n"
        "После подписки нажми «Проверить подписки».",
        reply_markup=subscriptions_keyboard()
    )
    await call.answer("Подпишись на все каналы.", show_alert=True)
    return False


@dp.callback_query(F.data == "check_subs")
async def check_subscriptions(call: CallbackQuery):
    missing = await check_required_subscriptions(call.from_user.id)
    if missing:
        names = "\n".join(f"• {title}" for _, title in missing)
        await call.message.edit_text(
            f"{pe('cross2', '❌')} Подписка ещё не подтверждена.\n\n"
            f"Нужно подписаться:\n{names}\n\n"
            "После подписки нажми кнопку ещё раз.",
            parse_mode="HTML",
            reply_markup=subscriptions_keyboard()
        )
        await call.answer("Есть неподтверждённые подписки.", show_alert=True)
        return

    await call.message.edit_text(
        f"{pe('check', '✅')} Все обязательные подписки подтверждены!\n\nДобро пожаловать в WinesWork {pe('gift', '🎁')}",
        reply_markup=main_menu(call.from_user.id)
    )
    await call.answer("Подписки подтверждены!")


def gift_label(gift: dict) -> str:
    """Человеческое название подарка для интерфейса.

    ID никогда не показываем пользователю как название: если Telegram
    не отдаёт имя, используем эмодзи. Сам ID остаётся только во внутренних
    callback_data/БД.
    """
    sticker = gift.get("sticker") or {}
    emoji = str(sticker.get("emoji") or gift.get("emoji") or "🎁").strip()
    names = {
        "🧸": "Мишка",
        "❤️": "Сердце",
        "❤": "Сердце",
        "🌹": "Роза",
        "🎁": "Подарочная коробка",
        "🎂": "Торт",
        "💐": "Букет цветов",
        "🚀": "Ракета",
        "🍾": "Бутылка шампанского",
        "🏆": "Трофей",
        "💍": "Бриллиантовое кольцо",
        "💎": "Драгоценный камень",
    }
    api_name = str(gift.get("name") or "").strip()
    if api_name and not api_name.isdigit():
        return api_name
    return names.get(emoji, emoji)

def gift_visual(gift: dict) -> str:
    sticker = gift.get("sticker") or {}
    emoji = str(sticker.get("emoji") or "🎁")
    custom_id = sticker.get("custom_emoji_id")
    if custom_id:
        return f'<tg-emoji emoji-id="{html.escape(str(custom_id), quote=True)}">{emoji}</tg-emoji>'
    return emoji

def hash_voucher_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

async def bot_username() -> str:
    me = await bot.get_me()
    return me.username or ""

async def make_voucher(order_id: int, gift_id: str, password: str = "") -> str:
    token = secrets.token_urlsafe(12)
    ph = hash_voucher_password(password) if password else None
    with db() as con:
        if password:
            con.execute("DELETE FROM gift_links WHERE order_id=? AND claimed_at IS NULL", (order_id,))
        con.execute(
            "INSERT INTO gift_links(token,order_id,gift_id,password_hash,created_at) VALUES(?,?,?,?,?)",
            (token, order_id, gift_id, ph, now()),
        )
    username = await bot_username()
    return f"https://t.me/{username}?start=gift_{token}"


async def create_admin_voucher_order(admin_id: int, gift_id: str, gift_message: str = "🎁 Подарок от администратора"):
    created_at = now()
    payload = f"admin_voucher:{gift_id}:{admin_id}:{secrets.token_hex(6)}"
    gifts = await get_available_gifts()
    gift = next((g for g in gifts if str(g.get("id")) == str(gift_id)), None)
    gift_name = gift_label(gift) if gift else str(gift_id)
    with db() as con:
        cur = con.execute(
            """INSERT INTO orders
               (user_id, gift_id, gift_name, price, recipient_id, status, payload, created_at, gift_message, delivery_mode)
               VALUES (?, ?, ?, 0, ?, 'paid', ?, ?, ?, 'voucher')""",
            (admin_id, gift_id, gift_name, admin_id, payload, created_at, gift_message[:500])
        )
        order_id = cur.lastrowid
        return order_id

async def create_voucher_invoice(user_id: int, gift_id: str, gift_message: str = "") -> bool:
    gifts = await get_available_gifts()
    gift = next((g for g in gifts if str(g.get("id")) == gift_id), None)
    if not gift:
        return False
    price = 4
    payload = f"voucher:{gift_id}:{user_id}:{secrets.token_hex(6)}"
    name = gift_label(gift)
    if not gift_message:
        sender = f"@{html.escape((await bot.get_chat(user_id)).username)}" if (await bot.get_chat(user_id)).username else "тебя"
        gift_message = f"🎁 Подарок от {sender}"
    with db() as con:
        con.execute("""
            INSERT INTO orders(user_id, gift_id, gift_name, price, recipient_id, status, payload, created_at, gift_message, delivery_mode)
            VALUES(?, ?, ?, ?, ?, 'pending', ?, ?, ?, 'voucher')
        """, (user_id, gift_id, name, price, user_id, payload, now(), gift_message[:500]))
    try:
        await bot.send_invoice(
            chat_id=user_id,
            title=f"Чек: {name}"[:32],
            description="Одноразовый чек-подарок за 4 Stars.",
            payload=payload,
            currency="XTR",
            prices=[LabeledPrice(label="Чек-подарок", amount=price)],
            provider_token="",
        )
        return True
    except TelegramAPIError:
        with db() as con:
            con.execute("UPDATE orders SET status='invoice_failed' WHERE payload=?", (payload,))
        return False

async def create_archived_invoice(user_id: int, archived: dict, recipient_id: int | None = None, recipient_username: str = "", gift_message: str = "") -> bool:
    price = int(archived["price"])
    gift_id = str(archived["gift_id"])
    name = f"{archived['emoji']} {archived['name']}"
    recipient_username = (recipient_username or "").strip().lstrip("@").lower()
    if not gift_message:
        gift_message = "🎁 Подарок от тебя"
    delivery_mode = "archived_direct" if recipient_id else "archived_pending_recipient"
    payload = f"archived:{gift_id}:buyer:{user_id}:recipient:{recipient_id or 0}:{secrets.token_hex(6)}"
    description = (
        f"{name}. После оплаты подарок будет автоматически отправлен выбранному получателю."
        if recipient_id else
        f"{name}. Получатель ещё не запускал бота; после оплаты появится персональная ссылка."
    )
    with db() as con:
        con.execute("""
            INSERT INTO orders(user_id, gift_id, gift_name, price, recipient_id, recipient_username,
                               status, payload, created_at, gift_message, delivery_mode)
            VALUES(?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?)
        """, (user_id, gift_id, name, price, recipient_id, recipient_username, payload, now(), gift_message[:500], delivery_mode))
    try:
        await bot.send_invoice(
            chat_id=user_id, title=name[:32], description=description[:255], payload=payload,
            currency="XTR", prices=[LabeledPrice(label=name[:32], amount=price)], provider_token="",
        )
        return True
    except TelegramAPIError:
        with db() as con:
            con.execute("UPDATE orders SET status='invoice_failed' WHERE payload=?", (payload,))
        return False

async def create_gift_invoice(
    user_id: int,
    gift_id: str,
    gift: dict,
    gift_message: str = "",
    recipient_id: int | None = None,
    recipient_username: str = "",
) -> bool:
    price = get_sale_price(gift)
    if price < 1:
        return False
    payload = f"gift:{gift_id}:buyer:{user_id}:recipient:{recipient_id or 0}:{secrets.token_hex(6)}"
    name = gift_label(gift)
    recipient_username = (recipient_username or "").strip().lstrip("@").lower()

    if not gift_message:
        sender = None
        try:
            sender_chat = await bot.get_chat(user_id)
            sender = sender_chat.username
        except Exception:
            with db() as con:
                row = con.execute("SELECT username FROM users WHERE user_id=?", (user_id,)).fetchone()
                sender = row["username"] if row else None
        gift_message = f"🎁 Подарок от @{sender}" if sender else "🎁 Подарок от тебя"

    if recipient_id:
        delivery_mode = "direct"
        description = f"{name}. После оплаты подарок будет автоматически отправлен выбранному получателю."
    else:
        # Получатель ещё не запускал бота. После оплаты создаём персональную ссылку.
        # Когда получатель нажмёт ссылку и запустит бота, подарок уйдёт автоматически.
        delivery_mode = "pending_recipient"
        description = (
            f"{name}. Получатель ещё не запускал бота. После оплаты появится ссылка, "
            f"по которой подарок автоматически отправится получателю."
        )

    with db() as con:
        con.execute("""
            INSERT INTO orders(user_id, gift_id, gift_name, price, recipient_id, recipient_username,
                               status, payload, created_at, gift_message, delivery_mode)
            VALUES(?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?)
        """, (user_id, gift_id, name, price, recipient_id, recipient_username,
              payload, now(), gift_message[:500], delivery_mode))
    try:
        await bot.send_invoice(
            chat_id=user_id,
            title=name[:32],
            description=description[:255],
            payload=payload,
            currency="XTR",
            prices=[LabeledPrice(label=name[:32], amount=price)],
            provider_token="",
        )
        return True
    except TelegramAPIError:
        with db() as con:
            con.execute("UPDATE orders SET status='invoice_failed' WHERE payload=?", (payload,))
        return False

def copy_prefix(text: str) -> str:
    if CHILD_MODE and CHILD_BOT_NAME:
        return f"<i>Это копия {html.escape(CHILD_BOT_NAME)}</i>\n\n{text}"
    return text


def partner_token_path(bot_id: int) -> FsPath:
    PARTNER_DIR.mkdir(parents=True, exist_ok=True)
    return PARTNER_DIR / f"{int(bot_id)}.token"


def save_partner_token(bot_id: int, token: str) -> str:
    PARTNER_DIR.mkdir(parents=True, exist_ok=True)
    path = partner_token_path(bot_id)
    path.write_text(token.strip(), encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return str(path)


def load_partner_token(path: str) -> str:
    return FsPath(path).read_text(encoding="utf-8").strip()


def launch_partner_bot(bot_id: int, bot_name: str, token_path: str):
    env = os.environ.copy()
    env["BOT_TOKEN"] = load_partner_token(token_path)
    env["WINESWORK_CHILD"] = "1"
    env["WINESWORK_CHILD_NAME"] = bot_name
    env["DB_PATH"] = str(FsPath(token_path).with_suffix(".sqlite3"))
    env["WINESWORK_MAIN_DB_PATH"] = str(FsPath(DB_PATH).resolve())
    env["WINESWORK_PARTNER_DIR"] = str(PARTNER_DIR)
    kwargs = {"env": env, "cwd": os.getcwd()}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    return subprocess.Popen([os.sys.executable, os.path.abspath(__file__)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kwargs)


def load_and_launch_partners():
    if CHILD_MODE:
        return
    with db() as con:
        rows = con.execute("SELECT bot_id, bot_name, token_file FROM partner_bots").fetchall()
    for row in rows:
        try:
            if FsPath(row["token_file"]).exists():
                launch_partner_bot(int(row["bot_id"]), str(row["bot_name"]), str(row["token_file"]))
        except Exception:
            logging.getLogger("WinesWork").exception("Не удалось запустить партнёрского бота %s", row["bot_id"])


async def send_home(message: Message):
    if not await require_subscriptions_message(message):
        return

    home_text = (
        f"{pe('gift', '🎁')} <b>Привет!</b>\n\n"
        "Добро пожаловать в WinesWork!\n\n"
        "Выбирай подарки, оформляй покупки за Telegram Stars и пользуйся чеками-подарками."
    )
    welcome_markup = main_menu(message.from_user.id)
    welcome_caption = copy_prefix(home_text)
    if WELCOME_PHOTO.exists():
        try:
            await message.answer_photo(
                photo=FSInputFile(str(WELCOME_PHOTO)),
                caption=welcome_caption,
                parse_mode="HTML",
                reply_markup=welcome_markup
            )
        except Exception:
            logging.getLogger("WinesWork").exception("Не удалось отправить фото приветствия")
            await message.answer(
                welcome_caption,
                parse_mode="HTML",
                reply_markup=welcome_markup
            )
    else:
        await message.answer(
            welcome_caption,
            parse_mode="HTML",
            reply_markup=welcome_markup
        )
    managed_kb = managed_bot_keyboard()
    if managed_kb is not None:
        await message.answer("🤖 <b>Партнёрские боты</b>", parse_mode="HTML", reply_markup=managed_kb)


@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def deny_group_messages(message: Message):
    # WinesWork-копии не обслуживают группы. Если бот уже добавлен, молча уходим.
    try:
        await bot.leave_chat(message.chat.id)
    except Exception:
        pass


@dp.channel_post()
async def deny_channel_posts(message: Message):
    # Не отвечаем на публикации каналов. Если Telegram разрешит, покидаем канал.
    try:
        await bot.leave_chat(message.chat.id)
    except Exception:
        pass


@dp.my_chat_member()
async def leave_non_private_chats(event: ChatMemberUpdated):
    if event.chat.type not in {"group", "supergroup", "channel"}:
        return
    try:
        await bot.leave_chat(event.chat.id)
    except Exception:
        pass


@dp.message(CommandStart())
async def start(message: Message):
    with db() as con:
        con.execute("""
            INSERT INTO users(user_id, username, first_name, joined_at)
            VALUES(?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username, first_name=excluded.first_name
        """, (message.from_user.id, message.from_user.username,
              message.from_user.first_name, now()))

    if user_blocked(message.from_user.id):
        await message.answer("🚫 Доступ к боту заблокирован.")
        return

    parts = (message.text or "").split(maxsplit=1)
    arg = parts[1].strip() if len(parts) > 1 else ""
    if arg.startswith("gift_"):
        token = arg[5:]
        await claim_voucher(message, token)
        return
    await send_home(message)


@dp.message(Command("id"))
async def show_id(message: Message):
    if user_blocked(message.from_user.id):
        return
    await message.answer(f"Твой Telegram ID: <code>{message.from_user.id}</code>", parse_mode="HTML")


@dp.callback_query(F.data == "home")
async def home(call: CallbackQuery):
    if not await require_subscriptions_callback(call):
        return
    await call.message.edit_text(f"{pe('gift', '🎁')} <b>Главное меню</b>", parse_mode="HTML", reply_markup=main_menu(call.from_user.id))
    await call.answer()


@dp.message(Command("createbot"))
async def create_bot_command(message: Message):
    if CHILD_MODE:
        await message.answer("Эта функция доступна в основном WinesWork.")
        return
    if KeyboardButtonRequestManagedBot is None:
        await message.answer("❌ Для Managed Bots обнови aiogram до версии с поддержкой Bot API 9.6+.")
        return
    kb = managed_bot_keyboard()
    await message.answer(
        f"{pe('robot','🤖')} <b>Создание своего бота</b>\n\n"
        "Нажми кнопку ниже и создай своего бота прямо через Telegram. "
        "Токен вручную отправлять не нужно.\n\n"
        "После создания WinesWork автоматически подключит копию.",
        parse_mode="HTML", reply_markup=kb
    )


@dp.message(F.managed_bot_created)
async def managed_bot_created(message: Message):
    if CHILD_MODE or not message.managed_bot_created or not message.from_user:
        return
    managed = message.managed_bot_created
    bot_user = getattr(managed, "bot_user", None) or getattr(managed, "bot", None)
    if not bot_user:
        await message.answer("❌ Telegram не передал данные созданного бота.")
        return
    bot_id = int(bot_user.id)
    bot_name = bot_user.first_name or bot_user.username or f"Bot {bot_id}"
    bot_username = bot_user.username or ""
    try:
        # Bot API getManagedBotToken возвращает сам токен строкой,
        # а не объект с полем .token. Оставляем совместимость с версиями
        # библиотек, где ответ мог быть обёрнут в объект.
        token_obj = await bot.get_managed_bot_token(user_id=bot_id)
        if isinstance(token_obj, str):
            token = token_obj.strip()
        else:
            token = getattr(token_obj, "token", None)
            if token is None and isinstance(token_obj, dict):
                token = token_obj.get("token") or token_obj.get("result")
            token = str(token).strip() if token else None
        if not token or ":" not in token:
            raise RuntimeError("Telegram не вернул корректный токен Managed Bot")
        with db() as con:
            existing = con.execute("SELECT bot_id FROM partner_bots WHERE bot_id=?", (bot_id,)).fetchone()
            if existing:
                await message.answer("ℹ️ Этот бот уже подключён к WinesWork.")
                return
            token_file = save_partner_token(bot_id, token)
            con.execute(
                "INSERT INTO partner_bots(owner_id, bot_id, bot_username, bot_name, token_file, created_at) VALUES(?,?,?,?,?,?)",
                (message.from_user.id, bot_id, bot_username, bot_name, token_file, now())
            )
        launch_partner_bot(bot_id, bot_name, token_file)
        await message.answer(
            f"{pe('check','✅')} <b>Бот создан и подключён!</b>\n\n"
            f"<b>{html.escape(bot_name)}</b>" + (f" (@{html.escape(bot_username)})" if bot_username else "") + "\n\n"
            f"Внутри будет показываться: <i>Это копия {html.escape(bot_name)}</i>.\n"
            "Бот работает только в личных чатах.",
            parse_mode="HTML", reply_markup=ReplyKeyboardRemove()
        )
    except Exception as exc:
        logging.getLogger("WinesWork").exception("Ошибка подключения Managed Bot: %s", exc)
        await message.answer("❌ Не удалось подключить Managed Bot. Проверь, что управление ботами включено в @BotFather.")


@dp.message(F.text == "🤖 Создать своего бота")
async def create_bot_button(message: Message):
    await create_bot_command(message)


@dp.callback_query(F.data == "create_bot")
async def create_bot_start(call: CallbackQuery):
    if CHILD_MODE:
        await call.answer("Эта функция доступна в основном WinesWork.", show_alert=True)
        return
    if KeyboardButtonRequestManagedBot is None:
        await call.answer("Обнови aiogram до версии с Managed Bots.", show_alert=True)
        return
    if not await require_subscriptions_callback(call):
        return
    await call.message.answer(
        f"{pe('robot','🤖')} <b>Создать своего бота</b>\n\n"
        "Нажми кнопку «Создать своего бота» ниже и заверши создание через Telegram.",
        parse_mode="HTML", reply_markup=managed_bot_keyboard()
    )
    await call.answer()


@dp.callback_query(F.data == "my_bots")
async def my_bots(call: CallbackQuery):
    with db() as con:
        rows = con.execute("SELECT bot_username, bot_name FROM partner_bots WHERE owner_id=? ORDER BY created_at DESC", (call.from_user.id,)).fetchall()
    if not rows:
        text = "У тебя пока нет созданных ботов."
    else:
        text = "<b>Мои боты</b>\n\n" + "\n".join(f"• <a href=\"https://t.me/{html.escape(r['bot_username'])}\">@{html.escape(r['bot_username'])}</a> — {html.escape(r['bot_name'])}" for r in rows)
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_menu("home"))
    await call.answer()


@dp.callback_query(F.data == "profile")
async def profile(call: CallbackQuery):
    if not await require_subscriptions_callback(call):
        return
    # На случай открытия профиля без /start — гарантируем наличие пользователя в БД.
    with db() as con:
        con.execute("""
            INSERT INTO users(user_id, username, first_name, joined_at)
            VALUES(?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username, first_name=excluded.first_name
        """, (call.from_user.id, call.from_user.username, call.from_user.first_name, now()))
        orders = con.execute("SELECT COUNT(*) n FROM orders WHERE user_id=? AND status IN ('paid','delivered')", (call.from_user.id,)).fetchone()["n"]
        spent = con.execute("SELECT COALESCE(SUM(price),0) n FROM orders WHERE user_id=? AND status IN ('paid','delivered')", (call.from_user.id,)).fetchone()["n"]
        reviews = con.execute("SELECT COUNT(*) n FROM reviews WHERE user_id=?", (call.from_user.id,)).fetchone()["n"]
        delivered = con.execute("SELECT COUNT(*) n FROM orders WHERE user_id=? AND status='delivered'", (call.from_user.id,)).fetchone()["n"]
        vouchers = con.execute("""
            SELECT COUNT(*) n FROM orders
            WHERE user_id=? AND delivery_mode='voucher' AND status IN ('paid','delivered')
        """, (call.from_user.id,)).fetchone()["n"]
    text = (
        f"{pe('eye1','👁')} <b>Профиль</b>\n\n"
        f"ID: <code>{call.from_user.id}</code>\n"
        f"Имя: {html.escape(call.from_user.full_name)}\n"
        f"Username: @{html.escape(call.from_user.username) if call.from_user.username else 'не указан'}\n\n"
        f"{pe('gift','🎁')} Заказов: <b>{orders}</b>\n"
        f"{pe('check','✅')} Доставлено: <b>{delivered}</b>\n"
        f"{pe('star1','⭐')} Потрачено: <b>{spent} Stars</b>\n"
        f"{pe('note1','📝')} Отзывов: <b>{reviews}</b>\n"
        f"{pe('check','✅')} Чеков-подарков: <b>{vouchers}</b>"
    )
    b = InlineKeyboardBuilder()
    b.row(button("Мои чеки", callback_data="profile:checks", emoji_name="check"))
    b.row(button("Идеи", callback_data="ideas", emoji_name="note2"), button("Поддержка", url=SUPPORT_URL, emoji_name="question"))
    b.row(button("Назад", callback_data="home", emoji_name="left1"))
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=b.as_markup())
    await call.answer()


@dp.callback_query(F.data == "profile:checks")
async def profile_checks(call: CallbackQuery):
    if not await require_subscriptions_callback(call):
        return
    with db() as con:
        rows = con.execute("""
            SELECT id, gift_name, price, status, created_at
            FROM orders
            WHERE user_id=? AND delivery_mode='voucher'
            ORDER BY id DESC LIMIT 20
        """, (call.from_user.id,)).fetchall()
    lines = [f"{pe('check','✅')} <b>Мои чеки-подарки</b>\n"]
    if not rows:
        lines.append("Чеков пока нет.")
    for r in rows:
        lines.append(f"#{r['id']} · {html.escape(r['gift_name'])} · {r['price']} ⭐ · {html.escape(r['status'])}")
    b = InlineKeyboardBuilder()
    b.row(button("Создать чек", callback_data="vouchers", emoji_name="plus"))
    b.row(button("Назад", callback_data="profile", emoji_name="left1"))
    await call.message.edit_text("\n".join(lines), parse_mode="HTML", reply_markup=b.as_markup())
    await call.answer()

@dp.callback_query(F.data == "gifts")
async def gifts(call: CallbackQuery):
    if not await require_subscriptions_callback(call):
        return
    await call.message.edit_text(f"{pe('folder1', '🗂')} Выбери раздел каталога:", reply_markup=gifts_menu())
    await call.answer()



@dp.callback_query(F.data == "vouchers")
async def vouchers_menu(call: CallbackQuery):
    if not await require_subscriptions_callback(call):
        return
    gifts = await get_available_gifts()
    if not gifts:
        await call.message.edit_text(
            f"{pe('warning','⚠️')} <b>Чеки-подарки</b>\n\nКаталог временно обновляется. Попробуй ещё раз через несколько секунд.",
            parse_mode="HTML", reply_markup=back_menu("home")
        )
        await call.answer()
        return
    b = InlineKeyboardBuilder()
    for gift in gifts[:40]:
        gid = str(gift.get("id"))
        label = gift_label(gift)
        kwargs = {"text": f"{label} · 4 ⭐", "callback_data": f"voucherbuy:{gid}"}
        sticker = gift.get("sticker") or {}
        if sticker.get("custom_emoji_id"):
            kwargs["icon_custom_emoji_id"] = str(sticker["custom_emoji_id"])
        b.button(**kwargs)
    b.button(text="Назад", callback_data="home")
    b.adjust(1)
    await call.message.edit_text(
        f"{pe('check','✅')} <b>Чек-подарок</b>\n\n"
        f"Выбери подарок для чека.\n"
        f"{pe('star1','⭐')} Цена чека: <b>4 Stars</b>.\n"
        f"{pe('gift','🎁')} После оплаты ты получишь одноразовую ссылку. "
        f"При открытии ссылки бот отправит выбранный подарок получателю.\n\n"
        f"{pe('note1','📝')} Перед оплатой можно добавить своё сообщение.",
        parse_mode="HTML", reply_markup=b.as_markup()
    )
    await call.answer()

@dp.callback_query(F.data.startswith("voucherbuy:"))
async def voucher_buy_start(call: CallbackQuery):
    if not await require_subscriptions_callback(call):
        return
    gift_id = call.data.split(":", 1)[1]
    gifts = await get_available_gifts()
    gift = next((g for g in gifts if str(g.get("id")) == gift_id), None)
    if not gift:
        await call.answer("Подарок временно недоступен. Обнови каталог.", show_alert=True)
        return
    set_setting(f"pending_voucher_gift_{call.from_user.id}", gift_id)
    set_setting(f"pending_voucher_message_{call.from_user.id}", "")
    b = InlineKeyboardBuilder()
    b.row(button("Без сообщения", callback_data=f"vmsg:none:{gift_id}", emoji_name="cross1"))
    b.row(button("Написать сообщение", callback_data=f"vmsg:custom:{gift_id}", emoji_name="pencil1"))
    b.row(button("Назад", callback_data="vouchers", emoji_name="left1"))
    await call.message.edit_text(
        f"{gift_visual(gift)} <b>{html.escape(gift_label(gift))}</b>\n\n"
        f"{pe('check','✅')} Чек стоит <b>4 ⭐</b>.\n"
        f"{pe('note1','📝')} Выбери сообщение, которое будет отправлено вместе с подарком.",
        parse_mode="HTML", reply_markup=b.as_markup()
    )
    await call.answer()

@dp.callback_query(F.data.startswith("vmsg:"))
async def voucher_message_choice(call: CallbackQuery):
    if not await require_subscriptions_callback(call):
        return
    _, mode, gift_id = call.data.split(":", 2)
    if mode == "custom":
        set_setting(f"awaiting_voucher_message_{call.from_user.id}", gift_id)
        await call.message.answer(
            f"{pe('pencil1','✏️')} Напиши сообщение для получателя одним сообщением (до 500 символов).",
            parse_mode="HTML"
        )
        await call.answer()
        return
    ok = await create_voucher_invoice(call.from_user.id, gift_id, "")
    await call.answer("Счёт на 4 ⭐ отправлен." if ok else "Не удалось создать счёт.", show_alert=not ok)

ARCHIVED_GIFTS = [
    # ID проверены по публичным каталогам/архивам Telegram Gifts.
    # Цена ниже — внутренняя цена WinesWork, а не историческая цена Telegram.
    {"name": "B-Day Candle", "emoji": "🕯", "gift_id": "5782984811920491178", "price": 12, "telegram_price": 350},
    {"name": "Desk Calendar", "emoji": "🗓", "gift_id": "5782988952268964995", "price": 18, "telegram_price": 150},
    {"name": "Homemade Cake", "emoji": "🎂", "gift_id": "5783075783622787539", "price": 24, "telegram_price": 500},
    {"name": "Sakura Flower", "emoji": "🌸", "gift_id": "5167939598143193218", "price": 12, "telegram_price": 25},
    {"name": "Lol Pop", "emoji": "🍭", "gift_id": "5170594532177215681", "price": 12, "telegram_price": 15},
    {"name": "Spy Agaric", "emoji": "🍄", "gift_id": "5821261908354794038", "price": 12, "telegram_price": 15},
    {"name": "Eternal Candle", "emoji": "🕯", "gift_id": "5821205665758053411", "price": 12, "telegram_price": 25},
    {"name": "Witch Hat", "emoji": "🎩", "gift_id": "5821384757304362229", "price": 12, "telegram_price": 15},
    {"name": "Scared Cat", "emoji": "🐈", "gift_id": "5837059369300132790", "price": 18, "telegram_price": 25},
    {"name": "Voodoo Doll", "emoji": "📍", "gift_id": "5836780359634649414", "price": 12, "telegram_price": 15},
    {"name": "Flying Broom", "emoji": "🧹", "gift_id": "5837063436634161765", "price": 12, "telegram_price": 15},
    {"name": "Record Player", "emoji": "🎵", "gift_id": "5856973938650776169", "price": 18, "telegram_price": 50},
    {"name": "Sharp Tongue", "emoji": "👅", "gift_id": "5841689550203650524", "price": 24, "telegram_price": 50},
    {"name": "Magic Potion", "emoji": "🧪", "gift_id": "5846226946928673709", "price": 30, "telegram_price": 50},
]

@dp.callback_query(F.data == "catalog:rare")
async def rare_catalog(call: CallbackQuery):
    if not await require_subscriptions_callback(call):
        return
    b = InlineKeyboardBuilder()
    for idx, gift in enumerate(ARCHIVED_GIFTS):
        b.button(text=f"{gift['emoji']} {gift['name']} — {gift['price']} ⭐", callback_data=f"archived:{idx}")
    b.adjust(1)
    b.row(button("Назад", callback_data="gifts", emoji_name="left1"))
    text = (
        f"{pe('star3','⭐️')} <b>Удалённые Подарки</b>\n\n"
        "Архивные подарки Telegram. Цена в WinesWork указана отдельно.\n"
        "После оплаты бот попытается отправить выбранный подарок напрямую через <code>sendGift</code>.\n\n"
        f"{pe('note1','📝')} Если Telegram больше не разрешает отправку конкретного ID, оплата не списывается окончательно — бот пытается автоматически вернуть Stars."
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=b.as_markup())
    await call.answer()

@dp.callback_query(F.data.startswith("archived:"))
async def archived_details(call: CallbackQuery):
    if not await require_subscriptions_callback(call):
        return
    try:
        idx = int(call.data.split(":", 1)[1])
        gift = ARCHIVED_GIFTS[idx]
    except (ValueError, IndexError):
        await call.answer("Подарок не найден", show_alert=True)
        return
    b = InlineKeyboardBuilder()
    b.row(button(f"Купить за {gift['price']} ⭐", callback_data=f"buyarch:{idx}", emoji_name="star1"))
    b.row(button("Назад", callback_data="catalog:rare", emoji_name="left1"))
    text = (
        f"{gift['emoji']} <b>{html.escape(gift['name'])}</b>\n\n"
        f"ID: <code>{gift['gift_id']}</code>\n"
        f"Цена WinesWork: <b>{gift['price']} ⭐</b>\n\n"
        "После оплаты подарок отправляется получателю автоматически.\n"
        "Для отправки используется официальный Telegram Bot API <code>sendGift</code>."
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=b.as_markup())
    await call.answer()

@dp.callback_query(F.data.startswith("buyarchself:"))
async def archived_buy_self(call: CallbackQuery):
    if not await require_subscriptions_callback(call):
        return
    try:
        idx = int(call.data.split(":", 1)[1])
        gift = ARCHIVED_GIFTS[idx]
    except (ValueError, IndexError):
        await call.answer("Подарок не найден", show_alert=True); return
    ok = await create_archived_invoice(call.from_user.id, gift, recipient_id=call.from_user.id)
    await call.answer("Счёт отправлен" if ok else "Не удалось создать счёт", show_alert=not ok)

@dp.callback_query(F.data.startswith("buyarchother:"))
async def archived_buy_other(call: CallbackQuery):
    if not await require_subscriptions_callback(call):
        return
    try:
        idx = int(call.data.split(":", 1)[1])
        gift = ARCHIVED_GIFTS[idx]
    except (ValueError, IndexError):
        await call.answer("Подарок не найден", show_alert=True); return
    set_setting(f"awaiting_archived_recipient_{call.from_user.id}", str(idx))
    await call.message.answer(
        f"{pe('gift','🎁')} Для подарка <b>{html.escape(gift['name'])}</b> отправь username получателя, например <code>@username</code>.",
        parse_mode="HTML")
    await call.answer()

@dp.callback_query(F.data.startswith("buyarch:"))
async def archived_buy_start(call: CallbackQuery):
    if not await require_subscriptions_callback(call):
        return
    try:
        idx = int(call.data.split(":", 1)[1])
        gift = ARCHIVED_GIFTS[idx]
    except (ValueError, IndexError):
        await call.answer("Подарок не найден", show_alert=True)
        return
    set_setting(f"pending_archived_{call.from_user.id}", str(idx))
    b = InlineKeyboardBuilder()
    b.row(button("Купить себе", callback_data=f"buyarchself:{idx}", emoji_name="gift"),
          button("Купить другому", callback_data=f"buyarchother:{idx}", emoji_name="gift"))
    b.row(button("Назад", callback_data=f"archived:{idx}", emoji_name="left1"))
    await call.message.edit_text(
        f"{gift['emoji']} <b>{html.escape(gift['name'])}</b>\n\n"
        f"Цена: <b>{gift['price']} ⭐</b>\n\n"
        "Выбери получателя:", parse_mode="HTML", reply_markup=b.as_markup())
    await call.answer()


# Скидка для покупателя. Разницу между ценой продажи и официальной ценой
# бот покрывает из собственного Stars-баланса.
GIFT_DISCOUNT_PERCENT = 34

# Фиксированные цены для основных официальных уровней Telegram.
SPECIAL_GIFT_PRICES = {
    "🧸": 2,
    "❤": 2,
    "❤️": 2,
}
PRICE_BY_OFFICIAL = {15: 3, 25: 17, 50: 31, 100: 73}


def get_sale_price(gift: dict) -> int:
    """Цена для покупателя ниже официальной цены Telegram.

    Для 🧸 и ❤️ действует цена 2 ⭐.
    Для остальных подарков используется скидка GIFT_DISCOUNT_PERCENT.
    Полную официальную стоимость sendGift оплачивает бот из своего Stars-баланса.
    """
    official_price = max(1, int(gift.get("star_count", 0)))
    emoji = str(gift.get("sticker", {}).get("emoji") or "🎁")

    special_price = SPECIAL_GIFT_PRICES.get(emoji)
    if special_price is not None:
        return max(1, min(official_price, special_price))
    if official_price in PRICE_BY_OFFICIAL:
        return max(1, min(official_price, PRICE_BY_OFFICIAL[official_price]))

    discount = max(0, min(90, int(GIFT_DISCOUNT_PERCENT)))
    sale_price = round(official_price * (100 - discount) / 100)
    return max(1, min(official_price, sale_price))


@dp.callback_query(F.data == "catalog:regular")
async def regular_catalog(call: CallbackQuery):
    if not await require_subscriptions_callback(call):
        return
    gifts = await get_available_gifts()
    if not gifts:
        await call.message.edit_text(
            f"{pe('cloud', '☁️')} Каталог сейчас обновляется. Попробуй открыть его ещё раз через несколько секунд.",
            reply_markup=back_menu("gifts")
        )
        await call.answer()
        return

    # Цена для покупателя ниже официальной; разницу покрывает Stars-баланс бота.
    builder = InlineKeyboardBuilder()
    for gift in gifts[:40]:
        gift_id = str(gift.get("id", ""))
        telegram_price = int(gift.get("star_count", 0))
        price = get_sale_price(gift)
        sticker = gift.get("sticker", {})
        emoji = sticker.get("emoji") or "🎁"
        limited = gift.get("remaining_count")
        status = f" · осталось {limited}" if limited is not None else ""
        button_kwargs = {
            "text": f"{emoji} {gift_label(gift)} · {price} ⭐{status}",
            "callback_data": f"gift:{gift_id}",
        }
        if sticker.get("custom_emoji_id"):
            button_kwargs["icon_custom_emoji_id"] = str(sticker["custom_emoji_id"])
        builder.button(**button_kwargs)
    builder.button(text="Назад", callback_data="gifts")
    builder.adjust(1)
    await call.message.edit_text(
        f"{pe('gift', '🎁')} <b>Доступные подарки</b>\n\n"
        f"Скидка для покупателя — <b>{GIFT_DISCOUNT_PERCENT}%</b>.\n"
        f"{pe('star1', '⭐')} Разницу до официальной цены бот оплачивает со своего Stars-баланса.\n"
        f"{pe('check', '✅')} После оплаты подарок автоматически отправится получателю.",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await call.answer()


@dp.callback_query(F.data.startswith("gift:"))
async def gift_details(call: CallbackQuery):
    if not await require_subscriptions_callback(call):
        return
    gift_id = call.data.split(":", 1)[1]
    gifts = await get_available_gifts()
    gift = next((g for g in gifts if str(g.get("id")) == gift_id), None)
    if not gift:
        await call.answer("Каталог обновляется. Открой раздел ещё раз.", show_alert=True)
        return

    telegram_price = int(gift.get("star_count", 0))
    price = get_sale_price(gift)
    emoji = gift.get("sticker", {}).get("emoji") or "🎁"
    name = gift_label(gift)
    remaining = gift.get("remaining_count")
    limit_text = f"\nОстаток: {remaining}" if remaining is not None else "\nКоличество: без указанного лимита"
    b = InlineKeyboardBuilder()
    b.button(text="Купить себе", callback_data=f"buy:{gift_id}:self")
    b.button(text="Купить другому", callback_data=f"buy:{gift_id}:other")
    b.button(text="К подаркам", callback_data="catalog:regular")
    b.adjust(1)
    await call.message.edit_text(
        f"{gift_visual(gift)} <b>{html.escape(name)}</b>\n\nID: <code>{gift_id}</code>\nЦена для покупателя: <b>{price} ⭐</b>\n"
        f"Официальная цена Telegram: <b>{telegram_price} ⭐</b>"
        f"{limit_text}\n\n"
        f"Скидка: <b>{GIFT_DISCOUNT_PERCENT}%</b>. Разницу до официальной цены "
        f"бот покрывает из собственного Stars-баланса. {pe('check', '✅')} "
        "После оплаты подарок автоматически отправится получателю.",
        parse_mode="HTML",
        reply_markup=b.as_markup()
    )
    await call.answer()


@dp.callback_query(F.data.startswith("buy:"))
async def buy_start(call: CallbackQuery):
    if not await require_subscriptions_callback(call):
        return
    _, gift_id, recipient_kind = call.data.split(":")
    gifts = await get_available_gifts()
    gift = next((g for g in gifts if str(g.get("id")) == gift_id), None)
    if not gift:
        await call.answer("Подарок временно обновляется. Открой каталог ещё раз.", show_alert=True)
        return
    if recipient_kind == "other":
        uid = call.from_user.id
        set_setting(f"awaiting_gift_recipient_{uid}", gift_id)
        set_setting(f"pending_recipient_{uid}", "")
        await call.message.edit_text(
            f"{pe('question','❓')} <b>Кому вы хотите отправить подарок?</b>\n\n"
            "Отправь @username получателя. Например: <code>@username</code>\n\n"
            "После этого появится выбор сообщения и затем оплата.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[button("Назад", callback_data=f"gift:{gift_id}", emoji_name="left1")]])
        )
        await call.answer()
        return

    set_setting(f"pending_gift_{call.from_user.id}", gift_id)
    set_setting(f"pending_message_{call.from_user.id}", "")
    name = gift_label(gift)
    b = InlineKeyboardBuilder()
    b.row(button("Без сообщения", callback_data=f"giftmsg:none:{gift_id}", emoji_name="cross1"))
    b.row(button("Написать сообщение", callback_data=f"giftmsg:custom:{gift_id}", emoji_name="pencil1"))
    b.row(button("Готовое сообщение", callback_data=f"giftmsg:ready:{gift_id}", emoji_name="note1"))
    b.row(button("Назад", callback_data=f"gift:{gift_id}", emoji_name="left1"))
    await call.message.edit_text(
        f"{pe('gift','🎁')} <b>{html.escape(name)}</b>\n\n"
        f"Цена: <b>{get_sale_price(gift)} ⭐</b>\n\n"
        f"{pe('note1','📝')} Выбери, какое сообщение получатель увидит вместе с подарком.",
        parse_mode="HTML", reply_markup=b.as_markup())
    await call.answer()

@dp.callback_query(F.data.startswith("giftmsg:ready:"))
async def gift_ready_messages(call: CallbackQuery):
    if not await require_subscriptions_callback(call):
        return
    gift_id = call.data.split(":", 2)[2]
    b = InlineKeyboardBuilder()
    messages = [
        ("🎉 С днём рождения!", "🎉 С днём рождения! Желаю счастья и исполнения желаний!"),
        ("❤️ От всего сердца!", "❤️ От всего сердца!"),
        ("✨ Просто хотел(а) порадовать тебя!", "✨ Просто хотел(а) порадовать тебя!"),
        ("🥰 Ты особенный человек!", "🥰 Ты особенный человек!"),
        ("Пошел нахуй бро!", "Пошел нахуй бро!"),
        ("📝 Своё сообщение", "custom"),
    ]
    for title, value in messages:
        if value == "custom":
            b.row(button(title, callback_data=f"giftmsg:custom:{gift_id}", emoji_name="pencil1"))
        else:
            token = secrets.token_hex(4)
            set_setting(f"ready_{call.from_user.id}_{token}", value)
            b.row(button(title, callback_data=f"giftready:{gift_id}:{token}", emoji_name="note1"))
    b.row(button("Назад", callback_data=f"buy:{gift_id}:self", emoji_name="left1"))
    await call.message.edit_text(
        f"{pe('note1','📝')} <b>Готовые сообщения</b>\n\nВыбери вариант:",
        parse_mode="HTML", reply_markup=b.as_markup()
    )
    await call.answer()

@dp.callback_query(F.data.startswith("giftready:"))
async def gift_ready_select(call: CallbackQuery):
    _, gift_id, token = call.data.split(":", 2)
    msg = get_setting(f"ready_{call.from_user.id}_{token}", "")
    if not msg:
        await call.answer("Сообщение устарело.", show_alert=True)
        return
    set_setting(f"ready_{call.from_user.id}_{token}", "")
    gifts = await get_available_gifts()
    gift = next((g for g in gifts if str(g.get("id")) == gift_id), None)
    if not gift:
        await call.answer("Подарок временно недоступен.", show_alert=True)
        return
    recipient_raw = get_setting(f"pending_recipient_{call.from_user.id}", "")
    recipient_id = int(recipient_raw) if recipient_raw else None
    recipient_username = get_setting(f"pending_recipient_username_{call.from_user.id}", "")
    ok = await create_gift_invoice(
        call.from_user.id, gift_id, gift, msg,
        recipient_id=recipient_id, recipient_username=recipient_username
    )
    await call.answer("Счёт отправлен." if ok else "Не удалось создать счёт.", show_alert=not ok)

@dp.callback_query(F.data.startswith("giftmsg:"))
async def gift_message_choice(call: CallbackQuery):
    if not await require_subscriptions_callback(call):
        return
    _, mode, gift_id = call.data.split(":", 2)
    gifts = await get_available_gifts()
    gift = next((g for g in gifts if str(g.get("id")) == gift_id), None)
    if not gift:
        await call.answer("Подарок временно недоступен.", show_alert=True); return
    if mode == "custom":
        set_setting(f"awaiting_gift_message_{call.from_user.id}", gift_id)
        await call.message.answer(f"{pe('pencil1','✏️')} Напиши своё сообщение для получателя одним сообщением (до 500 символов).")
        await call.answer()
        return
    recipient_raw = get_setting(f"pending_recipient_{call.from_user.id}", "")
    recipient_id = int(recipient_raw) if recipient_raw else None
    recipient_username = get_setting(f"pending_recipient_username_{call.from_user.id}", "")
    ok = await create_gift_invoice(
        call.from_user.id, gift_id, gift, "",
        recipient_id=recipient_id, recipient_username=recipient_username
    )
    await call.answer("Счёт отправлен." if ok else "Не удалось создать счёт. Попробуй позже.", show_alert=not ok)

async def get_bot_star_balance() -> int:
    """Возвращает текущий баланс Stars самого бота."""
    result = await api_call("getMyStarBalance")
    if not isinstance(result, dict):
        raise RuntimeError("Некорректный ответ getMyStarBalance")
    return int(result.get("amount", 0))


@dp.message(Command("balance"))
async def bot_balance_command(message: Message):
    if not is_admin(message):
        return
    try:
        balance = await get_bot_star_balance()
        await message.answer(
            f"{pe('star1', '⭐')} Баланс бота: <b>{balance} Stars</b>",
            parse_mode="HTML",
        )
    except Exception:
        await message.answer(
            f"{pe('warning', '⚠️')} Баланс временно не удалось получить. Попробуй ещё раз."
        )


@dp.pre_checkout_query()
async def pre_checkout(pre_checkout: PreCheckoutQuery):
    payload = pre_checkout.invoice_payload

    if payload.startswith("admin_topup:"):
        with db() as con:
            topup = con.execute("SELECT * FROM admin_topups WHERE payload=?", (payload,)).fetchone()
        if not topup or topup["status"] != "pending" or pre_checkout.currency != "XTR" or pre_checkout.total_amount != topup["amount"]:
            await pre_checkout.answer(ok=False, error_message="Счёт пополнения недействителен.")
            return
        await pre_checkout.answer(ok=True)
        return

    with db() as con:
        order = con.execute("SELECT * FROM orders WHERE payload=?", (payload,)).fetchone()

    if not order or order["status"] != "pending":
        await pre_checkout.answer(ok=False, error_message="Заказ уже обработан или не найден.")
        return

    if pre_checkout.currency != "XTR" or pre_checkout.total_amount != order["price"]:
        await pre_checkout.answer(ok=False, error_message="Сумма заказа изменилась. Открой подарок заново.")
        return

    if str(order["delivery_mode"]).startswith("archived_"):
        archived = next((g for g in ARCHIVED_GIFTS if str(g["gift_id"]) == str(order["gift_id"])), None)
        if not archived:
            await pre_checkout.answer(ok=False, error_message="Архивный подарок больше недоступен.")
            return
        try:
            balance = await get_bot_star_balance()
        except Exception:
            await pre_checkout.answer(ok=False, error_message="Не удалось проверить Stars-баланс бота. Попробуй позже.")
            return
        if balance < int(archived.get("telegram_price", archived["price"])):
            await pre_checkout.answer(ok=False, error_message="Недостаточно Stars в резерве бота для отправки этого подарка.")
            return
        await pre_checkout.answer(ok=True)
        return

    try:
        balance = await get_bot_star_balance()
    except Exception:
        # Если не удалось узнать баланс, безопаснее не принимать оплату:
        # иначе скидка может оказаться больше доступного резерва бота.
        await pre_checkout.answer(
            ok=False,
            error_message="Не удалось проверить Stars-баланс бота. Попробуй оплатить ещё раз позже."
        )
        return

    # Бот оплачивает полную официальную стоимость sendGift.
    # Покупатель платит цену со скидкой, поэтому из баланса бота заранее
    # должен быть доступен минимум размер скидки.
    gifts = await get_available_gifts()
    gift = next((g for g in gifts if str(g.get("id")) == str(order["gift_id"])), None)
    if not gift:
        gifts = await get_available_gifts(force_refresh=True)
        gift = next((g for g in gifts if str(g.get("id")) == str(order["gift_id"])), None)
    gift_cost = int(gift.get("star_count", 0)) if gift else 0

    if not gift or gift_cost < 1:
        await pre_checkout.answer(
            ok=False,
            error_message="Каталог подарков сейчас обновляется. Открой подарок заново через несколько секунд."
        )
        return

    subsidy = max(0, gift_cost - int(order["price"]))
    if balance < subsidy:
        await pre_checkout.answer(
            ok=False,
            error_message="Сейчас недостаточно Stars в резерве бота для этой скидки. Попробуй позже."
        )
        return

    await pre_checkout.answer(ok=True)


@dp.message(F.successful_payment)
async def successful_payment(message: Message):
    payment = message.successful_payment
    payload = payment.invoice_payload

    if payload.startswith("admin_topup:"):
        with db() as con:
            topup = con.execute("SELECT * FROM admin_topups WHERE payload=?", (payload,)).fetchone()
            if not topup or int(topup["admin_id"]) != int(message.from_user.id):
                await message.answer(f"{pe('warning','⚠️')} Платёж получен, но пополнение не найдено для этого администратора.", parse_mode="HTML")
                return
            con.execute("UPDATE admin_topups SET status='paid', charge_id=? WHERE payload=?", (payment.telegram_payment_charge_id, payload))
        await message.answer(f"{pe('check','✅')} Баланс бота пополнен на <b>{topup['amount']} Stars</b>.", parse_mode="HTML")
        return

    with db() as con:
        order = con.execute("SELECT * FROM orders WHERE payload=?", (payload,)).fetchone()
        if not order:
            await message.answer("Платёж получен, но заказ не найден.")
            return
        if order["status"] in ("paid", "delivered"):
            await message.answer("Этот заказ уже обработан.")
            return
        con.execute(
            "UPDATE orders SET status='paid', charge_id=? WHERE payload=?",
            (payment.telegram_payment_charge_id, payload)
        )

    # Если получатель ещё не запускал бота, выдаём покупателю персональную ссылку.
    # После нажатия ссылки получателем подарок будет отправлен автоматически.
    if order["delivery_mode"] == "archived_pending_recipient":
        try:
            link = await make_voucher(int(order["id"]), str(order["gift_id"]))
            with db() as con:
                con.execute("UPDATE orders SET status='paid' WHERE payload=?", (payload,))
            b = InlineKeyboardBuilder()
            b.row(button("Открыть ссылку", url=link, emoji_name="gift"))
            await message.answer(
                f"{pe('check','✅')} <b>Оплата получена.</b>\n\n"
                f"{html.escape(order['gift_name'])}\n"
                "Получатель ещё не запускал WinesWork. Передай ему эту одноразовую ссылку.",
                parse_mode="HTML", reply_markup=b.as_markup())
            return
        except Exception:
            await message.answer(f"{pe('warning','⚠️')} Оплата получена, но ссылка пока не создана. Повторно не оплачивай.", parse_mode="HTML")
            return

    if order["delivery_mode"] == "archived_direct":
        try:
            recipient_id = int(order["recipient_id"] or message.from_user.id)
            kwargs = {"user_id": recipient_id, "gift_id": str(order["gift_id"])}
            if order["gift_message"]:
                kwargs["text"] = order["gift_message"][:128]
            result = await api_call("sendGift", **kwargs)
            if result is not True:
                raise RuntimeError("archived sendGift failed")
            with db() as con:
                con.execute("UPDATE orders SET status='delivered' WHERE payload=?", (payload,))
            await message.answer(
                f"{pe('check','✅')} <b>Удалённый подарок отправлен!</b>\n\n"
                f"{html.escape(order['gift_name'])}\n"
                f"Получатель: <code>{recipient_id}</code>", parse_mode="HTML")
            return
        except Exception:
            try:
                await api_call("refundStarPayment", user_id=int(order["user_id"]),
                               telegram_payment_charge_id=payment.telegram_payment_charge_id)
                with db() as con:
                    con.execute("UPDATE orders SET status='refunded' WHERE payload=?", (payload,))
                await message.answer(
                    f"{pe('warning','⚠️')} Telegram не разрешил отправить этот архивный подарок. "
                    "Оплата автоматически возвращена.", parse_mode="HTML")
            except Exception:
                await message.answer(
                    f"{pe('warning','⚠️')} Оплата получена, но архивный подарок пока не отправлен. "
                    "Повторно оплачивать не нужно.", parse_mode="HTML")
            return

    if order["delivery_mode"] == "pending_recipient":
        try:
            gifts = await get_available_gifts(force_refresh=True)
            gift = next((g for g in gifts if str(g.get("id")) == str(order["gift_id"])), None)
            token = secrets.token_urlsafe(12)
            with db() as con:
                con.execute(
                    "INSERT INTO gift_links(token, order_id, gift_id, password_hash, created_at) VALUES(?,?,?,?,?)",
                    (token, int(order["id"]), str(order["gift_id"]), None, now())
                )
            username = await bot_username()
            link = f"https://t.me/{username}?start=gift_{token}"
            with db() as con:
                con.execute("UPDATE orders SET status='paid' WHERE payload=?", (payload,))
            b = InlineKeyboardBuilder()
            b.row(button("Ссылка для получателя", url=link, emoji_name="link1"))
            b.row(button("Профиль", callback_data="profile", emoji_name="eye1"))
            target = f"@{html.escape(order['recipient_username'])}" if order["recipient_username"] else "получателя"
            await message.answer(
                f"{pe('check','✅')} <b>Оплата прошла!</b>\n\n"
                f"{gift_visual(gift) if 'gift' in locals() and gift else pe('gift','🎁')} "
                f"<b>{html.escape(order['gift_name'])}</b>\n\n"
                f"Получатель: <b>{target}</b>\n"
                "Он ещё не запускал бота, поэтому Telegram не позволяет отправить подарок напрямую.\n\n"
                "Передай ему эту ссылку. После нажатия <b>/start</b> подарок автоматически отправится ему.",
                parse_mode="HTML", reply_markup=b.as_markup()
            )
            return
        except Exception:
            await message.answer(
                f"{pe('warning','⚠️')} Оплата получена, но ссылка для получателя пока не создана. "
                "Не оплачивай повторно — заказ сохранён.",
                parse_mode="HTML"
            )
            return

    # Обычная покупка: подарок отправляется сразу, если получатель уже известен боту.
    if order["delivery_mode"] == "direct":
        try:
            gifts = await get_available_gifts(force_refresh=True)
            gift = next((g for g in gifts if str(g.get("id")) == str(order["gift_id"])), None)
            cost = int(gift.get("star_count", 0)) if gift else 0
            balance = await get_bot_star_balance()
            if not gift or cost < 1 or balance < cost:
                raise RuntimeError("gift unavailable or insufficient balance")
            recipient_id = int(order["recipient_id"] or message.from_user.id)
            kwargs = {"user_id": recipient_id, "gift_id": order["gift_id"]}
            if order["gift_message"]:
                kwargs["text"] = order["gift_message"]
            result = await api_call("sendGift", **kwargs)
            if result is not True:
                raise RuntimeError("sendGift failed")
            with db() as con:
                con.execute("UPDATE orders SET status='delivered', recipient_id=? WHERE payload=?", (recipient_id, payload))
            recipient_id = int(order["recipient_id"] or message.from_user.id)
            recipient_text = f"получателю <code>{recipient_id}</code>" if recipient_id != message.from_user.id else "тебе"
            await message.answer(
                f"{pe('check','✅')} <b>Подарок отправлен!</b>\n\n"
                f"{gift_visual(gift)} {html.escape(order['gift_name'])}\n"
                f"Получатель: {recipient_text}\n"
                f"{pe('note1','📝')} Сообщение отправлено вместе с подарком.",
                parse_mode="HTML"
            )
            return
        except Exception:
            try:
                await api_call("refundStarPayment", user_id=int(order["user_id"]),
                               telegram_payment_charge_id=payment.telegram_payment_charge_id)
                with db() as con:
                    con.execute("UPDATE orders SET status='refunded' WHERE payload=?", (payload,))
                await message.answer(
                    f"{pe('warning','⚠️')} Подарок временно не удалось отправить. "
                    f"Оплата автоматически возвращена.",
                    parse_mode="HTML"
                )
            except Exception:
                await message.answer(
                    f"{pe('warning','⚠️')} Оплата получена, но подарок пока не отправлен. "
                    f"Повторно оплачивать не нужно.",
                    parse_mode="HTML"
                )
            return

    # Чек-подарок: только здесь создаём ссылку.
    try:
        link = await make_voucher(int(order["id"]), str(order["gift_id"]))
        with db() as con:
            con.execute("UPDATE orders SET status='paid' WHERE payload=?", (payload,))
        b = InlineKeyboardBuilder()
        b.row(button("Открыть чек", url=link, emoji_name="check"))
        b.row(button("Поставить пароль", callback_data=f"voucher:password:{order['id']}", emoji_name="lock"))
        b.row(button("Назад", callback_data="profile", emoji_name="left1"))
        await message.answer(
            f"{pe('check','✅')} <b>Чек-подарок готов!</b>\n\n"
            f"{pe('gift','🎁')} {html.escape(order['gift_name'])}\n"
            f"{pe('star1','⭐')} Оплачено: <b>4 Stars</b>\n\n"
            f"Передай ссылку получателю. После открытия бот автоматически отправит подарок от своего имени.\n"
            f"Ссылка одноразовая.",
            parse_mode="HTML", reply_markup=b.as_markup())
        return
    except Exception:
        await message.answer(f"{pe('warning','⚠️')} Оплата получена, но чек временно не создан. Заказ сохранён.", parse_mode="HTML")


async def claim_voucher(message: Message, token: str):
    with db() as con:
        link = con.execute("SELECT * FROM gift_links WHERE token=?", (token,)).fetchone()
        if not link:
            await message.answer(f"{pe('warning','⚠️')} Ссылка недействительна или уже использована.", parse_mode="HTML")
            return
        if link["claimed_at"]:
            await message.answer(f"{pe('warning','⚠️')} Этот чек уже использован.", parse_mode="HTML")
            return
    if link["password_hash"]:
        set_setting(f"voucher_password_{message.from_user.id}", token)
        await message.answer(f"{pe('lock','🔐')} Введи пароль от чека одним сообщением.", parse_mode="HTML")
        return
    await deliver_voucher(message, token)

async def deliver_voucher(message: Message, token: str, password: str = ""):
    with db() as con:
        link = con.execute("SELECT * FROM gift_links WHERE token=?", (token,)).fetchone()
        if not link or link["claimed_at"]:
            await message.answer(f"{pe('warning','⚠️')} Этот чек недействителен или уже использован.", parse_mode="HTML")
            return
        if link["password_hash"] and hash_voucher_password(password) != link["password_hash"]:
            await message.answer(f"{pe('cross1','❌')} Неверный пароль.", parse_mode="HTML")
            return
        order = con.execute("SELECT * FROM orders WHERE id=?", (link["order_id"],)).fetchone()
    if not order:
        await message.answer(f"{pe('warning','⚠️')} Заказ не найден.", parse_mode="HTML")
        return
    target_username = str(order["recipient_username"] or "").strip().lstrip("@").lower() if "recipient_username" in order.keys() else ""
    if target_username:
        current_username = (message.from_user.username or "").strip().lstrip("@").lower()
        if current_username != target_username:
            await message.answer(
                f"{pe('warning','⚠️')} Эта ссылка предназначена для @{html.escape(target_username)}.\n\n"
                "Открой её с аккаунта, которому предназначен подарок.",
                parse_mode="HTML"
            )
            return
    try:
        balance = await get_bot_star_balance()
        gifts = await get_available_gifts(force_refresh=True)
        gift = next((g for g in gifts if str(g.get("id")) == str(order["gift_id"])), None)
        cost = int(gift.get("star_count", 0)) if gift else 0
        if not gift or balance < cost:
            await message.answer(f"{pe('warning','⚠️')} Сейчас недостаточно Stars или подарок временно недоступен. Попробуй позже.", parse_mode="HTML")
            return
        kwargs = {"user_id": message.from_user.id, "gift_id": order["gift_id"]}
        if order["gift_message"]:
            kwargs["text"] = order["gift_message"]
        result = await api_call("sendGift", **kwargs)
        if result is not True:
            raise RuntimeError("sendGift returned false")
        with db() as con:
            con.execute("UPDATE gift_links SET claimed_by=?, claimed_at=? WHERE token=? AND claimed_at IS NULL", (message.from_user.id, now(), token))
            con.execute("UPDATE orders SET status='delivered', recipient_id=? WHERE id=?", (message.from_user.id, order["id"]))
        if order["delivery_mode"] == "pending_recipient":
            await message.answer(
                f"{pe('check','✅')} <b>Подарок получен!</b>\n\n"
                f"{gift_visual(gift)} <b>{html.escape(order['gift_name'])}</b>\n"
                "Подарок автоматически отправлен тебе.",
                parse_mode="HTML"
            )
        else:
            await message.answer(f"{pe('check','✅')} Подарок автоматически отправлен тебе!", parse_mode="HTML")
    except Exception:
        await message.answer(f"{pe('warning','⚠️')} Не удалось выдать подарок сейчас. Ссылка останется действительной — попробуй позже.", parse_mode="HTML")

@dp.callback_query(F.data.startswith("voucher:password:"))
async def voucher_password_start(call: CallbackQuery):
    try:
        order_id = int(call.data.rsplit(":",1)[1])
    except Exception:
        await call.answer("Некорректный чек.", show_alert=True); return
    with db() as con:
        order = con.execute("SELECT * FROM orders WHERE id=? AND user_id=?", (order_id, call.from_user.id)).fetchone()
    if not order:
        await call.answer("Чек не найден.", show_alert=True); return
    set_setting(f"awaiting_voucher_password_{call.from_user.id}", str(order_id))
    await call.message.answer(f"{pe('lock','🔐')} Отправь пароль для ссылки одним сообщением (4–64 символа).")
    await call.answer()

@dp.callback_query(F.data == "admin:panel")
async def admin_panel(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("Нет доступа.", show_alert=True)
        return
    try:
        balance = await get_bot_star_balance()
        balance_text = f"{balance} Stars"
    except Exception:
        balance_text = "временно недоступен"
    with db() as con:
        users = con.execute("SELECT COUNT(*) n FROM users").fetchone()["n"]
        orders = con.execute("SELECT COUNT(*) n FROM orders").fetchone()["n"]
        delivered = con.execute("SELECT COUNT(*) n FROM orders WHERE status='delivered'").fetchone()["n"]
        paid = con.execute("SELECT COUNT(*) n FROM orders WHERE status='paid'").fetchone()["n"]
        revenue = con.execute("SELECT COALESCE(SUM(price),0) n FROM orders WHERE status IN ('paid','delivered')").fetchone()["n"]
        reviews = con.execute("SELECT COUNT(*) n FROM reviews").fetchone()["n"]
    text=(
        f"{pe('gear1','⚙️')} <b>Панель администратора</b>\n\n"
        f"{pe('star1','⭐')} Баланс бота: <b>{balance_text}</b>\n"
        f"{pe('desktop','🖥')} Пользователей: <b>{users}</b>\n"
        f"{pe('gift','🎁')} Заказов: <b>{orders}</b>\n"
        f"{pe('check','✅')} Доставлено: <b>{delivered}</b>\n"
        f"{pe('warning','⚠️')} Оплачено, ждёт выдачи: <b>{paid}</b>\n"
        f"{pe('star2','⭐')} Выручка: <b>{revenue} Stars</b>\n"
        f"{pe('note1','📝')} Отзывов: <b>{reviews}</b>"
    )
    b=InlineKeyboardBuilder()
    b.row(button("Статистика", callback_data="admin:stats", emoji_name="desktop"), button("Топ по чекам", callback_data="admin:top", emoji_name="star3"))
    b.row(button("Пополнить баланс", callback_data="admin:topup", emoji_name="plus"))
    b.row(button("Заказы", callback_data="admin:orders", emoji_name="document"))
    b.row(button("🎁 Бесплатный чек", callback_data="admin:voucher_free", emoji_name="gift"))
    b.row(button("📣 Рассылка", callback_data="admin:broadcast", emoji_name="news1"))
    b.row(button("Назад", callback_data="home", emoji_name="left1"))
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=b.as_markup())
    await call.answer()

@dp.callback_query(F.data == "admin:voucher_free")
async def admin_voucher_free(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        return await call.answer("Нет доступа.", show_alert=True)
    gifts = await get_available_gifts()
    b = InlineKeyboardBuilder()
    for g in gifts:
        gid = str(g.get("id"))
        name = gift_label(g)
        sticker = g.get("sticker") or {}
        gift_emoji_id = sticker.get("custom_emoji_id")
        visible_emoji = str(sticker.get("emoji") or g.get("emoji") or "🎁").strip()
        # На кнопке показываем именно эмодзи выбранного подарка; ID остаётся внутренним.
        b.row(button(f"{visible_emoji} {name} — бесплатно", callback_data=f"admin:voucher_make:{gid}", custom_emoji_id=gift_emoji_id or PREMIUM_EMOJI_IDS.get("gift")))
    b.row(button("Назад", callback_data="admin:panel", emoji_name="left1"))
    await call.message.edit_text(
        "🎁 <b>Бесплатный чек-подарок</b>\n\nВыбери подарок:",
        parse_mode="HTML",
        reply_markup=b.as_markup()
    )
    await call.answer()


@dp.callback_query(F.data.startswith("admin:voucher_make:"))
async def admin_voucher_make(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        return await call.answer("Нет доступа.", show_alert=True)
    gid = call.data.split(":", 2)[2]
    try:
        gifts = await get_available_gifts(force_refresh=True)
        gift = next((g for g in gifts if str(g.get("id")) == gid), None)
        if not gift:
            gifts = await get_available_gifts()
            gift = next((g for g in gifts if str(g.get("id")) == gid), None)
        if not gift:
            return await call.answer("Подарок сейчас недоступен. Обнови каталог и попробуй снова.", show_alert=True)
        order_id = await create_admin_voucher_order(
            call.from_user.id, gid, "Подарок от администратора"
        )
        token = await make_voucher(order_id, gid)
        username = await bot_username()
        if not username:
            raise RuntimeError("Не удалось определить username бота")
        link = f"https://t.me/{username}?start=gift_{token}"
    except Exception as exc:
        logging.getLogger("WinesWork").exception("Ошибка создания бесплатного чека: %s", exc)
        return await call.answer("Не удалось создать бесплатный чек. Проверь связь с Telegram и попробуй ещё раз.", show_alert=True)
    b = InlineKeyboardBuilder()
    b.row(button("Открыть чек", url=link, emoji_name="check"))
    b.row(button("Изменить подпись", callback_data=f"admin:voucher_msg:{order_id}", emoji_name="pencil1"))
    b.row(button("Назад", callback_data="admin:panel", emoji_name="left1"))
    await call.message.edit_text(
        f"{gift_visual(gift)} <b>Чек-подарок создан бесплатно</b>\n\n"
        f"🎁 Подарок: <b>{html.escape(gift_label(gift))}</b>\n"
        f"🔗 <code>{link}</code>\n\n"
        f"📨 Сообщение: <b>От администратора</b>\n"
        f"💫 Цена для получателя: <b>0 ⭐</b>",
        parse_mode="HTML",
        reply_markup=b.as_markup()
    )
    # Ссылка дополнительно отправляется всем администраторам отдельным сообщением,
    # чтобы бесплатный чек не потерялся и его можно было сразу переслать.
    admin_notice = (
        f"{gift_visual(gift)} <b>Новый бесплатный чек-подарок</b>\n\n"
        f"Подарок: <b>{html.escape(gift_label(gift))}</b>\n"
        f"Создал: <code>{call.from_user.id}</code>\n"
        f"Ссылка: <code>{link}</code>"
    )
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_notice, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[button("Открыть чек", url=link, emoji_name="check")]]))
        except Exception:
            pass
    await call.answer("Бесплатный чек создан и отправлен администраторам")


@dp.callback_query(F.data.startswith("admin:voucher_msg:"))
async def admin_voucher_msg_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in ADMIN_IDS:
        return await call.answer("Нет доступа.", show_alert=True)
    order_id=call.data.rsplit(":",1)[1]
    set_setting(f"admin_voucher_message_{call.from_user.id}", order_id)
    await state.set_state("admin_voucher_message")
    await call.message.answer("📝 Отправь подпись для подарка (до 128 символов).")
    await call.answer()

@dp.message(StateFilter("admin_voucher_message"))
async def admin_voucher_msg_receive(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await state.clear(); return
    order_id=get_setting(f"admin_voucher_message_{message.from_user.id}", "")
    set_setting(f"admin_voucher_message_{message.from_user.id}", "")
    await state.clear()
    msg=(message.text or message.caption or "").strip()[:128]
    if not msg:
        await message.answer("❌ Подпись пустая."); return
    with db() as con:
        order=con.execute("SELECT * FROM orders WHERE id=? AND user_id=? AND delivery_mode='voucher'", (int(order_id), message.from_user.id)).fetchone()
    if not order:
        await message.answer("❌ Чек не найден."); return
    with db() as con:
        con.execute("UPDATE orders SET gift_message=? WHERE id=?", (msg, int(order_id)))
        con.execute("DELETE FROM gift_links WHERE order_id=? AND claimed_at IS NULL", (int(order_id),))
    link=await make_voucher(int(order_id), str(order["gift_id"]))
    b=InlineKeyboardBuilder(); b.row(button("Открыть чек", url=link, emoji_name="check"))
    await message.answer("✅ Подпись обновлена. Ссылка пересоздана.", reply_markup=b.as_markup())

@dp.callback_query(F.data == "admin:stats")
async def admin_stats(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return await call.answer("Нет доступа.", show_alert=True)
    with db() as con:
        rows=con.execute("SELECT status, COUNT(*) n FROM orders GROUP BY status").fetchall()
        by_gift=con.execute("SELECT gift_name, COUNT(*) n, COALESCE(SUM(price),0) stars FROM orders WHERE status IN ('paid','delivered') GROUP BY gift_name ORDER BY n DESC LIMIT 10").fetchall()
    statuses = "\n".join(f"• {html.escape(r['status'])}: <b>{r['n']}</b>" for r in rows) or "Нет заказов"
    gifts = "\n".join(f"• {html.escape(r['gift_name'])}: {r['n']} шт. · {r['stars']} ⭐" for r in by_gift) or "Нет продаж"
    text=f"{pe('desktop','🖥')} <b>Статистика</b>\n\n<b>Статусы:</b>\n{statuses}\n\n<b>Популярные подарки:</b>\n{gifts}"
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_menu("admin:panel", "left1"))
    await call.answer()

@dp.callback_query(F.data == "admin:top")
async def admin_top(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return await call.answer("Нет доступа.", show_alert=True)
    with db() as con:
        rows=con.execute("""SELECT user_id, COALESCE(username,'') username, COUNT(*) checks, COALESCE(SUM(price),0) total FROM orders WHERE status IN ('paid','delivered') GROUP BY user_id ORDER BY total DESC, checks DESC LIMIT 15""").fetchall()
    lines=[f"{pe('star3','⭐')} <b>Топ по чекам</b>\n"]
    for i,r in enumerate(rows,1):
        name='@'+html.escape(r['username']) if r['username'] else f"ID {r['user_id']}"
        lines.append(f"<b>{i}.</b> {name} — <b>{r['total']} Stars</b> · {r['checks']} чек(ов)")
    if not rows: lines.append("Пока покупок нет.")
    await call.message.edit_text("\n".join(lines), parse_mode="HTML", reply_markup=back_menu("admin:panel"))
    await call.answer()

@dp.callback_query(F.data == "admin:orders")
async def admin_orders_panel(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return await call.answer("Нет доступа.", show_alert=True)
    with db() as con:
        rows=con.execute("SELECT id,user_id,gift_id,price,status,created_at FROM orders ORDER BY id DESC LIMIT 20").fetchall()
    lines=[f"{pe('document','📄')} <b>Последние заказы</b>"]
    for r in rows:
        lines.append(f"#{r['id']} · ID {r['user_id']} · {r['price']} ⭐ · {html.escape(r['status'])}")
    if not rows: lines.append("Заказов пока нет.")
    await call.message.edit_text("\n".join(lines), parse_mode="HTML", reply_markup=back_menu("admin:panel"))
    await call.answer()

@dp.callback_query(F.data == "admin:topup")
async def admin_topup_start(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return await call.answer("Нет доступа.", show_alert=True)
    set_setting("pending_topup_admin", str(call.from_user.id))
    await call.message.answer(f"{pe('plus','➕')} <b>Пополнение Stars-баланса бота</b>\n\nОтправь сумму в Stars одним сообщением, например: <code>100</code>.\nПосле этого бот выставит счёт тебе, и оплаченные Stars поступят на баланс бота.", parse_mode="HTML")
    await call.answer()

@dp.message(F.text.regexp(r"^\d+$"))
async def admin_topup_amount(message: Message):
    if not is_admin(message) or get_setting("pending_topup_admin") != str(message.from_user.id):
        return
    amount=int(message.text)
    if amount < 1 or amount > 25000:
        await message.answer(f"{pe('warning','⚠️')} Укажи сумму от 1 до 25000 Stars.", parse_mode="HTML")
        return
    set_setting("pending_topup_admin", "")
    payload=f"admin_topup:{message.from_user.id}:{int(time.time())}"
    with db() as con:
        con.execute("INSERT INTO admin_topups(payload,admin_id,amount,status,created_at) VALUES(?,?,?,?,?)", (payload,message.from_user.id,amount,'pending',now()))
    try:
        await bot.send_invoice(chat_id=message.from_user.id,title="Пополнение баланса WinesWork",description=f"Пополнение Stars-баланса бота на {amount} Stars.",payload=payload,currency="XTR",prices=[LabeledPrice(label="Пополнение баланса",amount=amount)],provider_token="")
        await message.answer(f"{pe('check','✅')} Счёт на <b>{amount} Stars</b> создан. После оплаты Stars поступят на баланс бота.", parse_mode="HTML")
    except TelegramAPIError:
        with db() as con: con.execute("UPDATE admin_topups SET status='invoice_failed' WHERE payload=?",(payload,))
        await message.answer(f"{pe('warning','⚠️')} Не удалось создать счёт.", parse_mode="HTML")

@dp.callback_query(F.data == "ideas")
async def ideas_start(call: CallbackQuery, state: FSMContext):
    if not await require_subscriptions_callback(call): return
    await state.set_state("idea_text")
    await call.message.answer("💡 Напиши свою идею, предложение или пожелание одним сообщением.")
    await call.answer()

@dp.message(StateFilter("idea_text"))
async def ideas_receive(message: Message, state: FSMContext):
    if user_blocked(message.from_user.id):
        await state.clear(); return
    text_in=(message.text or message.caption or "").strip()[:1000]
    await state.clear()
    if not text_in:
        await message.answer("❌ Идея пустая."); return
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, f"💡 <b>Новая идея</b>\n\nОт: <code>{message.from_user.id}</code>\n{text_in}", parse_mode="HTML")
        except Exception: pass
    await message.answer("✅ Спасибо! Идея отправлена администраторам.")

@dp.callback_query(F.data == "reviews")
async def reviews_menu(call: CallbackQuery):
    if not await require_subscriptions_callback(call):
        return
    b = InlineKeyboardBuilder()
    b.add(button("Оставить отзыв", callback_data="review:add", emoji_name="pencil1"))
    b.add(button("Последние отзывы", callback_data="review:list", emoji_name="note1"))
    b.add(button("Назад", callback_data="home", emoji_name="left1"))
    b.adjust(1)
    await call.message.edit_text(f"{pe('star2', '⭐️')} <b>Отзывы</b>\n\nВыбери действие:", parse_mode="HTML", reply_markup=b.as_markup())
    await call.answer()


@dp.callback_query(F.data == "review:add")
async def review_add(call: CallbackQuery, state: FSMContext):
    if not await require_subscriptions_callback(call):
        return
    await state.set_state("review_text")
    await call.message.answer(
        "⭐ <b>Новый отзыв</b>\n\n"
        "Отправь одним сообщением оценку от 1 до 5 и текст.\n"
        "Например: <code>5 Отличный бот, всё работает!</code>\n\n"
        "Отмена: /cancel",
        parse_mode="HTML"
    )
    await call.answer()


@dp.message(StateFilter("review_text"))
async def review_state_save(message: Message, state: FSMContext):
    if not await require_subscriptions_message(message):
        await state.clear()
        return
    raw = (message.text or "").strip()
    if raw.lower() == "/cancel":
        await state.clear()
        await message.answer("❌ Оставление отзыва отменено.")
        return
    parts = raw.split(maxsplit=1)
    if len(parts) < 2 or not parts[0].isdigit() or not 1 <= int(parts[0]) <= 5:
        await message.answer("Формат: <code>5 Отличный бот!</code>", parse_mode="HTML")
        return
    rating, text = int(parts[0]), parts[1].strip()
    if len(text) < 3 or len(text) > 800:
        await message.answer("Текст отзыва должен быть длиной от 3 до 800 символов.")
        return
    with db() as con:
        con.execute(
            "INSERT INTO reviews(user_id, username, rating, text, created_at) VALUES(?,?,?,?,?)",
            (message.from_user.id, message.from_user.username, rating, text, now())
        )
    await state.clear()
    await message.answer(f"{pe('check', '✅')} Спасибо! Отзыв опубликован.")


@dp.message(Command("review"))
async def review_save(message: Message):
    if not await require_subscriptions_message(message):
        return
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3 or not parts[1].isdigit() or not 1 <= int(parts[1]) <= 5:
        await message.answer("Формат: /review 5 Текст отзыва (оценка от 1 до 5)")
        return
    rating, text = int(parts[1]), parts[2].strip()
    if len(text) < 3 or len(text) > 800:
        await message.answer("Текст отзыва должен быть длиной от 3 до 800 символов.")
        return
    with db() as con:
        con.execute(
            "INSERT INTO reviews(user_id, username, rating, text, created_at) VALUES(?,?,?,?,?)",
            (message.from_user.id, message.from_user.username, rating, text, now())
        )
    await message.answer(f"{pe('check', '✅')} Спасибо! Отзыв сохранён")


@dp.callback_query(F.data == "review:list")
async def review_list(call: CallbackQuery):
    if not await require_subscriptions_callback(call):
        return
    with db() as con:
        rows = con.execute(
            "SELECT username, rating, text, created_at FROM reviews ORDER BY id DESC LIMIT 10"
        ).fetchall()
    if not rows:
        text = "Пока отзывов нет."
    else:
        chunks = [f"{pe('star2','⭐')} <b>Последние отзывы</b>\n"]
        for r in rows:
            username = "@" + r["username"] if r["username"] else "Пользователь"
            safe_text = r["text"].replace("<", "&lt;").replace(">", "&gt;")
            chunks.append(f"{pe('star2','⭐')} × {r['rating']} — {username}\n{safe_text}")
        text = "\n\n".join(chunks)
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_menu("reviews"))
    await call.answer()


@dp.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Текущее действие отменено.")


@dp.message(Command("ban"))
async def admin_ban(message: Message):
    if not is_admin(message): return
    parts=(message.text or "").split(maxsplit=2)
    if len(parts)<2 or not parts[1].isdigit():
        await message.answer("Использование: /ban ID [причина]"); return
    uid=int(parts[1]); reason=parts[2] if len(parts)>2 else "Без причины"
    if uid in ADMIN_IDS:
        await message.answer("❌ Нельзя заблокировать администратора."); return
    ban_user(uid, reason, message.from_user.id)
    await message.answer(f"🚫 Пользователь <code>{uid}</code> заблокирован.\nПричина: {html.escape(reason)}", parse_mode="HTML")

@dp.message(Command("unban"))
async def admin_unban(message: Message):
    if not is_admin(message): return
    parts=(message.text or "").split(maxsplit=1)
    if len(parts)<2 or not parts[1].isdigit():
        await message.answer("Использование: /unban ID"); return
    uid=int(parts[1]); unban_user(uid)
    await message.answer(f"✅ Пользователь <code>{uid}</code> разблокирован.", parse_mode="HTML")

@dp.message(Command("banlist"))
async def admin_banlist(message: Message):
    if not is_admin(message): return
    with db() as con: rows=con.execute("SELECT user_id,reason FROM bans ORDER BY created_at DESC LIMIT 100").fetchall()
    if not rows: await message.answer("Бан-лист пуст."); return
    lines=["🚫 <b>Бан-лист</b>"]+[f"<code>{r['user_id']}</code> — {html.escape(r['reason'])}" for r in rows]
    await message.answer("\n".join(lines), parse_mode="HTML")

@dp.message(Command("orders"))
async def admin_orders(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    with db() as con:
        rows = con.execute(
            "SELECT id,user_id,gift_id,price,status,created_at FROM orders ORDER BY id DESC LIMIT 20"
        ).fetchall()
    if not rows:
        await message.answer("Заказов пока нет.")
        return
    lines = [f"{pe('document','📄')} <b>Последние заказы</b>"]
    for r in rows:
        lines.append(
            f"#{r['id']} user={r['user_id']} gift={r['gift_id']} "
            f"{r['price']}⭐ status={r['status']} {r['created_at']}"
        )
    await message.answer("\n".join(lines), parse_mode="HTML")


@dp.message(F.text)
async def text_router(message: Message):
    if not message.from_user or message.chat.type != "private":
        return
    uid = message.from_user.id
    text_in = (message.text or "").strip()
    if text_in.startswith("/"):
        return

    awaiting_archived = get_setting(f"awaiting_archived_recipient_{uid}", "")
    if awaiting_archived:
        try:
            idx = int(awaiting_archived); archived = ARCHIVED_GIFTS[idx]
        except (ValueError, IndexError):
            set_setting(f"awaiting_archived_recipient_{uid}", "")
            await message.answer("Подарок не найден. Открой каталог заново."); return
        raw = text_in.strip()
        username = raw.lstrip("@").split()[0]
        if not re.fullmatch(r"[A-Za-z0-9_]{5,32}", username):
            await message.answer("Укажи корректный username, например <code>@username</code>", parse_mode="HTML"); return
        with db() as con:
            row = con.execute("SELECT user_id FROM users WHERE lower(username)=? LIMIT 1", (username.lower(),)).fetchone()
        recipient_id = int(row["user_id"]) if row else None
        set_setting(f"awaiting_archived_recipient_{uid}", "")
        ok = await create_archived_invoice(uid, archived, recipient_id=recipient_id, recipient_username=username)
        if ok:
            if recipient_id:
                await message.answer(f"{pe('check','✅')} Получатель найден. После оплаты <b>{html.escape(archived['name'])}</b> отправится ему автоматически.", parse_mode="HTML")
            else:
                await message.answer(f"{pe('check','✅')} Счёт создан. Получатель ещё не запускал WinesWork — после оплаты будет создана персональная ссылка.", parse_mode="HTML")
        else:
            await message.answer(f"{pe('warning','⚠️')} Не удалось создать счёт.", parse_mode="HTML")
        return

    # Выбор получателя для покупки подарка другому пользователю.
    awaiting_recipient = get_setting(f"awaiting_gift_recipient_{uid}", "")
    if awaiting_recipient:
        raw_username = text_in.strip()
        if raw_username.startswith("https://t.me/"):
            username = raw_username.rstrip("/").split("/")[-1]
        elif raw_username.startswith("t.me/"):
            username = raw_username.rstrip("/").split("/")[-1]
        else:
            username = raw_username.lstrip("@").split()[0]
        if not re.fullmatch(r"[A-Za-z0-9_]{5,32}", username):
            await message.answer(
                f"{pe('warning','⚠️')} Укажи корректный username Telegram.\n\nПример: <code>@username</code>",
                parse_mode="HTML"
            )
            return

        # Если человек уже запускал WinesWork, у нас есть его Telegram ID и
        # подарок можно отправить автоматически сразу после оплаты.
        with db() as con:
            row = con.execute(
                "SELECT user_id, username, first_name FROM users WHERE lower(username)=? LIMIT 1",
                (username.lower(),)
            ).fetchone()
        recipient_id = int(row["user_id"]) if row else None
        if recipient_id == uid:
            await message.answer(f"{pe('warning','⚠️')} Это твой собственный username. Для себя используй «Купить себе».", parse_mode="HTML")
            return

        set_setting(f"awaiting_gift_recipient_{uid}", "")
        set_setting(f"pending_recipient_{uid}", str(recipient_id) if recipient_id else "")
        set_setting(f"pending_recipient_username_{uid}", username)
        gift_id = awaiting_recipient
        gifts = await get_available_gifts()
        gift = next((g for g in gifts if str(g.get("id")) == str(gift_id)), None)
        if not gift:
            gifts = await get_available_gifts(force_refresh=True)
            gift = next((g for g in gifts if str(g.get("id")) == str(gift_id)), None)
        if not gift:
            await message.answer(f"{pe('warning','⚠️')} Подарок временно недоступен. Открой каталог заново.", parse_mode="HTML")
            return

        set_setting(f"pending_gift_{uid}", gift_id)
        set_setting(f"pending_message_{uid}", "")
        name = gift_label(gift)
        b = InlineKeyboardBuilder()
        b.row(button("Без сообщения", callback_data=f"giftmsg:none:{gift_id}", emoji_name="cross1"))
        b.row(button("Написать сообщение", callback_data=f"giftmsg:custom:{gift_id}", emoji_name="pencil1"))
        b.row(button("Готовое сообщение", callback_data=f"giftmsg:ready:{gift_id}", emoji_name="note1"))
        b.row(button("Изменить получателя", callback_data=f"buy:{gift_id}:other", emoji_name="repeat"))

        if recipient_id:
            status_text = "Получатель уже запускал WinesWork — после оплаты подарок уйдёт ему автоматически."
        else:
            status_text = (
                "Получатель ещё не запускал WinesWork. После оплаты бот выдаст тебе персональную ссылку; "
                "получатель нажмёт её, и подарок автоматически отправится ему."
            )
        await message.answer(
            f"{pe('check','✅')} Получатель: <b>@{html.escape(username)}</b>\n\n"
            f"{gift_visual(gift)} <b>{html.escape(name)}</b>\n"
            f"Цена: <b>{get_sale_price(gift)} ⭐</b>\n\n"
            f"{pe('info','ℹ️')} {status_text}\n\n"
            f"{pe('note1','📝')} Теперь выбери сообщение для получателя:",
            parse_mode="HTML", reply_markup=b.as_markup()
        )
        return

    # Установка пароля для уже созданного чека.
    pending_order = get_setting(f"awaiting_voucher_password_{uid}", "")
    if pending_order:
        set_setting(f"awaiting_voucher_password_{uid}", "")
        password = text_in[:64]
        if len(password) < 4:
            await message.answer(f"{pe('warning','⚠️')} Пароль должен быть не короче 4 символов.", parse_mode="HTML")
            return
        with db() as con:
            order = con.execute("SELECT * FROM orders WHERE id=? AND user_id=? AND delivery_mode='voucher' AND status='paid'",
                                 (int(pending_order), uid)).fetchone()
        if not order:
            await message.answer(f"{pe('warning','⚠️')} Чек не найден.", parse_mode="HTML")
            return
        try:
            link = await make_voucher(int(order["id"]), str(order["gift_id"]), password)
            b = InlineKeyboardBuilder()
            b.row(button("Открыть защищённый чек", url=link, emoji_name="lock"))
            await message.answer(
                f"{pe('lock','🔐')} Пароль установлен.\n\nПередай получателю эту ссылку и пароль отдельно.",
                parse_mode="HTML", reply_markup=b.as_markup()
            )
        except Exception:
            await message.answer(f"{pe('warning','⚠️')} Не удалось обновить чек.", parse_mode="HTML")
        return

    # Пароль для защищённого чека.
    token = get_setting(f"voucher_password_{uid}", "")
    if token:
        await deliver_voucher(message, token, text_in[:64])
        set_setting(f"voucher_password_{uid}", "")
        return

    # Пользовательское сообщение для чека-подарка.
    voucher_gift_id = get_setting(f"awaiting_voucher_message_{uid}", "")
    if voucher_gift_id:
        set_setting(f"awaiting_voucher_message_{uid}", "")
        ok = await create_voucher_invoice(uid, voucher_gift_id, text_in[:500])
        await message.answer(
            f"{pe('check','✅')} Счёт на чек-подарок за <b>4 ⭐</b> отправлен."
            if ok else
            f"{pe('warning','⚠️')} Не удалось создать счёт. Попробуй позже.",
            parse_mode="HTML"
        )
        return

    # Готовые сообщения.
    ready = {
        "🎉 С днём рождения! Желаю счастья и исполнения желаний!": "🎉 С днём рождения! Желаю счастья и исполнения желаний!",
        "❤️ От всего сердца!": "❤️ От всего сердца!",
        "✨ Просто хотел(а) порадовать тебя!": "✨ Просто хотел(а) порадовать тебя!",
        "🥰 Ты особенный человек!": "🥰 Ты особенный человек!",
        "Пошел нахуй бро!": "Пошел нахуй бро!",
    }
    pending_ready = get_setting(f"awaiting_ready_message_{uid}", "")
    if pending_ready:
        set_setting(f"awaiting_ready_message_{uid}", "")
        # Это сообщение относится к текущей покупке подарка.
        gift_id_ready = get_setting(f"pending_gift_{uid}", "")
        if gift_id_ready:
            gifts = await get_available_gifts()
            gift = next((g for g in gifts if str(g.get("id")) == gift_id_ready), None)
            if gift:
                recipient_raw = get_setting(f"pending_recipient_{uid}", "")
                recipient_id = int(recipient_raw) if recipient_raw else None
                recipient_username = get_setting(f"pending_recipient_username_{uid}", "")
                ok = await create_gift_invoice(uid, gift_id_ready, gift, ready.get(text_in, text_in)[:500], recipient_id=recipient_id, recipient_username=recipient_username)
                await message.answer(f"{pe('check','✅')} Счёт отправлен." if ok else f"{pe('warning','⚠️')} Не удалось создать счёт.", parse_mode="HTML")
                return

    # Пользовательский комментарий к подарку.
    gift_id = get_setting(f"awaiting_gift_message_{uid}", "")
    if gift_id:
        set_setting(f"awaiting_gift_message_{uid}", "")
        gifts = await get_available_gifts()
        gift = next((g for g in gifts if str(g.get("id")) == gift_id), None)
        if not gift:
            await message.answer(f"{pe('warning','⚠️')} Подарок временно недоступен. Открой каталог заново.", parse_mode="HTML")
            return
        recipient_raw = get_setting(f"pending_recipient_{uid}", "")
        recipient_id = int(recipient_raw) if recipient_raw else None
        recipient_username = get_setting(f"pending_recipient_username_{uid}", "")
        ok = await create_gift_invoice(uid, gift_id, gift, text_in[:500], recipient_id=recipient_id, recipient_username=recipient_username)
        if ok:
            await message.answer(f"{pe('check','✅')} Счёт создан. После оплаты подарок будет автоматически отправлен выбранному получателю.", parse_mode="HTML")
        else:
            await message.answer(f"{pe('warning','⚠️')} Не удалось создать счёт. Попробуй позже.", parse_mode="HTML")
        return




@dp.errors()
async def handle_bot_errors(event: ErrorEvent):
    """Не даёт временным сетевым сбоям Telegram ломать обработку update."""
    exc = event.exception
    if isinstance(exc, (TelegramNetworkError, aiohttp.ClientError, ConnectionError, TimeoutError)):
        # Сетевые сбои кратковременны и обрабатываются retry-логикой.
        # Не засоряем консоль Pydroid одинаковыми WARNING при каждом update.
        logging.getLogger("WinesWork").debug(
            "Telegram API временно недоступен — запрос будет повторён автоматически."
        )
        return True
    logging.getLogger("WinesWork").exception("Ошибка обработки Telegram update", exc_info=exc)
    return True


async def safe_start_polling():
    """Запускает polling и спокойно переживает обрыв соединения с Telegram."""
    logger = logging.getLogger("WinesWork")
    delay = 3
    while True:
        try:
            await dp.start_polling(bot)
            return
        except asyncio.CancelledError:
            raise
        except (TelegramNetworkError, aiohttp.ClientError, ConnectionError, TimeoutError):
            logger.debug("Соединение с Telegram потеряно. Повтор через %s сек.", delay)
            await asyncio.sleep(delay)
            delay = min(delay + 2, 15)
        except Exception:
            logger.exception("Ошибка polling. Повтор через %s сек.", delay)
            await asyncio.sleep(delay)
            delay = min(delay + 2, 15)


async def main():
    init_db()

    if not CHILD_MODE:
        load_and_launch_partners()

    # Токен берётся только из переменной окружения.
    if not BOT_TOKEN:
        return

    retry_delay = 5
    max_retry_delay = 60
    while True:
        try:
            await safe_start_polling()
            retry_delay = 5
            break
        except Exception as exc:
            logging.getLogger("WinesWork").debug(
                "Polling временно остановлен: %s. Повтор через %s сек.",
                exc, retry_delay
            )
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, max_retry_delay)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        logging.getLogger("WinesWork").exception("Критическая ошибка запуска", exc_info=exc)
