import streamlit as st
import pandas as pd
import os
import requests
import google.generativeai as genai

# Customizing the Streamlit app
st.markdown(
    """
    <style>
    .main {
        background-color: #ffffff;
    }
    .title {
        color: #00aeef;
        font-family: Verdana;
    }
    .header {
        text-align: center;
        color: #ca9630;
        font-family: Verdana;
        padding-bottom: 50px;
    }
    .text-input {
        color: #ca9630;
        font-family: Verdana;
    }
    .css-1aumxhk {
        text-align: center;
    }
    .css-1aumxhk img {
        width: 400px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

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
    prompt = f'''
                You are an advanced language model designed to assist with inquiries about rental properties. Your responses should be formal, detailed, and conversational, resembling how a kind and helpful person would converse. Use the provided information to answer any questions as accurately as possible. The information is given in triple backticks. 
                If you think that the question is about nearby places, you can output: "PLACES_API_CALL,[place_type]", where place_type resembles what the person is asking about. 
                If you are asked about Check in and check out, provide information about early check in and late check out as well which is subject to availiblity and extra fee. 
                If you don't have the answer, Please say: "Unfortunately I am not aware how to answer that question. Can you try framing it in a different way?"
                ```
                {context}
                ```

                Question: {query}
                '''
    try:
        response = model.generate_content(prompt)
        return response.text
    except ValueError as e:
        if "candidate.safety_ratings" in str(e):
            st.error("There was an error, please refresh and try again.")
            return None
        else:
            raise

def main():
    st.image('images/logo.png', use_column_width='auto')
    st.markdown("<h1 class='header'>Property Inquiry Chatbot</h1>", unsafe_allow_html=True)

    # Dropdown to select the property
    property_name = st.selectbox("Select the property you're staying at:", options=properties_info['Unit name'].unique(), format_func=lambda x: f"{x}", key='property_name')
    property_info = properties_info[properties_info['Unit name'] == property_name].iloc[0]

    # Prepare context
    context = property_info['context']
    
    # Get user input
    user_question = st.text_input("What would you like to know?", key='user_question')

    if user_question:
        response = generate_response(user_question, context)

        if response is not None:
            # Check if the response is instructing to call Places API
            if response.startswith("PLACES_API_CALL"):
                place_type = response.split(',')[1].strip().lower()
                if place_type == 'gardens':
                    place_type = 'park'  # Adjust for missing types in API
                places = fetch_nearby_places(property_info['latitude'], property_info['longitude'], place_type)
                if places:
                    places_formatted = '<br>'.join([f"{idx + 1}. {place[0]} ({place[1]})" for idx, place in enumerate(places[:10])])
                    reply_with_places = f"Here are some nearby {place_type} you might find interesting:<br>{places_formatted}"
                    st.markdown(reply_with_places, unsafe_allow_html=True)
                else:
                    st.write(f"No nearby {place_type} found.")
            else:
                # Display the original response if not a Places API call
                st.write("Answer:", response)

if __name__ == "__main__":
    main()
