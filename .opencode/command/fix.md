---
description: تشخيص وإصلاح مشاكل مشروع reading_reels. استخدم: /fix أو /fix error="ffmpeg not found"
agent: doctor
model: nvidia/meta/llama-3.3-70b-instruct
---

أنت وكيل التشخيص الذكي لـ reading_reels. المستخدم يواجه مشكلة ويطلب حلاً:

$ARGUMENTS

اتبع الخطوات بالترتيب:

## 1. تشخيص سريع
- تحقق من وجود `config/config.yaml`
- تحقق من وجود `.env` (إذا لزم الأمر)
- تحقق من توفر Python packages الأساسية
- تحقق من ffmpeg

## 2. قراءة الخطأ
- ابحث في مجلد `outputs/` عن أي logs أو أخطاء
- اقرأ الـ Traceback كاملاً

## 3. إصلاح المشكلة
- طبق الإصلاح المناسب
- اختبر الحل

## 4. أبلغ المستخدم
- قل بالضبط ماذا فعلت
- قل ما إذا نجح الإصلاح أم لا
