import streamlit as st 
from prompts import SYSTEM_PROMPT, WELCOME_MESSAGE_TEMPLATE, SUMMARY_REQUEST_PROMPT
from twilio.rest import Client as TwilioClient
import json
import time
from groq import Groq
import base64

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
TWILIO_ACCOUNT_SID = st.secrets["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = st.secrets["TWILIO_AUTH_TOKEN"] 
TWILIO_WHATSAPP_FROM = st.secrets["TWILIO_WHATSAPP_FROM"]
TWILIO_CONTENT_SID = st.secrets["TWILIO_CONTENT_SID"]

@st.cache_resource
def get_groq_client():
    return Groq(api_key=GROQ_API_KEY)

@st.cache_resource
def get_twilio_client():
    return TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

twilio_client = get_twilio_client()
groq_client = get_groq_client()
MODEL_NAME = "qwen/qwen3.8-27b"  # Fast Groq vision model

def clean_whatsapp_text(s):
    if not s:
        return "No nutrition summary available."
    s = " ".join(s.split()) # remove extra spaces and newlines
    return s[:1500] + "..." if len(s) > 1500 else s

def send_whatsapp(whatsapp_number, name , summary):
    """Send a WhatsApp message using Twilio."""
    try:
        content_variables = json.dumps(
            {"1": name, "2" : clean_whatsapp_text(summary)}, ensure_ascii=False
        )
        message = twilio_client.messages.create(
            from_ = TWILIO_WHATSAPP_FROM,
            to = f"whatsapp:{whatsapp_number}",
            content_sid = TWILIO_CONTENT_SID,
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

def ask_groq(additional_parts=None, retries=3, backoff_factor=2):
    groq_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    current_user_content = []
    
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            if msg["kind"] == "text":
                current_user_content.append({"type": "text", "text": msg["content"]})
            elif msg["kind"] == "image":
                base64_image = base64.b64encode(msg["content"]).decode('utf-8')
                current_user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                })
        elif msg["role"] == "assistant":
            if current_user_content:
                groq_messages.append({"role": "user", "content": current_user_content})
                current_user_content = []
            if msg["kind"] == "text":
                groq_messages.append({"role": "assistant", "content": msg["content"]})
                
    if current_user_content:
        groq_messages.append({"role": "user", "content": current_user_content})

    if additional_parts:
        parts_content = []
        for part in additional_parts:
            if isinstance(part, str):
                parts_content.append({"type": "text", "text": part})
        groq_messages.append({"role": "user", "content": parts_content})

    for attempt in range(retries):
        try:
            response = groq_client.chat.completions.create(
                model=MODEL_NAME,
                messages=groq_messages,
                temperature=0.7,
                max_tokens=1024,
            )
            return response.choices[0].message.content
        except Exception as e:
            error_str = str(e)
            if "503" in error_str or "429" in error_str:
                if attempt < retries - 1:
                    time.sleep(backoff_factor ** attempt)
                    continue
            st.error(f"Error communicating with Groq API: {e}")
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
            # initialize chat state
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
            summary = ask_groq([SUMMARY_REQUEST_PROMPT])
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
    if text:
        add_message("user", "text", text)
    elif photo is not None:
        add_message("user", "text", "What is this meal? Please provide an estimate of calories and macros (protein, carbs, fat).")

    with st.spinner("Thinking..."):
        answer = ask_groq()
    add_message("assistant", "text", answer)

