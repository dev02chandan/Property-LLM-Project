## Set Up Environment Variable

**On Windows:**
Open Command Prompt and run:
setx GEMINI_API_KEY "Your_Gemini_Api_Key_Here"
This command adds the API key to your environment variables permanently.

**On macOS/Linux:**
Open Terminal and add the following line to your .bashrc, .zshrc, or equivalent:
export GEMINI_API_KEY="Your_Gemini_Api_Key_Here"
After adding the line, run source ~/.bashrc or source ~/.zshrc to reload the configuration.

Also you need to export the following:
export PLACES_API_KEY="Your_google_places_api_key_here"
