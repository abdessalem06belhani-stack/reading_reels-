# Cloud Deployment (free-first)

Goal: generate videos automatically on a schedule with **no always-on server** and **no cost**.

## Option A — GitHub Actions cron (recommended, free)

GitHub Actions gives free CI minutes. A scheduled workflow runs the generator and uploads
the finished videos as **build artifacts** (downloadable from the run page) or commits
them to a `outputs/` branch / release.

A ready workflow is included: **`deploy/github-actions-generate.yml`**.

**Setup:**
1. Push this folder to a GitHub repo.
2. Copy the workflow into place:
   ```bash
   mkdir -p .github/workflows
   cp deploy/github-actions-generate.yml .github/workflows/generate.yml
   ```
3. In the repo: **Settings → Secrets and variables → Actions → New repository secret**, add:
   - `NVIDIA_API_KEY`
   - `PEXELS_API_KEY`
   - `PIXABAY_API_KEY`
4. Commit & push. The workflow runs on the cron schedule (default 07:00 UTC daily) and
   on manual **“Run workflow”**.
5. Open the run → **Artifacts** → download the generated videos.

**Bottleneck:** Actions artifacts expire (default 90 days) and have size limits. For
long-term storage, push outputs to **Cloudflare R2** (free tier), an S3 bucket, or attach
them to a **GitHub Release** in the same workflow.

## Option B — Docker anywhere (Fly.io / Railway / Render / your VPS)

A **`deploy/Dockerfile`** is included. Build and run:
```bash
docker build -t reading_reels -f deploy/Dockerfile .
docker run --rm -e NVIDIA_API_KEY=$NVIDIA_API_KEY \
                 -e PEXELS_API_KEY=$PEXELS_API_KEY \
                 -v "$PWD/outputs:/app/outputs" \
                 reading_reels python -m app.main accounts
```
- **Fly.io / Railway / Render** free-style tiers can run this as a **scheduled job /
  cron machine**. Mount or sync `outputs/` to object storage.
- For scheduled runs, use the platform's cron (Fly Machines schedule, Railway cron,
  Render Cron Job) to invoke `python -m app.main accounts` daily.

## Option C — Local cron (zero cloud)
```cron
# crontab -e  (run a daily batch at 07:00 local time)
0 7 * * *  cd /path/to/reading_reels && /path/to/.venv/bin/python -m app.main accounts >> cron.log 2>&1
```

## Storing outputs (free options, ranked)
1. **Cloudflare R2** — free egress, S3-compatible, great for video. (best)
2. **GitHub Releases / Artifacts** — simplest if already on GitHub.
3. **Supabase Storage free tier** — fine for metadata + small volumes.
4. Commit to a `outputs` branch — easy but bloats the repo over time (avoid for video).

## Metadata / dedup across runs
The dedup DB lives at `assets/used_assets.json`. In CI, **persist it** so backgrounds
aren't reused: commit it back after a run, cache it between runs, or store it in Supabase.
The included workflow caches it via `actions/cache`.

## Cost summary
| Piece | Free tier used | Realistic limit |
|-------|----------------|-----------------|
| Compute | GitHub Actions minutes | generous for daily small batches |
| AI text | NVIDIA NIM prototyping | rate-limited under heavy use → offline fallback |
| Backgrounds | Pexels/Pixabay free tiers | high; cached + deduped |
| Storage | R2 / Artifacts / Supabase | ample for early scaling |
