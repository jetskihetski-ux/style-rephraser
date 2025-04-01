"""
Core rephrasing logic using Claude API.
"""

import anthropic

CLIENT = anthropic.Anthropic()
MODEL  = "claude-opus-4-6"

# ── Rephrase modes ────────────────────────────────────────────────────────

MODES = {
    "match_style": {
        "label": "Match My Style",
        "icon":  "🪞",
        "desc":  "Rewrite using the exact tone, vocabulary, and structure from your uploaded documents.",
        "instruction": (
            "Rewrite the input text so it sounds exactly like the author of the reference documents. "
            "Mirror their sentence length, vocabulary choices, tone, punctuation habits, and overall feel. "
            "The output should be indistinguishable from something the original author wrote."
        ),
    },
    "formal": {
        "label": "Formal",
        "icon":  "🎩",
        "desc":  "Professional, polished language suitable for reports or emails.",
        "instruction": (
            "Rewrite the text in a formal, professional tone. Use complete sentences, precise vocabulary, "
            "avoid contractions, and structure the content clearly. Suitable for business or academic contexts."
        ),
    },
    "casual": {
        "label": "Casual",
        "icon":  "😎",
        "desc":  "Relaxed, conversational — like texting a friend.",
        "instruction": (
            "Rewrite the text in a casual, conversational tone. Use natural language, contractions, "
            "short sentences, and keep it easy and friendly — like you're talking to someone you know."
        ),
    },
    "shorter": {
        "label": "Shorter",
        "icon":  "✂️",
        "desc":  "Same meaning, fewer words — cut everything unnecessary.",
        "instruction": (
            "Rewrite the text to be significantly shorter. Remove all filler, redundancy, and unnecessary words. "
            "Keep only the core meaning. Cut at least 40% of the word count without losing key information."
        ),
    },
    "longer": {
        "label": "Longer",
        "icon":  "📝",
        "desc":  "Expand with more detail, examples, and explanation.",
        "instruction": (
            "Rewrite the text to be longer and more detailed. Add context, examples, elaboration, and smooth "
            "transitions. Make it richer and more complete without adding fluff."
        ),
    },
    "simpler": {
        "label": "Simpler",
        "icon":  "🧒",
        "desc":  "Plain English — easy for anyone to understand.",
        "instruction": (
            "Rewrite the text using simple, plain English. Use short sentences, common everyday words, "
            "and avoid jargon or complex phrases. Anyone should be able to understand it easily."
        ),
    },
    "persuasive": {
        "label": "Persuasive",
        "icon":  "🎯",
        "desc":  "Stronger, more convincing — built to persuade.",
        "instruction": (
            "Rewrite the text to be more persuasive and impactful. Use strong verbs, confident language, "
            "rhetorical techniques, and a compelling structure. Make the reader want to agree or act."
        ),
    },
    "academic": {
        "label": "Academic",
        "icon":  "🎓",
        "desc":  "Scholarly tone with structured arguments.",
        "instruction": (
            "Rewrite the text in an academic style. Use formal vocabulary, structured paragraphs, "
            "hedging language where appropriate (e.g. 'it may be argued'), and a logical, evidence-based flow."
        ),
    },
    "creative": {
        "label": "Creative",
        "icon":  "✨",
        "desc":  "Vivid, expressive, imaginative rewrite.",
        "instruction": (
            "Rewrite the text creatively. Use vivid language, metaphors, varied sentence rhythm, and expressive "
            "word choices. Make it engaging and memorable while preserving the core meaning."
        ),
    },
    "bullet_points": {
        "label": "Bullet Points",
        "icon":  "📋",
        "desc":  "Break it down into clear, scannable bullet points.",
        "instruction": (
            "Convert the text into a clean, organised list of bullet points. Group related ideas, "
            "use parallel structure, and make each point concise and standalone."
        ),
    },
}


# ── Prompts ───────────────────────────────────────────────────────────────

def _style_analysis_prompt(reference_text: str) -> str:
    return f"""Analyse the writing style of the following text samples and produce a concise style profile.

Cover:
- Sentence length and structure (short/long, simple/complex)
- Tone (formal/casual/technical/friendly/etc.)
- Vocabulary level and word choices
- Use of punctuation, contractions, emphasis
- Paragraph structure
- Any distinctive habits or patterns

Reference samples:
\"\"\"
{reference_text}
\"\"\"

Respond with a structured style profile in under 200 words."""


def _rephrase_prompt(input_text: str, instruction: str, style_profile: str | None) -> str:
    style_block = (
        f"\n\nWriting style profile to match:\n\"\"\"\n{style_profile}\n\"\"\""
        if style_profile else ""
    )
    return f"""You are a professional writing assistant.{style_block}

Task: {instruction}

Input text:
\"\"\"
{input_text}
\"\"\"

Output ONLY the rewritten text. No explanation, no preamble, no labels."""


# ── Public API ────────────────────────────────────────────────────────────

def analyse_style(reference_text: str) -> str:
    """Extract a style profile from reference documents."""
    msg = CLIENT.messages.create(
        model    = MODEL,
        max_tokens = 400,
        messages = [{"role": "user", "content": _style_analysis_prompt(reference_text)}],
    )
    return msg.content[0].text.strip()


def rephrase(
    input_text:    str,
    mode:          str,
    style_profile: str | None = None,
) -> str:
    """Rephrase input_text according to the chosen mode."""
    mode_cfg    = MODES.get(mode, MODES["formal"])
    instruction = mode_cfg["instruction"]

    # For match_style mode, style profile is essential
    if mode == "match_style" and not style_profile:
        instruction = (
            "Rewrite the text clearly and naturally, preserving the original meaning. "
            "(No reference documents provided — upload documents to enable style matching.)"
        )

    prompt = _rephrase_prompt(input_text, instruction, style_profile if mode == "match_style" else None)

    msg = CLIENT.messages.create(
        model      = MODEL,
        max_tokens = 2048,
        messages   = [{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()


def rephrase_stream(
    input_text:    str,
    mode:          str,
    style_profile: str | None = None,
):
    """Stream rephrased text token by token."""
    mode_cfg    = MODES.get(mode, MODES["formal"])
    instruction = mode_cfg["instruction"]

    if mode == "match_style" and not style_profile:
        instruction = (
            "Rewrite the text clearly and naturally, preserving the original meaning. "
            "(No reference documents provided — upload documents to enable style matching.)"
        )

    prompt = _rephrase_prompt(input_text, instruction, style_profile if mode == "match_style" else None)

    with CLIENT.messages.stream(
        model      = MODEL,
        max_tokens = 2048,
        messages   = [{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            yield text
