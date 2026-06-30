---
name: python-dev
description: استخدم لتطوير بايثون - من مشاريع صغيرة إلى تطبيقات ويب مع FastAPI، تحليل بيانات، أتمتة. يشمل pytest، Docker، النشر المجاني.
---

# دليل تطوير بايثون

## الأدوات الأساسية
- **مدير حزم**: pip + venv أو uv (أسرع)
- **جودة كود**: ruff (linter + formatter)، mypy (type checking)
- **اختبارات**: pytest + pytest-cov
- **توثيق**: pydoc أو mkdocs

## FastAPI (الأفضل لـ APIs)
```python
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello"}
```

## نشر بايثون مجاني
| المنصة | النوع |
|--------|-------|
| **Render** | Web service + cron |
| **Railway** | Docker + auto-deploy |
| **Fly.io** | Docker containers |
| **Cloudflare Workers** | Python via wasm |
