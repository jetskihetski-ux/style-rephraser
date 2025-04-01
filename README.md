# Style Rephraser

Upload your own writing samples — essays, emails, reports — and the tool learns exactly how you write. Then rephrase any text in your voice, or in 9 other modes.

## How it works
1. Upload your documents (PDF, DOCX, TXT)
2. Claude analyses your writing style — sentence length, tone, vocabulary, habits
3. Paste any text and choose a rephrasing mode
4. Get the output streamed in real time

## Rephrasing Modes
| Mode | What it does |
|------|-------------|
| 🪞 Match My Style | Rewrites to sound exactly like you |
| 🎩 Formal | Professional, polished language |
| 😎 Casual | Relaxed, conversational |
| ✂️ Shorter | Same meaning, fewer words |
| 📝 Longer | Expanded with more detail |
| 🧒 Simpler | Plain English anyone can understand |
| 🎯 Persuasive | Stronger, more convincing |
| 🎓 Academic | Scholarly, structured tone |
| ✨ Creative | Vivid, expressive rewrite |
| 📋 Bullet Points | Breaks it into scannable bullets |

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

Requires an Anthropic API key:
```bash
export ANTHROPIC_API_KEY=your_key_here
```
