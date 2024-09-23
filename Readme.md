# Near-Realtime Transcription with Gemini and Streamlit

This project demonstrates how to perform near-realtime audio transcription using Google AI's Gemini model and Streamlit for a user-friendly web interface.
## Features

* **Near-realtime transcription:** Transcribes audio from the user's microphone in near real-time using Gemini's powerful speech-to-text capabilities.
* **Streamlit web interface:** Provides an intuitive and easy-to-use interface for interacting with the transcription service.
* **Chunked audio processing:** Processes audio in smaller chunks for faster transcription and responsiveness.
* **Google Cloud Storage integration:** Uploads audio chunks to Google Cloud Storage for processing by Gemini.
* **Contextual transcription:** Provides Gemini with previous conversation history for improved accuracy.

## Requirements

* Python 3.7 or higher
* The following Python packages (install using `pip install -r requirements.txt`):
    * streamlit
    * streamlit-webrtc
    * google-cloud-storage
    * vertexai
    * pydub
    * numpy
    * asyncio

## Setup

1. **Set up a Google Cloud Project:** 
   * Create a Google Cloud project if you don't have one.
   * Enable the Vertex AI API and the Cloud Storage API.
2. **Create a Google Cloud Storage Bucket:**
   * Create a bucket to store the audio chunks that will be sent to Gemini.
3. **Set Environment Variables:**
   * Create a `.env` file in the project's root directory and add the following:
    ```
    GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service-account-key.json"
    GCS_BUCKET_NAME="your-gcs-bucket-name"
    PROJECT_ID="your-gcp-project-id" 
    LOCATION="your-gcp-region" (e.g., "us-central1")
    ```
4. **Install Dependencies:** 
   * Run `pip install -r requirements.txt` to install the necessary Python packages.

## Usage

### Local Development

Run the Streamlit app with the following command:

```bash
streamlit run app.py 
Open your web browser and navigate to http://localhost:8501 to access the application.
```
Docker Deployment
Build the Docker image:
```
docker build -t chat-transcribe .
```
Run the Docker image:
```
docker run -p 8501:8501 chat-transcribe
```
Open your web browser and navigate to http://localhost:8501 to access the application.

Limitations and Disclaimer
This app is a demonstration of the potential of Google's Gemini Multimodal model for audio transcription. The accuracy of the transcriptions depends on various factors such as the quality of the audio file, the language spoken, and background noise and chunking size. The app is not intended for use in production environments and should be used for demonstration purposes only.

Contributing
If you'd like to contribute to this project, please feel free to submit a pull request or create an issue for any bugs or feature requests. Your contributions are welcome and appreciated!
