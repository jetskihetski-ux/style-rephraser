# Humanizer

Upload your writing samples → train a custom local Ollama model on your style → humanize any text in your voice. Free, offline, no API key.

## How it works
1. Upload your documents (PDF, DOCX, TXT)
2. The app does a deep style analysis — vocabulary, rhythm, tone, habits
3. Builds an Ollama Modelfile with your style baked into the system prompt
4. Runs `ollama create my-style` — you now have a permanent custom model
5. Use it to humanize any text in your exact writing voice

## Modes
| Mode | What it does |
|------|-------------|
| 🧠 Humanize | Strips AI patterns — sounds like a real person |
| 🪞 Match My Style | Uses your trained model voice |
| 😎 Casual Human | Natural, relaxed, conversational |
| 🎒 Student | Smart but not overly polished |
| 💼 Professional | Clear and human, not robotic |
| 🗣️ Native Speaker | Fluent with real idioms |
| ✂️ Shorter | Humanized and condensed |
| ✨ Creative | Vivid, expressive, personality-driven |
| 📋 Bullet Points | Clean human-sounding bullets |
| 🕵️ Bypass AI Detection | Aggressively rewrites to evade detectors |

## Setup

```bash
# 1. Install Ollama
# Download from https://ollama.com

# 2. Pull a base model
ollama pull llama3

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
streamlit run app.py
```

No API key. Runs entirely on your machine.
