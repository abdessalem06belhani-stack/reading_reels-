# Fonts

Bundled default: **Lexend** (`Lexend-Regular.ttf`, `Lexend-Bold.ttf`) — an open-source
font (SIL OFL) specifically engineered to improve reading proficiency and reduce visual
stress, which is ideal for reading-practice content.

## Use a different font
1. Drop your `.ttf` files here (e.g. `Poppins-Regular.ttf`, `Inter-Bold.ttf`).
2. Point the config at them in `config/config.yaml`:
   ```yaml
   text:
     font_regular: "fonts/Inter-Regular.ttf"
     font_bold:    "fonts/Inter-Bold.ttf"
   ```
If a path is missing/invalid, the renderer automatically falls back to the system
**DejaVuSans** font so rendering never breaks.

## Good free reading fonts
- **Lexend** (default) — reading-optimized
- **Inter** — clean, neutral, very legible
- **Poppins** — friendly, rounded
- **Atkinson Hyperlegible** — designed for maximum legibility
All are free (Google Fonts / SIL OFL).
