import streamlit as st
import google.generativeai as genai
import os
import numpy as np
import pandas as pd
import textwrap

# App title and configuration
st.set_page_config(page_title="Grand Welcome Chatbot")

# Configure Gemini API
if 'GEMINI_API_KEY' in st.secrets:
    gemini_api = st.secrets['GEMINI_API_KEY']
else:
    gemini_api = st.text_input('Enter Gemini API token:', type='password', key='api_input')
    if gemini_api and gemini_api.startswith('r8_') and len(gemini_api) == 40:
        st.secrets['GEMINI_API_KEY'] = gemini_api
        st.experimental_rerun()

if 'GEMINI_API_KEY' in st.secrets:
    genai.configure(api_key=st.secrets['GEMINI_API_KEY'])
    hide_sidebar = True
else:
    st.sidebar.write("Please enter your API key")
    hide_sidebar = False

# Hide sidebar if API key is set
if hide_sidebar:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# Add logo
logo_path = "images/logo.png"
if os.path.exists(logo_path):
    st.image(logo_path, width=300)

# Dropdown to choose the property
property_files = {
    "Bearfoot Landing": "data/embeddings/Bearfoot_Landing_with_embeddings.feather",
    "Piece of Paradise": "data/embeddings/Piece_of_Paradise_with_embeddings.feather",
    "Ray's Chalet": "data/embeddings/Rays_Chalet_with_embeddings.feather",
    "Secluded in Paradise": "data/embeddings/Secluded_in_Paradise_with_embeddings.feather",
    "Sliver of Paradise": "data/embeddings/Sliver_of_Paradise_with_embeddings.feather",
    "The Real McCoy": "data/embeddings/The_Real_McCoy_with_embeddings.feather",
    "Treetop Paradise": "data/embeddings/Treetop_Paradise_with_embeddings.feather",
    "Woodland Wonder": "data/embeddings/Woodland_Wonder_with_embeddings.feather",
}

# Track the previously selected property to detect changes
if 'prev_property_name' not in st.session_state:
    st.session_state.prev_property_name = None

property_name = st.selectbox("Choose the property:", list(property_files.keys()), key='selected_property')

# Clear chat history if the property changes
if st.session_state.prev_property_name != property_name:
    st.session_state.prev_property_name = property_name
    st.session_state.messages = [{"role": "assistant", "content": f"A `Grand Welcome` to {property_name}! How can I assist you today?"}]

# Load the DataFrame with precomputed embeddings for the selected property
df = pd.read_feather(property_files[property_name])

# Function to find the best passages
def find_best_passages(query, dataframe, top_n=7):
    query_embedding = genai.embed_content(model='models/text-embedding-004', content=query)["embedding"]
    dot_products = np.dot(np.stack(dataframe['Embeddings']), query_embedding)
    top_indices = np.argsort(dot_products)[-top_n:][::-1]
    return dataframe.iloc[top_indices]['Text'].tolist()

# Function to make prompt
def make_prompt(query, relevant_passages):
    escaped_passages = [passage.replace("'", "").replace('"', "").replace("\n", " ") for passage in relevant_passages]
    joined_passages = "\n\n".join(f"PASSAGE {i+1}: {passage}" for i, passage in enumerate(escaped_passages))
    prompt = textwrap.dedent(f'''
                You are an advanced language model designed to assist with inquiries about rental properties. Your responses should be formal, detailed, and conversational, resembling how a kind and helpful person would converse. Use the provided information to answer any questions as accurately as possible. The information is given in triple backticks. 
                If you are asked about Check in and check out, provide information about early check in and late check out as well which is subject to availiblity and extra fee. 
                If you don't have the answer, Please say: "Unfortunately I am not aware how to answer that question. Can you try framing it in a different way?"
                ```
                {joined_passages}
                ```

                Question: {query}
                ''')
    return prompt

# Display or clear chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": f"Welcome to {property_name} Chatbot! How can I assist you today?"}]
st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

# Function for generating Gemini response
def generate_gemini_response(query):
    relevant_passages = find_best_passages(query, df)
    prompt = make_prompt(query, relevant_passages)
    response = genai.GenerativeModel('models/gemini-1.5-flash-latest').generate_content(prompt)
    return response.text

# User-provided prompt
if prompt := st.chat_input(disabled=not gemini_api):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

# Generate a new response if last message is not from assistant
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_gemini_response(prompt)
            placeholder = st.empty()
            placeholder.markdown(response)
    message = {"role": "assistant", "content": response}
    st.session_state.messages.append(message)
