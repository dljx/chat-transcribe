import os
import sys
import datetime
import google.generativeai as genai
from dotenv import load_dotenv
import streamlit as st
import tempfile

from audio_recorder_streamlit import audio_recorder

load_dotenv()

# Configure Google API for audio processing
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)



def transcribe(audio_file):
    model = genai.GenerativeModel("models/gemini-1.5-pro-latest")
    audio_file = genai.upload_file(path=audio_file)
    if st.session_state.transcript_text == "":
        user_prompt = """Can you transcribe this interview, in the format of timecode, speaker, caption.
        Use speaker A, speaker B, etc. to identify speakers."""

    else:
        user_prompt = """Accounting for the existing conversation provided here:\n\n""" + st.session_state.transcript_text + """\n\n
        Can you transcribe this interview, in the format of timecode, speaker, caption.
        Use speaker A, speaker B, etc. to identify speakers.
        """
    response = model.generate_content(
        [
            user_prompt,
            audio_file
        ]
    )
    return response.text


# def transcribe(audio_file):
#     transcript = openai.Audio.transcribe("whisper-1", audio_file)
#     return transcript


def save_audio_file(audio_bytes, file_extension):
    """
    Save audio bytes to a file with the specified extension.

    :param audio_bytes: Audio data in bytes
    :param file_extension: The extension of the output audio file
    :return: The name of the saved audio file
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"audio_{timestamp}.{file_extension}"

    with open(file_name, "wb") as f:
        f.write(audio_bytes)

    return file_name

def save_uploaded_file(uploaded_file):
    """Save uploaded file to a temporary file and return the path."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.' + uploaded_file.name.split('.')[-1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            return tmp_file.name
    except Exception as e:
        st.error(f"Error handling uploaded file: {e}")
        return None

def transcribe_audio(file_path):
    """
    Transcribe the audio file at the specified path.

    :param file_path: The path of the audio file to transcribe
    :return: The transcribed text
    """
    with open(file_path, "rb") as audio_file:
        transcript = transcribe(audio_file)

    return transcript["text"]

if 'transcript_text' not in st.session_state:
    st.session_state.transcript_text = ""

def main():
    """
    Main function to run the Whisper Transcription app.
    """
    st.title("Whisper Transcription")

    tab1, tab2 = st.tabs(["Record Audio", "Upload Audio"])
    # Record Audio tab
    with tab1:
        audio_bytes = audio_recorder(pause_threshold=3.0,auto_start=True)
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            audio_path = save_audio_file(audio_bytes, "mp3")
            #automatically transcribe
            st.session_state.transcript_text = st.session_state.transcript_text + transcribe(audio_path)
            st.text_area("Processed Output", st.session_state.transcript_text, height=300)

    # Upload Audio tab
    with tab2:
        audio_file = st.file_uploader("Upload Audio", type=["mp3", "mp4", "wav", "m4a"])
        if audio_file:
            file_extension = audio_file.type.split('/')[1]
            save_audio_file(audio_file.read(), file_extension)
            audio_path = save_uploaded_file(audio_file)
            st.audio(audio_path)

    # Transcribe button action
    if st.button("Transcribe"):
        with st.spinner('Processing...'):
            transcript_text = transcribe(audio_path)
            st.text_area("Processed Output", transcript_text, height=300)
        # Display the transcript
        st.header("Transcript")
        st.write(transcript_text)

        # Save the transcript to a text file
        with open("transcript.txt", "w") as f:
            f.write(transcript_text)

        # Provide a download button for the transcript
        st.download_button("Download Transcript", transcript_text)


if __name__ == "__main__":
    # Set up the working directory
    working_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(working_dir)

    # Run the main function
    main()
