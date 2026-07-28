import streamlit as st
import extra_streamlit_components as stx
from openai import OpenAI
import io
import re
import base64
import requests
from docx import Document
from audio_recorder_streamlit import audio_recorder
import speech_recognition as sr
import sqlite3
import json
import uuid
import hashlib
import datetime
import streamlit.components.v1 as components
from bs4 import BeautifulSoup 
import traceback
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Lagos AI 9.1 | Emergent Agent",
    page_icon="🔮",
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- 2. CUSTOM CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        .header-title {
            text-align: center;
            font-size: 2.2rem;
            font-weight: 700;
            background: linear-gradient(90deg, #7d4eff, #00d2ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0px;
            padding-top: 10px;
        }
        .header-subtitle {
            text-align: center;
            color: var(--text-color);
            opacity: 0.7;
            font-size: 0.95rem;
            font-weight: 300;
            margin-bottom: 30px;
        }
        .stChatMessage:nth-child(even) {
            background-color: var(--secondary-background-color) !important;
            border-radius: 12px;
            padding: 1rem;
        }
        .file-pill {
            display: inline-block;
            background: var(--secondary-background-color);
            color: var(--text-color);
            padding: 4px 14px;
            border-radius: 20px;
            font-size: 0.8rem;
            margin-right: 8px;
            margin-bottom: 12px;
            border: 1px solid var(--border-color);
        }
    </style>
""", unsafe_allow_html=True)

# --- PENGELOLA COOKIE & DATABASE ---
cookie_manager = stx.CookieManager(key="cookie_manager")
DB_NAME = 'lagos_multiuser.db'

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sessions (session_id TEXT PRIMARY KEY, username TEXT, title TEXT, updated_at TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, role TEXT, content TEXT)''')
    conn.commit()
    conn.close()

def register_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hash_password(password)))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False 
    conn.close()
    return success

def authenticate_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    return True if row and row[0] == hash_password(password) else False

def get_user_sessions(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT session_id, title FROM sessions WHERE username=? ORDER BY updated_at DESC", (username,))
    rows = c.fetchall()
    conn.close()
    return rows

# --- [SYSTEM PROMPT: FULLSTACK, ANTI-REFRESH & PARTIAL EDIT AMAN] ---
SYSTEM_PROMPT = """Anda adalah Lagos AI 9.1 (Rian Dev), Senior Fullstack Developer & Arsitek Sistem.
Anda memiliki 2 mode utama: PYTHON FULLSTACK (Streamlit + SQLite) dan FRONTEND WEB (HTML/JS/CSS).

ATURAN KODE:
1. Jika membuat aplikasi BARU dengan Streamlit: Bungkus seluruh kode dengan ```python ... ``` dan pastikan ada import streamlit as st.
2. Jika membuat aplikasi BARU dengan HTML: Bungkus HANYA dengan ```html ... ```.
3. MODE REVISI (SANGAT PENTING): Jika pengguna meminta revisi atau perubahan pada kode yang SUDAH ANDA BUAT, DILARANG mencetak ulang seluruh kode! Anda WAJIB menggunakan format edit berikut untuk mengubah bagian yang spesifik saja:

```edit
[SEARCH]
(masukkan potongan kode lama persis seperti aslinya di sini, TERMASUK SPASI DAN INDENTASI)
[REPLACE]
(masukkan potongan kode baru sebagai pengganti di sini, TERMASUK SPASI DAN INDENTASI)
```

ATURAN WAJIB HTML (SANDBOX SAFE):
- DILARANG menggunakan link dummy navigasi seperti `<a href="#">` atau `<a href="/">`. Gunakan `<a href="javascript:void(0);">`.
- Cegah refresh pada form dengan `<form onsubmit="event.preventDefault()">`.
- DILARANG menggunakan tag `<meta http-equiv="refresh">` atau manipulasi `window.location`.
"""

def load_session_messages(session_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT role, content FROM messages WHERE session_id=? ORDER BY id ASC", (session_id,))
    rows = c.fetchall()
    conn.close()
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    for r, c in rows:
        try: msgs.append({"role": r, "content": json.loads(c)})
        except: msgs.append({"role": r, "content": c})
    return msgs

def save_session_db(session_id, username, title, messages):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO sessions (session_id, username, title, updated_at) VALUES (?, ?, ?, ?)", 
              (session_id, username, title, datetime.datetime.now()))
    c.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
    for msg in messages:
        if msg["role"] != "system":
            c.execute("INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)", 
                      (session_id, msg["role"], json.dumps(msg["content"])))
    conn.commit()
    conn.close()

def delete_session_db(session_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM sessions WHERE session_id=?", (session_id,))
    c.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
    conn.commit()
    conn.close()

init_db()

# --- 3. SISTEM AUTENTIKASI ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

cookie_logged_in = cookie_manager.get("is_logged_in")
cookie_username = cookie_manager.get("saved_username")

if st.session_state.get("del_cookie") == True:
    cookie_manager.delete("is_logged_in", key="del_login_cookie")
    cookie_manager.delete("saved_username", key="del_user_cookie")
    st.session_state.del_cookie = False 
    cookie_logged_in = None 
    cookie_username = None

if cookie_logged_in == "True" and not st.session_state.logged_in:
    st.session_state.logged_in = True
    st.session_state.username = cookie_username

if st.session_state.get("set_cookie") == True:
    expire_date = datetime.datetime.now() + datetime.timedelta(days=7)
    cookie_manager.set("is_logged_in", "True", expires_at=expire_date, key="set_login_cookie")
    cookie_manager.set("saved_username", st.session_state.username, expires_at=expire_date, key="set_user_cookie")
    st.session_state.set_cookie = False

if not st.session_state.logged_in:
    st.markdown('<div class="header-title">🔮 Lagos AI 9.1</div>', unsafe_allow_html=True)
    st.markdown('<div class="header-subtitle">Silakan Masuk untuk Mengakses Asisten</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.container(border=True):
            tab_login, tab_register = st.tabs(["🔑 Masuk", "📝 Daftar Baru"])
            with tab_login:
                st.markdown("<h4 style='text-align: center; margin-bottom: 20px;'>Selamat Datang Kembali</h4>", unsafe_allow_html=True)
                log_user = st.text_input("Username", key="log_user")
                log_pass = st.text_input("Password", type="password", key="log_pass")
                if st.button("Masuk", use_container_width=True, type="primary"):
                    if authenticate_user(log_user, log_pass):
                        st.session_state.logged_in = True
                        st.session_state.username = log_user
                        st.session_state.set_cookie = True
                        st.rerun()
                    else: st.error("Username atau password salah!")
            with tab_register:
                st.markdown("<h4 style='text-align: center; margin-bottom: 20px;'>Buat Akun Baru</h4>", unsafe_allow_html=True)
                reg_user = st.text_input("Username Baru", key="reg_user")
                reg_pass = st.text_input("Password Baru", type="password", key="reg_pass")
                if st.button("Daftar & Buat Akun", use_container_width=True):
                    if reg_user and reg_pass:
                        if register_user(reg_user, reg_pass): st.success("✅ Berhasil mendaftar!")
                        else: st.error("❌ Username sudah dipakai.")
    st.stop()


# --- KODE SETELAH LOGIN ---
API_KEY = st.secrets.get("NVIDIA_API_KEY", "") 
BASE_URL = "https://integrate.api.nvidia.com/v1"

@st.cache_data(show_spinner=False)
def konversi_gambar_ke_base64(uploaded_file):
    if uploaded_file: return base64.b64encode(uploaded_file.read()).decode('utf-8')
    return None

@st.cache_data(show_spinner=False)
def ekstrak_teks_dari_dokumen(uploaded_file):
    teks_hasil = ""
    nama_file = uploaded_file.name.lower()
    try:
        if nama_file.endswith('.pdf'):
            from pypdf import PdfReader
            reader = PdfReader(uploaded_file)
            for page in reader.pages:
                teks = page.extract_text()
                if teks: teks_hasil += teks + "\n"
        elif nama_file.endswith('.txt'):
            teks_hasil = uploaded_file.read().decode("utf-8")
        return teks_hasil.strip()
    except Exception: return ""

def ambil_teks_dari_link(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'} 
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        text = ' '.join([p.get_text() for p in soup.find_all('p')])
        return re.sub(r'\s+', ' ', text).strip()
    except Exception as e: return f"Error saat membaca link: {str(e)}"

def generate_title_from_messages(messages):
    for msg in messages:
        if msg["role"] == "user":
            content = msg["content"]
            text = next((item["text"] for item in content if item["type"] == "text"), "") if isinstance(content, list) else str(content)
            return text[:25] + "..." if len(text) > 25 else "Obrolan Baru"
    return "Obrolan Baru"

# --- 4. INISIALISASI SESSION STATE ---
if "current_session_id" not in st.session_state: st.session_state.current_session_id = None
if "messages" not in st.session_state: st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
if "temp_image" not in st.session_state: st.session_state.temp_image = None
if "temp_doc" not in st.session_state: st.session_state.temp_doc = None
if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0
if "generated_code" not in st.session_state: st.session_state.generated_code = ""
if "code_type" not in st.session_state: st.session_state.code_type = "python"
if "auto_prompt" not in st.session_state: st.session_state.auto_prompt = None

# --- SIDEBAR ---
with st.sidebar:
    st.success(f"👤 Login: **{st.session_state.username}**")
    if st.button("➕ Mulai Obrolan Baru", use_container_width=True, type="primary"):
        st.session_state.current_session_id = None
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.session_state.generated_code = "" 
        st.session_state.code_type = "python"
        st.rerun()

    st.markdown("### 🗂️ Riwayat Obrolan")
    sessions = get_user_sessions(st.session_state.username)
    if sessions:
        with st.container(height=300, border=False):
            for sess_id, title in sessions:
                col_btn, col_del = st.columns([6, 1], gap="small") 
                with col_btn:
                    btn_type = "primary" if st.session_state.current_session_id == sess_id else "secondary"
                    if st.button(title, key=f"btn_{sess_id}", use_container_width=True, type=btn_type):
                        st.session_state.current_session_id = sess_id
                        st.session_state.messages = load_session_messages(sess_id)
                        
                        # Merekonstruksi state kode dari riwayat secara kronologis (maju)
                        st.session_state.generated_code = ""
                        st.session_state.code_type = "python"
                        for msg in st.session_state.messages:
                            if msg["role"] == "assistant":
                                # Cek Edit Parsial (Strip hanya pada karakter enter \r\n, pertahankan spasi)
                                code_match_edit = re.search(r'```edit\n\[SEARCH\]\n(.*?)\n\[REPLACE\]\n(.*?)\n```', msg["content"], re.DOTALL)
                                # Cek Kode Penuh Baru
                                code_match_py = re.search(r'```python\n(.*?)\n```', msg["content"], re.DOTALL)
                                code_match_html = re.search(r'```html\n(.*?)\n```', msg["content"], re.DOTALL)
                                
                                if code_match_edit:
                                    search_text = code_match_edit.group(1).strip('\r\n')
                                    replace_text = code_match_edit.group(2).strip('\r\n')
                                    if search_text in st.session_state.generated_code:
                                        st.session_state.generated_code = st.session_state.generated_code.replace(search_text, replace_text)
                                elif code_match_py:
                                    st.session_state.generated_code = code_match_py.group(1)
                                    st.session_state.code_type = "python"
                                elif code_match_html:
                                    st.session_state.generated_code = code_match_html.group(1)
                                    st.session_state.code_type = "html"
                        st.rerun()
                with col_del:
                    if st.button("🗑️", key=f"del_{sess_id}"):
                        delete_session_db(sess_id)
                        if st.session_state.current_session_id == sess_id:
                            st.session_state.current_session_id = None
                            st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                            st.session_state.generated_code = ""
                        st.rerun()

    st.divider()
    MODEL_NAME = st.selectbox(
        "🧠 Pilih Model AI:",
        ["poolside/laguna-xs-2.1", "nvidia/nemotron-3-ultra-550b-a55b", "google/diffusiongemma-26b-a4b-it", "google/gemma-4-31b-it"],
        index=1
    )

    if st.button("🚪 Keluar (Logout)", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.del_cookie = True 
        st.rerun()

    st.markdown(
        '''
        <div style="background-color: var(--secondary-background-color); border: 1px dashed var(--border-color); padding: 15px; border-radius: 10px; text-align: center; margin-top: 20px;">
            <span style="color: #888; font-size: 0.75rem;">Advertisement Space</span><br>
            <span style="font-size: 0.9rem;">Integrasi Iklan Akan Ditampilkan Di Sini</span>
        </div>
        ''', unsafe_allow_html=True
    )

# --- LAYOUT DINAMIS (KEMBALI KE EMERGENT LAYOUT - KOLOM) ---
if st.session_state.generated_code:
    col_chat, col_preview = st.columns([1, 1], gap="large")
else:
    _, col_chat, _ = st.columns([1, 4, 1])
    col_preview = None

# --- AREA OBROLAN ---
with col_chat:
    st.markdown('<div class="header-title" style="font-size: 1.8rem;">🔮 Lagos AI 9.1</div>', unsafe_allow_html=True)
    st.markdown('<div class="header-subtitle" style="margin-bottom: 10px;">Emergent Agent Chat</div>', unsafe_allow_html=True)
    
    chat_container = st.container(height=550, border=False)
    with chat_container:
        if len(st.session_state.messages) == 1:
            st.markdown("<p style='text-align: center; margin-top: 2vh; color: #666;'>Minta saya membuat sistem CRUD, dashboard data (Streamlit) atau web app (HTML)!</p>", unsafe_allow_html=True)

        for message in st.session_state.messages:
            if message["role"] == "system": continue
            with st.chat_message(message["role"]):
                content = message["content"]
                text_disp = next((item["text"] for item in content if item["type"] == "text"), "") if isinstance(content, list) else str(content)
                st.markdown(text_disp)

        st.markdown("<div id='bottom-marker'></div>", unsafe_allow_html=True)

    current_img = st.session_state.get(f"img_{st.session_state.uploader_key}")
    current_doc = st.session_state.get(f"doc_{st.session_state.uploader_key}")

    if current_img: st.markdown(f"<div class='file-pill'>📷 Gambar dilampirkan</div>", unsafe_allow_html=True)
    if current_doc: st.markdown(f"<div class='file-pill'>📄 Dokumen dilampirkan</div>", unsafe_allow_html=True)

    col_attach, col_input, col_mic = st.columns([1, 7, 1.5])
    with col_attach:
        with st.popover("➕"): 
            st.session_state.temp_image = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"], key=f"img_{st.session_state.uploader_key}")
            st.session_state.temp_doc = st.file_uploader("Upload Doc", type=["pdf", "txt"], key=f"doc_{st.session_state.uploader_key}")

    with col_input:
        prompt_text = st.chat_input("Tanyakan atau suruh buatkan aplikasi...")

    with col_mic:
        audio_bytes = audio_recorder(text="", recording_color="#ff4b4b", neutral_color="#888888", icon_name="microphone", key=f"mic_{st.session_state.uploader_key}")

    prompt = prompt_text
    
    if st.session_state.auto_prompt:
        prompt = st.session_state.auto_prompt
        st.session_state.auto_prompt = None 

    if audio_bytes and not prompt_text:
        with st.spinner("Menerjemahkan suara..."):
            r = sr.Recognizer()
            try:
                with io.BytesIO(audio_bytes) as source_bytes:
                    with sr.AudioFile(source_bytes) as source:
                        audio_data = r.record(source)
                        prompt = r.recognize_google(audio_data, language="id-ID")
            except:
                st.warning("Suara tidak jelas.")
                prompt = None

    if prompt:
        with chat_container: 
            with st.chat_message("user"):
                st.markdown(prompt)

        teks_tambahan = ""
        if st.session_state.temp_doc:
            teks_dok = ekstrak_teks_dari_dokumen(st.session_state.temp_doc)
            if teks_dok: teks_tambahan += f"\n[KONTEN DOKUMEN]\n{teks_dok}\n"

        urls_found = re.compile(r'https?://\S+').findall(prompt)
        if urls_found:
            for url in urls_found:
                teks_web = ambil_teks_dari_link(url)
                teks_tambahan += f"\n[ISI WEBSITE]\n{teks_web[:4000]}\n"

        final_prompt = f"{teks_tambahan}\n\nUser:\n{prompt}" if teks_tambahan else prompt
        
        konten_payload = final_prompt
        if st.session_state.temp_image:
            base64_img = konversi_gambar_ke_base64(st.session_state.temp_image)
            konten_payload = [{"type": "text", "text": final_prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}]

        st.session_state.messages.append({"role": "user", "content": konten_payload})

        with chat_container:
            with st.chat_message("assistant"):
                client = OpenAI(
                    base_url=BASE_URL, 
                    api_key=API_KEY,
                    timeout=120.0,
                    max_retries=3
                )
                placeholder = st.empty()
                full_response = ""

                try:
                    response_stream = client.chat.completions.create(
                        model=MODEL_NAME, 
                        messages=st.session_state.messages,
                        temperature=0.7, max_tokens=8096, stream=True
                    )
                    for chunk in response_stream:
                        if chunk.choices and len(chunk.choices) > 0:
                            delta = chunk.choices[0].delta.content
                            if delta:
                                full_response += delta
                                placeholder.markdown(full_response + "▌")
                    placeholder.markdown(full_response)
                    
                    st.session_state.messages[-1] = {"role": "user", "content": prompt}
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    
                    if st.session_state.current_session_id is None:
                        st.session_state.current_session_id = str(uuid.uuid4())
                    
                    save_session_db(st.session_state.current_session_id, st.session_state.username, generate_title_from_messages(st.session_state.messages), st.session_state.messages)

                    # --- [SISTEM DETEKSI DAN REVISI KODE PARSIAL AMAN] ---
                    # Perhatikan penggunaan strip('\r\n') agar spasi/indentasi Python tetap utuh!
                    code_match_edit = re.search(r'```edit\n\[SEARCH\]\n(.*?)\n\[REPLACE\]\n(.*?)\n```', full_response, re.DOTALL)
                    code_match_py = re.search(r'```python\n(.*?)\n```', full_response, re.DOTALL)
                    code_match_html = re.search(r'```html\n(.*?)\n```', full_response, re.DOTALL)
                    
                    if code_match_edit:
                        search_text = code_match_edit.group(1).strip('\r\n')
                        replace_text = code_match_edit.group(2).strip('\r\n')
                        
                        if search_text in st.session_state.generated_code:
                            st.session_state.generated_code = st.session_state.generated_code.replace(search_text, replace_text)
                        else:
                            st.error("⚠️ AI gagal melakukan revisi: Teks spesifik yang dicari tidak persis sama dengan kode asli. Silakan suruh AI ulangi.")
                            
                    elif code_match_py:
                        st.session_state.generated_code = code_match_py.group(1)
                        st.session_state.code_type = "python"
                        
                    elif code_match_html:
                        st.session_state.generated_code = code_match_html.group(1)
                        st.session_state.code_type = "html"

                    st.session_state.temp_image = None
                    st.session_state.temp_doc = None
                    st.session_state.uploader_key += 1 
                    st.rerun()

                except Exception as e:
                    st.error(f"Kesalahan teknis API: {str(e)}")
                    with st.expander("Lihat Detail Error Asli (Untuk Debugging)"):
                        st.code(traceback.format_exc(), language="bash")
                    st.session_state.messages.pop()

# --- AREA PREVIEW DYNAMIC ---
if col_preview is not None:
    with col_preview:
        st.markdown('<div class="header-title" style="font-size: 1.8rem; background: linear-gradient(90deg, #00d2ff, #7d4eff);">⚡ Render Workspace</div>', unsafe_allow_html=True)
        st.markdown('<div class="header-subtitle" style="margin-bottom: 10px;">Aplikasi yang dibuat AI akan muncul di sini</div>', unsafe_allow_html=True)
        
        if st.session_state.code_type == "html":
            file_name = "index.html"
            mime_type = "text/html"
            label_btn = "📥 Unduh Web HTML (Siap Pakai)"
        else:
            file_name = "app.py"
            mime_type = "text/x-python"
            label_btn = "📥 Unduh Web Streamlit (Siap Pakai)"
            
        st.download_button(
            label=label_btn,
            data=st.session_state.generated_code,
            file_name=file_name,
            mime=mime_type,
            use_container_width=True,
            type="primary"
        )
        st.markdown("<br>", unsafe_allow_html=True)

        tab_view, tab_code = st.tabs(["🚀 Aplikasi Dinamis", "💻 Source Code"])
        
        with tab_view:
            with st.container(border=True, height=550):
                try:
                    if st.session_state.code_type == "python":
                        # --- INJEKSI FULLSTACK ---
                        local_scope = {
                            "st": st, "pd": pd, "np": np, 
                            "datetime": datetime.datetime, 
                            "px": px, "go": go,
                            "sqlite3": sqlite3, 
                            "json": json,
                            "requests": requests 
                        }
                        exec(st.session_state.generated_code, globals(), local_scope)
                        
                    elif st.session_state.code_type == "html":
                        components.html(st.session_state.generated_code, height=530, scrolling=True)

                except Exception as e:
                    error_trace = traceback.format_exc()
                    st.error(f"⚠️ Terdapat kesalahan pada sintaks kode {st.session_state.code_type} yang dibuat AI.")
                    with st.expander("Lihat Detail Error"):
                        st.code(error_trace, language="bash")
                    
                    if st.button("🔧 Minta AI Perbaiki Otomatis", type="primary"):
                        st.session_state.auto_prompt = f"Kode yang Anda buat tadi menghasilkan error ini:\n```\n{e}\n```\nTolong perbaiki kodenya secara utuh tanpa error."
                        st.rerun()

        with tab_code:
            st.code(st.session_state.generated_code, language=st.session_state.code_type)
