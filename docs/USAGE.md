# Usage

All commands run from the project root: `python -m app.main <command> [options]`.

## Commands

### `doctor` — environment & key check
```bash
python -m app.main doctor
```

### `one` — generate a single video
```bash
python -m app.main one --level B1
python -m app.main one --level A2 --topic "a quiet morning routine"
python -m app.main one --level C1 --seed 42        # reproducible
python -m app.main one --level B1 --no-audio        # skip TTS
```
Options:
- `--level {A1,A2,B1,B2,C1}` (default `B1`)
- `--topic "free text"` (optional; otherwise a topic is auto-rotated)
- `--seed N` (optional; makes the offline content + choices reproducible)
- `--no-audio` (skip spoken intro)

### `batch` — generate N videos
```bash
python -m app.main batch --count 5 --level A2
python -m app.main batch --count 10                 # mixed levels
```

### `accounts` — one batch per configured account
```bash
python -m app.main accounts                          # uses posting.per_day
python -m app.main accounts --per-account 3          # override count
python -m app.main accounts --auto-upload            # generate + post to TikTok
```
Reads `config/accounts.yaml` and generates content matched to each account's level,
topic families, and style.

### `upload` — post an already-generated video to TikTok
```bash
python -m app.main upload --video "outputs/jobs/XXXX/name.mp4" --caption-file "outputs/jobs/XXXX/caption.txt"
```
Add `--auto-upload` to `one`/`batch`/`accounts` to upload right after rendering.
See **[UPLOAD_TIKTOK.md](UPLOAD_TIKTOK.md)** for first-time login and configuration.

## Switching reading levels
Levels are defined in `config/levels.yaml`. Pass `--level` on the CLI, or set a default
per account in `config/accounts.yaml`. Each level controls vocabulary, max words per
line, number of lines, reading speed (WPM), hook and ending strategy.

## Output of each run
A timestamped folder in `outputs/jobs/`:
```
20260101-090000_b1_small-steps/
├── b1_small-steps.mp4     # upload this
├── caption.txt            # paste this as the TikTok caption
├── metadata.json          # title/level/caption/hashtags/account
├── script.json            # the reading script (audit/edit)
└── timing.json            # per-line timing map
```

## Common tuning (edit `config/config.yaml`)
| Goal | Setting |
|------|---------|
| Faster prototyping renders | `video.preset: veryfast` (or `ultrafast`) |
| Final quality | `video.preset: medium`, `video.crf: 18` |
| Slower/calmer scroll | raise `text.end_visible_frac` toward 0.9 / lower WPM in levels.yaml |
| Bigger reading text | `text.body_font_size: 68` |
| More/less darkening | `scrim.opacity: 0.30–0.55` |
| Prefer photos over video bg | `background.media_type: image` |
| Turn off Ken Burns motion | `background.kenburns: false` |
| US/UK/AU voice accent | `audio.tts_tld: com / co.uk / com.au` |
| Add background music | `audio.music_file: "assets/music/loop.mp3"` |
| Force offline AI | `ai.provider: local` |

## Custom fonts
Drop `.ttf` files into `fonts/` and point `text.font_regular` / `text.font_bold` at
them in `config/config.yaml`. Bundled default is **Lexend** (reading-optimized).
See `fonts/README.md`.
