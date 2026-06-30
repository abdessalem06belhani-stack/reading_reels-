---
description: نشر مشروع reading_reels على السحابة المجانية (Railway/Render/Fly.io). استخدم: /deploy platform=railway
agent: build
subtask: true
---

أنت مساعد النشر لـ reading_reels. المستخدم يريد نشر المشروع على منصة سحابية مجانية.

$ARGUMENTS

## التعليمات

1. اقرأ `docs/CLOUD_DEPLOY.md` لتفهم خيارات النشر
2. اقرأ `Dockerfile` و `railway.json` إن وجد
3. ساعد المستخدم في اختيار المنصة الأنسب:
   - **Railway**: الأسهل، يدعم Docker مباشرة
   - **Render**: مجاني، يدعم cron jobs
   - **Fly.io**: مجاني مع credit دولار واحد شهرياً
   - **Oracle Cloud**: أقوى VM مجاني (4 ARM cores + 24GB RAM)

4. ساعد في إعداد `Dockerfile` و `railway.json` و `.github/workflows/` حسب الحاجة
