"""
NicheScriptGenerator — مولد سكريبتات لكل نيش من النيشات الـ 5.

يستخدم NVIDIA NIM (مجاني) أولاً، مع fallback لمحتوى محلي مدمج.
كل نيش له محتواه الخاص: finance, ai_tools, real_estate, health, productivity.
"""
from __future__ import annotations
import json, os, re, time, random
from typing import Dict, Optional
from pathlib import Path
import requests

from app.utils import get_logger

log = get_logger()

# ── محتوى احتياطي مدمج لكل نيش ─────────────────────────────────
_FALLBACK_SCRIPTS: Dict[str, list] = {
    "finance": [
        {
            "title": "The 50-30-20 Rule",
            "lines": [
                "Have you ever wondered where your money goes every month?",
                "The 50-30-20 rule is a simple way to manage your income.",
                "Fifty percent should go to your needs like rent and food.",
                "Thirty percent can go to wants like eating out or shopping.",
                "Twenty percent should be saved or invested for your future.",
                "This rule helps you build wealth without feeling restricted.",
                "You can adjust these numbers based on your personal goals.",
                "The key is consistency, not perfection, in your saving habit.",
                "Start today with just one small change to your spending.",
                "Your future self will thank you for starting now.",
            ],
            "hashtags": ["#personalfinance", "#moneytips"],
            "caption": "Master your money with the simple 50-30-20 rule",
        },
        {
            "title": "Building an Emergency Fund",
            "lines": [
                "Life is full of surprises, and not all of them are pleasant.",
                "An emergency fund is your financial safety net for tough times.",
                "Start by saving just one month of your essential expenses.",
                "Keep this money in a separate high-yield savings account.",
                "Build it gradually until you have three to six months saved.",
                "This fund protects you from debt when unexpected costs appear.",
                "Even saving twenty dollars per week adds up over time.",
                "Automate your transfers so you save without thinking about it.",
                "Your emergency fund is not an investment — it is protection.",
                "Sleep better knowing you are prepared for life's surprises.",
            ],
            "hashtags": ["#emergencyfund", "#savingmoney"],
            "caption": "Build your financial safety net starting today",
        },
    ],
    "ai_tools": [
        {
            "title": "Free AI That Changes Everything",
            "lines": [
                "Artificial intelligence is no longer science fiction — it is here.",
                "And the best part? Many powerful AI tools are completely free.",
                "You can generate images, write code, and analyze data instantly.",
                "ChatGPT and Claude can help you write better emails and reports.",
                "Stable Diffusion creates stunning images from your description.",
                "These tools save you hours of work every single day.",
                "The key is learning how to ask the right questions.",
                "Start with one tool and master it before moving to the next.",
                "AI will not replace you, but someone using AI might.",
                "The future belongs to those who learn to work with AI.",
            ],
            "hashtags": ["#aitools", "#artificialintelligence"],
            "caption": "Free AI tools that will transform your workflow",
        },
        {
            "title": "Automate Your Busy Work",
            "lines": [
                "Do you spend hours on repetitive tasks every week?",
                "AI automation can handle them in minutes instead of hours.",
                "Zapier connects your apps and automates boring workflows.",
                "Make.com lets you build powerful automations without coding.",
                "n8n is a free and open-source alternative for advanced users.",
                "You can automate data entry, email replies, and report generation.",
                "Imagine waking up to find your routine work already completed.",
                "Start by identifying one task you do every single day.",
                "Automate that one task this week and save hours monthly.",
                "Your time is too valuable to waste on repetitive busy work.",
            ],
            "hashtags": ["#automation", "#productivityhacks"],
            "caption": "Automate your repetitive tasks and save hours daily",
        },
    ],
    "real_estate": [
        {
            "title": "Real Estate Without Money Down",
            "lines": [
                "You do not need a huge down payment to invest in real estate.",
                "Creative financing strategies can get you started with less.",
                "Seller financing means the seller acts as your bank instead.",
                "Lease options let you control a property before buying it.",
                "House hacking means living in one unit and renting the others.",
                "Wholesaling involves finding deals and assigning them to investors.",
                "Real estate investment trusts let you invest with just a few dollars.",
                "Start by learning your local market and building relationships.",
                "Every wealthy investor began with their very first property.",
                "Your first deal is the hardest — after that, it gets easier.",
            ],
            "hashtags": ["#realestate", "#realestateinvesting"],
            "caption": "Start investing in real estate with little to no money down",
        },
        {
            "title": "The BRRRR Method Explained",
            "lines": [
                "BRRRR stands for Buy, Rehab, Rent, Refinance, Repeat.",
                "It is one of the most powerful strategies for building wealth.",
                "First you buy a property below market value, often distressed.",
                "Then you renovate it to increase its value and appeal.",
                "Next you rent it to tenants who pay you monthly income.",
                "After that you refinance based on the new higher value.",
                "You pull your original investment out tax-free at refinance.",
                "Finally you repeat the process with your recycled capital.",
                "Each cycle adds another cash-flowing asset to your portfolio.",
                "This is how average people build substantial real estate wealth.",
            ],
            "hashtags": ["#brrrr", "#realestatewealth"],
            "caption": "The BRRRR method that builds real estate wealth fast",
        },
    ],
    "health_biohacking": [
        {
            "title": "Biohacking Your Sleep",
            "lines": [
                "Quality sleep is the foundation of all health and performance.",
                "Biohackers use science to optimize their sleep naturally.",
                "Keep your bedroom completely dark with blackout curtains.",
                "Maintain a cool temperature around sixty-five degrees Fahrenheit.",
                "Avoid screens for at least one hour before going to bed.",
                "Blue light from phones disrupts your natural melatonin production.",
                "Morning sunlight exposure helps regulate your circadian rhythm.",
                "Consistent sleep and wake times matter more than total hours.",
                "Magnesium glycinate before bed can improve sleep depth.",
                "Track your sleep with a wearable to understand your patterns.",
            ],
            "hashtags": ["#biohacking", "#sleephacks"],
            "caption": "Science-backed biohacks for deeper, restorative sleep",
        },
        {
            "title": "Brain Optimization Basics",
            "lines": [
                "Your brain is the most powerful organ in your body.",
                "Optimizing it starts with what you eat and drink every day.",
                "Omega-3 fatty acids from fish support brain cell structure.",
                "Creatine monohydrate can improve short-term memory and focus.",
                "Lion's mane mushroom promotes nerve growth factor production.",
                "High-intensity exercise increases BDNF, a brain fertilizer protein.",
                "Cold exposure triggers norepinephrine which enhances alertness.",
                "Intermittent fasting promotes autophagy and brain cell cleanup.",
                "Meditation literally increases gray matter density over time.",
                "Small daily habits compound into remarkable cognitive enhancement.",
            ],
            "hashtags": ["#neuroscience", "#brainhealth"],
            "caption": "Natural ways to optimize your brain performance",
        },
    ],
    "productivity": [
        {
            "title": "The Two-Minute Rule",
            "lines": [
                "Do you struggle with procrastination on small tasks?",
                "The two-minute rule is a simple hack that changes everything.",
                "If a task takes less than two minutes, do it immediately.",
                "This prevents small tasks from piling up into overwhelming lists.",
                "Reply to that email, wash that dish, make that quick call now.",
                "The rule works because starting is always the hardest part.",
                "Once you start moving, momentum carries you forward naturally.",
                "Apply this rule for one week and watch your productivity soar.",
                "Small actions repeated consistently create massive results.",
                "Stop overthinking and start doing with the two-minute rule.",
            ],
            "hashtags": ["#productivity", "#timemanagement"],
            "caption": "The two-minute rule that kills procrastination forever",
        },
        {
            "title": "Building Your Second Brain",
            "lines": [
                "Your brain is for having ideas, not for holding them.",
                "A second brain is a digital system that captures everything.",
                "Use tools like Notion, Obsidian, or Evernote to store ideas.",
                "The key is to capture ideas immediately before they disappear.",
                "Organize your notes using the PARA method by Tiago Forte.",
                "Projects, Areas, Resources, Archives — four simple categories.",
                "Review your notes weekly to connect ideas and find patterns.",
                "Your second brain becomes more valuable the more you feed it.",
                "It helps you think better, create more, and stress less.",
                "Start building your second brain today with just one note.",
            ],
            "hashtags": ["#secondbrain", "#notion"],
            "caption": "Build a second brain that supercharges your thinking",
        },
    ],
}


class NicheScriptGenerator:
    """Generate reading scripts for any of the 5 TikTok niches."""

    def __init__(self, cfg):
        import yaml
        self.cfg = cfg
        # Load niche config
        niches_path = cfg.abspath("config/niches.yaml")
        self.niches_data = {}
        if niches_path.exists():
            self.niches_data = yaml.safe_load(niches_path.read_text(encoding="utf-8")).get("niches", {})
        # AI config
        ai = cfg.get("factory", "ai", default={}) or cfg.get("ai", default={})
        self.base_url = ai.get("base_url", "https://integrate.api.nvidia.com/v1")
        self.model = ai.get("model", "meta/llama-3.1-70b-instruct")
        self.temperature = ai.get("temperature", 0.85)
        self.max_tokens = ai.get("max_tokens", 1500)
        self.timeout = ai.get("timeout_sec", 90)
        self.retries = ai.get("retries", 2)
        self.api_key = os.getenv("NVIDIA_API_KEY", "").strip()
        self.fallback_to_local = ai.get("fallback_to_local", True)

    def generate(self, niche_key: str, seed: Optional[int] = None) -> Dict:
        """Generate a complete script for the given niche."""
        niche = self.niches_data.get(niche_key)
        if not niche:
            log.warning("Niche '%s' not found in config, using fallback", niche_key)
            return self._fallback(niche_key, seed)

        rng = random.Random(seed)

        hooks = niche.get("hooks", [])
        hook = rng.choice(hooks) if hooks else niche.get("name", niche_key)

        # Try AI generation first
        if self.api_key:
            try:
                data = self._call_ai(niche_key, niche, hook)
                data["source"] = "nvidia_nim"
                log.info("Script via AI for niche '%s' (%s)", niche_key, self.model)
                return self._normalize(data, niche_key, niche)
            except Exception as e:
                log.warning("AI script failed for '%s': %s", niche_key, e)
                if not self.fallback_to_local:
                    raise

        # Fallback to local bank
        log.info("Script via local bank for niche '%s'", niche_key)
        return self._fallback(niche_key, seed)

    def _call_ai(self, niche_key: str, niche: dict, hook: str) -> dict:
        """Call NVIDIA NIM for script generation."""
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"}

        system_prompt = (
            "You are an expert content creator for TikTok videos. "
            "You write engaging, educational scripts that keep viewers watching until the end. "
            "Each script tells ONE coherent story or explains ONE concept clearly. "
            "You write in natural, conversational English that is easy to follow. "
            "You ALWAYS reply with a single valid JSON object and nothing else."
        )

        niche_name = niche.get("name", niche_key)
        hooks_list = niche.get("hooks", [])
        hooks_text = "\n".join(f"- {h}" for h in hooks_list[:3])

        user_prompt = f"""Create a TikTok video script for the niche "{niche_name}".

HOOK IDEA: {hook}

RULES:
- EXACTLY 10 reading lines (each line is one short sentence or phrase)
- Each line should be 3-12 words max
- The lines must form ONE coherent, flowing paragraph that explains one concept
- Line 1-2 must hook the viewer instantly
- Lines 3-8 deliver the value/education
- Lines 9-10 end with a satisfying, shareable thought
- Natural, conversational tone — like a friend explaining something interesting
- No emojis in the reading lines
- No markdown or formatting inside lines

Also provide:
- A short title (2-5 words)
- A TikTok caption (<= 150 chars)
- 3-5 relevant hashtags

Return EXACTLY this JSON format:
{{
    "title": "short title here",
    "lines": ["line 1", "line 2", ... "line 10"],
    "caption": "TikTok caption here",
    "hashtags": ["#tag1", "#tag2", "#tag3"]
}}"""

        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        last_err = None
        for attempt in range(1, self.retries + 2):
            try:
                r = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
                if r.status_code == 429:
                    raise RuntimeError("rate limited (429)")
                r.raise_for_status()
                content = r.json()["choices"][0]["message"]["content"]
                data = _extract_json(content)
                if not data or "lines" not in data:
                    raise ValueError("model did not return valid JSON with 'lines'")
                return data
            except Exception as e:
                last_err = e
                if attempt <= self.retries:
                    time.sleep(1.5 * attempt)
        raise RuntimeError(f"NIM call failed after retries: {last_err}")

    def _fallback(self, niche_key: str, seed: Optional[int] = None) -> Dict:
        """Use built-in fallback scripts per niche."""
        rng = random.Random(seed)
        scripts = _FALLBACK_SCRIPTS.get(niche_key, _FALLBACK_SCRIPTS.get("finance", []))
        if not scripts:
            # Ultimate fallback
            return {
                "title": "Quick Tip",
                "lines": ["Here is a quick tip to improve your day."],
                "caption": "A quick tip for you",
                "hashtags": ["#tips"],
                "source": "fallback",
            }
        data = rng.choice(scripts)
        data["source"] = "fallback"
        return dict(data)

    def _normalize(self, data: dict, niche_key: str, niche: dict) -> dict:
        """Normalize script data to standard format."""
        lines = [str(x).strip() for x in data.get("lines", []) if str(x).strip()]
        if not lines:
            raise ValueError(f"Empty script for niche '{niche_key}'")

        data["lines"] = lines
        data.setdefault("title", data.get("title", niche.get("name", niche_key)))
        data.setdefault("caption", data.get("caption", ""))
        data.setdefault("hashtags", data.get("hashtags", []))
        data["niche"] = niche_key
        data["paragraph"] = " ".join(lines)
        data["niche_name"] = niche.get("name", niche_key)
        data["is_factory"] = True
        return data

    def get_niche_names(self) -> Dict[str, str]:
        """Return dict of niche_key -> display name."""
        return {k: v.get("name_ar", v.get("name", k))
                for k, v in self.niches_data.items()}

    def get_random_hook(self, niche_key: str) -> str:
        """Get a random hook for the given niche."""
        niche = self.niches_data.get(niche_key, {})
        hooks = niche.get("hooks", [])
        return random.choice(hooks) if hooks else "Check this out!"

    def get_visual_keywords(self, niche_key: str) -> list:
        """Get visual search keywords for the niche."""
        niche = self.niches_data.get(niche_key, {})
        return niche.get("visual_keywords", ["minimal aesthetic"])

    def get_niche_hashtags(self, niche_key: str) -> list:
        """Get recommended hashtags for the niche."""
        niche = self.niches_data.get(niche_key, {})
        return niche.get("hashtags", [])

    def get_color_palette(self, niche_key: str) -> dict:
        """Get color palette for the niche."""
        niche = self.niches_data.get(niche_key, {})
        return niche.get("color_palette", {
            "accent": "#FFFFFF",
            "text": "#FFFFFF",
            "highlight": "#FFD700",
            "stroke": "#000000",
        })

    def get_tts_voice(self, niche_key: str) -> str:
        """Get recommended TTS voice for the niche."""
        niche = self.niches_data.get(niche_key, {})
        return niche.get("tts_voice", "en-US-JennyNeural")


def _extract_json(text: str) -> Optional[dict]:
    """Pull the first valid JSON object out of a model response."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return None
    chunk = text[start:end + 1]
    try:
        return json.loads(chunk)
    except Exception:
        return None
