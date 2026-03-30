import streamlit as st
import google.generativeai as genai
import os
import requests
from PIL import Image
from io import BytesIO

# =========================================================
# 1. КОНФИГУРАЦИЯ БЕЗОПАСНОСТИ (SECRETS)
# =========================================================
if "API_KEY" in st.secrets:
    API_KEY = st.secrets["API_KEY"]
else:
    # Оставь пустую строку, если ключ в Secrets уже вставлен
    API_KEY = ""

# --- СТИЛИЗАЦИЯ ---
st.set_page_config(page_title="ToU AI Advisor", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Roboto', sans-serif; background-color: #fcfcfc; }
    .stApp::before {
        content: ""; position: fixed; top: 0; left: 0; width: 100%; height: 10px;
        background: linear-gradient(90deg, #0055A4 0%, #007FFF 50%, #FFCC00 100%); z-index: 9999;
    }
    .main-title { color: #0055A4; font-size: 2.2rem; font-weight: 700; border-bottom: 2px solid #FFCC00; padding-bottom: 10px; }
    .sub-title { color: #666; font-size: 1.1rem; margin-bottom: 25px; }
    [data-testid="stChatMessage"] {
        background-color: white; border-radius: 10px; border: 1px solid #e0e6ed;
        box-shadow: 0 2px 5px rgba(0,85,164,0.05); margin-bottom: 15px;
    }
    .footer { text-align: center; color: #888; font-size: 0.8rem; margin-top: 50px; border-top: 1px solid #eee; padding-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ШАПКА ---
header_col1, header_col2 = st.columns([1, 4])
with header_col1:
    try:
        response = requests.get("https://tou.edu.kz/images/logo_tou_ru.png", timeout=5)
        img = Image.open(BytesIO(response.content))
        st.image(img, width=180)
    except:
        st.markdown("<h2 style='color:#0055A4;'>ToU</h2>", unsafe_allow_html=True)

with header_col2:
    st.markdown("<div class='main-title'>Виртуальный консультант Торайгыров Университета</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Интеллектуальная поддержка факультета Computer Science</div>", unsafe_allow_html=True)

# --- 3. ЛОГИКА ИИ С АВТОПОДБОРОМ МОДЕЛИ ---
if API_KEY and API_KEY != "ВСТАВЬ_СВОЙ_КЛЮЧ_ДЛЯ_ЛОКАЛЬНОГО_ТЕСТА":
    try:
        genai.configure(api_key=API_KEY)
        
        # ЭТА ЧАСТЬ ИСПРАВЛЯЕТ ОШИБКУ 404
        @st.cache_resource
        def get_working_model():
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            # Ищем сначала 1.5-flash, так как она самая быстрая
            for m_name in available_models:
                if 'gemini-1.5-flash' in m_name:
                    return genai.GenerativeModel(m_name)
            # Если не нашли, берем любую первую доступную из списка
            if available_models:
                return genai.GenerativeModel(available_models[0])
            return None

        model = get_working_model()

        if model:
            if os.path.exists("knowledge.txt"):
                with open("knowledge.txt", "r", encoding="utf-8") as f:
                    kb_content = f.read()
            else:
                st.error("Файл knowledge.txt не найден!")
                st.stop()

            if "messages" not in st.session_state:
                st.session_state.messages = []

            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            if prompt := st.chat_input("Спросите что-нибудь о ToU..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    full_prompt = f"Контекст: {kb_content}\n\nВопрос: {prompt}\nОтвечай кратко и вежливо."
                    response = model.generate_content(full_prompt)
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
        else:
            st.error("На вашем аккаунте не найдено доступных моделей Gemini.")

    except Exception as e:
        st.error(f"Произошла ошибка API: {e}")
else:
    st.warning("⚠️ Система ожидает API Ключ. Добавьте его в Secrets (API_KEY) или в код.")

# --- 4. ПОДВАЛ ---
st.markdown("<div class='footer'>© 2026 ToU. Разработано в рамках учебной практики.</div>", unsafe_allow_html=True)