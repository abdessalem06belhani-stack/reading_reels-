"""
TikTok Factory Bot — بوت تليجرام مخصص لمصنع فيديوهات التيك توك.

يتيح:
  - اختيار النيش (5 نيشات)
  - توليد فيديوهات HD
  - معاينة وإرسال الفيديو
  - توليد batch (3, 5, 10 فيديوهات)
  - جدولة يومية

التشغيل:  python -m telegram_bot.factory_bot
"""
from __future__ import annotations
import os, asyncio
from collections import defaultdict
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from app.config_loader import load_config
from tiktok_factory.factory import TikTokFactory, SUPPORTED_NICHES

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

# ── Session ─────────────────────────────────────────────────────
sessions: dict = defaultdict(dict)
cfg = None

NICHE_EMOJI = {
    "finance": "💰",
    "ai_tools": "🤖",
    "real_estate": "🏠",
    "health_biohacking": "🧬",
    "productivity": "⚡",
}

NICHE_NAMES = {
    "finance": "تمويل واستثمار",
    "ai_tools": "أدوات AI وتقنية",
    "real_estate": "عقارات وثروة",
    "health_biohacking": "صحة و Biohacking",
    "productivity": "إنتاجية وأنظمة",
}

BATCH_SIZES = [1, 3, 5, 10]


def get_sess(chat_id):
    s = sessions[chat_id]
    s.setdefault("niche", "finance")
    s.setdefault("batch", 1)
    s.setdefault("audio", True)
    if "factory" not in s:
        s["factory"] = TikTokFactory(cfg)
    return s


# ── Keyboards ───────────────────────────────────────────────────
def main_menu():
    kb = [
        [InlineKeyboardButton("🎬 فيديو جديد", callback_data="new")],
        [InlineKeyboardButton("📊 تقرير النيشات", callback_data="report")],
        [InlineKeyboardButton("🛠 الإعدادات", callback_data="settings")],
    ]
    return InlineKeyboardMarkup(kb)


def niche_keyboard():
    kb = []
    row = []
    for i, niche in enumerate(SUPPORTED_NICHES):
        emoji = NICHE_EMOJI.get(niche, "📹")
        name = NICHE_NAMES.get(niche, niche)
        btn = InlineKeyboardButton(f"{emoji} {name}", callback_data=f"niche_{niche}")
        if i % 2 == 0 and row:
            kb.append(row)
            row = [btn]
        else:
            row.append(btn)
    if row:
        kb.append(row)
    kb.append([InlineKeyboardButton("🔀 عشوائي", callback_data="niche_random")])
    kb.append([InlineKeyboardButton("⬅️ رجوع", callback_data="back_main")])
    return InlineKeyboardMarkup(kb)


def batch_keyboard():
    kb = [[InlineKeyboardButton(f"📹 {s}", callback_data=f"batch_{s}")] for s in BATCH_SIZES]
    kb.append([InlineKeyboardButton("⬅️ رجوع", callback_data="back_main")])
    return InlineKeyboardMarkup(kb)


def settings_keyboard(sess):
    niche = sess["niche"]
    batch = sess["batch"]
    audio = sess["audio"]
    niche_show = f"{NICHE_EMOJI.get(niche, '📹')} {NICHE_NAMES.get(niche, niche)}"
    kb = [
        [InlineKeyboardButton(f"📂 النيش: {niche_show}", callback_data="set_niche")],
        [InlineKeyboardButton(f"📹 العدد: {batch}", callback_data="set_batch")],
        [InlineKeyboardButton(f"🔊 الصوت: {'✅' if audio else '❌'}", callback_data="toggle_audio")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(kb)


def confirm_keyboard():
    kb = [
        [InlineKeyboardButton("✅ ابدأ التوليد!", callback_data="launch")],
        [InlineKeyboardButton("🛠 الإعدادات", callback_data="settings")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(kb)


# ── Commands ────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 **TikTok AI Factory**\n\n"
        "مرحباً بك في مصنع فيديوهات التيك توك الآلي!\n"
        "5 نيشات عالية RPM • جودة HD • دقيقتان\n\n"
        "اختر من القائمة 👇",
        reply_markup=main_menu(), parse_mode="Markdown"
    )


async def handle_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    chat_id = q.message.chat_id
    s = get_sess(chat_id)
    d = q.data

    # ── Navigation ──
    if d == "back_main":
        await q.edit_message_text(
            "🎬 **TikTok AI Factory**\n\nاختر من القائمة 👇",
            reply_markup=main_menu(), parse_mode="Markdown"
        )

    elif d == "new":
        await q.edit_message_text(
            "📂 **اختر النيش**\n\n"
            "اختر المجال الذي تريد فيديو عنه:",
            reply_markup=niche_keyboard(), parse_mode="Markdown"
        )

    elif d == "report":
        factory: TikTokFactory = s["factory"]
        report = factory.niche_report()
        await q.edit_message_text(
            report, reply_markup=main_menu(), parse_mode="Markdown"
        )

    elif d == "settings":
        await show_settings(q, s)

    # ── Niche selection ──
    elif d.startswith("niche_"):
        niche = d.split("_", 1)[1]
        if niche == "random":
            import random
            niche = random.choice(SUPPORTED_NICHES)
        s["niche"] = niche
        await show_confirm(q, s)

    # ── Batch size ──
    elif d.startswith("batch_"):
        s["batch"] = int(d.split("_")[1])
        await show_confirm(q, s)

    # ── Toggle audio ──
    elif d == "toggle_audio":
        s["audio"] = not s["audio"]
        await show_settings(q, s)

    # ── Set niche from settings ──
    elif d == "set_niche":
        await q.edit_message_text(
            "📂 **اختر النيش**",
            reply_markup=niche_keyboard(), parse_mode="Markdown"
        )

    # ── Set batch from settings ──
    elif d == "set_batch":
        await q.edit_message_text(
            "📹 **اختر عدد الفيديوهات**",
            reply_markup=batch_keyboard(), parse_mode="Markdown"
        )

    # ── Launch ──
    elif d == "launch":
        await q.edit_message_text("⏳ **جاري التوليد...**", parse_mode="Markdown")
        await run_generation(q, chat_id)


async def show_settings(q, s):
    niche = s["niche"]
    batch = s["batch"]
    audio = s["audio"]
    niche_show = f"{NICHE_EMOJI.get(niche, '📹')} {NICHE_NAMES.get(niche, niche)}"
    text = (
        f"⚙️ **الإعدادات الحالية**\n\n"
        f"📂 النيش     : {niche_show}\n"
        f"📹 العدد      : {batch}\n"
        f"🔊 الصوت     : {'✅ مفعل' if audio else '❌ معطل'}\n"
    )
    await q.edit_message_text(text, reply_markup=settings_keyboard(s),
                               parse_mode="Markdown")


async def show_confirm(q, s):
    niche = s["niche"]
    batch = s["batch"]
    audio = s["audio"]
    niche_show = f"{NICHE_EMOJI.get(niche, '📹')} {NICHE_NAMES.get(niche, niche)}"
    text = (
        f"🔍 **مراجعة قبل التوليد**\n\n"
        f"📂 النيش     : {niche_show}\n"
        f"📹 العدد      : {batch}\n"
        f"🔊 الصوت     : {'✅' if audio else '❌'}\n"
        f"⏱ المدة      : ~دقيقتين (HD 1080×1920)\n\n"
        f"هل تريد البدء؟"
    )
    await q.edit_message_text(text, reply_markup=confirm_keyboard(),
                               parse_mode="Markdown")


async def run_generation(q, chat_id):
    s = get_sess(chat_id)
    factory: TikTokFactory = s["factory"]
    niche = s["niche"]
    count = s["batch"]
    with_audio = s["audio"]

    await q.message.reply_text(
        f"🔨 **جاري توليد {count} فيديو...**\n"
        f"📂 النيش: {NICHE_NAMES.get(niche, niche)}\n"
        f"🎬 جودة: HD 1080×1920 | ⏱ دقيقتان",
        parse_mode="Markdown"
    )

    results = []
    for i in range(count):
        try:
            msg = await q.message.reply_text(f"⏳ فيديو {i+1}/{count}...")
            res = factory.generate(
                niche_key=niche,
                seed=None,
                with_audio=with_audio,
                prefer_video_bg=True,
            )
            results.append(res)
            vid_path = res["video"]
            meta = res.get("meta", {})
            caption = meta.get("caption", "")[:800]
            hashtags = " ".join(meta.get("hashtags", []))

            with open(vid_path, "rb") as f:
                await q.message.reply_video(
                    video=f,
                    caption=f"🎬 **{meta.get('title', '')}**\n\n"
                            f"📂 {NICHE_EMOJI.get(niche, '')} {NICHE_NAMES.get(niche, niche)}\n"
                            f"{caption}\n\n{hashtags}",
                    supports_streaming=True,
                    parse_mode="Markdown",
                )
        except Exception as e:
            await q.message.reply_text(f"❌ فشل الفيديو {i+1}: {str(e)[:200]}")

    await q.message.reply_text(
        f"✅ **تم الانتهاء!** {len(results)}/{count} فيديو بنجاح.\n"
        f"📂 النيش: {NICHE_NAMES.get(niche, niche)}\n"
        f"🎬 جودة HD | ⏱ دقيقتان لكل فيديو\n\n"
        f"لتجربة جديدة ارسل /start",
        reply_markup=main_menu(), parse_mode="Markdown"
    )


# ── Main ────────────────────────────────────────────────────────
def main():
    global cfg
    cfg = load_config()

    token = BOT_TOKEN
    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN not set in environment.")
        return

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("🤖 TikTok AI Factory Bot is running... Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
