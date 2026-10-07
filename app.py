from google import genai
from google.genai import types
import streamlit as st 
from prompts import SYSTEM_PROMPT, WELCOME_MESSAGE_TEMPLATE, SUMMARY_REQUEST_PROMPT
from twilio.rest import Client as TwilioClient
import json

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
TWILIO_ACCOUNT_SID = st.secrets["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = st.secrets["TWILIO_AUTH_TOKEN"] 
TWILIO_WHATSAPP_FROM = st.secrets["TWILIO_WHATSAPP_FROM"]
TWILIO_CONTENT_SID = st.secrets["TWILIO_CONTENT_SID"]

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)

@st.cache_resource
def get_twilio_client():
    return TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

twilio_client = get_twilio_client()
gemini_client = get_gemini_client()
MODEL_NAME = "gemini-3.8-flash"  # Fast, cost-effective model with vision support

def clean_whatsapp_text(s):
    if not text:
        return "No nutrition summary available."
    text = " ".joion(text.split()) # remove extra spaces and newlines
    return text[:1500] + "..." if len(text) > 1500 else text

def send_whatsapp(whatsapp_number, name , summary):
    """Send a WhatsApp message using Twilio."""
    try:
        content_variables = json.dumps(
            {"1": name, "2" : clean_whatsapp_text(summary)}, ensure_ascii=False
        )
        message = twilio_client.messages.create(
            from_ = TWILIO_WHATSAPP_FROM,
            to = f"whatsapp:{whatsapp_number}",
            conten_sid = TWILIO_CONTENT_SID,                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              t_sid = TWILIO_CONTENT_SID,
            content_variables = content_variables,
        )
        return True, message.sid
    
    except Exception as e:
        return False, str(e)

def render_message(message):
    with st.chat_message(message["role"]):
        if message["kind"] == "text":
            st.write(message["content"])
        elif message["kind"] == "image":
            st.image(message["content"])   

def add_message(role, kind, content):
    """Add a message to the session state."""
    st.session_state.messages.append({"role": role, "kind": kind, "content": content})
    render_message(st.session_state.messages[-1])  # Render the new message immediately

def ask_gemini(parts):
    try:
        return st.session_state.chat.send_message(message = parts).text
    except Exception as e:
        st.error(f"Error communicating with Gemini API: {e}")
        return "Sorry, I couldn't process that. Please try again."

# step : 1 onboarding (username and phone)

if "onboarded" not in st.session_state:
    st.title("MacroSnap 🥗")
    st.caption("snap it, Track it. Text yourself the results. Powered by Google GenAI.")

    with st.form("onboarding_form"):
        name = st.text_input("Your Name")
        whatsapp_number = st.text_input("Your WhatsApp Number (with country code)", 
        placeholder="+91XXXXXXXXXX", 
        help = "This is the number Macrosnap will text yours results to. Make sure to include your country code."
        )   

        submitted = st.form_submit_button("Let's go 🚀")

    if submitted:
        if not name.strip() or not whatsapp_number.strip():
            st.warning("Please enter both your name and WhatsApp number to continue.")

        else:
            st.session_state.name = name.strip()
            st.session_state.whatsapp_number = whatsapp_number.strip()
            # activate my ai 
            st.session_state.chat = gemini_client.chats.create(
                model =MODEL_NAME,
                config = types.GenerateContentConfig(system_instruction = SYSTEM_PROMPT)
            ) 
            st.session_state.messages = []
            st.session_state.onboarded = True
            st.rerun() # Rerun the app to move to the next step
    st.stop()  # Stop further execution until the form is submitted 

# create the chat interface 

header_col, button_col = st.columns([5, 2] , vertical_alignment="center")

with header_col:
    st.title("MacroSnap 🥗")

with button_col:
    send_disable = len(st.session_state.messages) <= 1
    if st.button("📩 Send details to WhatsApp", disabled=send_disable):
        # send the summary to whatsapp 
        with st.spinner("Generating summary..."):
            summary = ask_gemini([SUMMARY_REQUEST_PROMPT])
        success, info = send_whatsapp(st.session_state.whatsapp_number, summary)
        if success:
            st.success("✅ Summary sent to WhatsApp! checkout your messages on your phone📱")
        else:
            st.error(f"❌ Failed to send summary: {info}")  

st.caption(f"Logged in as: {st.session_state.name} - updates go to {st.session_state.whatsapp_number}")

if not st.session_state.messages:
    add_message("assistant", "text" , WELCOME_MESSAGE_TEMPLATE.format(name=st.session_state.name))
else:
    for message in st.session_state.messages:
        render_message(message)

# user input ai to give inputs 

user_input = st.chat_input(
    "Ask a question, or attach a photo of your Query",
    accept_file=True,
    file_type=["png", "jpeg", "jpg"],
)

if user_input:
    photo = user_input.files[0] if user_input.files else None
    text = user_input.text
    parts = []

    if photo is not None:
        photo_bytes = photo.getvalue()
        add_message("user" , "image" , photo_bytes)
        parts.append(types.Part.from_bytes(data = photo_bytes, mime_type = photo.type))
    if text:
        add_message("user", "text", text)
        parts.append(text)
    elif photo is not None:
        parts.append("What is this meal? Please provide an estimate of calories and macros (protein, carbs, fat).")

    with st.spinner("Thinking..."):
        answer = ask_gemini(parts)
    add_message("assistant", "text", answer)

