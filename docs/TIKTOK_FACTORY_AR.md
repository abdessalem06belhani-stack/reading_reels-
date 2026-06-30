# مصنع TikTok AI — TikTok AI Factory 🏭

توليد فيديوهات TikTok قصيرة جذابة في **5 تخصصات (niches)** مختلفة، بصوت احترافي
وخلفيات فيديو HD، **بدون أي اشتراكات مدفوعة** — كل الأدوات مجانية.

---

## لمحة سريعة

| التخصص | الجمهور المستهدف | أمثلة فيديوهات |
|--------|-------------------|----------------|
| **المالية (finance)** | 25-45 سنة | نصائح استثمار، توفير، ميزانية |
| **الذكاء الاصطناعي (ai_tools)** | 18-35 سنة | أدوات AI جديدة، إنتاجية |
| **العقارات (real_estate)** | 25-50 سنة | نصائح شراء، استثمار عقاري |
| **الصحة والبيوهيكينغ (health_biohacking)** | 20-40 سنة | تحسين النوم، تغذية، صحة |
| **الإنتاجية (productivity)** | 20-40 سنة | إدارة وقت، عادات يومية |

كل فيديو: **9:16 عمودي (1080×1920) • 30-60 ثانية • صوت بشري طبيعي**

---

## المتطلبات

- Python 3.10+
- اتصال بالإنترنت (للصوت عبر Edge-TTS)
- (اختياري) مفاتيح API المجانية: NVIDIA, Pexels, Pixabay

## التركيب

```bash
# 1. تنزيل التبعيات (بما فيها edge-tts)
pip install -r requirements.txt

# 2. تأكد من اكتمال التركيب
python -m app.main doctor
```

---

## أوامر CLI

### توليد فيديو واحد

```bash
# تخصص معين بشكل عشوائي
python -m app.main factory-one --niche finance

# بدون صوت
python -m app.main factory-one --niche ai_tools --no-audio

# باستخدام صور بدل فيديو كخلفية
python -m app.main factory-one --niche real_estate --no-video

# مع بذرة عشوائية محددة (لإعادة نفس النتيجة)
python -m app.main factory-one --niche productivity --seed 42
```

النتيجة: مقطع فيديو + ملف caption.txt + hashtags في `outputs/jobs/<timestamp>_factory_<niche>/`.

### توليد Batch

```bash
# 5 فيديوهات من تخصص معين
python -m app.main factory-batch --niche finance --count 5

# 3 فيديوهات من تخصصات عشوائية
python -m app.main factory-batch --count 3
```

### عرض تقرير التخصصات

```bash
python -m app.main factory-report
```

النتيجة: جدول يوضح التخصصات المتاحة وأعداد الفيديوهات المنتجة لكل تخصص.

---

## المحتوى الصوتي (Voice Engine)

`edge-tts` هو المحرك الافتراضي — يستخدم Microsoft Edge TTS المجاني.
أصوات عربية وإنجليزية طبيعية جداً.

### الأصوات المتاحة

النظام يختار صوتاً عشوائياً من القائمة تلقائياً:

| الصوت | اللغة | الوصف |
|-------|-------|-------|
| `en-US-JennyNeural` | إنجليزية أمريكية | أنثى، طبيعي |
| `en-US-GuyNeural` | إنجليزية أمريكية | ذكر |
| `en-GB-SoniaNeural` | إنجليزية بريطانية | أنثى |
| `en-GB-RyanNeural` | إنجليزية بريطانية | ذكر |
| `en-AU-NatashaNeural` | إنجليزية أسترالية | أنثى |

إذا لم يعمل Edge-TTS (بدون إنترنت)، يرجع تلقائياً إلى gTTS ثم pyttsx3.

---

## المحتوى البصري (Visual Engine)

### خلفيات الفيديو (افتراضي)
- **Pexels** ← فيديو HD حسب الكلمة المفتاحية
- **Pixabay** ← بديل إذا لم يجد Pexels
- **تدرج لوني (Gradient)** ← بديل نهائي بدون مفتاح

### صور Slideshow (إذا اخترت `--no-video`)
- 3-5 صور عالية الجودة
- تأثير تكبير/تصغير بطيء (Ken Burns effect)
- انتقال سلس بين الصور

---

## المصنع الأساسي (How It Works)

```
factory-one --niche finance
  │
  ├── 1. niche_scripts.py → توليد سكريبت مخصص للتخصص
  │     (NVIDIA NIM إن وجد، وإلا نصوص مدمجة افتراضية)
  │
  ├── 2. voice_engine.py → تحويل النص إلى صوت (Edge-TTS)
  │     مع سرعة نطق مناسبة (1.1x - 1.2x)
  │
  ├── 3. visual_engine.py → اختيار خلفية فيديو HD
  │     مع تحسين الألوان والتباين للنص
  │
  ├── 4. video_composer.py → تركيب الفيديو النهائي
  │     (نص متحرك + صوت + خلفية + توقيت)
  │
  └── ✅ فيديو جاهز في outputs/jobs/
```

---

## التوليد اليومي التلقائي (GitHub Actions)

1. ملف `.github/workflows/factory.yml` موجود وجاهز — تأكد من رفعه للريبو
2. أضف الـ Secrets في إعدادات الريبو (Settings → Secrets and variables → Actions):
   - `NVIDIA_API_KEY`
   - `PEXELS_API_KEY`
   - `PIXABAY_API_KEY`
3. الفيدوهات تتولد تلقائياً:
   - كل يوم 06:00 UTC (التخصصات الخمسة)
   - كل يوم 14:00 UTC (التخصصات الخمسة)
   - 3 فيديوهات لكل تخصص = 15 فيديو في كل run

---

## بوت التليجرام

إذا كان البوت مفعّل، أرسل:
```
/factory finance        ← توليد فيديو مالي
/factory-batch 5        ← توليد 5 فيديوهات عشوائية
/factory-report         ← عرض التقرير
```

---

## هيكل المشروع (TikTok Factory)

```
reading_reels/
├── tiktok_factory/          # 🔧 مصنع الفيديو بالكامل
│   ├── __init__.py          # تصدير TikTokFactory و SUPPORTED_NICHES
│   ├── factory.py           # المنسق الرئيسي (orchestrator)
│   ├── niche_scripts.py     # توليد سكريبتات لكل تخصص
│   ├── voice_engine.py      # تحويل النص إلى صوت (Edge-TTS + gTTS + pyttsx3)
│   ├── visual_engine.py     # اختيار وتحسين الخلفيات (فيديو/صور)
│   ├── video_composer.py    # تركيب الفيديو النهائي (نص + صوت + خلفية)
│   └── sources/
│       ├── __init__.py
│       └── scraper.py       # كشط محتوى من Reddit/Douyin/RSS
├── config/
│   ├── factory.yaml         # إعدادات المصنع
│   └── niches.yaml          # إعدادات التخصصات الخمسة
├── telegram_bot/
│   └── factory_bot.py       # بوت تليجرام للمصنع
├── .github/workflows/
│   └── factory.yml          # GitHub Actions للمصنع
└── app/
    └── main.py              # أوامر CLI (factory-one, factory-batch, factory-report)
```

---

## مثال عملي

```bash
# 1. تأكد من التثبيت
python -m app.main doctor

# 2. توليد فيديو عن التمويل الشخصي
python -m app.main factory-one --niche finance

# 3. النتيجة:
# {
#   "video": "outputs/jobs/20260630_factory_finance/final_video.mp4",
#   "job_dir": "outputs/jobs/20260630_factory_finance/",
#   "niche": "finance",
#   "niche_name": "نصائح مالية ذكية 💰",
#   "duration": 42,
#   "script_source": "ai_nvidia"
# }

# 4. توليد 10 فيديوهات إنتاجية للشهر
python -m app.main factory-batch --niche productivity --count 10
```

---

## استكشاف الأخطاء

| المشكلة | الحل |
|---------|------|
| `edge-tts غير مثبت` | شغّل `pip install edge-tts` |
| `لا يوجد فيديوهات خلفية` | تأكد من مفاتيح Pexels/Pixabay في `.env` |
| `الصوت لا يعمل` | تأكد من اتصال الإنترنت، سيحاول gTTS ثم pyttsx3 |
| `خطأ NVIDIA` | تأكد من `NVIDIA_API_KEY` أو سيعمل بنصوص افتراضية |
| `الملفات لا تظهر` | تأكد من وجود مجلد `outputs/jobs/` |
