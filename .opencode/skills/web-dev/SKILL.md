---
name: web-dev
description: استخدم لتطوير وتصميم مواقع وتطبيقات ويب. يشمل React/Next.js، Tailwind CSS، APIs، ونشر مجاني على Vercel/Netlify/Cloudflare.
---

# دليل تطوير الويب

## الـ Stack المقترح (مجاني بالكامل)
- **Framework**: Next.js 15 (React) أو Astro
- **Styling**: Tailwind CSS v4
- **Database**: Supabase (PostgreSQL مجاني)
- **Auth**: NextAuth.js / Supabase Auth
- **Deployment**: Vercel (مجاني)
- **CI/CD**: GitHub Actions + Vercel

## هياكل المشاريع

### Next.js App Router
```
my-app/
├── app/
│   ├── page.tsx
│   ├── layout.tsx
│   └── api/
├── components/
├── lib/
├── public/
├── tailwind.config.ts
└── package.json
```

### نشر فوري على Vercel
1. ادفع الكود إلى GitHub
2. Vercel يكتشفه وينشر تلقائياً
3. HTTPS مجاني + custom domain
4. Serverless functions + Edge functions
