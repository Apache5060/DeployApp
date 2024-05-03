import streamlit as st
import requests
import re
from templates.css import get_css  # Ensure this module is correctly implemented
import os

st.set_page_config(page_title='Video and Audio Insight Generator', page_icon='🎥')

def upload_and_get_insights(media_file):
    response = requests.post(
        'http://localhost:5000/generate-insights',
        files={'media_file': (media_file.name, media_file, media_file.type)}
    )
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.text}

def ask_chatbot(context, question):
    response = requests.post(
        'http://localhost:5000/chatbot-response',
        json={'context': context, 'question': question}
    )
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.text}

def clean_text(text):
    text = re.sub(r'\*\*', '', text)
    text = re.sub(r'#', '', text)
    return text

def app():
    st.markdown(get_css(), unsafe_allow_html=True)
    st.title("Video and Audio Insight Generator")

    media_file = st.file_uploader("Upload a Video or Audio File", type=['mp4', 'mp3', 'mov', 'avi', 'mkv', 'flv', 'wmv', 'wav', 'ogg', 'm4a', 'aac'])

    generate_button = st.button("Generate Insights")

    if generate_button and media_file:
        with st.spinner("Processing..."):
            insights = upload_and_get_insights(media_file)

        if "error" not in insights:
            summary = clean_text(insights["summary"])
            transcript = clean_text(insights["transcript"])

            st.session_state['summary'] = summary
            st.session_state['transcript'] = transcript

            st.subheader("Summary:")
            st.write(summary)
            st.subheader("Transcript:")
            st.write(transcript)

            combined_content = f"Summary:\n{summary}\n\nTranscript:\n{transcript}"
            original_filename = os.path.splitext(media_file.name)[0]  # Get the base filename without extension
            downloadable_filename = f"{original_filename}_summary_transcript.txt"

            st.download_button("Download Combined Content", combined_content, downloadable_filename, "text/plain")

            with st.sidebar:
                st.header("Chatbot")
                question = st.text_input("Ask a question:")

                if st.button("Submit Question"):
                    with st.spinner("Processing..."):
                        chatbot_response = ask_chatbot(f"{summary} {transcript}", question)

                    if "error" not in chatbot_response:
                        st.write(chatbot_response["response"])
                    else:
                        st.error(chatbot_response["error"])
        else:
            st.error(f"Error: {insights['error']}")

    elif 'summary' in st.session_state and 'transcript' in st.session_state:
        summary = st.session_state['summary']
        transcript = st.session_state['transcript']

        st.subheader("Summary:")
        st.write(summary)
        st.subheader("Transcript:")
        st.write(transcript)

        combined_content = f"Summary:\n{summary}\n\nTranscript:\n{transcript}"
        original_filename = os.path.splitext(media_file.name)[0]  # Or retrieve from session state
        downloadable_filename = f"{original_filename}_summary_transcript.txt"

        st.download_button("Download Combined Content", combined_content, downloadable_filename, "text/plain")

        with st.sidebar:
            st.header("Chatbot")
            question = st.text_input("Ask a question:")

            if st.button("Submit Question"):
                with st.spinner("Processing..."):
                    chatbot_response = ask_chatbot(f"{summary} {transcript}", question)

                if "error" not in chatbot_response:
                    st.write(chatbot_response["response"])
                else:
                    st.error(chatbot_response["error"])

if __name__ == "__main__":
    app()
