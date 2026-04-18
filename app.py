"""
Humanizer — train a custom local model on your writing style.
Powered by Ollama. Free, offline, no API key.
Run: streamlit run app.py
"""

import streamlit as st
from extractor import extract_text, summarise_for_style
from rephraser import MODES, check_ollama, humanize_stream, flag_ai_words, DEFAULT_MODEL
from trainer import analyse_style_detailed, build_modelfile, create_model, delete_model, list_custom_models

# ── Page config ───────────────────────────────────────────────────────────

st.set_page_config(page_title="Humanizer", page_icon="🧠", layout="wide")

st.markdown("""
<style>
  .stApp { background: #0e0e16; color: #e2e2e2; }
  .block-container { padding-top: 2rem; }
  div[data-testid="stTextArea"] textarea {
    background: #1a1a28 !important; color: #e2e2e2 !important;
    border: 1px solid #2a2a3a !important; border-radius: 8px !important;
    font-size: 0.95rem !important;
  }
  .output-box {
    background: #111120; border: 1px solid #3a3a5a;
    border-radius: 10px; padding: 20px; font-size: 0.97rem;
    line-height: 1.8; min-height: 140px; white-space: pre-wrap;
  }
  .train-box {
    background: #111a11; border: 1px solid #2a5a2a;
    border-radius: 10px; padding: 20px;
  }
  .stat-pill {
    display:inline-block; background:#1e1a36; border:1px solid #3a3a5a;
    border-radius:20px; padding:3px 12px; font-size:0.8rem;
    margin-right:6px; margin-top:6px;
  }
  .ai-word {
    display:inline-block; background:#3a1a1a; border:1px solid #6a2a2a;
    border-radius:4px; padding:2px 8px; font-size:0.8rem; color:#f87; margin:2px;
  }
  .model-badge {
    display:inline-block; background:#1a2a1a; border:1px solid #3a6a3a;
    border-radius:20px; padding:4px 14px; font-size:0.85rem; color:#8f8;
  }
  .warn { background:#1e1410; border:1px solid #6a4a20;
    border-radius:8px; padding:12px 16px; font-size:0.85rem; color:#f0a; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────

for key, val in {
    "trained_model":   None,
    "style_profile":   None,
    "ref_text":        None,
    "output":          "",
    "selected_mode":   "humanize",
    "model":           DEFAULT_MODEL,
    "training_status": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ── Ollama check ──────────────────────────────────────────────────────────

ollama_ok, available_models = check_ollama()

# ── Header ────────────────────────────────────────────────────────────────

st.title("🧠 Humanizer")
st.caption("Train a custom local model on your writing — then humanize anything in your voice.")

if not ollama_ok:
    st.markdown('<div class="warn">⚠️ Ollama not running. Install from ollama.com → run: <code>ollama serve</code> → <code>ollama pull llama3</code></div>', unsafe_allow_html=True)

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────

tab_train, tab_use = st.tabs(["🏋️ Train Your Model", "✍️ Humanize"])


# ════════════════════════════════════════════════════════
# TAB 1 — TRAIN
# ════════════════════════════════════════════════════════
with tab_train:

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.subheader("1. Upload Your Writing")
        st.caption("Essays, emails, reports, messages — anything you personally wrote.")

        uploaded = st.file_uploader(
            "Drop files",
            type=["pdf", "docx", "txt", "doc"],
            accept_multiple_files=True,
            label_visibility="collapsed",
            key="train_upload",
        )

        if uploaded:
            texts = [extract_text(f.read(), f.name) for f in uploaded]
            st.session_state.ref_text = summarise_for_style(texts, max_chars=8000)
            st.success(f"{len(uploaded)} file(s) loaded — {len(st.session_state.ref_text):,} characters")
            for f in uploaded:
                st.markdown(f"- `{f.name}`")

        st.divider()
        st.subheader("2. Configure")

        model_name = st.text_input(
            "Model name",
            value="my-style",
            help="This is the name your custom model will have in Ollama.",
        )

        base_model = st.selectbox(
            "Base model",
            options=available_models if available_models else [DEFAULT_MODEL],
            help="The model to build on top of.",
        )

        temperature = st.slider("Temperature", 0.5, 1.0, 0.75, 0.05,
                                help="Higher = more creative. Lower = more consistent.")

        st.divider()

        train_btn = st.button(
            "🏋️ Train My Model",
            use_container_width=True,
            type="primary",
            disabled=not st.session_state.ref_text or not ollama_ok,
        )

        if train_btn and st.session_state.ref_text:
            progress = st.progress(0, text="Analysing your writing style...")

            with st.spinner("Step 1/3 — Deep style analysis..."):
                profile = analyse_style_detailed(st.session_state.ref_text, base_model)
                st.session_state.style_profile = profile
            progress.progress(40, text="Building Modelfile...")

            with st.spinner("Step 2/3 — Building Modelfile..."):
                modelfile = build_modelfile(
                    style_profile  = profile,
                    sample_text    = st.session_state.ref_text,
                    model_name     = model_name,
                    base_model     = base_model,
                    temperature    = temperature,
                )
            progress.progress(70, text="Creating model in Ollama...")

            with st.spinner(f"Step 3/3 — Creating '{model_name}' in Ollama..."):
                ok, msg = create_model(model_name, modelfile)

            progress.progress(100, text="Done!")

            if ok:
                st.session_state.trained_model   = model_name
                st.session_state.training_status = "success"
                st.success(f"✅ Model '{model_name}' is ready! Switch to the Humanize tab to use it.")
            else:
                st.session_state.training_status = "error"
                st.error(f"Training failed: {msg}")

    with col_right:
        st.subheader("Style Profile Preview")
        st.caption("What the model will learn about your writing.")

        if st.session_state.style_profile:
            st.markdown(
                f'<div style="background:#0e1a0e;border:1px solid #2a5a2a;border-radius:10px;'
                f'padding:18px;font-size:0.88rem;line-height:1.7;color:#cdc">'
                f'{st.session_state.style_profile}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="background:#111120;border:1px solid #2a2a3a;border-radius:10px;'
                'padding:40px;text-align:center;color:#444">'
                'Upload your writing and click Train to see your style profile here.</div>',
                unsafe_allow_html=True,
            )

        # Existing custom models
        custom_models = list_custom_models()
        if custom_models:
            st.divider()
            st.subheader("Your Trained Models")
            for m in custom_models:
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f'<span class="model-badge">✓ {m}</span>', unsafe_allow_html=True)
                with c2:
                    if st.button("Delete", key=f"del_{m}", type="secondary"):
                        ok, msg = delete_model(m)
                        if ok:
                            st.success(f"Deleted {m}")
                            st.rerun()
                        else:
                            st.error(msg)


# ════════════════════════════════════════════════════════
# TAB 2 — HUMANIZE
# ════════════════════════════════════════════════════════
with tab_use:

    left, right = st.columns([1, 1.6], gap="large")

    with left:

        # Model selector — put trained model first
        all_models = available_models or [DEFAULT_MODEL]
        trained    = st.session_state.trained_model

        st.subheader("Model")
        if trained and trained in all_models:
            st.markdown(f'<span class="model-badge">✓ Using your trained model: {trained}</span>', unsafe_allow_html=True)
            st.session_state.model = trained
            if st.button("Use a different model", use_container_width=True):
                st.session_state.model = DEFAULT_MODEL
        else:
            chosen = st.selectbox("Select model", all_models,
                                  index=all_models.index(st.session_state.model)
                                  if st.session_state.model in all_models else 0)
            st.session_state.model = chosen
            if not trained:
                st.info("Train a model in the 🏋️ tab to use your personal writing style.")

        st.divider()
        st.subheader("Mode")

        for key, cfg in MODES.items():
            is_sel = st.session_state.selected_mode == key
            if st.button(
                f"{cfg['icon']}  {cfg['label']}",
                key=f"use_mode_{key}",
                use_container_width=True,
                type="primary" if is_sel else "secondary",
                help=cfg["desc"],
            ):
                st.session_state.selected_mode = key
                st.session_state.output = ""
                st.rerun()

    with right:

        sel = MODES[st.session_state.selected_mode]
        st.subheader(f"{sel['icon']} {sel['label']}")
        st.caption(sel["desc"])

        input_text = st.text_area(
            "Paste text",
            height=220,
            placeholder="Paste AI-generated text here...",
            label_visibility="collapsed",
            key="use_input",
        )

        if input_text.strip():
            found = flag_ai_words(input_text)
            if found:
                pills = "".join(f'<span class="ai-word">{w}</span>' for w in found)
                st.markdown(f'<div style="margin-bottom:10px">⚠️ AI words detected: {pills}</div>',
                            unsafe_allow_html=True)

        c1, c2 = st.columns([2, 1])
        with c1:
            go = st.button("🧠 Humanize", use_container_width=True, type="primary",
                           disabled=not input_text.strip() or not ollama_ok)
        with c2:
            if st.button("🗑 Clear", use_container_width=True, key="clear_use"):
                st.session_state.output = ""
                st.rerun()

        if go and input_text.strip():
            st.session_state.output = ""
            placeholder = st.empty()
            collected   = []

            with st.spinner("Humanizing..."):
                for chunk in humanize_stream(
                    input_text    = input_text.strip(),
                    mode          = st.session_state.selected_mode,
                    style_profile = st.session_state.style_profile,
                    model         = st.session_state.model,
                ):
                    collected.append(chunk)
                    placeholder.markdown(
                        f'<div class="output-box">{"".join(collected)}</div>',
                        unsafe_allow_html=True,
                    )

            st.session_state.output = "".join(collected)

        if st.session_state.output:
            st.divider()
            orig_w = len(input_text.split()) if input_text else 0
            out_w  = len(st.session_state.output.split())
            diff   = out_w - orig_w
            ai_rem = flag_ai_words(st.session_state.output)

            st.markdown(
                f'<div style="margin-bottom:10px">'
                f'<span class="stat-pill">📥 {orig_w} words in</span>'
                f'<span class="stat-pill">📤 {out_w} words out</span>'
                f'<span class="stat-pill">{"📈" if diff>=0 else "📉"} {diff:+d}</span>'
                + (f'<span class="stat-pill" style="border-color:#6a2a2a;color:#f87">⚠️ {len(ai_rem)} AI words remain</span>'
                   if ai_rem else
                   '<span class="stat-pill" style="border-color:#2a6a2a;color:#8f8">✓ No AI words</span>')
                + '</div>',
                unsafe_allow_html=True,
            )

            st.code(st.session_state.output, language=None)
            st.caption("Click the copy icon above to copy.")
        elif not go:
            st.markdown(
                '<div class="output-box" style="color:#333;text-align:center;padding-top:50px">'
                'Humanized output will appear here.'
                '</div>', unsafe_allow_html=True,
            )
