import streamlit as st
import json
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
        'radius': 1500,  # Adjust radius as needed
        'type': place_type,
        'key': api_key_places
    }
    response = requests.get(places_url, params=params)
    results = response.json().get('results', [])
    places = [place['name'] for place in results]
    return places

# Load property data
@st.cache_data
def load_property_data():
    with open('properties.json', 'r') as f:
        properties = json.load(f)
    return properties

properties_info = load_property_data()

# Function to generate responses using Gemini API
def generate_response(query, context):
    # Detailed instructional prompt example
    prompt = (
        f"You are a sophisticated virtual assistant for XYZ Company, specializing in property management. "
        f"Your task is to analyze the user's question '{query}' and determine the best way to respond. "
        f"Consider the context: '{context}'. If the inquiry relates to specific local locations such as restaurants, playgrounds, or gyms, "
        f"you should identify this need and respond with 'PLACES_API CALL,[location type]'. For more general inquiries about property features or details, "
        f"use the available data from our property database to craft a detailed answer directly."
    )
    response = model.generate_content(prompt)
    return response.text

def main():
    st.image('images/logo.png', width=200)
    st.title('Property Inquiry Chatbot')

    # Dropdown to select the property
    property_name = st.selectbox("Select the property you're staying at:", options=list(properties_info.keys()))
    property_info = properties_info[property_name]

    # Prepare context
    context = (
        f"{property_info['description']} Amenities include: {', '.join(property_info['amenities'])}. "
        f"Pets policy: {property_info['pets']}. Latitude: {property_info['latitude']}, Longitude: {property_info['longitude']}."
    )

    # Get user input
    user_question = st.text_input("What would you like to know?")

    if user_question:
        response = generate_response(user_question, context)

        # Check if the response is instructing to call Places API
        if response.startswith("PLACES_API CALL"):
            place_type = response.split(',')[1].strip()
            places = fetch_nearby_places(property_info['latitude'], property_info['longitude'], place_type)
            if places:
                # Format the places into a structured list for better readability
                places_formatted = ', '.join([f"{idx + 1}. {place}" for idx, place in enumerate(places)])
                reply_with_places = f"Here are some nearby {place_type} you might find interesting:\n{places_formatted}"
                st.write(reply_with_places)
            else:
                st.write(f"No nearby {place_type} found.")
        else:
            # Display the original response if not a Places API call
            st.write("Answer:", response)

if __name__ == "__main__":
    main()
