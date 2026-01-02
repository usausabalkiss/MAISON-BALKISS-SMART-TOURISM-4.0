import streamlit as st
import pandas as pd
import os
from datetime import datetime
import requests
import folium 
from streamlit_folium import st_folium 
from geopy.geocoders import Nominatim 

# 1. إعدادات الصفحة والهوية البصرية (محفوظة حرفياً)
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

# --- وظائف قاعدة البيانات ---
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

# وظيفة الفيدباك الجديدة (حفظ صامت في الخلفية)
def save_feedback(name, email, message):
    if message:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        df = pd.DataFrame([[now, name, email, message]], columns=['Date', 'Name', 'Email', 'Message'])
        df.to_csv('feedback_log.csv', mode='a', header=not os.path.exists('feedback_log.csv'), index=False)
        return True
    return False

# 2. قاموس اللغات (محفوظ كما هو)
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

# 4. القائمة الجانبية (الأدمن مصلح لعرض كل الملفات)
with st.sidebar:
    st.title("MAISON BALKISS")
    lang = st.selectbox("🌐 Language", ['English', 'العربية'])
    t = lang_dict[lang]
    st.markdown("---")
    with st.expander("🔐 Admin Area"):
        if st.text_input("Password", type="password", key="adm_final") == "BALKISS2024":
            st.success("Admin Verified")
            if os.path.exists('stamps_log.csv'):
                st.subheader("📍 Stamps Activity")
                st.dataframe(pd.read_csv('stamps_log.csv'))
            if os.path.exists('feedback_log.csv'):
                st.subheader("💬 Feedback")
                st.dataframe(pd.read_csv('feedback_log.csv'))
            if os.path.exists('visitors_log.csv'):
                st.subheader("👥 Visitors")
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

# 6. الواجهة الرئيسية (هنا فين رجعت ليك كل مجهودك الأصلي)
else:
    st.title(f"👑 {t['welcome']}")
    st.subheader(t['subtitle'])
    tab1, tab2, tab3 = st.tabs([t['tab1'], t['tab2'], t['tab3']])

    with tab1:
        st.header(t['tab1'])
        api_key = "AIzaSyBN9cmExKPo5Mn9UAtvdYKohgODPf8hwbA"
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
        user_query = st.chat_input("Ask Maison Balkiss AI...")
        if user_query:
            prompt = f"You are a professional Moroccan Virtual Guide for Maison Balkiss. Promote tourism in Sefrou, Figuig, Tangier. Answer in {lang}: {user_query}"
            try:
                response = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, headers={"Content-Type": "application/json"}, timeout=15)
                res_json = response.json()
                answer = res_json['candidates'][0]['content']['parts'][0]['text'] if 'candidates' in res_json else "Welcome!"
                st.session_state.chat_history.append({"u": user_query, "a": answer})
            except: st.error("Offline Mode")
        for chat in reversed(st.session_state.chat_history):
            st.markdown(f"**👤 You:** {chat['u']}\n\n**🏛️ Maison Balkiss:** {chat['a']}\n---")

    with tab2:
        st.header(t['tab2'])
        col1, col2 = st.columns([2, 1])
        with col1:
            selected_city = st.selectbox(t['select_city'], ["", "Sefrou (صفرو)", "Figuig (فكيك)", "Tangier (طنجة)"])
        with col2:
            if st.button(t['locate_me']):
                st.session_state.map_center = [33.8247, -4.8278]
                st.rerun()

        search_q = st.text_input(t['search_place'])

        if search_q:
            try:
                geolocator = Nominatim(user_agent="balkiss_app_v4")
                location = geolocator.geocode(search_q)
                if location: st.session_state.map_center = [location.latitude, location.longitude]
            except: st.warning("Showing last known location.")
        elif selected_city:
            city_coords = {"Sefrou (صفرو)": [33.8247, -4.8278], "Figuig (فكيك)": [32.1083, -1.2283], "Tangier (طنجة)": [35.7595, -5.8340]}
            st.session_state.map_center = city_coords.get(selected_city, st.session_state.map_center)

        m = folium.Map(location=st.session_state.map_center, zoom_start=14, tiles='OpenStreetMap')
        
        # رجعت ليك كاع الماركرز اللي كنتي دايرة في صفرو
        is_sefrou = "Sefrou" in (search_q or selected_city) or "صفرو" in (search_q or selected_city)
        if is_sefrou:
            folium.Marker([33.8280, -4.8521], popup="Oued Aggai Waterfalls", icon=folium.Icon(color='red', icon='star')).add_to(m)
            folium.Marker([33.8210, -4.8250], popup="Historical Mellah", icon=folium.Icon(color='red', icon='info-sign')).add_to(m)
            folium.Marker([33.8300, -4.8320], popup="Bab El Maqam Square", icon=folium.Icon(color='red', icon='camera')).add_to(m)
            folium.Marker([33.8323, -4.8268], popup="Flame & Fork", icon=folium.Icon(color='green', icon='cutlery')).add_to(m)
            folium.Marker([33.8315, -4.8260], popup="Restaurant Es-saqia", icon=folium.Icon(color='green', icon='cutlery')).add_to(m)
            folium.Marker([33.7873, -4.8207], popup="Al Iklil Cooperative", icon=folium.Icon(color='blue', icon='leaf')).add_to(m)
            folium.Marker([33.8340, -4.8280], popup="Artisan Cooperative Sefrou", icon=folium.Icon(color='blue', icon='wrench')).add_to(m)
        elif search_q:
            folium.Marker(st.session_state.map_center, popup=search_q, icon=folium.Icon(color='gold')).add_to(m)

        st_folium(m, width=900, height=450, key="main_map")

        if is_sefrou:
            st.markdown(f"## 🍒 {t['sefrou_title']}")
            st.write(t['sefrou_desc'])
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"### 📍 {t['route_plan']}")
                for stop in t['stops']: st.markdown(f"* {stop}")
            with c2:
                st.info(t['tips'])
                st.markdown("🍽️ **Local Flavors:** Don't miss the *Sefroui Harira* and local olives.")

    with tab3:
        st.header(f"📜 {t['tab3']}")
        user_stamps = load_user_stamps(st.session_state.visitor_email)
        stamps_count = len(user_stamps)

        # رجعت ليك التصميم الكامل ديال الباسبور والكاشي
        st.markdown(f"""
            <div style="border: 3px double #D4AF37; padding: 25px; border-radius: 15px; background: linear-gradient(145deg, #111, #000); text-align: center;">
                <h2 style="color: #D4AF37; margin-bottom: 5px;">HERITAGE AMBASSADOR PASSPORT</h2>
                <p style="color: #D4AF37; font-style: italic;">جواز سفر سفير التراث</p>
                <hr style="border-color: #D4AF37;">
                <div style="display: flex; justify-content: space-around; margin-top: 20px;">
                    <div><p style="color: #D4AF37; font-size: 12px;">HOLDER</p><h3 style="color: white;">{st.session_state.visitor_name}</h3></div>
                    <div><p style="color: #D4AF37; font-size: 12px;">STAMPS</p><h3 style="color: white;">{stamps_count} / 10</h3></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.progress(min(stamps_count / 10, 1.0))
        st.subheader("📸 Collect New Stamp")
        loc_to_scan = st.selectbox("Current Location:", ["Dar El Ghezl", "Bab El Maqam", "The Mellah", "Oued Aggai Falls"])
        qr_verify = st.text_input("Verification Code", placeholder="Code from QR", key="qr_v_input")
        
        if st.button("🌟 Verify & Stamp"):
            if qr_verify == "1234":
                save_stamp_to_db(st.session_state.visitor_name, st.session_state.visitor_email, loc_to_scan)
                st.success("Verified! Stamp added.")
                st.rerun()

        # رجعت ليك الكاشي الأثري (Stamp Design)
        st.markdown("---")
        st.subheader("🏺 Your Digital Heritage Stamps")
        cols = st.columns(2)
        for i, visit in enumerate(reversed(user_stamps)):
            with cols[i % 2]:
                st.markdown(f'''
                    <div style="background-color: #fdf5e6; padding: 15px; border: 3px dashed #b8860b; border-radius: 2px; margin-bottom: 20px; position: relative; color: black; box-shadow: 5px 5px 15px rgba(0,0,0,0.3); font-family: 'Courier New', Courier, monospace; min-height: 180px;">
                        <div style="border: 1px solid #d2b48c; padding: 10px;">
                            <span style="float: right; color: #b8860b; font-weight: bold; font-size: 18px;">10<br><small>DH</small></span>
                            <h3 style="margin:0; color: #333; text-transform: uppercase;">{visit['Place']}</h3>
                            <p style="font-size: 10px; color: #8b4513; margin: 5px 0; font-weight: bold;">ROYAUME DU MAROC - HERITAGE</p>
                            <hr style="border-top: 1px solid #d2b48c; margin: 10px 0;">
                            <p style="font-size: 13px; color: #000; margin: 5px 0;"><b>HOLDER:</b> {visit['Name']}</p>
                            <p style="font-size: 11px; color: #000; margin: 0;"><b>DATE:</b> {visit['Date']}</p>
                        </div>
                        <div style="position: absolute; bottom: 10px; right: 10px; width: 85px; height: 85px; border: 4px double rgba(139, 0, 0, 0.7); border-radius: 50%; display: flex; flex-direction: column; align-items: center; justify-content: center; transform: rotate(-15deg); background: rgba(255, 255, 255, 0.1);">
                            <div style="border: 1px solid rgba
