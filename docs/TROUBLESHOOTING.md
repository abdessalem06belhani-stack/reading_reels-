# Troubleshooting

Run `python -m app.main doctor` first — it surfaces most issues.

## "ffmpeg not found"
The tool uses the **bundled** ffmpeg from `imageio-ffmpeg`. If it's missing:
```bash
pip install imageio-ffmpeg
```
Or install system ffmpeg (`sudo apt-get install ffmpeg` / `brew install ffmpeg`).

## Script generation always says "local fallback"
- `NVIDIA_API_KEY` is not set or invalid. Check `.env` and `doctor` output.
- Make sure `ai.provider: nvidia_nim` in `config/config.yaml`.
- If you see `NIM failed ... 401` → key is wrong/expired → regenerate at build.nvidia.com.
- `429` (rate limited) → reduce batch size / stagger runs; it auto-falls back to offline.
- Wrong model name → set a valid one (e.g. `meta/llama-3.1-70b-instruct`).

## Backgrounds are always gradients
- No `PEXELS_API_KEY` / `PIXABAY_API_KEY` set, or the query returned nothing.
- Check `doctor`; verify keys in `.env`.
- If a provider errors, it's logged as a warning and the next source is tried.

## No audio in the video
- gTTS needs **internet**. Offline? install pyttsx3 + an engine:
  - Linux: `sudo apt-get install espeak` (or `espeak-ng`).
  - macOS/Windows: pyttsx3 works natively.
- Or set `audio.intro_tts: false` to render silently on purpose.
- The video still renders with a silent track if all TTS engines fail.

## Text is hard to read over the background
- Increase `scrim.opacity` (e.g. 0.5).
- Increase `text.stroke_width` (e.g. 8) or enable `text.shadow`.
- Use a calmer `background.media_type: image`.

## Text scrolls too fast / too slow
- Slower: lower `words_per_minute` in `config/levels.yaml`, or raise
  `text.end_visible_frac` toward 0.9.
- Faster: raise WPM, or lower `end_visible_frac`.
- The total duration is fit toward `video.duration_sec` within readable bounds.

## Rendering is slow
- Set `video.preset: veryfast` (or `ultrafast`) while prototyping.
- Use image/gradient backgrounds (video bg + Ken Burns is heavier).
- A full ~2-min 1080×1920 render is a few minutes on CPU; render finals in parallel.

## "unknown level"
Use one of `A1 A2 B1 B2 C1` (see `config/levels.yaml`). Add your own level by copying a
block there.

## Fonts look generic / missing glyphs
- Bundled default is **Lexend** (`fonts/`). If a custom font path in `config.yaml` is
  wrong, the renderer falls back to DejaVuSans. Point `text.font_regular`/`font_bold` at
  valid `.ttf` files. See `fonts/README.md`.

## YAML errors after editing config
- Keep two-space indentation, and always put a **space after every colon**
  (`key: value`, not `key:value`). Validate quickly:
  ```bash
  python -c "import yaml,sys; yaml.safe_load(open('config/config.yaml'))"
  ```

## Windows path / activation issues
- Activate venv with `.venv\Scripts\activate`.
- If `python` isn't found, try `py -3 -m app.main doctor`.

## Still stuck?
Re-run with the offline defaults (no keys, `ai.provider: local`,
`audio.intro_tts: false`) to isolate whether the issue is a provider or the core render.
