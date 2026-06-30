# منصة تطوير opencode - Zen Free فقط

## النماذج الأساسية (Zen Free - بدون API key)
| النموذج | المعرف | القوة |
|---------|--------|-------|
| **Nemotron 3 Ultra Free** | `opencode/nemotron-3-ultra-free` | **الأساسي** - 1M سياق، أقوى Zen مجاني |
| **DeepSeek V4 Flash Free** | `opencode/deepseek-v4-flash-free` | **الخفيف** - سريع جداً للمهام اليومية |
| **Big Pickle** | `opencode/big-pickle` | نموذج متخفي قوي - للمهام المعقدة |
| **MiMo V2.5 Free** | `opencode/mimo-v2.5-free` | من Xiaomi - سريع وخفيف |
| **North Mini Code Free** | `opencode/north-mini-code-free` | متخصص بالبرمجة - دقيق للكود |

## اختيار النماذج أثناء المحادثة

### 1. التبديل الفوري
```
/model opencode/deepseek-v4-flash-free
```

### 2. عرض كل النماذج المتاحة
```
/models
```

### 3. استخدام وكيل Zen
```
@zen-ultra حلل هذا المشروع كاملاً بسياق 1M
@zen-flash نفذ هذا الأمر بسرعة
@zen-pickle حل هذه المشكلة المعقدة
@zen-mimo اقرأ لي هذا الملف
@zen-north اكتب كود Python لهذه الدالة
```

### 4. تشغيل opencode بنموذج معين
```bash
opencode --model opencode/nemotron-3-ultra-free
```

## الوكلاء المتخصصون (كلها Zen Free)
| الوكيل | النموذج | المهمة |
|--------|---------|--------|
| `@build` (افتراضي) | Nemotron 3 Ultra | تطوير وتنفيذ عام |
| `@plan` | Nemotron 3 Ultra | تخطيط وتحليل بدون تعديل |
| `@explore` | DeepSeek V4 Flash | استكشاف سريع للكود |
| `@research` | Nemotron 3 Ultra | بحث وتحليل بسياق 1M |
| `@coding` | North Mini Code | برمجة متخصصة |
| `@cheap` | DeepSeek V4 Flash | مهام سريعة وخفيفة |
| `@zen-ultra` | Nemotron 3 Ultra | سياق 1M - تحليل مشاريع كاملة |
| `@zen-flash` | DeepSeek V4 Flash | أسرع استجابة |
| `@zen-pickle` | Big Pickle | نموذج متخفي للمهام الصعبة |
| `@zen-mimo` | MiMo V2.5 | مهام بسيطة وسريعة |
| `@zen-north` | North Mini Code | برمجة نقية |

## الأوامر المخصصة
| الأمر | الاستخدام |
|-------|-----------|
| `/generate` | توليد فيديو: `/generate level=A1 count=3 topic=travel` |
| `/fix` | تشخيص وإصلاح: `/fix` أو `/fix error="..."` |
| `/deploy` | نشر سحابي: `/deploy platform=railway` |
| `/test` | تشغيل الاختبارات: `/test type=unit` |

## أين توجد ملفات الإعدادات؟
| الملف | الموقع |
|-------|--------|
| الإعدادات العامة | `~/.config/opencode/opencode.json` |
| إعدادات المشروع | `./opencode.json` |
| الوكلاء | `.opencode/agent/` |
| الأوامر | `.opencode/command/` |
| المهارات | `.opencode/skills/` |

**مبدأ التوريث**: الإعدادات العامة ← إعدادات المشروع (الأحدث يغلب)

## مبادئ العمل
1. **ابحث أولاً** - استخدم `@research` أو `@explore` قبل بناء أي شيء
2. **استخدم Zen** - كل النماذج Zen Free، بدون API key، بدون حدود
3. **جودة عالية** - استخدم `@build` أو `@zen-ultra` للمهام المعقدة (1M سياق)
4. **اقتصاد** - استخدم `@cheap` أو `@zen-flash` للمهام السريعة
5. **اختبر قبل النشر** - استخدم `/test` قبل `/deploy`
