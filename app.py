import streamlit as st
import json
import os
import google.generativeai as genai

# Load environment variable for API key
api_key = os.getenv('GEMINI_API_KEY')
if api_key is None:
    st.error("API key is not set in environment variables. Please set it before proceeding.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')

# Load property data from JSON file
@st.cache_data  # Updated cache mechanism
def load_property_data():
    with open('properties.json', 'r') as f:
        properties = json.load(f)
    return properties

properties_info = load_property_data()

def generate_response(query, property_info):
    # Updated context to include a more polite and professional tone
    context = f"{property_info['description']} Amenities include: {', '.join(property_info['amenities'])}. Pets policy: {property_info['pets']}."
    full_query = f"""
                You are a helpful assistant for XYZ company. 
                Our company gives out guest houses on rent for a few days.
                Your role is to politely and professionaly reply to the queries of the client, who have already booked the rooms based on the given context.
                Given the context: '{context}', how would you professionally answer the guest's question: '{query}'?
                """
    response = model.generate_content(full_query)
    return response.text

def main():
    st.title('Property Inquiry Chatbot')

    # Dropdown to select the property
    property_name = st.selectbox("Select the property you're staying at:", options=list(properties_info.keys()))
    property_info = properties_info[property_name]
    # User inputs their question
    user_question = st.text_input("What would you like to know?")
    if user_question:
        response = generate_response(user_question, property_info)
        st.write("Answer:\n", response)

if __name__ == "__main__":
    main()
