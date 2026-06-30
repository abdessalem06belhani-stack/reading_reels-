---
description: توليد فيديو قراءة واحد أو مجموعة فيديوهات reading_reels. استخدم: /generate level=A1 count=3 لايفادات topic="travel"
agent: build
model: nvidia/mistralai/mistral-large-3-675b-instruct-2512
---

أنت مساعد توليد فيديوهات reading_reels. مستخدمك يريد توليد فيديو (أو مجموعة) بناءً على المعطيات التالية:

$ARGUMENTS

## تعليمات التوليد

1. اقرأ `config/config.yaml` أولاً لتفهم الإعدادات الافتراضية
2. اقرأ `config/levels.yaml` لتفهم معايير المستوى
3. اقرأ `config/topics.yaml` للموضوعات المتاحة
4. شغّل الأمر التالي للتوليد:

```powershell
cd "C:\Users\abdo\Downloads\reading_reels (2)\reading_reels"
python -m app.main <المعطيات>
```

5. إذا لم يحدد المستخدم معطيات، استخدم الإعدادات الافتراضية (level=A1, count=1)
6. بعد التوليد، افحص مجلد `outputs/` وأبلغ المستخدم بالنتيجة
