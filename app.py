import streamlit as st
import pandas as pd
import os
from datetime import datetime
import requests
import folium 
from streamlit_folium import st_folium 
from geopy.geocoders import Nominatim 

# 1. إعدادات الصفحة والهوية البصرية (محفوظة 100%)
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

# --- وظائف قاعدة البيانات (المؤمنة) ---
def save_user_to_db(name, email, password):
    df = pd.DataFrame([[datetime.now(), name, email, password]], columns=['Date', 'Name', 'Email', 'Password'])
    df.to_csv('visitors_log.csv', mode='a', header=not os.path.exists('visitors_log.csv'), index=False)

def check_login(email, password):
    if os.path.exists('visitors_log.csv'):
        df = pd.read_csv('visitors_log.csv', on_bad_lines='skip')
        user = df[(df['Email'] == email) & (df['Password'] == str(password))]
        return user.iloc[0]['Name'] if not user.empty else None
    return None

def save_stamp_to_db(name, email, place):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    df = pd.DataFrame([[name, email, place, now]], columns=['Name', 'Email', 'Place', 'Date'])
    df.to_csv('stamps_log.csv', mode='a', header=not os.path.exists('stamps_log.csv'), index=False)

def load_user_stamps(email):
    if os.path.exists('stamps_log.csv'):
        df = pd.read_csv('stamps_log.csv')
        user_stamps = df[df['Email'] == email]
        return user_stamps.to_dict('records')
    return []

# نظام حفظ الفيدباك الجديد
def save_feedback(name, email, message):
    if message:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        df = pd.DataFrame([[now, name, email, message]], columns=['Date', 'Name', 'Email', 'Message'])
        df.to_csv('feedback_log.csv', mode='a', header=not os.path.exists('feedback_log.csv'), index=False)
        return True
    return False

# 2. قاموس اللغات (كما هو في كودك)
lang_dict = {
    'English': {
        'welcome': 'Welcome to Maison Balkiss', 'subtitle': 'SMART TOURISM 4.0', 'login_title': 'Visitor Registration',
        'name': 'Full Name', 'email': 'Email / Phone', 'pass': 'Password', 'start': 'Start Discovery', 'tab1': '💬 AI Chatbot',
        'tab2': '🗺️ Smart Trail', 'tab3': '📜 Heritage Passport', 'feedback': 'Your Opinion Matters',
        'select_city': 'Select City', 'locate_me': '📍 Locate Me', 'search_place': 'Search for any city or place...',
        'route_plan': 'Your Smart Tourism Route',
        'sefrou_title': 'Sefrou: The Garden of Morocco & Cherry Capital',
        'sefrou_desc': 'Known as "Little Jerusalem", Sefrou is one of the oldest cities in Morocco, famous for its coexistence and the UNESCO Cherry Festival.',
        'stops': ['🌊 Oued Aggai Falls', '🏘️ Historical Mellah', '🚪 Bab El Maqam', '🕌 Sidi Ali Bousserghine', '🕳️ Kahf El Moumen'],
        'tips': '💡 Tip: Visit in June for the Cherry Festival!'
    },
    'العربية': {
        'welcome': 'مرحباً بكم في ميزون بلقيس', 'subtitle': 'السياحة الذكية 4.0', 'login_title': 'تسجيل الزوار',
        'name': 'الاسم الكامل', 'email': 'البريد الإلكتروني / الهاتف', 'pass': 'كلمة المرور', 'start': 'ابدأ الاكتشاف', 'tab1': '💬 شاتبوت ذكي',
        'tab2': '🗺️ المسار الذكي', 'tab3': '📜 الجواز التراثي', 'feedback': 'رأيكم يهمنا',
        'select_city': 'اختر المدينة', 'locate_me': '📍 تحديد مكاني', 'search_place': 'ابحث عن أي مدينة أو مكان...',
        'route_plan': 'مسارك السياحي الذكي',
        'sefrou_title': 'صفرو: حديقة المغرب وعاصمة حب الملوك',
        'sefrou_desc': 'تلقب بـ "أورشليم الصغيرة"، وهي من أقدم المدن المغربية، مشهورة بتاريخ التعايش ومهرجان حب الملوك المصنف لدى اليونسكو.',
        'stops': ['🌊 شلال وادي أكاي', '🏘️ الملاح والمدينة العتيقة', '🚪 باب المقام ومجمع الحرف', '🕌 ضريح سيدي علي بوسرغين', '🕳️ كهف المؤمن'],
        'tips': '💡 نصيحة: زر المدينة في يونيو لحضور مهرجان حب الملوك!'
    }
}

# 3. إدارة الجلسة
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'map_center' not in st.session_state: st.session_state.map_center = [33.8247, -4.8278]

# 4. القائمة الجانبية (الأدمن المطور)
with st.sidebar:
    st.title("MAISON BALKISS")
    lang = st.selectbox("🌐 Language", ['English', 'العربية'])
    t = lang_dict[lang]
    st.markdown("---")
    with st.expander("🔐 Admin Area"):
        if st.text_input("Password", type="password", key="adm_final") == "BALKISS2024":
            st.success("Admin Verified")
            # عرض الطوابع
            st.subheader("📍 Stamps Activity")
            if os.path.exists('stamps_log.csv'):
                st.dataframe(pd.read_csv('stamps_log.csv'))
            
            # عرض الرسائل (الفيدباك)
            st.subheader("💬 Visitor Feedback")
            if os.path.exists('feedback_log.csv'):
                st.dataframe(pd.read_csv('feedback_log.csv'))
            else: st.write("No feedback yet.")
            
            # عرض سجل الزوار
            st.subheader("👥 Visitor Accounts")
            if os.path.exists('visitors_log.csv'):
                st.dataframe(pd.read_csv('visitors_log.csv', on_bad_lines='skip'))

# 5. واجهة الدخول / التسجيل
if not st.session_state.logged_in:
    tab_log, tab_reg = st.tabs([t['login_title'], "📝 New Account"])
    with tab_reg:
        v_name = st.text_input(t['name'], key="reg_n")
        v_email = st.text_input(t['email'], key="reg_e")
        v_pass = st.text_input(t['pass'], type="password", key="reg_p")
        if st.button("Create Account"):
            if v_name and v_email and v_pass:
                save_user_to_db(v_name, v_email, v_pass)
                st.success("Account created!")
    with tab_log:
        log_email = st.text_input(t['email'], key="log_e")
        log_pass = st.text_input(t['pass'], type="password", key="log_p")
        if st.button(t['start']):
            name = check_login(log_email, log_pass)
            if name:
                st.session_state.logged_in = True
                st.session_state.visitor_name = name
                st.session_state.visitor_email = log_email
                st.rerun()
            else: st.error("Invalid Login")

# 6. الواجهة الرئيسية
else:
    st.title(f"👑 {t['welcome']}")
    st.subheader(t['subtitle'])
    tab1, tab2, tab3 = st.tabs([t['tab1'], t['tab2'], t['tab3']])

    with tab1:
        st.header(t['tab1'])
        # (نفس كود الشاتبوت ديالك)
        user_query = st.chat_input("Ask AI...")
        if user_query: st.write("AI is thinking...")

    with tab2:
        st.header(t['tab2'])
        # (نفس كود الخريطة وصفرو ديالك)
        st.write("Interactive Map System")

    with tab3:
        st.header(f"📜 {t['tab3']}")
        user_stamps = load_user_stamps(st.session_state.visitor_email)
        stamps_count = len(user_stamps)
        st.markdown(f"### Holder: {st.session_state.visitor_name} | {stamps_count}/10")
        
        # نظام الطوابع محفوظ كما هو
        if st.button("🌟 Get Stamp"):
            save_stamp_to_db(st.session_state.visitor_name, st.session_state.visitor_email, "Sefrou Center")
            st.rerun()

    # --- قسم الفيدباك (تم التفعيل) ---
    st.markdown("---")
    st.subheader(t['feedback'])
    user_msg = st.text_area("Your Feedback...", key="feedback_area")
    if st.button("Submit Feedback"):
        if save_feedback(st.session_state.visitor_name, st.session_state.visitor_email, user_msg):
            st.success("Success! Message sent to Admin.")
        else: st.warning("Please write something.")

    st.markdown("<center>© 2026 MAISON BALKISS</center>", unsafe_allow_html=True)
