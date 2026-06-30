# reddit-reels - Draft (FINAL)

## Intent
Build a Reddit story video generator for TikTok/YouTube/Instagram — faceless, free, automated, with copyright-safe advanced editing using trending gameplay backgrounds.

## ALL DECISIONS (Complete)

### 1. المشروع
- **الاسم**: reddit-reels
- **الموقع**: مجلد منفصل `../reddit-reels/` بجانب reading_reels
- **الرخصة**: MIT (مفتوح المصدر)

### 2. المحتوى (Content)
- **النيش**: مزيج **عدالة + دراما**
- **Subreddits**:
  - العدالة: r/ProRevenge, r/MaliciousCompliance, r/pettyrevenge, r/NuclearRevenge
  - الدراما: r/AmITheAsshole, r/relationship_advice, r/confessions
- **اختيار القصة**: scoring engine (upvote_velocity + comment_ratio + word_count)
- **طول القصة**: 800-1500 كلمة = 60-90 ثانية فيديو

### 3. الخلفيات (Background)
- **المصدر**: تحميل فيديوهات ترند من YouTube (Minecraft parkour, Subway Surfers, GTA 5)
- **المعيار**: الأكثر مشاهدة + الأعلى retention
- **التنويع**: مكتبة دوارة (rotation pool) لمنع التكرار
- **Copyright safety pipeline**:
  - تغيير السرعة (±2-5% عشوائي)
  - Color grading (LUT)
  - Crop + zoom مختلف
  - حذف ALL metadata (EXIF, headers, software signatures)
  - Overlay: captions + voice + music + watermark

### 4. الصوت (Audio)
- **TTS**: edge-tts (Microsoft Edge — طبيعي جداً، مجاني، unlimited)
- **الصوت**: "en-US-GuyNeural" (ذكر أمريكي)
- **السرعة**: +10% (لـ retention — أسرع قليلاً)
- **الموسيقى الخلفية**: مكتبة خالية من الحقوق (YouTube Audio Library, Pixabay Music)
- **Sound design**: voice_gain + music_gain + loudnorm (EBU R128)

### 5. الترجمة (Captions)
- **النظام**: Word-by-word animated captions
- **المصدر**: Whisper (openai-whisper) — word-level timestamps
- **الأسلوب**: كلمة تظهر وتتhighlight مع الصوت
- **الخط**: Sans-serif كبير (مقروء على الجوال)
- **اللون**: أبيض مع stroke أسود (تباين عالي)

### 6. المونتاج (Video Composition)
- **المكتبة**: MoviePy (Python + ffmpeg)
- **الأبعاد**: 1080×1920 (9:16 — يعمل على TikTok, YouTube Shorts, Instagram Reels)
- **FPS**: 30
- **المدة**: 60-90 ثانية (مثالية لـ TikTok Creativity Program)
- **الميزات المتقدمة**:
  - Title card (أول 3 ثوانٍ — اسم subreddit + hook)
  - Question-based hook (مثال: "ما الذي ستفعله لو مديرك ظلمك؟")
  - Ken Burns بطيء (حركة خلفية)
  - Word-by-word captions متزامنة
  - Transitions ناعمة
  - Sound design: voice → music → effects
  - Loop-friendly ending (آخر كلمة تبقى 2 ثانية)

### 7. المنصات (Cross-Platform)
| المنصة | طريقة الرفع | الحالة |
|--------|------------|--------|
| **TikTok** | Web (Selenium) + API | ✅ من reading_reels |
| **YouTube Shorts** | YouTube Data API v3 | 🆕 جديد |
| **Instagram Reels** | Instagram Graph API | 🆕 جديد |
| **الكل في أمر واحد** | `python -m app.main upload --all` | 🆕 جديد |

### 8. النشر والاستضافة (Deployment)
- **GitHub**: رفع الكود
- **GitHub Actions**:
  - `generate.yml` — cron daily + manual
  - متغيرات: REDDIT_CLIENT_ID, subreddits, count, platform
  - مستوحى من: `reading_reels/.github/workflows/generate.yml`
- **Cloud**: Railway.app / Deta Space / Fly.io (free tiers)
- **التكلفة**: $0 — كل شيء في free tier

### 9. الأمان من الكوبيرايت (Copyright Safety)
مشكلة | الحل
-------|------
الميتاداتا | حذف ALL metadata قبل الاستخدام
التعديل | Speed change, color grade, crop, overlay
المحتوى الأصلي | Voiceover + captions + music = عمل تحويلي
المصدر | Pexels/Pixabay للخالية من الحقوق + تعديل على المحمية

### 10. الهندسة (Architecture)
```
Reddit API (PRAW) → story
    ↓
Score & Filter → top story by engagement velocity
    ↓
edge-tts → audio.mp3
    ↓
Whisper → word_timestamps[]
    ↓
Download Background → YouTube trending gameplay
    ↓
Metadata Scrubber → strip ALL identifying info
    ↓
Transformative Edit → speed + color + crop
    ↓
Advanced Composer (MoviePy):
    - Title card (hook)
    - Background + Ken Burns
    - Word-by-word animated captions
    - Audio: voice + music + effects
    - Transitions
    ↓
outputs/jobs/<timestamp>_<subreddit>/
    └── video.mp4 + caption.txt + hashtags.txt + story.json + metadata.json
    ↓
Uploader → TikTok + YouTube + Instagram
```

### 11. إعادة الاستخدام من reading_reels
| الملف | الوظيفة | التعديل |
|-------|---------|---------|
| `app/main.py` | CLI (argparse) | إضافة subreddit, platform params |
| `app/pipeline.py` | Pipeline orchestrator | تخصيص agents الجديدة |
| `app/config_loader.py` | YAML + .env | لا تغيير |
| `app/utils.py` | logging, ffmpeg, files | إضافة metadata_scrubber |
| `agents/metadata.py` | caption + hashtags | تخصيص للقصص |
| `agents/uploader.py` | TikTok upload | إضافة YouTube + Instagram |
| `tests/test_smoke.py` | اختبارات | إضافة اختبارات agents الجديدة |

### 12. Agents الجديدة (للبرمجة)
1. `agents/reddit_scraper.py` — PRAW + scoring engine
2. `agents/tts_edgetts.py` — edge-tts async
3. `agents/whisper_timing.py` — Whisper word alignment
4. `agents/background_pool.py` — clip manager + downloader + metadata scrubber
5. `agents/caption_renderer.py` — word-by-word animated captions
6. `agents/composer.py` — MoviePy advanced composition
7. `agents/youtube_uploader.py` — YouTube API
8. `agents/instagram_uploader.py` — Instagram API
9. `agents/metadata_scrubber.py` — strip EXIF/headers/signatures

## Status
**القرارات كاملة — في انتظار الموافقة النهائية**
