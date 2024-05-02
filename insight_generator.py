import streamlit as st
import tempfile
import os
from moviepy.editor import VideoFileClip
import google.generativeai as genai
from templates.css import get_css
import re

# Configure your Google API key
GOOGLE_API_KEY = 'AIzaSyBwuhgihPcTMcMA8s3i9suv7TePcwESLlA'  
genai.configure(api_key=GOOGLE_API_KEY)

def extract_or_handle_audio(media_file):
    file_extension = media_file.name.split('.')[-1].lower()
    video_extensions = ['mp4', 'mov', 'avi', 'mkv', 'flv', 'wmv', 'mpeg', 'mpg']
    audio_extensions = ['mp3', 'wav', 'ogg', 'm4a', 'aac', 'mpeg', 'mpg']

    if file_extension in video_extensions:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as temp_video_file:
            temp_video_file.write(media_file.getvalue())
            video_path = temp_video_file.name

        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as audio_file:
            video = VideoFileClip(video_path)
            audio = video.audio
            audio.write_audiofile(audio_file.name, codec='libmp3lame')
            video.close()
            os.remove(video_path)
            return audio_file.name

    elif file_extension in audio_extensions:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as audio_file:
            audio_file.write(media_file.getvalue())
            return audio_file.name

    else:
        st.error(f"Unsupported file type: {media_file.type}")
        return None

def generate_summary(audio_file_path):
    try:
        audio_file = genai.upload_file(path=audio_file_path)
        model = genai.GenerativeModel("models/gemini-1.5-pro-latest")
        response = model.generate_content(["Please summarize the following audio.", audio_file])
        return response.text if hasattr(response, 'text') else "Summary attribute is missing."
    except Exception as e:
        return str(e)

def generate_transcript(audio_file_path):
    try:
        audio_file = genai.upload_file(path=audio_file_path)
        model = genai.GenerativeModel("models/gemini-1.5-pro-latest")
        response = model.generate_content(["Please generate transcript of audio with the speaker name accurately for the following audio.", audio_file])
        return response.text if hasattr(response, 'text') else "Transcript attribute is missing."
    except Exception as e:
        return str(e)

def clean_text(text):
    text = re.sub(r'\*\*', '', text)  # Remove double asterisks used for bold in Markdown
    text = re.sub(r'#', '', text)  # Remove hash symbols used for headers in Markdown
    return text

def app():
    st.markdown(get_css(), unsafe_allow_html=True)
    st.title("Video and Audio Insight Generator")
    media_file = st.file_uploader("Upload a Video or Audio File", type=['mp4', 'mp3', 'mov', 'avi', 'mkv', 'flv', 'wmv', 'wav', 'ogg', 'm4a', 'aac', 'mpeg', 'mpg'])
    generate_button = st.button("Generate Insights")

    if generate_button and media_file:
        audio_path = extract_or_handle_audio(media_file)

        if audio_path:
            summary = generate_summary(audio_path)
            transcript = generate_transcript(audio_path)
            os.remove(audio_path)  # Clean up the audio file after processing

            cleaned_summary = clean_text(summary)
            cleaned_transcript = clean_text(transcript)

            st.session_state['summary'] = summary
            st.session_state['transcript'] = transcript

            st.subheader("Summary")
            st.text_area("Generated Summary", cleaned_summary, height=250)
            st.subheader("Transcript")
            st.text_area("Generated Transcript", cleaned_transcript, height=250)

            combined_content = f"Summary:\n{cleaned_summary}\n\nTranscript:\n{cleaned_transcript}"
            st.download_button("Download Combined Content", combined_content, "combined_content.txt", "text/plain")
        else:
            st.error("Error processing the file.")

