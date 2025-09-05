

import streamlit as st
from PIL import Image
import google.generativeai as genai
import io
from deep_translator import GoogleTranslator
import textwrap
from gtts import gTTS


# Load Gemini API key
GOOGLE_API_KEY= "AIzaSyApSLRRJYndtVyPxMHL-ugqSDsey_3U--I"
genai.configure(api_key=GOOGLE_API_KEY)

st.title("🗿 Sculpture Storyteller with Gemini")
st.write("Upload a photo or click a picture of a sculpture, and I'll tell you its story, style, and historical background.")

# Session state setup
if "story_text" not in st.session_state:
    st.session_state.story_text = ""
if "summary" not in st.session_state:
    st.session_state.summary = ""
if "open_camera" not in st.session_state:
    st.session_state.open_camera = False
if "captured_image" not in st.session_state:
    st.session_state.captured_image = None

languages = {
    "English": "en",
    "Hindi": "hi",
    "Kannada": "kn",
    "Tamil": "ta",
    "Telugu": "te"
}

# File uploader
uploaded_file = st.file_uploader("Upload a sculpture image", type=["jpg", "jpeg", "png"])

# Camera control
if not st.session_state.open_camera and st.button("📷 Open Camera"):
    st.session_state.open_camera = True

camera_file = None
if st.session_state.open_camera:
    camera_file = st.camera_input("Take a picture with your webcam")

    if camera_file:
        st.session_state.captured_image = camera_file
        st.session_state.open_camera = False  # ✅ Close camera after capture

# Use uploaded file > captured photo
image_source = uploaded_file if uploaded_file else st.session_state.captured_image

place_name = st.text_input("Enter the temple or place name (optional)", placeholder="e.g., Belur Temple, Karnataka")
selected_language = st.selectbox("Select story language:", list(languages.keys()), index=0)

def translate_text(text, target_lang):
    max_len = 4999
    chunks = textwrap.wrap(text, max_len, replace_whitespace=False)
    translated_chunks = []
    for chunk in chunks:
        try:
            translated_chunk = GoogleTranslator(source='auto', target=target_lang).translate(chunk)
            translated_chunks.append(translated_chunk)
        except Exception as e:
            translated_chunks.append(f"[Translation Error: {e}]")
    return " ".join(translated_chunks)

if image_source:
    image = Image.open(image_source)
    st.image(image, caption="Selected Sculpture", use_column_width=True)

    image_bytes = io.BytesIO()
    image.save(image_bytes, format="PNG")
    image_bytes = image_bytes.getvalue()

    model = genai.GenerativeModel("gemini-2.5-pro")

    if st.button("Get Sculpture Story"):
        with st.spinner("Analyzing the sculpture..."):
            prompt = [
                "You are a friendly local temple guide. Look at the uploaded sculpture and explain it in a simple, storytelling way that visitors can easily understand.",
                "1. If you can recognise, describe which deity or deities are shown, and their special features or symbols.",
                "2. Tell the main story or belief connected with this deity/deities, in short and clear language.",
                "3. Share some history about the sculpture — which period, dynasty, or temple style it belongs to.",
                "4. Point out a few interesting artistic details like posture, gestures (mudras), ornaments, or carving style.",
                "5. Keep the explanation warm, easy to follow, and not too long, as if you are guiding tourists.",
                "6. Output must be in plain text only — do not use bold (**), italics (*), markdown, or special formatting."
            ]

            if place_name:
                prompt.insert(0, f"The sculpture is located at or associated with: {place_name}.")

            response = model.generate_content(
                prompt + [{"mime_type": "image/png", "data": image_bytes}]
            )
            story_text = response.text

            if selected_language != "English":
                story_text = translate_text(story_text, languages[selected_language])

            st.session_state.story_text = story_text
            st.success(f"📖 Story in {selected_language}:")
            st.write(st.session_state.story_text)

# Audio button
if st.session_state.story_text:
    if st.button("🔊 Play Summarised Audio"):
        with st.spinner("Summarising and generating voice..."):
            summary = genai.GenerativeModel("gemini-2.5-flash").generate_content(
                f"Summarise this in simple {selected_language} for narration: {st.session_state.story_text} IN AROUND 500 WORDS"
            ).text

            st.session_state.summary = summary
            tts = gTTS(text=summary, lang=languages[selected_language])
            tts.save("story.mp3")

            audio_file = open("story.mp3", "rb")
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format="audio/mp3")
