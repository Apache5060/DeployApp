import streamlit as st
import requests
from templates.css import get_css
import re

def upload_and_get_insights(media_file):
    response = requests.post(
        'http://localhost:5000/generate-insights',
        files={'media_file': media_file}
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

    media_file = st.file_uploader("Upload a Video or Audio File", type=['mp4', 'mp3', 'mov', 'avi', 'mkv', 'flv', 'wmv', 'wav', 'ogg', 'm4a', 'aac', 'mpeg', 'mpg'])

    generate_button = st.button("Generate Insights")

    if generate_button and media_file:
        insights = upload_and_get_insights(media_file)

        if "error" not in insights:
            summary = clean_text(insights["summary"])
            transcript = clean_text(insights["transcript"])

            st.session_state['summary'] = summary
            st.session_state['transcript'] = transcript

            # Display insights directly:
            st.subheader("Summary:")
            st.write(summary)
            st.subheader("Transcript:")
            st.write(transcript)

            combined_content = f"Summary:\n{summary}\n\nTranscript:\n{transcript}"
            st.download_button("Download Combined Content", combined_content, "combined_content.txt", "text/plain")

            # Chatbot sidebar integration:
            with st.sidebar:
                st.header("Chatbot")
                question = st.text_input("Ask a question:")

                if st.button("Submit Question"):
                    chatbot_response = ask_chatbot(f"{summary} {transcript}", question)

                    if "error" not in chatbot_response:
                        st.write(chatbot_response["response"])
                    else:
                        st.error(chatbot_response["error"])
        else:
            st.error(insights["error"])

    elif 'summary' in st.session_state and 'transcript' in st.session_state:
        # Redisplay previous results if session state is available
        summary = st.session_state['summary']
        transcript = st.session_state['transcript']

        # Display insights directly:
        st.subheader("Summary:")
        st.write(summary)
        st.subheader("Transcript:")
        st.write(transcript)

        combined_content = f"Summary:\n{summary}\n\nTranscript:\n{transcript}"
        st.download_button("Download Combined Content", combined_content, "combined_content.txt", "text/plain")

        # Chatbot sidebar integration:
        with st.sidebar:
            st.header("Chatbot")
            question = st.text_input("Ask a question:")

            if st.button("Submit Question"):
                chatbot_response = ask_chatbot(f"{summary} {transcript}", question)

                if "error" not in chatbot_response:
                    st.write(chatbot_response["response"])
                else:
                    st.error(chatbot_response["error"])

if __name__ == "__main__":
    app()
