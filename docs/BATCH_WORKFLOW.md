# Batch & Mass-Production Workflow

## Daily content run (all accounts)
```bash
python -m app.main accounts
```
For each account in `config/accounts.yaml` this generates `posting.per_day` videos,
matched to the account's level, topic families and style. Outputs land in
`outputs/jobs/`. Each folder is a self-contained, upload-ready package.

## Fixed-size batch (one level)
```bash
python -m app.main batch --count 10 --level B1
```

## Mixed-level batch
```bash
python -m app.main batch --count 12          # random level per video
```

## Recommended production loop
1. **Generate** the day's batch (`accounts` or `batch`).
2. **Review** quickly — open a few `*.mp4`, skim `script.json` for quality.
3. **Upload** each video manually or via TikTok's scheduler, pasting `caption.txt`.
4. **Track** which performed best; feed winning topics back into `topics.yaml`.

## Speed tips for big batches
- Set `video.preset: veryfast` in `config/config.yaml` (final quality: `medium`).
- Prefer `background.media_type: image` (photos/gradients render faster than video bg).
- Use `--no-audio` while prototyping; re-render finals with audio.
- Run videos in **parallel** (each job is independent). Simple parallel example:
  ```bash
  # 4 videos in parallel (GNU parallel or xargs)
  printf 'A2\nB1\nB1\nC1\n' | xargs -P4 -I{} python -m app.main one --level {}
  ```
- In the cloud, shard the account matrix across multiple Actions jobs / machines.

## Anti-repetition (built in)
- **Backgrounds**: deduped per account via `assets/used_assets.json` — the same asset id
  is never reused for one account.
- **Topics**: rotated across families each run (`app/pipeline.py::choose_topic`).
- **Scripts**: NIM uses temperature; the offline engine randomizes assembly + seeds.

## Analytics feedback loop (lightweight)
1. Note each upload's views/retention in a sheet keyed by `metadata.json::title`.
2. Promote high-retention **topic families** by adding more entries under that family in
   `config/topics.yaml`.
3. Tune pacing per level in `config/levels.yaml` (`words_per_minute`, `target_lines`)
   based on completion rate.
4. Re-run batches — the system compounds on what works.

## Output hygiene
- `outputs/jobs/` grows over time. Archive or move uploaded jobs to cold storage.
- Keep `assets/used_assets.json` (it powers dedup). Back it up if you reset `outputs/`.
- The background cache in `assets/cache/` can be cleared anytime to reclaim disk.
