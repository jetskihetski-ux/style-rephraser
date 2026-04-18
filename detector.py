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


def score_burstiness(text: str) -> tuple[float, dict]:
    """
    Burstiness = variance in sentence length.
    Humans: high variance (CV > 0.5). AI: low variance (CV < 0.25).
    Returns (score 0-1, details dict).
    """
    sents = _sentences(text)
    if len(sents) < 3:
        return 0.5, {"cv": 0, "min_len": 0, "max_len": 0, "avg_len": 0}
    lengths  = [len(s.split()) for s in sents]
    mean     = sum(lengths) / len(lengths)
    if mean == 0:
        return 0, {}
    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    std_dev  = math.sqrt(variance)
    cv       = std_dev / mean
    score    = min(cv / 0.6, 1.0)
    return score, {
        "cv":      round(cv, 3),
        "min_len": min(lengths),
        "max_len": max(lengths),
        "avg_len": round(mean, 1),
        "std_dev": round(std_dev, 1),
    }


def score_perplexity_proxy(text: str) -> tuple[float, dict]:
    """
    Proxy for perplexity using word frequency analysis.
    AI uses high-frequency (predictable) words. Humans use more varied vocabulary.
    Common words list approximates what a language model would predict.
    Returns (score 0-1, details).
    """
    # Top 200 most common English words — AI overuses these
    COMMON = set([
        "the","be","to","of","and","a","in","that","have","it","for","not",
        "on","with","he","as","you","do","at","this","but","his","by","from",
        "they","we","say","her","she","or","an","will","my","one","all","would",
        "there","their","what","so","up","out","if","about","who","get","which",
        "go","me","when","make","can","like","time","no","just","him","know",
        "take","people","into","year","your","good","some","could","them","see",
        "other","than","then","now","look","only","come","its","over","think",
        "also","back","after","use","two","how","our","work","first","well",
        "way","even","new","want","because","any","these","give","day","most",
        "us","is","was","are","were","been","has","had","did","said","each",
        "more","very","great","between","need","large","often","hand","high",
        "place","hold","turn","found","still","should","through","both","where",
        "much","before","right","too","mean","old","any","same","tell","boy",
        "follow","came","show","form","three","small","set","put","end","does",
    ])
    words     = _words(text)
    if len(words) < 10:
        return 0.5, {}
    common_ct = sum(1 for w in words if w in COMMON)
    ratio     = common_ct / len(words)
    # humans ~55-65% common words, AI ~70-80%
    if ratio < 0.60:   score = 1.0
    elif ratio < 0.68: score = 0.7
    elif ratio < 0.74: score = 0.4
    else:              score = 0.15
    return score, {
        "common_word_ratio": round(ratio * 100, 1),
        "unique_words":      len(set(words)),
        "total_words":       len(words),
    }


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
    Returns overall human score (0-100) and breakdown including
    real burstiness CV and perplexity proxy.
    """
    if not text.strip():
        return {"score": 0, "label": "N/A", "color": "#888", "breakdown": {},
                "burstiness": {}, "perplexity": {}}

    ai_penalty, found_words = score_ai_words(text)
    burst_score, burst_info = score_burstiness(text)
    perp_score,  perp_info  = score_perplexity_proxy(text)

    components = {
        "Burstiness (sentence variety)": burst_score              * 30,
        "Perplexity (word choice)":      perp_score               * 25,
        "Contractions":                  score_contractions(text) * 15,
        "Sentence Length Mix":           score_avg_sentence_length(text) * 15,
        "Vocab Diversity":               score_vocab_diversity(text)     * 10,
        "Punctuation Variety":           score_punctuation_variety(text) * 5,
    }

    raw    = sum(components.values())
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
        "score":       score,
        "label":       label,
        "color":       color,
        "ai_words":    found_words,
        "breakdown":   {k: round(v) for k, v in components.items()},
        "deduction":   round(deduct),
        "burstiness":  burst_info,
        "perplexity":  perp_info,
    }
