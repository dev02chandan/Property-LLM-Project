import streamlit as st
import os
import requests
import google.generativeai as genai
import pandas as pd

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
def fetch_nearby_places(lat, lon, place_type='restaurant', radius=5000):
    params = {
        'location': f'{lat},{lon}',
        'radius': radius,
        'type': place_type,
        'key': api_key_places
    }
    response = requests.get(places_url, params=params)
    results = response.json().get('results', [])
    places = [{'name': place['name'], 'location': place['geometry']['location']} for place in results]
    return places

# Load property data from CSV file
@st.cache_data
def load_property_data():
    file_path = 'client_data_new.csv'  # Path to the CSV file
    df = pd.read_csv(file_path, encoding='ISO-8859-1')
    properties = df.set_index('Unit name').T.to_dict()
    return properties

properties_info = load_property_data()

# Function to generate responses using Gemini API
def generate_response(query, context):
    # Detailed and courteous instructional prompt
    prompt = (
        f"You are a sophisticated and courteous virtual assistant for XYZ Company, specializing in property management. "
        f"Your task is to analyze the user's question '{query}' and determine the best way to respond. "
        f"Consider the context: '{context}'. If the inquiry relates to specific local locations such as restaurants, playgrounds, or gyms, "
        f"you should identify this need and respond with 'PLACES_API CALL,[location type]'. For more general inquiries about property features or details, "
        f"use the available data from our property database to craft a detailed and courteous answer directly. "
        f"Always respond in a friendly and helpful manner, similar to how a hotel concierge would treat a guest. Provide as much detail as possible to ensure the user feels well-informed and valued."
    )
    response = model.generate_content(prompt)
    return response.text

def main():
    st.image('images/logo.png', width=200)
    st.title('Property Inquiry Chatbot')

    # Dropdown to select the property
    property_name = st.selectbox("Select the property you're staying at:", options=list(properties_info.keys()))
    property_info = properties_info[property_name]

    # Prepare context with all columns
    context = (
        f"Property Details: {property_info.get('pms_units_listing_grand_welcome', 'N/A')} "
        f"Airbnb Listing: {property_info.get('pms_units_listing_airbnb', 'N/A')} "
        f"Supplies during arrival: {property_info.get('supplies during arrival', 'N/A')} "
        f"Address: {property_info.get('streetAddress', 'N/A')}, {property_info.get('locality', 'N/A')}, {property_info.get('region', 'N/A')} {property_info.get('postal', 'N/A')}. "
        f"Country: {property_info.get('country', 'N/A')}. "
        f"Max Discount: {property_info.get('maxDiscount', 'N/A')}. "
        f"Area: {property_info.get('area', 'N/A')} sq. ft. "
        f"Floors: {property_info.get('floors', 'N/A')}. "
        f"Max Occupancy: {property_info.get('maxOccupancy', 'N/A')}. "
        f"Bedrooms: {property_info.get('bedrooms', 'N/A')}. "
        f"Full Bathrooms: {property_info.get('fullBathrooms', 'N/A')}, Three Quarter Bathrooms: {property_info.get('threeQuarterBathrooms', 'N/A')}, Half Bathrooms: {property_info.get('halfBathrooms', 'N/A')}. "
        f"Timezone: {property_info.get('timezone', 'N/A')}. "
        f"Latitude: {property_info.get('latitude', 'N/A')}, Longitude: {property_info.get('longitude', 'N/A')}. "
        f"Check-in Time: {property_info.get('checkinTime', 'N/A')}, Check-out Time: {property_info.get('checkoutTime', 'N/A')}, "
        f"Early Check-in Time: {property_info.get('earlyCheckinTime', 'N/A')}, Late Check-out Time: {property_info.get('lateCheckoutTime', 'N/A')}. "
        f"Access: {property_info.get('Access', 'N/A')}. "
        f"Team: {property_info.get('Team', 'N/A')}. "
        # f"Team Notes: {property_info.get('Team Notes', 'N/A')}. "
        f"General: {property_info.get('Gereral', 'N/A')}. "
        f"Contacts: {property_info.get('Contacts', 'N/A')}. "
        f"Task: {property_info.get('Task', 'N/A')}."
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
                places_formatted = '\n'.join([f"{idx + 1}. {place['name']}" for idx, place in enumerate(places)])
                reply_with_places = f"Here are some nearby {place_type} you might find interesting:\n{places_formatted}"
                st.write(reply_with_places)
            else:
                st.write(f"No nearby {place_type} found within the selected radius.")
        else:
            # Display the original response if not a Places API call
            st.write("Answer:", response)

if __name__ == "__main__":
    main()
