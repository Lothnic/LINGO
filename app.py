import streamlit as st
import argostranslate.translate

# Page config
st.set_page_config(
    page_title="Kangri-Hindi Translator",
    page_icon="🌍",
    layout="centered"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        padding: 1rem 0;
    }
    .translation-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .stTextArea textarea {
        font-size: 18px !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'translation_history' not in st.session_state:
    st.session_state.translation_history = []

@st.cache_resource
def load_models():
    """Load Argos Translate models once"""
    installed_langs = argostranslate.translate.get_installed_languages()
    
    # Find Kangri and Hindi
    kangri = next((l for l in installed_langs if l.name == "Kangri"), None)
    hindi = next((l for l in installed_langs if l.name == "Hindi"), None)
    
    if not kangri or not hindi:
        st.error("⚠️ Models not installed! Please run: python install_model.py")
        st.stop()
    
    return {
        "kangri": kangri,
        "hindi": hindi,
        "kangri_to_hindi": kangri.get_translation(hindi),
        "hindi_to_kangri": hindi.get_translation(kangri)
    }

def translate_text(text, direction):
    """Translate text in specified direction"""
    models = load_models()
    
    if direction == "Kangri → Hindi":
        translation = models["kangri_to_hindi"]
    else:
        translation = models["hindi_to_kangri"]
    
    return translation.translate(text)

# Header
st.markdown('<h1 class="main-header">🌍 Kangri ↔ Hindi Translator</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #666;">Neural Machine Translation powered by Transformer models</p>', unsafe_allow_html=True)

# Load models
models = load_models()

# Direction selector
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    direction = st.selectbox(
        "Translation Direction",
        ["Kangri → Hindi", "Hindi → Kangri"],
        label_visibility="collapsed"
    )

st.markdown("---")

# Input/Output layout
col_input, col_output = st.columns(2)

with col_input:
    st.markdown(f"### {'📝 Kangri' if direction == 'Kangri → Hindi' else '📝 Hindi'}")
    input_text = st.text_area(
        "Enter text",
        height=200,
        placeholder=f"Type your {'Kangri' if direction == 'Kangri → Hindi' else 'Hindi'} text here...",
        label_visibility="collapsed",
        key="input"
    )

with col_output:
    st.markdown(f"### {'✨ Hindi' if direction == 'Kangri → Hindi' else '✨ Kangri'}")
    output_placeholder = st.empty()

# Translate button
if st.button("🔄 Translate", type="primary", use_container_width=True):
    if input_text.strip():
        with st.spinner("Translating..."):
            try:
                translation = translate_text(input_text, direction)
                
                # Display result
                with col_output:
                    output_placeholder.text_area(
                        "Translation",
                        value=translation,
                        height=200,
                        label_visibility="collapsed",
                        key="output"
                    )
                
                # Add to history
                st.session_state.translation_history.insert(0, {
                    "direction": direction,
                    "input": input_text,
                    "output": translation
                })
                
                st.success("✅ Translation complete!")
                
            except Exception as e:
                st.error(f"❌ Translation failed: {str(e)}")
    else:
        st.warning("⚠️ Please enter some text to translate")

# Example sentences
st.markdown("---")
st.markdown("### 💡 Try These Examples")

examples = {
    "Kangri → Hindi": [
        "मैं तुसां नैं प्यार करदा",
        "तुस्सां किदा ओ",
        "मेरा नां राज है"
    ],
    "Hindi → Kangri": [
        "मैं आपसे प्यार करता हूँ",
        "आप कैसे हैं",
        "मेरा नाम राज है"
    ]
}

cols = st.columns(3)
for idx, example in enumerate(examples[direction]):
    with cols[idx]:
        if st.button(example, key=f"ex_{idx}"):
            st.session_state.input = example
            st.rerun()

# Translation history
if st.session_state.translation_history:
    st.markdown("---")
    with st.expander("📜 Translation History"):
        for i, item in enumerate(st.session_state.translation_history[:5]):
            st.markdown(f"**{item['direction']}**")
            st.text(f"Input:  {item['input']}")
            st.text(f"Output: {item['output']}")
            if i < 4 and i < len(st.session_state.translation_history) - 1:
                st.markdown("---")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p>Transformer-based NMT | 5000 Training Steps | INT8 Quantized</p>
    <p>Model v1.1 (Kangri→Hindi) | Model v1.0 (Hindi→Kangri)</p>
</div>
""", unsafe_allow_html=True)
