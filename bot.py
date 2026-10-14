
import asyncio
import logging
import os
import sqlite3
import time

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery, LabeledPrice, PreCheckoutQuery,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

# =========================================================
#                        CONFIG
# =========================================================
BOT_TOKEN   = os.getenv("BOT_TOKEN")

# ID Telegram des admins (toi). Va voir @userinfobot pour ton ID.
ADMIN_IDS   = [int(os.getenv("ADMIN_ID", "0"))]

# Chaîne + groupe obligatoires
CHANNEL_ID  = os.getenv("CHANNEL_ID", "@PhenixGuy")
GROUP_ID    = os.getenv("GROUP_ID", "@phenixchat")
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/PhenixGuy")
GROUP_URL   = os.getenv("GROUP_URL", "https://t.me/phenixchat")

# IA locale via Ollama (pas de clé API, pas de filtre backend)
AI_API_URL  = os.getenv("AI_API_URL", "http://localhost:11434/api/generate")
AI_MODEL    = os.getenv("AI_MODEL", "llama3")

# L'IA est spécialisée "dev web" : elle construit du code de site.
SYSTEM_PROMPT = (
    "Tu es un développeur web expert. L'utilisateur décrit un site, "
    "tu réponds UNIQUEMENT avec du code complet et fonctionnel "
    "(HTML/CSS/JS, ou React, Vue, PHP, etc. selon la demande). "
    "Structure claire, responsive, prêt à copier-coller. "
    "Si la demande est floue, choisis la meilleure stack et livre le code."
)

# Limite gratuite
FREE_LIMIT  = 10
WINDOW_H    = 24

DB = "bot.db"

# Premium : étoiles -> jours
PREMIUM_TIERS = {
    50:   14,
    100:  28,
    200:  63,
    500:  180,
    1000: 420,
}

# =========================================================
#                      BASE DE DONNÉES
# =========================================================
def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS users(
            uid           INTEGER PRIMARY KEY,
            count         INTEGER DEFAULT 0,
            window_start  REAL    DEFAULT 0,
            premium_until REAL    DEFAULT 0)""")

def get_user(uid):
    with db() as c:
        row = c.execute("SELECT * FROM users WHERE uid=?", (uid,)).fetchone()
        if not row:
            c.execute("INSERT INTO users(uid, window_start) VALUES(?,?)",
                      (uid, time.time()))
            row = c.execute("SELECT * FROM users WHERE uid=?", (uid,)).fetchone()
    return row

def is_premium(row):
    return row["premium_until"] > time.time()

def check_quota(uid):
    row = get_user(uid)
    if is_premium(row):
        return True, 999
    now = time.time()
    if now - row["window_start"] > WINDOW_H * 3600:
        with db() as c:
            c.execute("UPDATE users SET count=0, window_start=? WHERE uid=?",
                      (now, uid))
        row = get_user(uid)
    left = FREE_LIMIT - row["count"]
    return left > 0, max(left, 0)

def inc_count(uid):
    with db() as c:
        c.execute("UPDATE users SET count=count+1 WHERE uid=?", (uid,))

def add_premium(uid, days):
    row = get_user(uid)
    base = max(row["premium_until"], time.time())
    until = base + days * 86400
    with db() as c:
        c.execute("UPDATE users SET premium_until=? WHERE uid=?", (until, uid))
    return until

def del_premium(uid):
    with db() as c:
        c.execute("UPDATE users SET premium_until=0 WHERE uid=?", (uid,))

# =========================================================
#                        BOT
# =========================================================
logging.basicConfig(level=logging.INFO)
bot = Bot(BOT_TOKEN)
dp  = Dispatcher()

async def subscribed(uid):
    for chat in (CHANNEL_ID, GROUP_ID):
        try:
            m = await bot.get_chat_member(chat, uid)
            if m.status in ("left", "kicked"):
                return False
        except Exception:
            return False
    return True

def sub_kb():
    b = InlineKeyboardBuilder()
    b.button(text="📢 S'abonner à la chaîne", url=CHANNEL_URL)
    b.button(text="👥 Rejoindre le groupe",   url=GROUP_URL)
    b.button(text="✅ J'ai fait",             callback_data="check")
    b.adjust(1)
    return b.as_markup()

# ------------------------- /start -------------------------
@dp.message(CommandStart())
async def start(m: Message):
    if not await subscribed(m.from_user.id):
        await m.answer(
            "ᴀᴠᴀɴᴛ ᴅᴇ sɪᴄᴜᴛᴇʀ, àʙᴏɴɴᴇ-ᴛᴏɪ ᴀ ᴍᴀ ᴄʜᴀɴᴇ ᴇᴛ ᴍᴏɴ ɢʀᴏᴜᴘᴇ 👇",
            reply_markup=sub_kb())
        return
    await m.answer("sᴀʟᴜᴛ 👋 ᴛᴜ ᴠᴇᴜx ᴄᴏᴅᴇʀ ǫᴜᴇʟ sɪᴛᴇ ᴅᴇᴄʀɪs ʟᴇ sɪᴛᴇ 1ᴜᴇ ᴛᴜ ᴠᴇᴜx ᴊᴇ ᴛᴇ ᴄᴏᴅᴇ çᴀ ᴠɪᴛᴇ ғᴀɪᴛ ᴇᴛ ʙɪᴇɴ ғᴀɪᴛ. 🍓\n"
                   "Tape /premium pour l'illimité.")

@dp.callback_query(F.data == "check")
async def check(cb: CallbackQuery):
    if await subscribed(cb.from_user.id):
        await cb.message.edit_text("✅ᴄ'ᴇsᴛ ʙᴏɴ, ᴛᴜ ᴘᴇᴜx ᴅɪsᴄᴜᴛᴇʀ !♘")
    else:
        await cb.answer("ᴘᴀs ᴇɴᴄᴏʀᴇ ᴀʙᴏɴɴé 😅", show_alert=True)

# ------------------- ADMIN : premium ---------------------
@dp.message(Command("givepremium"))
async def givepremium(m: Message):
    if m.from_user.id not in ADMIN_IDS:
        return
    try:
        _, target, days = m.text.split()
        target, days = int(target), int(days)
    except Exception:
        await m.answer("Usage : /givepremium <user_id> <jours>")
        return
    add_premium(target, days)
    await m.answer(f"✅ᴘʀᴇᴍɪᴜᴍ  {days}j ᴀᴄᴛɪᴠé ᴘᴏᴜʀ {target}")

@dp.message(Command("delpremium"))
async def delpremium(m: Message):
    if m.from_user.id not in ADMIN_IDS:
        return
    try:
        target = int(m.text.split()[1])
    except Exception:
        await m.answer("Usage : /delpremium <user_id>")
        return
    del_premium(target)
    await m.answer(f"❌ᴘʀᴇᴍɪᴜᴍ ʀᴇᴛɪʀé ᴀ {target}")

# ------------------------- /premium ----------------------
@dp.message(Command("premium"))
async def premium(m: Message):
    b = InlineKeyboardBuilder()
    for stars, days in PREMIUM_TIERS.items():
        b.button(text=f"{stars} ⭐ — {days} ᴊᴏᴜʀs", callback_data=f"buy:{stars}")
    b.button(text="❌ Fermer", callback_data="close")
    b.adjust(1)
    await m.answer("ᴘᴀssᴇ ᴇɴ *ᴘʀᴇᴍɪᴜᴍ* : ɪᴀ ɪʟʟɪᴍɪᴛéᴇ ᴘʟᴜs ᴅᴇ ʟɪᴍɪᴛᴇ 24ʜ ×͜×.",
                   parse_mode="Markdown", reply_markup=b.as_markup())

@dp.callback_query(F.data == "close")
async def close(cb: CallbackQuery):
    await cb.message.delete()

@dp.callback_query(F.data.startswith("buy:"))
async def buy(cb: CallbackQuery):
    stars = int(cb.data.split(":")[1])
    days  = PREMIUM_TIERS[stars]
    await bot.send_invoice(
        chat_id=cb.from_user.id,
        title="Premium IA",
        description=f"{days} jours d'accès illimité",
        payload=f"premium:{stars}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Premium", amount=stars)],
    )
    await cb.answer()

@dp.pre_checkout_query()
async def pre_checkout(q: PreCheckoutQuery):
    await q.answer(ok=True)

@dp.message(F.successful_payment)
async def paid(m: Message):
    stars = int(m.successful_payment.invoice_payload.split(":")[1])
    days  = PREMIUM_TIERS.get(stars, 14)
    add_premium(m.from_user.id, days)
    await m.answer(f"🎉 ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴛɪᴠé ᴘᴏᴜʀ {days} ᴊᴏᴜʀs ! ᴘʀᴏғɪᴛᴇ ʙɪᴇɴ ᴅᴜ ʙᴇsᴛ ɪᴀ.")

# ========================= IA ============================
======================= .star VIDEO ======================

STAR_VIDEO = "https://www.image2url.com/r2/default/videos/1791989101630-b8bbb94a-6c43-4f5d-8d00-878bb7e5c4ba.mp4"

@dp.message(F.text == ".star")
async def star_command(m: Message):
await m.answer_video(
video=STAR_VIDEO,
caption="⭐ PHENIX GEMINI ⭐"
)
async def ask_ai(text):
    import aiohttp
    prompt = f"{SYSTEM_PROMPT}\n\nDemande utilisateur : {text}"
    async with aiohttp.ClientSession() as s:
        async with s.post(AI_API_URL,
                          json={"model": AI_MODEL, "prompt": prompt,
                                "stream": False}) as r:
            return (await r.json())["response"]

@dp.message(F.text)
async def handle(m: Message):
    uid = m.from_user.id

    if not await subscribed(uid):
        await m.answer("Abonne-toi d'abord 👇", reply_markup=sub_kb())
        return

    ok, left = check_quota(uid)
    if not ok:
        await m.answer("⏳ ʟɪᴍɪᴛᴇ ᴅᴇ 10 ǫᴜᴇsᴛɪᴏɴ /24ʜ ᴀᴛᴛᴇɪɴᴛᴇ 🐾.\n"
                       "ᴀᴛᴛᴇɴᴅs 24 ʜ ᴘᴏᴜʀ ᴄᴏᴅé ᴛ'ᴇs ᴏᴜᴛɪʟs ᴏᴜ ᴘʀᴇɴᴅs /ᴘʀᴇᴍɪᴜᴍ ᴘᴏᴜʀ ʟ'ɪʟʟɪᴍɪᴛé.")
        return

    inc_count(uid)
    await bot.send_chat_action(m.chat.id, "typing")
    try:
        ans = await ask_ai(m.text)
    except Exception as e:
        await m.answer(f"Erreur IA : {e}")
        return
    await m.answer(ans)

# =========================================================
if __name__ == "__main__":
    init_db()
    asyncio.run(dp.start_polling(bot))
