# Account Setup & Multi-Account Content Operation

> **Important & honest:** TikTok does **not** offer an open public API to auto-post to
> personal accounts, and automated posting can violate platform rules and get accounts
> limited or banned. This tool therefore **prepares upload-ready packages**
> (video + caption + hashtags) and leaves the actual publishing to you (manual upload,
> TikTok's own scheduler, or an approved Business API if you qualify). This keeps your
> accounts safe and policy-compliant.

## 1. Which accounts to create

Create **one TikTok account per educational identity**, not random clones. Each identity
targets a clear level + niche so the algorithm learns a consistent audience. Example
matrix (already scaffolded in `config/accounts.yaml`):

| Account id | Level | Niche / families | Audience | Voice/Style |
|------------|-------|------------------|----------|-------------|
| `read_a1_daily` | A1 | daily_life, study | absolute beginners | calm, warm, simple |
| `read_b1_motivation` | B1 | motivation, work, study | intermediate | uplifting, modern |
| `read_b2_stories` | B2 | micro_story, travel | upper-intermediate | cinematic, reflective |

Add more by copying a block in `config/accounts.yaml`. Recommended starter: **2–3
accounts**, scale once your render + posting routine is smooth.

## 2. Setting up each TikTok account (manual, one-time)
1. Create the account with a **clear handle** (e.g. `easy.english.reading`).
2. Fill the bio with the level + promise (“Read English with me • Beginner friendly”).
3. Set a recognizable profile picture (consistent per identity).
4. Post **consistently** at the `best_times` defined per account.
5. Keep each account's content **on-theme** (don't mix A1 and C1 on one account).

## 3. The content differentiation strategy
To avoid “same video” fatigue across accounts and uploads, the pipeline rotates:
- **topic families** (daily_life, work, travel, study, motivation, micro_story)
- **specific topics** within each family
- **backgrounds** (deduplicated per account — never reuse the same asset id)
- **AI variations** (temperature + fresh generation each run)

Anti-repetition is enforced in `agents/background.py` (dedup DB at
`assets/used_assets.json`, keyed by account) and by topic rotation in
`app/pipeline.py::choose_topic`.

## 4. Naming logic
- Account id: `read_<level>_<niche>` (machine key)
- Display name: human, benefit-led (“Read & Grow English”)
- Output filename: `<level>_<topic-slug>.mp4` (auto)

## 5. Posting calendar separation
Each account has its own `posting.per_day` and `best_times` in `accounts.yaml`.
Generate a day's content per account with:
```bash
python -m app.main accounts
```
Then upload each `outputs/jobs/.../*.mp4` at the scheduled time using `caption.txt`.

## 6. Asset reuse rules
- Backgrounds: **never reused within the same account** (dedup DB). Different accounts
  may reuse the same background since their audiences don't overlap.
- Scripts: every run is freshly generated; the offline engine randomizes assembly.
- Intro phrases: intentionally consistent (“Let's practice English” / “Education is the
  key”) — they are the recognizable brand signature.

## 7. Uploading (recommended, safe options)
1. **Manual upload** in the TikTok app / web — most reliable, fully compliant.
2. **TikTok's built-in scheduler** (web upload supports scheduling) — paste `caption.txt`.
3. **TikTok Content Posting API** — only if you have an approved Business/developer app;
   integrate it yourself in a thin publisher script that reads `outputs/jobs/*/metadata.json`.

## 8. Scaling responsibly
- Keep production quality high; quantity without quality hurts reach.
- Don't spin up many accounts at once — grow 2–3 first.
- Vary topics and pacing so the format stays fresh but recognizable.
