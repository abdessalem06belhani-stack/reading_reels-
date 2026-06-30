---
description: أنشئ مشروعاً جديداً بهيكل نظيف وجاهز للتطوير. استخدم: /init-project [اللغة/الإطار] [اسم المشروع]
agent: code-agent
---

أنشئ مشروع $ARGUMENTS جديداً بهيكل احترافي.

المطلوب:
1. إنشاء هيكل المجلدات المناسب
2. إنشاء ملفات التكوين الأساسية (package.json, requirements.txt, Cargo.toml, إلخ)
3. إعداد ESLint/Prettier/Ruff/tools الجودة
4. إعداد pytest/vitest للاختبارات
5. إضافة README.md مع تعليمات البدء
6. إعداد Dockerfile + docker-compose.yml
7. إعداد GitHub Actions workflow (CI/CD)
8. إعداد .gitignore مناسب

اختر أفضل الممارسات حسب نوع المشروع:
- الويب: Next.js + Tailwind + TypeScript
- API: FastAPI/Express + PostgreSQL
- CLI: Python (argparse/click) + rich
- ML: Python + Jupyter + requirements.txt
