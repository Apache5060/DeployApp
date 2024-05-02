from flask import Flask, request, jsonify
from moviepy.editor import VideoFileClip
import tempfile
import os
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
import re

# Configure Google API key
GOOGLE_API_KEY = 'AIzaSyBwuhgihPcTMcMA8s3i9suv7TePcwESLlA'
genai.configure(api_key=GOOGLE_API_KEY)

app = Flask(__name__)

def extract_or_handle_audio(media_file_path):
    file_extension = media_file_path.split('.')[-1].lower()
    video_extensions = ['mp4', 'mov', 'avi', 'mkv', 'flv', 'wmv', 'mpeg', 'mpg']
    audio_extensions = ['mp3', 'wav', 'ogg', 'm4a', 'aac', 'mpeg', 'mpg']

    if file_extension in video_extensions:
        try:
            audio_file_path = f"{media_file_path.split('.')[0]}.mp3"

            # Convert video to audio
            video = VideoFileClip(media_file_path)
            audio = video.audio
            audio.write_audiofile(audio_file_path, codec='libmp3lame')
            video.close()

            return audio_file_path
        except Exception as e:
            print(f"Error processing video file: {e}")
            return None

    elif file_extension in audio_extensions:
        return media_file_path

    else:
        return None

def generate_summary(audio_file_path):
    try:
        audio_file = genai.upload_file(path=audio_file_path)
        model = genai.GenerativeModel("models/gemini-1.5-pro-latest")
        response = model.generate_content(["Please summarize the following audio.", audio_file])
        return response.text if hasattr(response, 'text') else "Summary attribute is missing."
    except Exception as e:
        print(f"Error generating summary: {e}")
        return str(e)

def generate_transcript(audio_file_path):
    try:
        audio_file = genai.upload_file(path=audio_file_path)
        model = genai.GenerativeModel("models/gemini-1.5-pro-latest")
        response = model.generate_content(["Please generate a transcript of the audio, with accurate speaker names.", audio_file])
        return response.text if hasattr(response, 'text') else "Transcript attribute is missing."
    except Exception as e:
        print(f"Error generating transcript: {e}")
        return str(e)

def clean_text(text):
    text = re.sub(r'\*\*', '', text)
    text = re.sub(r'#', '', text)
    return text

@app.route('/generate-insights', methods=['POST'])
def generate_insights():
    try:
        file = request.files['media_file']
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
            temp_file.write(file.read())
            temp_file_path = temp_file.name

        audio_file_path = extract_or_handle_audio(temp_file_path)

        if audio_file_path:
            summary = generate_summary(audio_file_path)
            transcript = generate_transcript(audio_file_path)
            os.remove(audio_file_path)

            return jsonify({"summary": clean_text(summary), "transcript": clean_text(transcript)})
        else:
            print("Unsupported file type or processing error.")
            return jsonify({"error": "Unsupported file type or processing error."})
    except Exception as e:
        # Log error for debugging
        print(f"Error generating insights: {e}")
        return jsonify({"error": str(e)})

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
    model = ChatGoogleGenerativeAI(
        model="models/gemini-1.5-pro-latest",
        temperature=0.3,
        google_api_key=GOOGLE_API_KEY
    )
    return load_qa_chain(model, chain_type="stuff", prompt=prompt)

@app.route('/chatbot-response', methods=['POST'])
def chatbot_response():
    data = request.get_json()
    context = data['context']
    question = data['question']

    chatbot_chain = initialize_chatbot()
    response = chatbot_chain({
        "context": context,
        "question": question,
        "input_documents": [Document(context)]
    }, return_only_outputs=True)

    return jsonify({"response": clean_text(response["output_text"])})

class Document:
    def __init__(self, content):
        self.content = content
        self.metadata = {}

    @property
    def page_content(self):
        return self.content

if __name__ == "__main__":
    app.run(debug=True)
