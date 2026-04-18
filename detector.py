"""
Local AI detection scorer — heuristic based, no API needed.
Scores text on how human it sounds (0-100%).
"""

import re
import math

AI_WORDS = [
    "delve", "delving", "furthermore", "moreover", "utilize", "utilise",
    "consequently", "nevertheless", "nonetheless", "paradigm", "leverage",
    "synergy", "holistic", "robust", "seamless", "cutting-edge", "groundbreaking",
    "it is worth noting", "it is important to note", "in conclusion", "in summary",
    "to summarize", "certainly", "absolutely", "of course", "invaluable",
    "multifaceted", "nuanced", "comprehensive", "facilitate", "regarding",
    "pertaining to", "in order to", "it should be noted", "overall",
    "it is essential", "plays a crucial role", "plays a vital role",
    "it is imperative", "demonstrate", "ensure", "implement",
]

AI_OPENERS = [
    "certainly", "absolutely", "of course", "great question",
    "as an ai", "i cannot", "i apologize", "i'd be happy",
    "in conclusion", "in summary", "to summarize", "overall,",
    "it is worth", "it is important", "it should be noted",
]


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]


def _words(text: str) -> list[str]:
    return re.findall(r'\b\w+\b', text.lower())


def score_ai_words(text: str) -> tuple[float, list[str]]:
    """Penalty for AI buzzwords. Returns (penalty 0-1, found words)."""
    lower  = text.lower()
    found  = [w for w in AI_WORDS if w in lower]
    words  = _words(text)
    if not words:
        return 0, found
    density = len(found) / max(len(words) / 10, 1)
    penalty = min(density * 0.15, 0.40)
    return penalty, found


def score_burstiness(text: str) -> float:
    """
    Burstiness = variance in sentence length.
    Humans write with high variance (short + long mixed).
    AI writes consistently similar-length sentences.
    Returns bonus 0-1.
    """
    sents = _sentences(text)
    if len(sents) < 3:
        return 0.5
    lengths = [len(s.split()) for s in sents]
    mean    = sum(lengths) / len(lengths)
    if mean == 0:
        return 0
    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    std_dev  = math.sqrt(variance)
    cv       = std_dev / mean   # coefficient of variation
    # humans typically CV > 0.4, AI typically CV < 0.25
    return min(cv / 0.6, 1.0)


def score_contractions(text: str) -> float:
    """Humans use contractions. AI avoids them. Returns bonus 0-1."""
    contractions = re.findall(
        r"\b(don't|doesn't|didn't|can't|won't|wouldn't|shouldn't|couldn't|"
        r"it's|that's|there's|they're|we're|you're|I'm|I've|I'll|I'd|"
        r"he's|she's|we've|you've|they've|isn't|aren't|wasn't|weren't)\b",
        text, re.IGNORECASE
    )
    words = _words(text)
    if not words:
        return 0
    rate = len(contractions) / len(words)
    return min(rate / 0.04, 1.0)


def score_avg_sentence_length(text: str) -> float:
    """
    AI tends to write long sentences (20-30 words avg).
    Humans vary more, often shorter.
    Returns bonus 0-1.
    """
    sents = _sentences(text)
    if not sents:
        return 0.5
    avg = sum(len(s.split()) for s in sents) / len(sents)
    # sweet spot: 10-18 words = human, 20+ = AI
    if avg <= 15:   return 1.0
    if avg <= 20:   return 0.7
    if avg <= 25:   return 0.4
    return 0.2


def score_opener(text: str) -> float:
    """Penalty if text starts with a classic AI opener."""
    first_line = text.strip().lower()[:80]
    for opener in AI_OPENERS:
        if first_line.startswith(opener):
            return -0.20
    return 0.0


def score_vocab_diversity(text: str) -> float:
    """Type-token ratio — diverse vocabulary = more human."""
    words = _words(text)
    if len(words) < 10:
        return 0.5
    ttr = len(set(words)) / len(words)
    return min(ttr / 0.6, 1.0)


def score_punctuation_variety(text: str) -> float:
    """Humans use dashes, ellipses, exclamations, questions more freely."""
    human_punct = len(re.findall(r'[—–\-]{2,}|\.{2,}|!|\?', text))
    sentences   = len(_sentences(text))
    if not sentences:
        return 0.5
    rate = human_punct / sentences
    return min(rate / 0.3, 1.0)


def human_score(text: str) -> dict:
    """
    Returns overall human score (0-100) and breakdown.
    """
    if not text.strip():
        return {"score": 0, "label": "N/A", "color": "#888", "breakdown": {}}

    ai_penalty, found_words = score_ai_words(text)

    components = {
        "Sentence Variety":    score_burstiness(text)          * 25,
        "Contractions":        score_contractions(text)        * 20,
        "Sentence Length":     score_avg_sentence_length(text) * 20,
        "Vocabulary Diversity":score_vocab_diversity(text)     * 15,
        "Punctuation":         score_punctuation_variety(text) * 10,
        "AI Opener":           max(score_opener(text), 0)      * 10,
    }

    raw    = sum(components.values())          # max ~100
    deduct = ai_penalty * 100
    score  = max(0, min(100, raw - deduct))
    score  = round(score)

    if score >= 75:
        label, color = "Likely Human", "#4caf50"
    elif score >= 50:
        label, color = "Mixed", "#ff9800"
    elif score >= 30:
        label, color = "Likely AI", "#f44336"
    else:
        label, color = "AI Generated", "#b71c1c"

    return {
        "score":      score,
        "label":      label,
        "color":      color,
        "ai_words":   found_words,
        "breakdown":  {k: round(v) for k, v in components.items()},
        "deduction":  round(deduct),
    }
