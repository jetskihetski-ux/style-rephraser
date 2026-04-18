"""
Humanizer core — powered by Ollama (local, free, no API key).
Install Ollama: https://ollama.com
Then run: ollama pull llama3
"""

import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3"

# ── AI words to flag/remove ───────────────────────────────────────────────

AI_WORDS = [
    "delve", "delving", "furthermore", "moreover", "utilize", "utilise",
    "consequently", "nevertheless", "nonetheless", "paradigm", "leverage",
    "synergy", "holistic", "robust", "seamless", "cutting-edge", "groundbreaking",
    "it is worth noting", "it is important to note", "in conclusion", "in summary",
    "to summarize", "as an AI", "I cannot", "I apologize", "certainly",
    "absolutely", "of course", "invaluable", "multifaceted", "nuanced",
    "comprehensive", "facilitate", "implement", "regarding", "pertaining to",
    "in order to", "due to the fact that", "it should be noted",
]

# ── Modes ─────────────────────────────────────────────────────────────────

MODES = {
    "humanize": {
        "label": "Humanize",
        "icon":  "🧠",
        "desc":  "Strip AI patterns — make it sound like a real person wrote it.",
        "instruction": """You are a humanizer. Your job is to rewrite AI-generated text so it sounds like a real human wrote it.

Rules:
- Vary sentence length — mix short punchy ones with longer ones
- Use contractions naturally (don't, it's, you'll, I've)
- Remove AI buzzwords: delve, furthermore, utilize, leverage, seamless, robust, paradigm, holistic, groundbreaking, invaluable, multifaceted, nuanced, comprehensive, facilitate
- Remove filler openers: "It is worth noting that", "It is important to note", "In conclusion", "Certainly"
- Add natural flow — how a real person would say it out loud
- Keep the meaning 100% intact
- Do NOT add new information
- Sound genuine, not polished to perfection""",
    },
    "match_style": {
        "label": "Match My Style",
        "icon":  "🪞",
        "desc":  "Rewrite to sound exactly like you based on your uploaded documents.",
        "instruction": """Rewrite the text to sound exactly like the author of the reference documents.
Copy their sentence length, vocabulary, tone, punctuation habits, and overall voice.
The result should be indistinguishable from something they personally wrote.""",
    },
    "casual": {
        "label": "Casual Human",
        "icon":  "😎",
        "desc":  "Natural, relaxed — like a real person talking.",
        "instruction": """Rewrite this to sound like a real person casually explaining something.
Use everyday words, contractions, short sentences mixed with longer ones.
Imagine you're explaining this to a friend — natural, genuine, zero corporate-speak.""",
    },
    "student": {
        "label": "Student",
        "icon":  "🎒",
        "desc":  "Sounds like a university student wrote it — smart but not perfect.",
        "instruction": """Rewrite this to sound like it was written by a university student.
It should be intelligent and well-argued but not overly polished.
Use a mix of formal and casual phrasing, occasional directness, and genuine opinions.
Avoid all AI buzzwords and corporate language.""",
    },
    "professional": {
        "label": "Professional",
        "icon":  "💼",
        "desc":  "Professional but human — not stiff, not robotic.",
        "instruction": """Rewrite this in a professional human tone.
Clear, confident, and well-structured — but it should still sound like a person, not a press release.
Avoid jargon, buzzwords, and filler phrases. Be direct and genuine.""",
    },
    "native": {
        "label": "Native Speaker",
        "icon":  "🗣️",
        "desc":  "Fluent, natural native-level English with real idioms.",
        "instruction": """Rewrite this to sound like a fluent native English speaker wrote it naturally.
Use real idioms, natural phrasing, and colloquial expressions where appropriate.
The rhythm should feel effortless — the way a native speaker actually writes, not textbook-perfect.""",
    },
    "shorter": {
        "label": "Shorter",
        "icon":  "✂️",
        "desc":  "Humanized and cut down — same meaning, fewer words.",
        "instruction": """Rewrite this to be shorter and more human.
Cut all filler, AI buzzwords, and unnecessary words. Remove at least 35% of the word count.
Keep the core meaning. Make what's left sound natural, not robotic.""",
    },
    "creative": {
        "label": "Creative",
        "icon":  "✨",
        "desc":  "Vivid and expressive — a human with personality.",
        "instruction": """Rewrite this with creative, expressive human writing.
Use vivid language, personality, metaphors where they fit, and a varied rhythm.
It should feel alive — written by someone with a distinct voice, not a machine.""",
    },
    "bullet_points": {
        "label": "Bullet Points",
        "icon":  "📋",
        "desc":  "Break it into clear, human-sounding bullet points.",
        "instruction": """Convert this into bullet points that sound like a real person wrote them.
No corporate-speak, no AI filler. Keep each point concise, plain, and genuine.
Use parallel structure but let the language feel natural.""",
    },
    "bypass": {
        "label": "Bypass AI Detection",
        "icon":  "🕵️",
        "desc":  "Targets perplexity + burstiness — the actual metrics Turnitin uses.",
        "instruction": """Rewrite this text to fool AI detection models that measure PERPLEXITY and BURSTINESS.

BURSTINESS (critical — this is what detectors look for most):
- Violently vary sentence length. Put a 3-word sentence right after a long one.
- Short. Then a sentence that runs longer and includes more detail, packed with clauses and specifics that make it feel like a real human thought that kept going.
- Then short again.
- Mix 2-word fragments, 5-word sentences, 30-word sentences randomly.
- Never write 3 sentences of similar length in a row.

PERPLEXITY (make word choices unpredictable):
- Replace predictable words with less common but natural alternatives
- Use unexpected transitions instead of: however, furthermore, additionally, therefore
- Add informal asides in parentheses or after a dash — the kind of thing a person just thinks of
- Use specific concrete details instead of vague generalities
- Throw in a rhetorical question where it fits
- Use "and" to start sentences sometimes. It's how people actually write.
- Vary your sentence openings — don't start multiple sentences with the subject

ALSO:
- Remove ALL AI words: delve, utilize, leverage, seamless, robust, paradigm, nuanced, comprehensive, furthermore, moreover
- Use contractions everywhere naturally
- Make it opinionated — humans have views, AI is neutral
- Active voice only
- Restructure ideas — don't follow original word order slavishly

Keep the full meaning. Output ONLY the rewritten text.""",
    },
}


# ── Ollama helpers ────────────────────────────────────────────────────────

def check_ollama() -> tuple[bool, str]:
    """Check if Ollama is running and return available models."""
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            return True, models
        return False, []
    except Exception:
        return False, []


def build_prompt(input_text: str, instruction: str, style_profile: str | None) -> str:
    style_block = (
        f"\n\nReference writing style to match:\n---\n{style_profile}\n---"
        if style_profile else ""
    )
    return (
        f"{instruction}{style_block}\n\n"
        f"Text to rewrite:\n---\n{input_text}\n---\n\n"
        f"Output ONLY the rewritten text. No explanation, no preamble, no labels."
    )


def humanize_stream(
    input_text:    str,
    mode:          str,
    style_profile: str | None = None,
    model:         str = DEFAULT_MODEL,
):
    """Stream humanized text token by token via Ollama."""
    mode_cfg    = MODES.get(mode, MODES["humanize"])
    instruction = mode_cfg["instruction"]

    if mode == "match_style" and not style_profile:
        instruction = MODES["humanize"]["instruction"]  # fallback

    prompt = build_prompt(input_text, instruction, style_profile if mode == "match_style" else None)

    try:
        with requests.post(
            OLLAMA_URL,
            json={"model": model, "prompt": prompt, "stream": True},
            stream=True,
            timeout=120,
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line:
                    chunk = json.loads(line)
                    if token := chunk.get("response", ""):
                        yield token
                    if chunk.get("done"):
                        break
    except requests.exceptions.ConnectionError:
        yield "[ERROR] Ollama is not running. Start it with: ollama serve"
    except Exception as e:
        yield f"[ERROR] {e}"


def analyse_style(reference_text: str, model: str = DEFAULT_MODEL) -> str:
    """Extract a writing style profile from reference documents."""
    prompt = f"""Analyse the writing style of these text samples and give a concise style profile.

Cover: sentence length, tone, vocabulary level, use of contractions, paragraph structure, distinctive habits.

Samples:
---
{reference_text[:5000]}
---

Write a style profile in under 150 words."""

    result = []
    try:
        with requests.post(
            OLLAMA_URL,
            json={"model": model, "prompt": prompt, "stream": True},
            stream=True,
            timeout=60,
        ) as resp:
            for line in resp.iter_lines():
                if line:
                    chunk = json.loads(line)
                    result.append(chunk.get("response", ""))
                    if chunk.get("done"):
                        break
    except Exception as e:
        return f"Style analysis failed: {e}"
    return "".join(result).strip()


def flag_ai_words(text: str) -> list[str]:
    """Return list of AI buzzwords found in the text."""
    lower = text.lower()
    return [w for w in AI_WORDS if w.lower() in lower]
