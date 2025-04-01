"""
Style Rephraser — learns your writing style and rephrases any text.
Run: streamlit run app.py
"""

import streamlit as st
from extractor import extract_text, summarise_for_style
from rephraser import MODES, analyse_style, rephrase_stream

# ── Page config ───────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Style Rephraser",
    page_icon="✍️",
    layout="wide",
)

st.markdown("""
<style>
  .stApp { background: #0e0e16; color: #e2e2e2; }
  .block-container { padding-top: 2rem; }
  div[data-testid="stTextArea"] textarea {
    background: #1a1a28; color: #e2e2e2;
    border: 1px solid #2a2a3a; border-radius: 8px;
    font-size: 0.95rem;
  }
  .mode-card {
    background: #1a1a28; border: 1px solid #2a2a3a;
    border-radius: 10px; padding: 12px 16px; margin-bottom: 8px;
    cursor: pointer;
  }
  .mode-card.selected { border-color: #7c6ef7; background: #1e1a36; }
  .style-box {
    background: #111120; border: 1px solid #2a2a3a;
    border-radius: 8px; padding: 14px; font-size: 0.85rem;
    color: #aaa; font-family: monospace;
  }
  .output-box {
    background: #111120; border: 1px solid #3a3a5a;
    border-radius: 10px; padding: 20px; font-size: 0.97rem;
    line-height: 1.7; min-height: 120px;
  }
  .stat-pill {
    display:inline-block; background:#1e1a36; border:1px solid #3a3a5a;
    border-radius:20px; padding:3px 12px; font-size:0.8rem; margin-right:6px;
  }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────

if "style_profile"  not in st.session_state: st.session_state.style_profile  = None
if "ref_filenames"  not in st.session_state: st.session_state.ref_filenames  = []
if "output"         not in st.session_state: st.session_state.output         = ""
if "selected_mode"  not in st.session_state: st.session_state.selected_mode  = "match_style"

# ── Header ────────────────────────────────────────────────────────────────

st.title("✍️ Style Rephraser")
st.caption("Upload your documents — the tool learns how you write, then rephrases anything in your voice.")

st.divider()

# ── Layout ────────────────────────────────────────────────────────────────

left, right = st.columns([1, 1.6], gap="large")

# ════════════════════════════════════════════════════════
# LEFT — Upload + Mode selector
# ════════════════════════════════════════════════════════
with left:

    # ── Reference documents ──
    st.subheader("1. Upload Your Writing Samples")
    st.caption("PDFs, Word docs, or text files — essays, reports, emails, anything you wrote.")

    uploaded = st.file_uploader(
        "Drop files here",
        type=["pdf", "docx", "txt", "doc"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded:
        new_names = [f.name for f in uploaded]
        if new_names != st.session_state.ref_filenames:
            st.session_state.ref_filenames = new_names
            st.session_state.style_profile = None   # reset if files change

        with st.expander(f"📄 {len(uploaded)} file(s) loaded", expanded=False):
            for f in uploaded:
                st.markdown(f"- `{f.name}`")

        if st.session_state.style_profile is None:
            with st.spinner("Analysing your writing style..."):
                texts = [extract_text(f.read(), f.name) for f in uploaded]
                ref   = summarise_for_style(texts)
                st.session_state.style_profile = analyse_style(ref)
            st.success("Style learned!")

    if st.session_state.style_profile:
        with st.expander("🧠 Style Profile", expanded=False):
            st.markdown(
                f'<div class="style-box">{st.session_state.style_profile}</div>',
                unsafe_allow_html=True,
            )
        if st.button("🔄 Reset Style", use_container_width=True):
            st.session_state.style_profile = None
            st.session_state.ref_filenames = []
            st.rerun()
    else:
        st.info("No style learned yet. Upload files above, or use any mode without matching.")

    st.divider()

    # ── Mode selector ──
    st.subheader("2. Choose a Mode")

    for key, cfg in MODES.items():
        is_selected = st.session_state.selected_mode == key
        label = f"{'**' if is_selected else ''}{cfg['icon']} {cfg['label']}{'**' if is_selected else ''}"
        if st.button(
            f"{cfg['icon']} {cfg['label']}",
            key=f"mode_{key}",
            use_container_width=True,
            type="primary" if is_selected else "secondary",
            help=cfg["desc"],
        ):
            st.session_state.selected_mode = key
            st.session_state.output = ""
            st.rerun()


# ════════════════════════════════════════════════════════
# RIGHT — Input + Output
# ════════════════════════════════════════════════════════
with right:

    selected = MODES[st.session_state.selected_mode]
    st.subheader(f"3. Rephrase — {selected['icon']} {selected['label']}")
    st.caption(selected["desc"])

    input_text = st.text_area(
        "Paste your text here",
        height=200,
        placeholder="Type or paste any text you want to rephrase...",
        label_visibility="collapsed",
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        rephrase_btn = st.button(
            f"✍️ Rephrase — {selected['label']}",
            use_container_width=True,
            type="primary",
            disabled=not input_text.strip(),
        )
    with col2:
        if st.button("🗑 Clear", use_container_width=True):
            st.session_state.output = ""
            st.rerun()

    # ── Run rephrase ──
    if rephrase_btn and input_text.strip():
        st.session_state.output = ""
        output_box = st.empty()
        collected  = []

        with st.spinner("Rephrasing..."):
            for chunk in rephrase_stream(
                input_text    = input_text.strip(),
                mode          = st.session_state.selected_mode,
                style_profile = st.session_state.style_profile,
            ):
                collected.append(chunk)
                output_box.markdown(
                    f'<div class="output-box">{"".join(collected)}</div>',
                    unsafe_allow_html=True,
                )

        st.session_state.output = "".join(collected)

    # ── Show output ──
    if st.session_state.output:
        st.divider()
        st.subheader("Output")

        st.markdown(
            f'<div class="output-box">{st.session_state.output}</div>',
            unsafe_allow_html=True,
        )

        # Stats
        orig_words = len(input_text.split()) if input_text else 0
        out_words  = len(st.session_state.output.split())
        diff       = out_words - orig_words
        diff_s     = f"+{diff}" if diff >= 0 else str(diff)

        st.markdown(
            f'<div style="margin-top:10px">'
            f'<span class="stat-pill">📥 {orig_words} words in</span>'
            f'<span class="stat-pill">📤 {out_words} words out</span>'
            f'<span class="stat-pill">{"📈" if diff>=0 else "📉"} {diff_s} words</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown("&nbsp;")
        st.code(st.session_state.output, language=None)
        st.caption("☝️ Click the copy icon on the code block above to copy.")

    elif not rephrase_btn:
        st.markdown(
            '<div class="output-box" style="color:#444; text-align:center; padding-top:40px;">'
            'Your rephrased text will appear here.'
            '</div>',
            unsafe_allow_html=True,
        )
