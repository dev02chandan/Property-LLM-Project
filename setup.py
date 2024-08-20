import pandas as pd
import google.generativeai as genai
import os
import json

# Configure Gemini API
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set.")

genai.configure(api_key=api_key)

# Load JSON data
with open('data/data_v1.1.json', 'r') as f:
    data = json.load(f)

# Function to embed both title and text content
def embed_fn(title, text):
    combined_content = f"{title}\n{text}"
    return genai.embed_content(model='models/text-embedding-004', content=combined_content)["embedding"]

# Process each property individually
for property_name, property_data in data.items():
    rows = []
    for key, value in property_data.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, dict):
                    row = {'Title': f"{key} - {sub_key}", 'Text': str(sub_value['value'])}
                else:
                    row = {'Title': f"{key} - {sub_key}", 'Text': str(sub_value)}
                rows.append(row)
        else:
            row = {'Title': f"{key}", 'Text': str(value)}
            rows.append(row)

    # Convert to DataFrame
    df = pd.DataFrame(rows)

    # Generate embeddings by combining Title and Text
    df['Embeddings'] = df.apply(lambda row: embed_fn(row['Title'], row['Text']), axis=1)

    # Save to a separate Feather file for each property
    file_name = f"data/embeddings/{property_name.replace(' ', '_')}_with_embeddings.feather"
    df.to_feather(file_name)

    print(f"Saved embeddings for {property_name} to {file_name}")
