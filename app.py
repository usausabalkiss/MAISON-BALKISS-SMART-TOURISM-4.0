import streamlit as st
import pandas as pd
from datetime import datetime
import requests

# 1. إعدادات الصفحة والهوية البصرية
st.set_page_config(page_title="MAISON BALKISS SMART TOURISM 4.0", layout="wide")

# تصميم CSS المصحح (الأسود والذهبي)
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
    'English': {
        'welcome': 'Welcome to Maison Balkiss',
        'subtitle': 'SMART TOURISM 4.0',
        'login_title': 'Visitor Registration',
        'name': 'Full Name',
        'email': 'Email / Phone',
        'start': 'Start Discovery',
        'tab1': '💬 AI Chatbot',
        'tab2': '🗺️ Smart Trail',
        'tab3': '📜 Heritage Passport',
        'feedback': 'Your Opinion Matters'
    },
    'العربية': {
        'welcome': 'مرحباً بكم في ميزون بلقيس',
        'subtitle': 'السياحة الذكية 4.0',
        'login_title': 'تسجيل الزوار',
        'name': 'الاسم الكامل',
        'email': 'البريد الإلكتروني / الهاتف',
        'start': 'ابدأ الاكتشاف',
        'tab1': '💬 شاتبوت ذكي',
        'tab2': '🗺️ المسار الذكي',
        'tab3': '📜 الجواز التراثي',
        'feedback': 'رأيكم يهمنا'
    }
}

# 3. إدارة الجلسة
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# 4. القائمة الجانبية
with st.sidebar:
    st.title("MAISON BALKISS")
    lang = st.selectbox("🌐 Language", ['English', 'العربية'])
    t = lang_dict[lang]
    st.markdown("---")
    with st.expander("🔐 Admin Area"):
        admin_pass = st.text_input("Password", type="password")
        if admin_pass == "BALKISS2024":
            st.success("Admin Verified")
            try:
                df_log = pd.read_csv('visitors_log.csv', names=['Date', 'Name', 'Contact', 'Lang'])
                st.dataframe(df_log)
            except:
                st.write("No logs yet.")

# 5. واجهة الدخول (Leads)
if not st.session_state.logged_in:
    st.header(f"🏛️ {t['login_title']}")
    v_name = st.text_input(t['name'])
    v_contact = st.text_input(t['email'])
    if st.button(t['start']):
        if v_name and v_contact:
            new_entry = f"{datetime.now()},{v_name},{v_contact},{lang}\n"
            with open('visitors_log.csv', 'a') as f:
                f.write(new_entry)
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.warning("Please fill your details.")

# 6. الواجهة الرئيسية بعد الدخول
else:
    st.title(f"👑 {t['welcome']}")
    st.subheader(t['subtitle'])

    tab1, tab2, tab3 = st.tabs([t['tab1'], t['tab2'], t['tab3']])

    with tab1:
        st.header(t['tab1'])
        api_key = "AIzaSyBN9cmExKPo5Mn9UAtvdYKohgODPf8hwbA"
        
        # التعديل: استخدام رابط v1 مع gemini-1.5-flash لضمان التوافق التام
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"

        user_query = st.chat_input("Ask Maison Balkiss AI...")
        if user_query:
            prompt = f"You are a professional Moroccan Virtual Guide for Maison Balkiss. Promote tourism in Sefrou, Figuig, Tangier. Answer in {lang}: {user_query}"
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }]
            }
            headers = {"Content-Type": "application/json"}
            
            try:
                with st.spinner('Maison Balkiss is thinking...'):
                    response = requests.post(url, json=payload, headers=headers, timeout=15)
                    res_json = response.json()
                    
                    if 'candidates' in res_json:
                        answer = res_json['candidates'][0]['content']['parts'][0]['text']
                        st.session_state.chat_history.append({"u": user_query, "a": answer})
                    else:
                        # عرض رسالة الخطأ الحقيقية من جوجل للتشخيص
                        error_msg = res_json.get('error', {}).get('message', 'Check API Status')
                        st.error(f"AI Status: {error_msg}")
            except Exception as e:
                st.error(f"Connection Error: {str(e)}")

        for chat in reversed(st.session_state.chat_history):
            st.markdown(f"**👤 You:** {chat['u']}")
            st.markdown(f"**🏛️ Maison Balkiss:** {chat['a']}")
            st.markdown("---")

    with tab2:
        st.header(t['tab2'])
        st.write("Smart Discovery for Sefrou, Figuig, and Tangier is coming next!")

    with tab3:
        st.header(t['tab3'])
        st.write("Collect your Heritage Passport stamps here.")

    st.markdown("---")
    st.subheader(t['feedback'])
    st.text_area("Your Feedback...")
    st.button("Submit Feedback")
    st.markdown("<center>© 2024 MAISON BALKISS - Smart Tourism 4.0</center>", unsafe_allow_html=True)
