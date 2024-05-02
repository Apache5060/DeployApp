import streamlit as st
from templates.css import get_css
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
import re

class Document:
    def __init__(self, content):
        self.content = content
        self.metadata = {}

    @property
    def page_content(self):
        return self.content
    

def clean_text(text):
    # Remove Markdown bold markers, asterisks, and other unwanted characters
    text = re.sub(r'\*\*', '', text)  # Remove double asterisks used for bold in Markdown
    text = re.sub(r'#', '', text)  # Remove hash symbols used for headers in Markdown

    return text

def initialize_chatbot():
    prompt_template = """
    Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
    provided context Search the google web and give the answer, don't provide the wrong answer\n\n
    Context:\n {context}?\n
    Question: \n{question}\n

    Answer:
    """
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question", "input_documents"])
    model = ChatGoogleGenerativeAI(model="models/gemini-1.5-pro-latest", temperature=0.3,GOOGLE_API_KEY = 'AIzaSyBwuhgihPcTMcMA8s3i9suv7TePcwESLlA')
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain

def get_response(chain, context, question):
    input_documents = [Document(context)]
    result = chain({
        "context": context,
        "question": question,
        "input_documents": input_documents
    }, return_only_outputs=True)
    cleaned_response = clean_text(result["output_text"])
    return cleaned_response

def preprocess_context_to_documents(context):
    return [Document(context)]



def app():
    st.markdown(get_css(), unsafe_allow_html=True)
    st.title("Chatbot for Insights")

    if 'summary' in st.session_state and 'transcript' in st.session_state:
        chatbot_chain = initialize_chatbot()
        context = st.session_state['summary'] + " " + st.session_state['transcript']

        question = st.text_input("Ask a question about the summary or transcript:")
        submit_button = st.button("Submit")

        if submit_button and question:  # Check if the submit button is pressed and question is not empty
            response = get_response(chatbot_chain, context, question)
            st.text("Chatbot Response:")
            st.write(response)  # Using st.write to directly display the response
    else:
        st.write("No summary or transcript available. Please generate them on the Insight Generator page first.")
