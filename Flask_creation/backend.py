from flask import Flask, request, jsonify
from moviepy.editor import VideoFileClip,AudioFileClip
import tempfile
import os
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
import re
from bs4 import BeautifulSoup
from multiprocessing import Pool
import time
import numpy as np
# Configure Google API key
GOOGLE_API_KEY = 'AIzaSyBwuhgihPcTMcMA8s3i9suv7TePcwESLlA'
genai.configure(api_key=GOOGLE_API_KEY)

app = Flask(__name__)


class Document:
    def __init__(self, content):
        self.content = content
        self.metadata = {}

    @property
    def page_content(self):
        return self.content

def clean_text(text):
    text = re.sub(r'\*\*', '', text)
    text = re.sub(r'#', '', text)
    return text

def extract_or_handle_audio(media_file):
    file_extension = media_file.filename.split('.')[-1].lower()
    video_extensions = ['mp4', 'mov', 'avi', 'mkv', 'flv', 'wmv', 'mpeg', 'mpg']
    audio_extensions = ['mp3', 'wav', 'ogg', 'm4a', 'aac', 'mpeg', 'mpg']

    if file_extension in video_extensions:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as temp_video_file:
            temp_video_file.write(media_file.read())
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
            audio_file.write(media_file.read())
            return audio_file.name

    return None

def process_chunk_with_retry(args, max_retries=5, retry_delay=30):
    audio_chunk_path, prompt = args
    for attempt in range(max_retries):
        try:
            audio_file = genai.upload_file(path=audio_chunk_path)
            model = genai.GenerativeModel("models/gemini-1.5-pro-latest")
            response = model.generate_content([prompt, audio_file])

            if hasattr(response, 'text'):
                return response.text
            elif hasattr(response, 'safety_ratings'):
                return f"Response blocked due to safety ratings: {response.safety_ratings}"
            else:
                return "No valid content returned, check model parameters or input."

        except Exception as e:
            error_message = str(e)
            if "429" in error_message or "504" in error_message:
                print(f"API error on attempt {attempt + 1}: {error_message}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential back-off
            else:
                return f"Unhandled error: {error_message}"

    return "Failed after multiple attempts due to rate limit or other errors."

def generate_summary_and_transcript(audio_file_path):
    audio_file = genai.upload_file(path=audio_file_path)
    model = genai.GenerativeModel("models/gemini-1.5-pro-latest")
    summary_response = model.generate_content(["Please summarize the following audio.", audio_file])
    summary = summary_response.text if hasattr(summary_response, 'text') else "Content attribute missing."

    chunk_paths = split_audio(audio_file_path)
    transcript_args = [(chunk, "Please transcribe this audio segment. Include speaker names.") for chunk in chunk_paths]
    with Pool() as pool:
        transcripts = pool.map(process_chunk_with_retry, transcript_args)

    for chunk_path in chunk_paths:
        os.remove(chunk_path)

    combined_transcript = "\n\n".join(transcripts)
    return summary, combined_transcript

def split_audio(audio_file_path, chunk_duration=300):
    audio = AudioFileClip(audio_file_path)
    chunks = []
    for start in np.arange(0, audio.duration, chunk_duration):
        end = min(start + chunk_duration, audio.duration)
        chunk_path = tempfile.mktemp(suffix='.mp3')
        audio.subclip(start, end).write_audiofile(chunk_path, codec='libmp3lame')
        chunks.append(chunk_path)

    audio.close()
    return chunks


def initialize_chatbot():
    prompt_template = """
    Answer the question as detailed as possible from the provided context.
    If the answer is not in the provided context, search the web and give the answer.
    Do not provide an incorrect answer.\n\n
    Context:\n {context}\n
    Question: \n{question}\n

    Answer:
    """
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    model = ChatGoogleGenerativeAI(model="models/gemini-1.5-pro-latest", temperature=0.3, google_api_key=GOOGLE_API_KEY)
    return load_qa_chain(model, chain_type="stuff", prompt=prompt)

def get_links_from_bing(query, subscription_key):
    endpoint = "https://api.bing.microsoft.com/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    params = {"q": query, "textFormat": "HTML", "count": "5"}
    response = request.get(endpoint, headers=headers, params=params)
    results = response.json()
    return [item['url'] for item in results.get('webPages', {}).get('value', [])]

def extract_text_from_urls(urls):
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36"
    texts = []
    for url in urls:
        try:
            response = request.get(url, headers={"User-Agent": user_agent}, timeout=10)
            if response is 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                texts.append(' '.join(soup.stripped_strings))
        except request.exceptions.RequestException:
            continue
    return ' '.join(texts)

def get_response(chain, context, question, subscription_key):
    input_documents = [Document(context)]
    result = chain({
        "context": context,
        "question": question,
        "input_documents": input_documents
    }, return_only_outputs=True)

    cleaned_response = clean_text(result["output_text"])

    # Uncertain Responses Handling
    if any(phrase in cleaned_response.lower() for phrase in [
         "answer is not available in the context",
      "i can't answer that based on the given text",
      "there's not enough information in the context",
      "i am not sure",
      "unclear",
    ]):
        links = get_links_from_bing(question, subscription_key)
        additional_context = extract_text_from_urls(links)
        full_context = context + " " + additional_context

        result = chain({
            "context": full_context,
            "question": question,
            "input_documents": [Document(full_context)]
        }, return_only_outputs=True)

        cleaned_response = clean_text(result["output_text"])
    return cleaned_response

# Flask Endpoints
@app.route('/generate-insights', methods=['POST'])
def generate_insights():
    file = request.files['media_file']
    audio_file_path = extract_or_handle_audio(file)
    if audio_file_path:
        summary, transcript = generate_summary_and_transcript(audio_file_path)
        os.remove(audio_file_path)
        return jsonify({"summary": clean_text(summary), "transcript": clean_text(transcript)})
    else:
        return jsonify({"error": "Unsupported file type or processing error."})

@app.route('/chatbot-response', methods=['POST'])
def chatbot_response():
    data = request.get_json()
    context = data['context']
    question = data['question']

    chatbot_chain = initialize_chatbot()
    response = get_response(chatbot_chain, context, question, 'Ocp-Apim-Subscription-Key')

    return jsonify({"response": clean_text(response)})

if __name__ == "__main__":
    app.run(debug=True)
