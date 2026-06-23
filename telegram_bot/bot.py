"""
Full-featured Telegram bot for reading_reels.
Interactive video customization + generation + delivery.

Start:  python -m telegram_bot.bot
"""
from __future__ import annotations
import os, asyncio, threading, tempfile
from collections import defaultdict
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from dotenv import load_dotenv

from app.config_loader import load_config
from app.pipeline import Pipeline

# Load .env BEFORE reading env vars (supports both local .env and Railway OS env)
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

# ── user session ──────────────────────────────────────────────
# session[chat_id] = {
#   "level": "B1", "topic": "", "style": "auto", "voice": True,
#   "count": 1, "busy": False, "pipeline": Pipeline, "cfg": Config
# }
sessions: dict = defaultdict(dict)
cfg = None
pipes: dict = {}

LEVEL_EMOJI = {"A1": "🟢", "A2": "🟡", "B1": "🟠", "B2": "🔵", "C1": "🔴"}
TOPIC_FAMILIES = {
    "daily_life": "🏠 الحياة اليومية",
    "work": "💼 العمل",
    "travel": "🌍 السفر",
    "study": "📚 الدراسة",
    "motivation": "🔥 تحفيز",
    "micro_story": "📖 قصة قصيرة",
}
STYLES = {"auto": "🎲 تلقائي", "motivational": "🔥 تحفيزي", "calm": "🌙 هادئ", "cinematic": "🎬 سينمائي", "bright": "☀️ مشرق"}
COUNTS = [1, 2, 3, 5, 10]


def get_sess(chat_id):
    s = sessions[chat_id]
    s.setdefault("level", "B1")
    s.setdefault("topic", "")
    s.setdefault("style", "auto")
    s.setdefault("voice", True)
    s.setdefault("count", 1)
    if chat_id not in pipes:
        pipes[chat_id] = Pipeline(cfg)
    s["pipeline"] = pipes[chat_id]
    return s


# ── keyboards ─────────────────────────────────────────────────
def main_menu():
    kb = [
        [InlineKeyboardButton("🎬 إنشاء فيديو جديد", callback_data="new")],
        [InlineKeyboardButton("📊 حالتي المفضلة", callback_data="status")],
        [InlineKeyboardButton("🛠 الإعدادات", callback_data="settings")],
    ]
    return InlineKeyboardMarkup(kb)


def settings_keyboard(sess):
    level = sess["level"]
    style = sess["style"]
    voice = sess["voice"]
    kb = [
        [InlineKeyboardButton(f"📊 المستوى: {LEVEL_EMOJI[level]} {level}", callback_data="set_level")],
        [InlineKeyboardButton(f"🎨 الأسلوب: {STYLES.get(style, style)}", callback_data="set_style")],
        [InlineKeyboardButton(f"🔊 الصوت: {'✅ مفعل' if voice else '❌ معطل'}", callback_data="toggle_voice")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(kb)


def level_keyboard():
    kb = [
        [InlineKeyboardButton(f"{LEVEL_EMOJI['A1']} A1 - مبتدئ", callback_data="level_A1"),
         InlineKeyboardButton(f"{LEVEL_EMOJI['A2']} A2 - أساسي", callback_data="level_A2")],
        [InlineKeyboardButton(f"{LEVEL_EMOJI['B1']} B1 - متوسط", callback_data="level_B1"),
         InlineKeyboardButton(f"{LEVEL_EMOJI['B2']} B2 - متقدم", callback_data="level_B2")],
        [InlineKeyboardButton(f"{LEVEL_EMOJI['C1']} C1 - محترف", callback_data="level_C1")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="back_settings")],
    ]
    return InlineKeyboardMarkup(kb)


def style_keyboard():
    kb = [
        [InlineKeyboardButton(f"{v}", callback_data=f"style_{k}")] for k, v in STYLES.items()
    ]
    kb.append([InlineKeyboardButton("⬅️ رجوع", callback_data="back_settings")])
    return InlineKeyboardMarkup(kb)


def count_keyboard():
    kb = [
        [InlineKeyboardButton(f"📹 {c} فيديو" if c == 1 else f"📹 {c} فيديوهات", callback_data=f"count_{c}")]
        for c in COUNTS
    ]
    kb.append([InlineKeyboardButton("❌ إلغاء", callback_data="back_main")])
    return InlineKeyboardMarkup(kb)


def topic_keyboard():
    kb = [[InlineKeyboardButton(v, callback_data=f"topic_{k}")] for k, v in TOPIC_FAMILIES.items()]
    kb.append([InlineKeyboardButton("🎲 عشوائي", callback_data="topic_random")])
    kb.append([InlineKeyboardButton("❌ إلغاء", callback_data="back_main")])
    return InlineKeyboardMarkup(kb)


def confirm_keyboard(sess):
    kb = [
        [InlineKeyboardButton("✅ نعم - ابدأ!", callback_data="launch")],
        [InlineKeyboardButton("📹 اختر العدد", callback_data="set_count")],
        [InlineKeyboardButton("📊 غير المستوى", callback_data="set_level")],
        [InlineKeyboardButton("📂 غير الموضوع", callback_data="set_topic")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(kb)


# ── commands ──────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً بك في بوت **Reading Reels** 🎬\n\n"
        "أقوى أداة لصنع فيديوهات تعليم القراءة الإنجليزية المتوافقة مع خوارزميات تيك توك 2026!\n\n"
        "اختر من القائمة:",
        reply_markup=main_menu(), parse_mode="Markdown"
    )


async def handle_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    chat_id = q.message.chat_id
    s = get_sess(chat_id)
    d = q.data

    # ── navigation ──
    if d == "new":
        await q.edit_message_text("اختر موضوع الفيديو 📂", reply_markup=topic_keyboard())
    elif d == "status":
        await status_cmd(update, ctx, edit=True)
    elif d == "settings":
        await show_settings(update, s)
    elif d == "back_main":
        await q.edit_message_text("القائمة الرئيسية:", reply_markup=main_menu())
    elif d == "back_settings":
        await show_settings(update, s)

    # ── level ──
    elif d == "set_level":
        await q.edit_message_text("اختر المستوى التعليمي 📊", reply_markup=level_keyboard())
    elif d.startswith("level_"):
        lv = d.split("_", 1)[1]
        s["level"] = lv
        await show_settings(update, s)

    # ── style ──
    elif d == "set_style":
        await q.edit_message_text("اختر أسلوب الفيديو 🎨", reply_markup=style_keyboard())
    elif d.startswith("style_"):
        st = d.split("_", 1)[1]
        s["style"] = st
        await show_settings(update, s)

    # ── voice toggle ──
    elif d == "toggle_voice":
        s["voice"] = not s["voice"]
        await show_settings(update, s)

    # ── topic ──
    elif d.startswith("topic_"):
        tp = d.split("_", 1)[1]
        if tp == "random":
            s["topic"] = ""
        else:
            s["topic"] = tp
        await show_confirm(update, s)

    # ── count ──
    elif d == "set_count":
        await q.edit_message_text("كم فيديو تريد؟", reply_markup=count_keyboard())
    elif d.startswith("count_"):
        s["count"] = int(d.split("_")[1])
        await show_confirm(update, s)

    # ── launch ──
    elif d == "launch":
        await q.edit_message_text("جاري التوليد... ⏳")
        await run_generation(q, chat_id)

    # ── set topic ──
    elif d == "set_topic":
        await q.edit_message_text("اختر الموضوع 📂", reply_markup=topic_keyboard())


async def show_settings(update: Update, s):
    q = update.callback_query
    summary = (
        f"⚙️ **الإعدادات الحالية**\n\n"
        f"📊 المستوى: {LEVEL_EMOJI[s['level']]} **{s['level']}**\n"
        f"🎨 الأسلوب : {STYLES.get(s['style'], s['style'])}\n"
        f"🔊 الصوت   : {'✅ مفعل' if s['voice'] else '❌ معطل'}\n"
        f"📹 العدد    : **{s['count']}** فيديو\n"
        f"📂 الموضوع : {'🎲 عشوائي' if not s['topic'] else TOPIC_FAMILIES.get(s['topic'], s['topic'])}"
    )
    await q.edit_message_text(summary, reply_markup=settings_keyboard(s), parse_mode="Markdown")


async def show_confirm(update: Update, s):
    q = update.callback_query
    summary = (
        f"🔍 **مراجعة قبل البدء:**\n\n"
        f"📊 المستوى : {LEVEL_EMOJI[s['level']]} **{s['level']}**\n"
        f"🎨 الأسلوب  : {STYLES.get(s['style'], s['style'])}\n"
        f"🔊 الصوت    : {'✅ مفعل' if s['voice'] else '❌ معطل'}\n"
        f"📹 العدد     : **{s['count']}**\n"
        f"📂 الموضوع  : {'🎲 عشوائي' if not s['topic'] else TOPIC_FAMILIES.get(s['topic'], s['topic'])}\n\n"
        f"هل تريد البدء؟"
    )
    await q.edit_message_text(summary, reply_markup=confirm_keyboard(s), parse_mode="Markdown")


async def status_cmd(update: Update, ctx, edit=False):
    chat_id = (update.callback_query.message.chat_id if edit else update.message.chat_id) if update.callback_query else update.message.chat_id
    if hasattr(update, "message") and update.message:
        chat_id = update.message.chat_id
    s = sessions.get(chat_id, {})
    level = s.get("level", "B1")
    style = s.get("style", "auto")
    voice = s.get("voice", True)
    count = s.get("count", 1)
    topic = s.get("topic", "")
    text = (
        f"📊 **حالتك المفضلة**\n\n"
        f"المستوى: {LEVEL_EMOJI.get(level,'')} {level}\n"
        f"الأسلوب: {STYLES.get(style, style)}\n"
        f"الصوت: {'✅' if voice else '❌'}\n"
        f"العدد الافتراضي: {count}\n"
        f"الموضوع: {'عشوائي' if not topic else topic}\n"
    )
    if edit:
        await update.callback_query.edit_message_text(text, reply_markup=main_menu(), parse_mode="Markdown")
    else:
        await update.message.reply_text(text, parse_mode="Markdown")


async def run_generation(callback_query, chat_id):
    s = get_sess(chat_id)
    pipe: Pipeline = s["pipeline"]
    count = s["count"]
    level = s["level"]
    topic = s["topic"] or None
    voice = s["voice"]

    await callback_query.message.reply_text(f"🔨 جاري إنشاء {count} فيديو...\n📊 المستوى: {level}\n📂 {'عشوائي' if not topic else topic}")

    results = []
    for i in range(count):
        await callback_query.message.reply_text(f"⏳ فيديو {i+1}/{count}...")
        try:
            r = pipe.generate_one(level, topic=topic, account=None, seed=None, with_audio=voice)
            results.append(r)
            vid_path = r["video"]
            meta = r.get("meta", {})
            caption = meta.get("caption", "")[:1000]
            with open(vid_path, "rb") as f:
                await callback_query.message.reply_video(
                    video=f, caption=f"{'🔊' if voice else '🔇'} مستوى {level} | {meta.get('title', '')}\n\n{caption}",
                    supports_streaming=True
                )
        except Exception as e:
            await callback_query.message.reply_text(f"❌ فشل الفيديو {i+1}: {str(e)[:200]}")

    await callback_query.message.reply_text(
        f"✅ **تم الانتهاء!** {len(results)}/{count} فيديو ناجح.\n\nلتجربة جديدة: /start",
        reply_markup=main_menu(), parse_mode="Markdown"
    )


# ── main ──────────────────────────────────────────────────────
def main():
    global cfg
    cfg = load_config()

    token = BOT_TOKEN
    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN not set in environment.")
        return

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("Bot is running... Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
