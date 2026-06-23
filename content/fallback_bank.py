"""
Offline content engine (coherent paragraph version).

Produces a SINGLE coherent reading paragraph (a small connected story on one
topic) split into short reading lines, with vocabulary and sentence complexity
scaled to the CEFR level. Used with NO external API when:
  * ai.provider == "local", OR
  * the NVIDIA NIM call fails / has no key (and ai.fallback_to_local is true).

The whole paragraph keeps ONE subject and ONE topic so it reads as a connected
text, not a list of random sentences.
"""
from __future__ import annotations
import random
from typing import Dict, List, Optional

# ----------------------------------------------------------------------
# Topic vocabulary. {p} = possessive (her/his) is filled per chosen subject.
# Every "open"/"action" is a present-simple verb phrase with a clear subject,
# so sentences are always grammatical regardless of how we connect them.
# ----------------------------------------------------------------------
FAMILY: Dict[str, Dict] = {
    "daily_life": {
        "subjects": [("she", "She"), ("he", "He")],
        "time": ["morning", "day"],
        "open": ["wakes up slowly", "opens {p} eyes", "gets out of bed quietly"],
        "actions": ["makes a cup of coffee", "opens the window", "feeds the small cat",
                    "reads a few pages", "writes in {p} notebook", "waters the plants",
                    "listens to soft music"],
        "senses": ["The house is calm and quiet.", "Warm light fills the room.",
                   "The street outside is still asleep.", "The coffee smells warm and sweet."],
        "feelings": ["calm", "ready for the day", "happy with the silence", "slow and relaxed"],
    },
    "work": {
        "subjects": [("she", "She"), ("he", "He")],
        "time": ["morning", "week"],
        "open": ["arrives at the office early", "sits down at {p} desk", "opens {p} laptop"],
        "actions": ["checks the first email", "makes a short plan", "starts the hard task",
                    "helps a new coworker", "takes a deep breath", "finishes one small job",
                    "writes a clear list"],
        "senses": ["The office is quiet in the morning.", "The screen glows softly.",
                   "A cup of tea sits on the desk.", "The day feels full of work."],
        "feelings": ["focused", "calm", "proud of the work", "ready to begin"],
    },
    "travel": {
        "subjects": [("she", "She"), ("he", "He")],
        "time": ["morning", "afternoon"],
        "open": ["arrives in a new city", "steps off the slow train", "walks out into the street"],
        "actions": ["follows a narrow road", "watches the calm sea", "buys a warm drink",
                    "takes a few photos", "listens to the city sounds", "rests on an old bench",
                    "reads an old map"],
        "senses": ["The air smells of salt and rain.", "The streets are full of soft light.",
                   "The sea is quiet and wide.", "Strangers pass by with kind faces."],
        "feelings": ["free", "curious", "calm and happy", "far from home but safe"],
    },
    "study": {
        "subjects": [("she", "She"), ("he", "He"), ("the student", "The student")],
        "time": ["evening", "night"],
        "open": ["opens a new book", "sits down to study", "turns on a small lamp"],
        "actions": ["reads one more page", "repeats the new words", "writes a short note",
                    "reviews the lesson", "says each word slowly", "keeps a quiet promise",
                    "tries one more example"],
        "senses": ["The room is silent.", "Rain taps on the window.",
                   "The words begin to make sense.", "Time moves slowly and gently."],
        "feelings": ["patient", "clear and awake", "proud of the progress", "calm and focused"],
    },
    "motivation": {
        "subjects": [("she", "She"), ("he", "He")],
        "time": ["morning", "day"],
        "open": ["starts again after a hard week", "takes one small step", "makes a simple plan"],
        "actions": ["tries one more time", "keeps the daily habit", "stays calm and patient",
                    "writes down one goal", "trusts the slow progress", "does the next small thing",
                    "believes in the work"],
        "senses": ["The road ahead is long but clear.", "Small steps add up over time.",
                   "Today is a new chance.", "Nothing changes in one day."],
        "feelings": ["hopeful", "stronger than before", "calm and sure", "ready to grow"],
    },
    "micro_story": {
        "subjects": [("she", "She"), ("he", "He")],
        "time": ["night", "evening"],
        "open": ["finds an old letter", "hears a soft knock at night", "walks into the empty house"],
        "actions": ["opens the dusty box", "reads the faded words", "remembers a quiet promise",
                    "follows the dim light", "waits by the window", "lights one small candle",
                    "smiles at last"],
        "senses": ["The house is dark and still.", "A candle burns low.",
                   "The night is very quiet.", "Old memories fill the room."],
        "feelings": ["calm", "full of memory", "quiet and warm", "at peace"],
    },
}

_CONN = {
    "A1": [""],
    "A2": ["Then,", "Soon,", "After that,", "Slowly,"],
    "B1": ["Then", "Soon", "After a while", "Little by little", "At the same time"],
    "B2": ["Gradually,", "In that quiet moment,", "Without rushing,", "As the minutes passed,"],
    "C1": ["Gradually,", "In that unhurried moment,", "Almost without noticing,",
           "As the morning unfolded,"],
}
_REASONS = ["because the day feels new", "because there is no rush",
            "while the world is still quiet", "and time moves gently",
            "because small things matter"]
_CLOSERS = {
    "A1": ["This is a good day.", "Reading is fun.", "Try it every day."],
    "A2": ["A small habit can change a lot.", "Keep going, day by day.",
           "Every page makes you better."],
    "B1": ["The smallest habits shape the longest journeys.",
           "What you read every day, you slowly become.",
           "Patience turns practice into progress."],
    "B2": ["The quiet moments are the ones that teach us the most.",
           "We rarely notice change until we look back.",
           "Consistency, not speed, is what carries us forward."],
    "C1": ["It is in the unhurried hours that we are truly shaped.",
           "Mastery is merely patience repeated until it looks like talent.",
           "What we revisit daily eventually becomes who we are."],
}


def _cap(t: str) -> str:
    t = t.strip()
    return (t[0].upper() + t[1:]) if t else t


def _match_family(topic: Optional[str], rng: random.Random) -> str:
    if topic:
        tl = topic.lower()
        for fam in FAMILY:
            if fam.replace("_", " ") in tl:
                return fam
        # keyword hints
        hints = {"morning": "daily_life", "coffee": "daily_life", "work": "work",
                 "job": "work", "sea": "travel", "city": "travel", "travel": "travel",
                 "study": "study", "read": "study", "word": "study", "habit": "motivation",
                 "step": "motivation", "goal": "motivation", "letter": "micro_story",
                 "night": "micro_story", "story": "micro_story"}
        for k, v in hints.items():
            if k in tl:
                return v
    return rng.choice(list(FAMILY))


def _action_sentence(level, S, s, ph, rng) -> str:
    if level == "A1":
        return _cap(f"{S} {ph}.")
    if level == "A2":
        if rng.random() < 0.5:
            return _cap(f"{rng.choice(_CONN['A2'])} {s} {ph}.")
        return _cap(f"{S} {ph}.")
    conn = rng.choice(_CONN[level]) if rng.random() < 0.7 else ""
    reason = (" " + rng.choice(_REASONS)) if (level in ("B1", "B2", "C1") and rng.random() < 0.3) else ""
    if conn:
        return _cap(f"{conn} {s} {ph}{reason}.")
    return _cap(f"{S} {ph}{reason}.")


def generate(level_key: str, level_spec: Dict, topic: str, n_lines: int,
             seed: Optional[int] = None, family: Optional[str] = None) -> Dict:
    rng = random.Random(seed)
    fam = family if family in FAMILY else _match_family(topic, rng)
    d = FAMILY[fam]
    s, S = rng.choice(d["subjects"])
    poss = "her" if s == "she" else ("his" if s == "he" else "my" if s == "I" else "the")
    fmt = lambda ph: ph.replace("{p}", poss)
    if s == "I":
        S = "I"

    N = max(5, int(n_lines))
    acts = d["actions"][:]; rng.shuffle(acts)
    senses = d["senses"][:]; rng.shuffle(senses)
    feels = d["feelings"][:]; rng.shuffle(feels)

    lines: List[str] = []
    # opening line — sets the scene with ONE subject we keep throughout
    op = fmt(rng.choice(d["open"]))
    if level_key in ("A1",):
        lines.append(_cap(f"{S} {op}."))
    else:
        lines.append(_cap(f"Every {rng.choice(d['time'])}, {s} {op}."))

    i = 0
    while len(lines) < N - 1:
        if i % 3 == 2 and senses:
            lines.append(senses.pop())
        elif i % 4 == 3 and feels:
            lines.append(_cap(f"{S} feels {feels.pop()}." if S != "I" else f"I feel {feels.pop()}."))
        else:
            if not acts:
                acts = d["actions"][:]; rng.shuffle(acts)
            lines.append(_action_sentence(level_key, S, s, fmt(acts.pop()), rng))
        i += 1

    lines.append(rng.choice(_CLOSERS.get(level_key, _CLOSERS["B1"])))

    # de-duplicate accidental repeats while preserving order
    seen, clean = set(), []
    for ln in lines:
        if ln not in seen:
            clean.append(ln); seen.add(ln)
    lines = clean

    title = topic.strip().capitalize() if isinstance(topic, str) and topic else fam.replace("_", " ").title()
    return {
        "title": title,
        "level": level_key,
        "topic": topic,
        "hook": lines[0],
        "lines": lines,
        "ending": lines[-1],
        "paragraph": " ".join(lines),
        "source": "local_fallback",
    }
