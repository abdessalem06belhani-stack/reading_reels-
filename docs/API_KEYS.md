# API Keys — Step-by-Step (all free)

**You do NOT need any key to make your first video.** With no keys the tool uses an
offline content engine + generated gradient backgrounds. Add keys to upgrade quality.

All keys go in a file named **`.env`** in the project root. Create it once:

```bash
cp .env.example .env        # Windows: copy .env.example .env
```

Then open `.env` in any text editor and paste your keys after the `=` signs.
**Never commit `.env` to git** (a `.gitignore` already excludes it).

---

## 1. NVIDIA NIM — free AI reading scripts (recommended)

NVIDIA gives developers **free hosted API endpoints for prototyping** through the
NVIDIA Developer Program / build.nvidia.com. The endpoints are **OpenAI-compatible**.

**Steps:**
1. Go to **https://build.nvidia.com**
2. Sign in / create a free NVIDIA account (use any email; it's free).
3. Open any model card you want to use, e.g. **Llama 3.1 70B Instruct**
   (search "llama-3.1-70b-instruct") or **Nemotron**.
4. Click **“Get API Key”** (top-right of the code panel) → **Generate Key**.
5. Copy the key. It looks like: `nvapi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
6. Paste it into `.env`:
   ```
   NVIDIA_API_KEY=nvapi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
7. (Optional) pick a different model in `config/config.yaml` under `ai.model`,
   or set `NIM_MODEL=` in `.env`. Good free choices:
   - `meta/llama-3.1-70b-instruct`  (default, great balance)
   - `meta/llama-3.1-8b-instruct`   (faster, lighter)
   - `nvidia/llama-3.1-nemotron-70b-instruct`  (very strong writing)

**Verify:** `python -m app.main doctor` should show `NVIDIA_API_KEY : set`.
Then `python -m app.main one --level B1` — the log will say `script via NVIDIA NIM`.

**Bottleneck / fallback:** free prototyping endpoints can rate-limit (HTTP 429) under
heavy batch use. The generator auto-retries, then **falls back to the offline content
engine** so a batch never fully fails. For large daily volume, see CLOUD_DEPLOY.md
(stagger jobs) or self-host a NIM container later.

---

## 2. Pexels — free photo & video backgrounds (recommended)

**Steps:**
1. Go to **https://www.pexels.com/api/**
2. Click **“Get Started”** and sign in / create a free account.
3. Describe your use (“educational video backgrounds”) when asked.
4. Your API key appears on the dashboard — copy it.
5. Paste into `.env`:
   ```
   PEXELS_API_KEY=your_pexels_key_here
   ```

Pexels is generous and free. The tool prefers **portrait video**, then falls back to
portrait photos, then to a generated gradient.

---

## 3. Pixabay — extra free background source (optional)

**Steps:**
1. Go to **https://pixabay.com/api/docs/**
2. Sign in / create a free account.
3. Your API key is shown on that docs page once logged in — copy it.
4. Paste into `.env`:
   ```
   PIXABAY_API_KEY=your_pixabay_key_here
   ```

Used automatically if Pexels has no match (order is set in `config/config.yaml`
under `background.source_priority`).

---

## 4. Where each key is used

| Key | Used by | File |
|-----|---------|------|
| `NVIDIA_API_KEY` | AI script generation | `agents/script_generator.py` |
| `PEXELS_API_KEY` | backgrounds (video+photo) | `agents/background.py` |
| `PIXABAY_API_KEY` | backgrounds (video+photo) | `agents/background.py` |

The keys are read from environment variables via `python-dotenv` (loads `.env`
automatically). You can also `export NVIDIA_API_KEY=...` in your shell or set them as
GitHub Actions **Secrets** for cloud runs (see CLOUD_DEPLOY.md).

---

## 5. Security checklist
- ✅ Keep keys in `.env` (already git-ignored).
- ✅ In CI/cloud, store them as encrypted **Secrets**, never in code.
- ❌ Never hard-code keys in `config/*.yaml` or commit them.
- 🔁 Rotate a key immediately if it leaks (regenerate on the provider dashboard).
