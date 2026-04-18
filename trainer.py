"""
Trainer — builds a custom Ollama model from your writing samples.
Creates a Modelfile with your style baked into the system prompt,
then runs `ollama create` to register it as a permanent local model.
"""

import subprocess
import requests
import json
import os
import re
from pathlib import Path

MODELFILE_PATH = Path("MyStyleModel")
DEFAULT_BASE   = "llama3"

AI_WORDS = [
    "delve", "delving", "furthermore", "moreover", "utilize", "utilise",
    "consequently", "nevertheless", "nonetheless", "paradigm", "leverage",
    "synergy", "holistic", "robust", "seamless", "cutting-edge", "groundbreaking",
    "it is worth noting", "it is important to note", "in conclusion", "in summary",
    "to summarize", "as an AI", "certainly", "absolutely", "of course",
    "invaluable", "multifaceted", "nuanced", "comprehensive", "facilitate",
    "regarding", "pertaining to", "in order to", "it should be noted",
]


def analyse_style_detailed(reference_text: str, base_model: str = DEFAULT_BASE) -> str:
    """Deep style analysis — extracts vocabulary, rhythm, tone, habits."""
    prompt = f"""You are a writing style analyst. Study these text samples carefully.

Produce a detailed writing style profile covering ALL of the following:

1. SENTENCE STRUCTURE — average length, variety, complexity, use of fragments
2. TONE — formal/casual/assertive/conversational/etc.
3. VOCABULARY — level, word choices, favourite expressions, unique words they use
4. PUNCTUATION HABITS — comma usage, dashes, ellipsis, exclamation marks
5. CONTRACTIONS — do they use them? how often?
6. PARAGRAPH STYLE — length, how they open/close paragraphs
7. PERSONALITY MARKERS — humour, directness, hedging, opinions
8. WORDS/PHRASES THEY REPEAT — specific to this author
9. WHAT TO AVOID — patterns that would break their style

Text samples:
---
{reference_text[:8000]}
---

Write a detailed profile (200-300 words). Be specific — quote examples from the text where possible."""

    result = []
    try:
        with requests.post(
            "http://localhost:11434/api/generate",
            json={"model": base_model, "prompt": prompt, "stream": True},
            stream=True, timeout=120,
        ) as resp:
            for line in resp.iter_lines():
                if line:
                    chunk = json.loads(line)
                    result.append(chunk.get("response", ""))
                    if chunk.get("done"): break
    except Exception as e:
        return f"Analysis failed: {e}"
    return "".join(result).strip()


def build_modelfile(
    style_profile:  str,
    sample_text:    str,
    model_name:     str,
    base_model:     str = DEFAULT_BASE,
    temperature:    float = 0.75,
) -> str:
    """Generate the Ollama Modelfile content."""

    ai_words_list = ", ".join(AI_WORDS[:20])
    sample_snippet = sample_text[:3000].strip()

    system_prompt = f"""You are a writing assistant that has been trained to write exactly like a specific person.

═══ THEIR WRITING STYLE PROFILE ═══
{style_profile}

═══ REAL SAMPLES OF THEIR WRITING ═══
{sample_snippet}

═══ YOUR JOB ═══
When asked to rephrase, rewrite, or humanize text:
- Write EXACTLY like the person above — same vocabulary, rhythm, tone, sentence length
- Mirror their punctuation habits and paragraph style
- Use their favourite expressions and patterns
- Sound completely human and natural — never robotic
- NEVER use these AI words: {ai_words_list}
- NEVER start with "Certainly", "Absolutely", "Of course", "Great question"
- Output ONLY the rewritten text — no explanations, no preamble

You are their writing voice. Everything you write should be indistinguishable from them."""

    modelfile = f"""FROM {base_model}

SYSTEM \"\"\"{system_prompt}\"\"\"

PARAMETER temperature {temperature}
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
"""
    return modelfile


def create_model(model_name: str, modelfile_content: str) -> tuple[bool, str]:
    """Write Modelfile and run ollama create."""
    path = MODELFILE_PATH
    path.write_text(modelfile_content, encoding="utf-8")

    try:
        result = subprocess.run(
            ["ollama", "create", model_name, "-f", str(path)],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode == 0:
            return True, f"Model '{model_name}' created successfully."
        else:
            return False, result.stderr or result.stdout
    except FileNotFoundError:
        return False, "Ollama not found. Make sure it's installed and in your PATH."
    except subprocess.TimeoutExpired:
        return False, "Model creation timed out."
    except Exception as e:
        return False, str(e)


def delete_model(model_name: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["ollama", "rm", model_name],
            capture_output=True, text=True, timeout=30,
        )
        return result.returncode == 0, result.stdout or result.stderr
    except Exception as e:
        return False, str(e)


def list_custom_models() -> list[str]:
    """Return models that look like user-trained ones (contain 'style' or 'my-')."""
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        if r.status_code == 200:
            all_models = [m["name"] for m in r.json().get("models", [])]
            # flag models that were created by this tool
            custom = [m for m in all_models if "style" in m.lower() or m.startswith("my-")]
            return custom
        return []
    except Exception:
        return []
