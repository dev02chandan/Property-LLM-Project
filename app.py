import streamlit as st
import pandas as pd
import os
import requests
import google.generativeai as genai

# Setup Gemini API
api_key_gemini = os.getenv('GEMINI_API_KEY')
if api_key_gemini is None:
    st.error("Gemini API key is not set in environment variables. Please set it before proceeding.")
    st.stop()

genai.configure(api_key=api_key_gemini)
model = genai.GenerativeModel('gemini-pro')

# Setup Google Places API
api_key_places = os.getenv('PLACES_API_KEY')
places_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

# Function to fetch nearby places from Google Places API
def fetch_nearby_places(lat, lon, place_type='restaurant'):
    params = {
        'location': f'{lat},{lon}',
        'radius': 5000,  # Set to maximum radius
        'type': place_type,
        'key': api_key_places
    }
    response = requests.get(places_url, params=params)
    results = response.json().get('results', [])
    places = [(place['name'], place['vicinity']) for place in results]
    return places

# Load property data
@st.cache_data
def load_property_data():
    file_path = 'data_v2.xlsx'  # Adjust the file path if necessary
    df = pd.read_excel(file_path)
    return df

properties_info = load_property_data()

# Function to generate responses using Gemini API
def generate_response(query, context):
    # prompt = (
    #     f"You are a sophisticated virtual assistant for XYZ Company, specializing in property management. "
    #     f"Your task is to analyze the user's question '{query}' and determine the best way to respond. "
    #     f"Consider the context: '{context}'. If the inquiry relates to specific local locations such as restaurants, playgrounds, or gyms, "
    #     f"you should identify this need and respond with 'PLACES_API CALL,[location type]'. For more general inquiries about property features or details, "
    #     f"use the available data from our property database to craft a detailed answer directly."
    # )

    prompt = f'''
                You are an advanced language model designed to assist with inquiries about rental properties based on specific context provided.
                Your responses should be formal and detailed. 
                Use the context to answer any questions as accurately as possible.
                Context is given in triple backticks. 
                If a question falls outside the given context, respond by stating that you cannot answer the question based on the information provided.

                ```
                {context}
                ```

                Question: {query}
                '''
    response = model.generate_content(prompt)
    return response.text

def main():
    st.image('images/logo.png', width=200)
    st.title('Property Inquiry Chatbot')

    # Dropdown to select the property
    property_name = st.selectbox("Select the property you're staying at:", options=properties_info['Unit name'].unique())
    property_info = properties_info[properties_info['Unit name'] == property_name].iloc[0]

    # Prepare context
    context = property_info['context']
    
    # Get user input
    user_question = st.text_input("What would you like to know?")

    if user_question:
        response = generate_response(user_question, context)

        # Check if the response is instructing to call Places API
        if response.startswith("PLACES_API CALL"):
            place_type = response.split(',')[1].strip().lower()
            if place_type == 'gardens':
                place_type = 'park'  # Adjust for missing types in API
            places = fetch_nearby_places(property_info['latitude'], property_info['longitude'], place_type)
            if places:
                print('places_api_call')
                # Format the places into a structured list for better readability
                places_formatted = ', '.join([f"{idx + 1}. {place[0]} ({place[1]})" for idx, place in enumerate(places[:10])])
                reply_with_places = f"Here are some nearby {place_type} you might find interesting:\n{places_formatted}"
                st.write(reply_with_places)
            else:
                st.write(f"No nearby {place_type} found.")
        else:
            # Display the original response if not a Places API call
            st.write("Answer:", response)

if __name__ == "__main__":
    main()
