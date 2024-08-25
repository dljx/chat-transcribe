import os
import sys
import datetime
import google.generativeai as genai
from dotenv import load_dotenv
import streamlit as st
import tempfile
import soundfile as sf

from audio_recorder_streamlit import audio_recorder

load_dotenv()

# Configure Google API for audio processing
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# Set a flag to indicate if transcription is in progress
transcribing = False

def transcribe(audio_file):
    """Transcribes a single audio chunk using the Gemini model."""
    global transcribing
    transcribing = True
    try:
        model = genai.GenerativeModel("models/gemini-1.5-pro-latest")
        audio_file = genai.upload_file(path=audio_file)
        if 'transcript_text' not in st.session_state or st.session_state.transcript_text == "":
            user_prompt = """You are a transcriber transcribing 3 second chunks of audio.
            Transcribe this audio by accounting for the input coming in 3 second chunks and give the output directly with correct punctuations.
            It is possible that the audio might cut mid sentence, in that case join the end of the previous chunk transcription with the beginning of the next chunk's transcription appropriately."""
        else:
            user_prompt = """Accounting for the existing conversation provided here:\n\n""" + st.session_state.transcript_text + """\n\n
            Transcribe this audio by accounting for the input coming in 3 second chunks and give the output directly with correct punctuations.
            It is possible that the audio might cut mid sentence, in that case join the end of the previous chunk transcription with the beginning of the next chunk's transcription appropriately.
            """
        response = model.generate_content(
            [
                user_prompt,
                audio_file
            ]
        )
        return response.text
    except Exception as e:
        st.error(f"An error occurred during transcription: {e}")
        return ""
    finally:
        transcribing = False

def save_audio_file(audio_bytes, file_extension):
    """Saves audio bytes to a temporary file."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"audio_{timestamp}.{file_extension}"
    with open(file_name, "wb") as f:
        f.write(audio_bytes)
    return file_name

def save_uploaded_file(uploaded_file):
    """Saves an uploaded file to a temporary location."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.' + uploaded_file.name.split('.')[-1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            return tmp_file.name
    except Exception as e:
        st.error(f"Error handling uploaded file: {e}")
        return None

def chunk_audio(audio_file, chunk_duration=5):
    """Chunks an audio file into segments."""
    y, sr = sf.read(audio_file)
    chunk_samples = int(chunk_duration * sr)
    chunks = []
    for i in range(0, len(y), chunk_samples):
        chunk = y[i:i + chunk_samples]
        chunk_path = f"{os.path.splitext(audio_file)[0]}_{i // chunk_samples}.wav"
        sf.write(chunk_path, chunk, sr)
        chunks.append(chunk_path)
    return chunks

def transcribe_chunks(chunk_paths):
    """Transcribes chunks and streams output to Streamlit."""
    global transcribing 
    transcript = ""
    for i, chunk_path in enumerate(chunk_paths):
        with st.spinner(f"Transcribing chunk {i+1}/{len(chunk_paths)}..."):
            chunk_transcript = transcribe(chunk_path)
            transcript += chunk_transcript + "\n"
            st.session_state.transcript_text = transcript # Update the session state
            st.text_area("Processed Output", st.session_state.transcript_text, height=300) # Update the text area
            # Remove temporary chunk files after transcription
            os.remove(chunk_path)
    return transcript

if 'transcript_text' not in st.session_state:
    st.session_state.transcript_text = ""

def main():
    st.title("Gemini Audio Transcription Demo")

    tab1, tab2 = st.tabs(["Record Audio", "Upload Audio"])

    # Record Audio tab
    with tab1:
        audio_bytes = audio_recorder(pause_threshold=3.0, auto_start=False)
        if audio_bytes and not transcribing:
            st.audio(audio_bytes, format="audio/wav")
            audio_path = save_audio_file(audio_bytes, "wav")
            chunk_paths = chunk_audio(audio_path)
            st.session_state.transcript_text = transcribe_chunks(chunk_paths) 

    # Upload Audio tab
    with tab2:
        audio_file = st.file_uploader("Upload Audio", type=["mp3", "mp4", "wav", "m4a"])
        if audio_file and not transcribing: 
            file_extension = audio_file.type.split('/')[1]
            save_audio_file(audio_file.read(), file_extension)
            audio_path = save_uploaded_file(audio_file)
            st.audio(audio_path)
            chunk_paths = chunk_audio(audio_path)
            st.session_state.transcript_text = transcribe_chunks(chunk_paths)

if __name__ == "__main__":
    working_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(working_dir)
    main()