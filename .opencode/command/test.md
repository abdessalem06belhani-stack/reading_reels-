---
description: تشغيل اختبارات مشروع reading_reels. استخدم: /test أو /test type=unit path=tests/
agent: build
subtask: true
---

أنت مساعد اختبارات reading_reels. المستخدم يريد تشغيل الاختبارات.

$ARGUMENTS

## التعليمات

1. ابحث عن الاختبارات في مجلد `tests/`
2. شغّل الاختبارات:

```powershell
cd "C:\Users\abdo\Downloads\reading_reels (2)\reading_reels"
python -m pytest tests/ -v
```

3. إذا فشلت الاختبارات، شخّص المشكلة وحاول إصلاحها
4. أبلغ المستخدم بنتائج الاختبارات
