import streamlit as st
import pandas as pd
from datetime import datetime
import google.generativeai as genai # المكتبة الرسمية اللي كيخدمو بها المحترفين

# 1. إعدادات الصفحة والهوية البصرية (الأسود والذهبي)
st.set_page_config(page_title="MAISON BALKISS SMART TOURISM 4.0", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #000000 !important; color: #D4AF37 !important; }
    .stApp { background-color: #000000; }
    .stButton>button { background-color: #D4AF37; color: black; border-radius: 20px; font-weight: bold; }
    h1, h2, h3, p, span, label { color: #D4AF37 !important; }
    .stTextInput>div>div>input { background-color: #1a1a1a; color: #D4AF37; border: 1px solid #D4AF37; }
    [data-testid="stSidebar"] { background-color: #111111; border-right: 1px solid #D4AF37; }
    </style>
    """, unsafe_allow_html=True)

# 2. قاموس اللغات
lang_dict = {
    'English': {'welcome': 'Welcome to Maison Balkiss', 'subtitle': 'SMART TOURISM 4.0', 'tab1': '💬 AI Chatbot', 'tab2': '🗺️ Smart Trail', 'tab3': '📜 Heritage Passport', 'login_title': 'Visitor Registration', 'name': 'Full Name', 'email': 'Email', 'start': 'Start'},
    'العربية': {'welcome': 'مرحباً بكم في ميزون بلقيس', 'subtitle': 'السياحة الذكية 4.0', 'tab1': '💬 شاتبوت ذكي', 'tab2': '🗺️ المسار الذكي', 'tab3': '📜 الجواز التراثي', 'login_title': 'تسجيل الزوار', 'name': 'الاسم الكامل', 'email': 'البريد', 'start': 'ابدأ'}
}

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'chat_history' not in st.session_state: st.session_state.chat_history = []

with st.sidebar:
    st.title("MAISON BALKISS")
    lang = st.selectbox("🌐 Language", ['English', 'العربية'])
    t = lang_dict[lang]
    st.markdown("---")
    with st.expander("🔐 Admin Area"):
        if st.text_input("Password", type="password") == "BALKISS2024":
            st.success("Admin Verified")
            try: st.dataframe(pd.read_csv('visitors_log.csv', names=['Date', 'Name', 'Contact', 'Lang']))
            except: st.write("No logs.")

if not st.session_state.logged_in:
    st.header(f"🏛️ {t['login_title']}")
    v_name = st.text_input(t['name'])
    v_contact = st.text_input(t['email'])
    if st.button(t['start']):
        if v_name and v_contact:
            with open('visitors_log.csv', 'a') as f: f.write(f"{datetime.now()},{v_name},{v_contact},{lang}\n")
            st.session_state.logged_in = True
            st.rerun()
else:
    st.title(f"👑 {t['welcome']}")
    st.subheader(t['subtitle'])
    tab1, tab2, tab3 = st.tabs([t['tab1'], t['tab2'], t['tab3']])

    with tab1:
        st.header(t['tab1'])
        # --- الطريقة الاحترافية ---
        try:
            genai.configure(api_key="AIzaSyBN9cmExKPo5Mn9UAtvdYKohgODPf8hwbA")
            model = genai.GenerativeModel('gemini-1.5-flash') # هاد السطر هو اللي كيحل المشكل
            
            user_query = st.chat_input("Ask Maison Balkiss AI...")
            if user_query:
                prompt = f"You are a professional Moroccan Virtual Guide for Maison Balkiss. Promote tourism in Sefrou, Figuig, Tangier. Answer in {lang}: {user_query}"
                with st.spinner('Maison Balkiss is thinking...'):
                    response = model.generate_content(prompt)
                    st.session_state.chat_history.append({"u": user_query, "a": response.text})
            
            for chat in reversed(st.session_state.chat_history):
                st.markdown(f"**👤 You:** {chat['u']}")
                st.markdown(f"**🏛️ Maison Balkiss:** {chat['a']}")
                st.markdown("---")
        except Exception as e:
            st.error(f"AI Connection issue. Please ensure 'Generative Language API' is enabled in your Google AI Studio.")

    with tab2:
        st.header(t['tab2'])
        st.write("Smart Discovery maps coming next!")
    with tab3:
        st.header(t['tab3'])
        st.write("Heritage Passport details here.")

    st.markdown("<center>© 2024 MAISON BALKISS - Smart Tourism 4.0</center>", unsafe_allow_html=True)
