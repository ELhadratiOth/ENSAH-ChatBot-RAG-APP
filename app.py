import streamlit as st
import requests

st.set_page_config(
    page_title="ENSAH Assistant",
    page_icon="🎓",
    layout="wide"
)

API_URL = "http://localhost:8000/chat/invoke"
HEADERS = {"Content-Type": "application/json"}

import uuid
from streamlit_local_storage import LocalStorage

localS = LocalStorage()

def get_from_local_storage(key):
    value = localS.getItem(key)
    return value

def set_to_local_storage(key, value):
    localS.setItem(key, value)

def init_storage():

    user_id = get_from_local_storage('streamlit_user_id')
    # print("this is the key:", user_id)
    
    if not user_id:
        user_id = f"streamlit_{str(uuid.uuid4())[:8]}"
        set_to_local_storage('streamlit_user_id', user_id)
    
    return user_id

if "session_id" not in st.session_state:
    user_id = init_storage()
    # print("user created :", user_id)
    st.session_state.session_id = user_id

if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        color: #E0E0E0;
    }
    
    h1 {
        color: #2196F3 !important;
        font-family: 'Arial', sans-serif;
        text-align: center;
        padding: 20px;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    h2, h3 {
        color: #2196F3 !important;
        font-family: 'Arial', sans-serif;
        margin-top: 20px;
    }
    
    .stChatMessage {
        background-color: #1A1E24 !important;
        border-radius: 15px !important;
        padding: 15px !important;
        margin-bottom: 15px !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
        animation: fadeIn 0.5s ease-in-out;
    }
    
    .stChatMessage[data-testid="user-message"] {
        background-color: #1E3A5F !important;
        border: 1px solid #2196F3 !important;
        margin-left: 20% !important;
    }
    
    .stChatMessage[data-testid="assistant-message"] {
        background-color: #162231 !important;
        border: 1px solid #1976D2 !important;
        margin-right: 20% !important;
    }
    
    .stTextInput input {
        background-color: #1A1E24 !important;
        border-radius: 10px !important;
        padding: 15px !important;
        border: 2px solid #1976D2 !important;
        color: white !important;
        font-size: 16px !important;
    }
    
    .stTextInput input:focus {
        border-color: #2196F3 !important;
        box-shadow: 0 0 10px rgba(33, 150, 243, 0.3) !important;
    }
    
    .css-1d391kg {
        background-color: #1A1E24;
        padding: 20px;
    }
    
    .css-1kyxreq {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }
    
    .stAlert {
        background-color: #1A1E24 !important;
        border: 1px solid #2196F3 !important;
        color: #E0E0E0 !important;
        border-radius: 10px !important;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .source-doc {
        background-color: #162231;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 4px solid #2196F3;
        font-size: 14px;
    }
    
    .divider {
        border-bottom: 2px solid #2D3748;
        margin: 20px 0;
        width: 100%;
    }
    
    .stChatMessage [data-testid="StChatMessageAvatar"] div {
        width: 40px !important;
        height: 40px !important;
        border-radius: 50% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background-color: #1A1E24 !important;
    }

    .stChatMessage[data-testid="user-message"] [data-testid="StChatMessageAvatar"] div::before {
        content: "👤" !important;
        font-size: 24px !important;
    }

    .stChatMessage[data-testid="assistant-message"] [data-testid="StChatMessageAvatar"] div::before {
        content: "🎓" !important;
        font-size: 24px !important;
    }
    
    @keyframes blink {
        0% { opacity: .2; }
        20% { opacity: 1; }
        100% { opacity: .2; }
    }
    
    .loading span {
        font-size: 24px;
        animation-name: blink;
        animation-duration: 1.4s;
        animation-iteration-count: infinite;
        animation-fill-mode: both;
    }
    
    .loading span:nth-child(2) {
        animation-delay: .2s;
    }
    
    .loading span:nth-child(3) {
        animation-delay: .4s;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("ENSA Al-Hoceima Assistant 🎓")

if not st.session_state.messages:
    st.markdown("""
    <div style='text-align: center; padding: 20px; background-color: #1A1E24; border-radius: 10px; margin: 20px 0;'>
        <h2 style='color: #2196F3;'>Welcome to ENSAH Assistant! 👋</h2>
        <p style='color: #E0E0E0; font-size: 18px;'>I'm here to help you learn about ENSA Al-Hoceima.</p>
        <p style='color: #E0E0E0; font-size: 16px;'>You can ask me about:</p>
        <ul style='color: #E0E0E0; list-style-type: none; '>
            <li>📚 Academic Programs and Courses</li>
            <li>👨‍🏫 Faculty and Staff</li>
            <li>🏫 Campus Facilities</li>
            <li>📅 Events and News</li>
            <li>🎯 Student Activities and Clubs</li>
         </ul>
    </div>
    """, unsafe_allow_html=True)

with st.sidebar:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("./assets/logo-ensah.png", width=150)
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    st.markdown("""
    <h3 style='color: #2196F3; text-align: center;'>How to Use</h3>
    """, unsafe_allow_html=True)
    
    st.info("""
    💡 Tips for better results:\n
    • Ask specific questions\n
    • You can use French or English\n
    • Feel free to ask follow-up questions\n
    • Be clear and concise
    """)
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    st.markdown("""
    <h3 style='color: #2196F3; text-align: center;'>About</h3>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    This AI assistant uses advanced language models to provide accurate information about ENSA Al-Hoceima. All information is based on official ENSAH documentation and public resources.
    """)
    
    st.markdown("---")
    st.markdown("## About the Creator")
    st.markdown("""
    <div style='background-color: #1A1E24; padding: 20px; border-radius: 10px; border: 1px solid #2196F3;'>
        <h3 style='color: #2196F3; text-align: center;'>Developed by Othman El Hadrati</h3>
        <p style='color: #E0E0E0; text-align: center;'>
            Data Engineer Student at ENSAH<br>
            Passionate about AI and Software Development
        </p>
        <div style='text-align: center; margin-top: 15px;'>
            <a href='https://github.com/ELhadratiOth' target='_blank' style='text-decoration: none; color: #2196F3; margin: 0 10px;'>
                GitHub
            </a>
            <a href='https://www.linkedin.com/in/othman-el-hadrati-91aa98243/' target='_blank' style='text-decoration: none; color: #2196F3; margin: 0 10px;'>
                LinkedIn
            </a>
            <a href='https://www.0thman.tech' target='_blank' style='text-decoration: none; color: #2196F3; margin: 0 10px;'>
                Portfolio
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

def format_source_docs(source_docs):
    if not source_docs:
        return ""
    
    formatted_sources = ""
    for i, doc in enumerate(source_docs, 1):
        if isinstance(doc, dict):
            content = doc.get('content', '')
            metadata = doc.get('metadata', {})
            source = metadata.get('source', 'Unknown')
            source = source.replace('./Data\\', '').replace('_', ' ').title()
            
            formatted_sources += f"""
            <div class="source-doc">
                <div class="source-title">📚 Source {i} - {source}</div>
                <div class="source-content">
                    {content.replace('\\n', '<br>')}
                </div>
            </div>
            """
    return formatted_sources

def loading_message():
    return """
    <div style='text-align: center; padding: 20px;'>
        <div style='display: inline-block; '>
            <div class='loading'>
                <span>.</span>
                <span>.</span>
                <span>.</span>
            </div>
        </div>
    </div>
    """

for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=None):
        st.markdown(message["content"])
        if message.get("source_docs"):
            st.markdown(format_source_docs(message["source_docs"]), unsafe_allow_html=True)

if prompt := st.chat_input("Ask me anything about ENSAH..."):
    st.chat_message("user", avatar=None).markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    loading_placeholder = st.empty()
    loading_placeholder.markdown(loading_message(), unsafe_allow_html=True)
    
    try:
        # print("hell no")
        # print("user sent :",st.session_state.session_id )
        payload = {
            "input": {
                "input": prompt
            },
            "config": {
                "configurable": {
                    "session_id": st.session_state.session_id
                }
            }
        }
        
        response = requests.post(API_URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        result = response.json()
        
        output = result.get("output", {})
        answer = output.get("answer", "I couldn't process your request.")
        sources = output.get("source_documents", [])
        
        loading_placeholder.empty()
        
        with st.chat_message("assistant", avatar=None):
            st.markdown(answer)
            if sources:
                formatted_sources = format_source_docs(sources)
                if formatted_sources:
                    st.markdown("### Reference Sources:", unsafe_allow_html=True)
                    st.markdown(formatted_sources, unsafe_allow_html=True)
        
        st.session_state.messages.append({
            "role": "assistant", 
            "content": answer,
            "source_docs": sources
        })
        
    except Exception as e:
        loading_placeholder.empty()
        st.error(f"Error: {str(e)}")

if st.button("🗑️ Clear Chat", key="clear_chat"):
    st.session_state.messages = []
    st.rerun()