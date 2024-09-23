
import os
import time
import tempfile
import threading
import queue
import logging
import io
import asyncio
import vertexai
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
from google.cloud import storage
from vertexai.generative_models import GenerativeModel, Part
from pydub import AudioSegment
import numpy as np
import datetime

vertexai.init(project="[PROJECT_ID]", location="asia-southeast1")  # Replace with your project and location
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables (replace with your actual values)
GCS_BUCKET_NAME = "[BUCKET_NAME]"  # Replace with your bucket name

# Configure Gemini
GEMINI_MODEL_ID = "gemini-1.5-pro-001"  # Replace with the appropriate model ID
gemini_model = GenerativeModel(GEMINI_MODEL_ID)

# Configure Google Cloud Storage
storage_client = storage.Client()
bucket = storage_client.bucket(GCS_BUCKET_NAME)

# Configuration
CHUNK_DURATION = 8 # seconds

# Global variables
audio_queue = queue.Queue()
transcript = ""
transcribing_lock = threading.Lock()
recording = False  # Flag to indicate recording status
full_audio = AudioSegment.empty()  # Store the complete audio recording

# Simplified ICE server configuration (using Google's STUN server)
RTC_CONFIGURATION = RTCConfiguration(
    iceServers=[{"urls": ["stun:stun.l.google.com:19302"]}]
)

# Callback queue for updating the transcript from the worker thread
callback_queue = queue.Queue()

def upload_chunk_to_gcs(audio_bytes):
    """Uploads audio chunk to GCS and returns URI."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    blob_name = f"audio_chunk_{timestamp}.wav"
    blob = bucket.blob(blob_name)
    blob.upload_from_string(audio_bytes, content_type="audio/wav")
    gcs_uri = f"gs://{GCS_BUCKET_NAME}/{blob_name}"
    logger.info(f"Uploaded audio chunk to GCS: {gcs_uri}")
    return gcs_uri


def transcribe_chunk(audio_uri):
    """Transcribes audio chunk using Gemini."""
    global transcript
    try:
        audio_part = Part.from_uri(audio_uri, mime_type="audio/wav")

        if not st.session_state.transcript_text:
            user_prompt = """You are a transcriber transcribing audio chunks.
            Pay close attention to the very beginning of the audio chunk to ensure that no words or sounds are transcribed wrongly, even if they are brief. Fill up the transcription gap as best as you can.
            Accuracy is crucial, especially at the beginning of the audio chunk. Please ensure that the transcription is complete and precise. 
            Transcribe this audio and give the output directly with correct punctuation.
            Join partial sentences from previous chunks for context.
            """
        else:
            user_prompt = f"""Accounting for the existing conversation:\n\n{st.session_state.transcript_text}\n\n
            Pay close attention to the very beginning of the audio chunk to ensure that no words or sounds are transcribed wrongly, even if they are brief. Fill up the transcription gap as best as you can.
            Accuracy is crucial, especially at the beginning of the audio chunk. Please ensure that the transcription is complete and precise. 
            Transcribe this audio and give the output directly with correct punctuation.
            Join partial sentences from previous chunks for context.

            If the audio does not contain any pronounced words, just return an empty output, not even '<noise>'.
            """



        text_part = Part.from_text(user_prompt)
        response = gemini_model.generate_content([text_part, audio_part])
        transcribed_text = response.text
        logger.info(f"Gemini Transcription: {transcribed_text}")

        with transcribing_lock:
            transcript += transcribed_text
            st.session_state.transcript_text = transcript  # Update session state
    except Exception as e:
        logger.error(f"Error transcribing chunk with Gemini: {e}")


async def audio_callback(frames):
    """WebRTC audio frames callback."""
    global full_audio, recording

    if recording:
        audio_queue.put(frames)
        for frame in frames:
            full_audio += AudioSegment(
                data=frame.to_ndarray().tobytes(),
                sample_width=frame.format.bytes,
                frame_rate=frame.sample_rate,
                channels=len(frame.layout.channels),
            )
    return frames


def transcribe_worker():
    """Worker thread to process audio chunks."""
    global full_audio, recording
    last_chunk_time = time.time()
    while recording:
        try:
            # Check if enough time has passed for a new chunk
            if time.time() - last_chunk_time >= CHUNK_DURATION:
                # Check if there's enough audio data for a chunk
                if len(full_audio) >= CHUNK_DURATION * 1000:
                    # Extract chunk from full audio
                    chunk = full_audio[: CHUNK_DURATION * 1000]
                    full_audio = full_audio[CHUNK_DURATION * 1000:]

                    # Resample and convert to mono
                    chunk = chunk.set_frame_rate(16000).set_channels(1)
                    audio_bytes = chunk.export(format="wav").read()

                    audio_uri = upload_chunk_to_gcs(audio_bytes)

                    # Add the audio URI to the callback queue
                    callback_queue.put(audio_uri)

                    last_chunk_time = time.time()
            time.sleep(0.1)
        except Exception as e:
            logger.error(f"Error in transcribe_worker: {e}")


def process_callback_queue():
    """Processes items in the callback queue in the main thread."""
    global transcript, i  # Access global variables

    while True:
        try:
            item = callback_queue.get_nowait()  # Get item without blocking
            if item is not None:
                transcribe_chunk(item)  # Call transcribe_chunk in the main thread

                # Update the transcript output with the full transcript
                with transcribing_lock:
                    transcript_output.text_area(
                        " ", transcript, height=300, key=f"transcript_area_{i}"
                    )
                    i += 1  # Increment i for unique key
        except queue.Empty:
            break


def main():
    global recording, i  # Declare i as global

    st.title("Near-Realtime Transcription with Gemini")

    # Initialize session state for transcript
    if "transcript_text" not in st.session_state:
        st.session_state.transcript_text = ""

    webrtc_ctx = webrtc_streamer(
        key="speech-to-text",
        mode=WebRtcMode.SENDRECV,
        audio_receiver_size=1024,
        queued_audio_frames_callback=audio_callback,
        rtc_configuration=RTC_CONFIGURATION,
        media_stream_constraints={"video": False, "audio": True},
    )

    # Start/Stop recording button
    if st.button("Start Recording"):
        recording = True
        st.session_state.transcript_text = ""
        i = 0  # Reset i when starting recording

        # Start transcription worker thread
        worker_thread = threading.Thread(target=transcribe_worker)
        worker_thread.daemon = True
        worker_thread.start()

    if st.button("Stop Recording") and recording:
        recording = False
        audio_queue.put(None)

    # Display transcript
    st.header("Transcript")
    global transcript_output  # Make transcript_output accessible
    transc
