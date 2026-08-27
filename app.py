import streamlit as st
import sqlite3
import hashlib
import os
import requests

# --- KONFIGURASI HALAMAN & TEMA GEMINI ---
st.set_page_config(
    page_title="Lagøs AI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# Custom CSS untuk tampilan ala Google Gemini
def load_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --gemini-blue: #4285F4;
        --gemini-purple: #9B72CB;
        --gemini-red: #D94538;
        --gemini-orange: #FBBC04;
        --bg-light: #F0F4F9;
        --surface-light: #FFFFFF;
        --text-primary: #1f1f1f;
        --text-secondary: #5f6368;
        --border-color: #e0e0e0;
        --shadow-sm: 0 1px 2px rgba(0,0,0,0.1);
        --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
        --radius-pill: 28px;
        --radius-bubble: 18px;
    }

    [data-theme="dark"] {
        --bg-light: #131314;
        --surface-light: #1E1F20;
        --text-primary: #E8EAED;
        --text-secondary: #9AA0A6;
        --border-color: #3C4043;
        --shadow-sm: 0 1px 2px rgba(0,0,0,0.3);
        --shadow-md: 0 4px 6px rgba(0,0,0,0.3);
    }

    .stApp {
        background-color: var(--bg-light);
        font-family: 'Outfit', sans-serif;
        color: var(--text-primary);
    }
    
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    
    section[data-testid="stSidebar"] {
        background-color: var(--surface-light);
        border-right: 1px solid var(--border-color);
        width: 280px !important;
    }
    
    .logo-text {
        font-size: 22px;
        font-weight: 600;
        background: linear-gradient(90deg, var(--gemini-blue), var(--gemini-purple));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .message-row {
        display: flex;
        gap: 16px;
        margin-bottom: 24px;
        animation: fadeIn 0.4s ease-out;
    }
    
    .message-row.user { flex-direction: row-reverse; }

    .avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 14px;
        flex-shrink: 0;
    }
    
    .avatar.ai {
        background: linear-gradient(135deg, var(--gemini-blue), var(--gemini-purple));
        color: white;
    }
    
    .avatar.user {
        background-color: var(--text-secondary);
        color: var(--surface-light);
    }

    .message-content {
        max-width: 85%;
        padding: 12px 18px;
        border-radius: var(--radius-bubble);
        line-height: 1.6;
        font-size: 15px;
    }
    
    .message-row.user .message-content {
        background-color: var(--surface-light);
        color: var(--text-primary);
        border-bottom-right-radius: 4px;
        box-shadow: var(--shadow-sm);
    }
    
    .message-row.ai .message-content {
        background-color: transparent;
        color: var(--text-primary);
        padding-left: 0;
    }

    .message-content pre {
        background-color: #1e1e1e;
        color: #d4d4d4;
        padding: 16px;
        border-radius: 12px;
        overflow-x: auto;
    }

    .welcome-screen {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 80vh;
        text-align: center;
    }
    
    .gemini-logo-large {
        width: 80px;
        height: 80px;
        background: linear-gradient(135deg, var(--gemini-blue), var(--gemini-purple), var(--gemini-red), var(--gemini-orange));
        border-radius: 50%;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 40px;
        color: white;
    }
    
    .suggestion-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 12px;
        width: 100%;
        max-width: 700px;
        margin-top: 40px;
    }
    
    .suggestion-card {
        background-color: var(--surface-light);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 16px;
        text-align: left;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .suggestion-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-sm);
        border-color: var(--gemini-blue);
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @media (max-width: 768px) {
        .message-content { max-width: 90%; }
        section[data-testid="stSidebar"] {
            transform: translateX(-100%);
            position: fixed;
            height: 100%;
            z-index: 2000;
        }
    }
    
    div[data-testid="stTextArea"] {
        position: fixed;
        bottom: 24px;
        left: 50%;
        transform: translateX(-50%);
        width: 90%;
        max-width: 800px;
        z-index: 999;
    }
    div[data-testid="stTextArea"] div[data-baseweb="textarea"] {
        background-color: var(--surface-light) !important;
        border-radius: var(--radius-pill) !important;
        border: 1px solid var(--border-color) !important;
        box-shadow: var(--shadow-md) !important;
        padding: 12px 20px !important;
        font-family: 'Outfit', sans-serif !important;
    }
    div[data-testid="stTextArea"] div[data-baseweb="textarea"]:focus-within {
        border-color: var(--gemini-blue) !important;
        box-shadow: 0 6px 12px rgba(66, 133, 244, 0.15) !important;
    }
    </style>
    """, unsafe_allow_html=True)

load_css()

# --- STATE & DATABASE ---
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'active_session_id' not in st.session_state:
    st.session_state.active_session_id = None
if 'user_info' not in st.session_state:
    st.session_state.user_info = None

DB_PATH = "lagos_agents.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    role TEXT,
                    content TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(session_id) REFERENCES sessions(id)
                )''')
    conn.commit()
    conn.close()

init_db()

def make_password_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                  (username, make_password_hash(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, username FROM users WHERE username = ? AND password_hash = ?", 
              (username, make_password_hash(password)))
    user = c.fetchone()
    conn.close()
    if user:
        return {"id": user[0], "username": user[1]}
    return None

def get_user_sessions(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, title, updated_at FROM sessions WHERE user_id = ? ORDER BY updated_at DESC", (user_id,))
    sessions = c.fetchall()
    conn.close()
    return sessions

def create_session(user_id, title="New Chat"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO sessions (user_id, title) VALUES (?, ?)", (user_id, title))
    session_id = c.lastrowid
    conn.commit()
    conn.close()
    return session_id

def save_message_to_db(session_id, role, content):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)", 
              (session_id, role, content))
    c.execute("UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

def get_messages_from_db(session_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT role, content FROM messages WHERE session_id = ? ORDER BY timestamp ASC", (session_id,))
    messages = c.fetchall()
    conn.close()
    return [{"role": r, "content": c} for r, c in messages]

def delete_session(session_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    c.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

# --- MODEL CONFIG ---
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
MODEL_MAPPING = {
    "Aether": "minimax/minimax-m3:free",
    "Nexus": "meta/llama-3.1-405b-instruct",
    "Pulse": "mistralai/mistral-large-2407",
}

def get_ai_response(prompt, model_key, history):
    if not NVIDIA_API_KEY:
        return "⚠️ Error: NVIDIA API Key tidak ditemukan."
    
    model_id = MODEL_MAPPING.get(model_key, MODEL_MAPPING["Aether"])
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {NVIDIA_API_KEY}", "Content-Type": "application/json"}
    
    api_messages = [{"role": msg["role"], "content": msg["content"]} for msg in history]
    api_messages.append({"role": "user", "content": prompt})

    payload = {"model": model_id, "messages": api_messages, "temperature": 0.7, "max_tokens": 1024}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# --- UI COMPONENTS ---
def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="logo-text">Lagøs AI</div>', unsafe_allow_html=True)
        st.divider()
        
        if st.session_state.user_info:
            st.markdown(f"""
            <div style="padding: 10px; background: var(--bg-light); border-radius: 12px; margin-bottom: 20px;">
                <div style="font-weight: 600;">{st.session_state.user_info['username']}</div>
                <div style="font-size: 12px; color: var(--text-secondary);">Active Now</div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🆕 New Chat", use_container_width=True, type="primary"):
                new_id = create_session(st.session_state.user_info['id'])
                st.session_state.active_session_id = new_id
                st.session_state.messages = []
                st.rerun()
            
            st.divider()
            sessions = get_user_sessions(st.session_state.user_info['id'])
            for sid, title, _ in sessions:
                if st.button(f"💬 {title[:20]}", key=f"s_{sid}", use_container_width=True):
                    st.session_state.active_session_id = sid
                    st.session_state.messages = get_messages_from_db(sid)
                    st.rerun()

def render_welcome():
    st.markdown("""
    <div class="welcome-screen">
        <div class="gemini-logo-large">✨</div>
        <h1>Halo, bagaimana saya bisa membantu?</h1>
        <p style="color: var(--text-secondary);">Powered by NVIDIA AI</p>
        <div class="suggestion-grid">
            <div class="suggestion-card"><b>Konsep Teknis</b><br><small>Jelaskan Quantum Computing</small></div>
            <div class="suggestion-card"><b>Strategi Bisnis</b><br><small>Rencana marketing produk</small></div>
            <div class="suggestion-card"><b>Coding Help</b><br><small>Buatkan script Python</small></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_chat():
    for msg in st.session_state.messages:
        role_class = "user" if msg["role"] == "user" else "ai"
        avatar = "U" if msg["role"] == "user" else "L"
        av_class = "user" if msg["role"] == "user" else "ai"
        content = markdown.markdown(msg["content"], extensions=['fenced_code'])
        
        st.markdown(f"""
        <div class="message-row {role_class}">
            <div class="avatar {av_class}">{avatar}</div>
            <div class="message-content">{content}</div>
        </div>
        """, unsafe_allow_html=True)

def handle_input(text):
    st.session_state.messages.append({"role": "user", "content": text})
    
    if not st.session_state.active_session_id and st.session_state.user_info:
        title = text[:30] + "..." if len(text) > 30 else text
        st.session_state.active_session_id = create_session(st.session_state.user_info['id'], title)
    
    if st.session_state.active_session_id:
        save_message_to_db(st.session_state.active_session_id, "user", text)
    
    with st.spinner("Thinking..."):
        response = get_ai_response(text, "Aether", st.session_state.messages)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    if st.session_state.active_session_id:
        save_message_to_db(st.session_state.active_session_id, "assistant", response)
    st.rerun()

# --- MAIN ---
def main():
    if st.session_state.user_info:
        if not st.session_state.messages:
            render_welcome()
        else:
            render_chat()
        
        user_input = st.text_area("Input", placeholder="Ask Lagøs anything...", 
                                  height=100, label_visibility="collapsed", key="main_input")
        if user_input:
            handle_input(user_input)
    else:
        st.markdown("""
        <div class="welcome-screen">
            <div class="gemini-logo-large">✨</div>
            <h1>Lagøs AI Agent</h1>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Login", "Register"])
        with tab1:
            with st.form("login"):
                u = st.text_input("Username")
                p = st.text_input("Password", type="password")
                if st.form_submit_button("Masuk"):
                    user = login_user(u, p)
                    if user:
                        st.session_state.user_info = user
                        st.rerun()
                    else:
                        st.error("Login gagal")
        with tab2:
            with st.form("reg"):
                u = st.text_input("Username Baru")
                p = st.text_input("Password Baru", type="password")
                if st.form_submit_button("Daftar"):
                    if register_user(u, p):
                        st.success("Berhasil! Silakan login.")
                    else:
                        st.error("Username sudah ada")

if __name__ == "__main__":
    main()
