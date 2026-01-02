import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import folium 
from streamlit_folium import st_folium 
from geopy.geocoders import Nominatim 

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
        'welcome': 'Welcome to Maison Balkiss', 'subtitle': 'SMART TOURISM 4.0', 'login_title': 'Visitor Registration',
        'name': 'Full Name', 'email': 'Email / Phone', 'start': 'Start Discovery', 'tab1': '💬 AI Chatbot',
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
        'name': 'الاسم الكامل', 'email': 'البريد الإلكتروني / الهاتف', 'start': 'ابدأ الاكتشاف', 'tab1': '💬 شاتبوت ذكي',
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

# 4. القائمة الجانبية
with st.sidebar:
    st.title("MAISON BALKISS")
    lang = st.selectbox("🌐 Language", ['English', 'العربية'])
    t = lang_dict[lang]
    st.markdown("---")
    with st.expander("🔐 Admin Area"):
        if st.text_input("Password", type="password") == "BALKISS2024":
            st.success("Admin Verified")
            try: st.dataframe(pd.read_csv('visitors_log.csv', names=['Date', 'Name', 'Contact', 'Lang']))
            except: st.write("No logs yet.")

# 5. واجهة الدخول
if not st.session_state.logged_in:
    st.header(f"🏛️ {t['login_title']}")
    v_name = st.text_input(t['name'])
    v_contact = st.text_input(t['email'])
    if st.button(t['start']):
        if v_name and v_contact:
            with open('visitors_log.csv', 'a') as f: f.write(f"{datetime.now()},{v_name},{v_contact},{lang}\n")
            st.session_state.logged_in = True
            st.rerun()
        else: st.warning("Please fill your details.")

# 6. الواجهة الرئيسية
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
                answer = res_json['candidates'][0]['content']['parts'][0]['text'] if 'candidates' in res_json else "Welcome! I am your Maison Balkiss guide."
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
                for stop in t['stops']:
                    st.markdown(f"* {stop}")
            with c2:
                st.info(t['tips'])
                st.markdown("🍽️ **Local Flavors:** Don't miss the *Sefroui Harira* and local olives in the artisan district.")

    with tab3:
        st.header(f"📜 {t['tab3']}")
        
        # تصميم الجواز التراثي
        st.markdown(f"""
            <div style="border: 2px solid #D4AF37; padding: 20px; border-radius: 15px; background-color: #111111;">
                <h2 style="text-align: center; color: #D4AF37;">HERITAGE PASSPORT</h2>
                <p style="text-align: center; color: #D4AF37; font-style: italic;">Maison Balkiss - Sefrou Edition</p>
                <hr style="border-color: #D4AF37;">
                <div style="display: flex; justify-content: space-around; text-align: center;">
                    <div>
                        <h4 style="color: #D4AF37;">Visitor</h4>
                        <p style="color: white;">{v_name if 'v_name' in locals() else "Guest"}</p>
                    </div>
                    <div>
                        <h4 style="color: #D4AF37;">Status</h4>
                        <p style="color: #D4AF37; font-weight: bold;">Explorer 🛡️</p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.write("")
        st.subheader("Your Collected Stamps / طوابعك التراثية")
        
        col_s1, col_s2, col_s3 = st.columns(3)
        
        with col_s1:
            st.markdown("""
                <div style="text-align: center; opacity: 1.0;">
                    <div style="font-size: 50px;">🌊</div>
                    <p style="color: #D4AF37; font-weight: bold;">Sefrou Falls</p>
                    <span style="color: green;">✓ Collected</span>
                </div>
            """, unsafe_allow_html=True)

        with col_s2:
            st.markdown("""
                <div style="text-align: center; opacity: 0.3;">
                    <div style="font-size: 50px;">🧵</div>
                    <p style="color: #D4AF37; font-weight: bold;">Dar El Ghezl</p>
                    <span style="color: grey;">Locked</span>
                </div>
            """, unsafe_allow_html=True)

        with col_s3:
            st.markdown("""
                <div style="text-align: center; opacity: 0.3;">
                    <div style="font-size: 50px;">🍒</div>
                    <p style="color: #D4AF37; font-weight: bold;">Cherry Fest</p>
                    <span style="color: grey;">Locked</span>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        if st.button("📸 Scan QR at Location to Collect Stamp"):
            st.success("Feature coming soon: This will open your camera to scan QR codes at Dar El Ghezl, The Waterfall, etc.")

    # نهاية قسم الواجهة الرئيسية
    st.markdown("---")
    st.subheader(t['feedback'])
    st.text_area("Your Feedback...")
    st.button("Submit Feedback")
    st.markdown("<center>© 2026 MAISON BALKISS - Smart Tourism 4.0</center>", unsafe_allow_html=True)
