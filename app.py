import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import folium # مكتبة الخرائط الاحترافية
from streamlit_folium import st_folium # لربط الخريطة بـ Streamlit
from geopy.geocoders import Nominatim # الخدمة اللي غتخلي البحث يخدم لأي مدينة

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
        'feedback': 'Your Opinion Matters',
        'select_city': 'Select City',
        'locate_me': '📍 Locate Me',
        'search_place': 'Search for a specific place (e.g. Agadir)...',
        'route_plan': 'Your Smart Tourism Route'
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
        'feedback': 'رأيكم يهمنا',
        'select_city': 'اختر المدينة',
        'locate_me': '📍 تحديد مكاني',
        'search_place': 'ابحث عن مكان محدد (مثلاً: أكادير)...',
        'route_plan': 'مسارك السياحي الذكي'
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
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"

        user_query = st.chat_input("Ask Maison Balkiss AI...")
        if user_query:
            prompt = f"You are a professional Moroccan Virtual Guide for Maison Balkiss. Promote tourism in Sefrou, Figuig, Tangier. Answer in {lang}: {user_query}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            headers = {"Content-Type": "application/json"}
            
            try:
                with st.spinner('Maison Balkiss is thinking...'):
                    response = requests.post(url, json=payload, headers=headers, timeout=15)
                    res_json = response.json()
                    
                    if 'candidates' in res_json:
                        answer = res_json['candidates'][0]['content']['parts'][0]['text']
                    else:
                        q_low = user_query.lower()
                        if any(x in q_low for x in ["sefrou", "صفرو"]):
                            answer = "🍒 **Sefrou:** Known for the Cherry Festival and waterfalls. Visit the ancient Mellah!" if lang=='English' else "🍒 **صفرو:** مدينة حب الملوك! يجب زيارة مهرجانها المصنف ضمن اليونسكو والشلالات الرائعة."
                        elif any(x in q_low for x in ["figuig", "فكيك"]):
                            answer = "🌴 **Figuig:** A majestic oasis with 7 ancient Ksars." if lang=='English' else "🌴 **فكيك:** واحة مهيبة تضم 7 قصور قديمة."
                        else:
                            answer = "I am your Maison Balkiss guide. How can I help you discover Morocco?" if lang=='English' else "أنا مرشد ميزون بلقيس. كيف يمكنني مساعدتك؟"
                    
                    st.session_state.chat_history.append({"u": user_query, "a": answer})
            except:
                st.error("AI connection lost. Using local guide mode.")

        for chat in reversed(st.session_state.chat_history):
            st.markdown(f"**👤 You:** {chat['u']}")
            st.markdown(f"**🏛️ Maison Balkiss:** {chat['a']}")
            st.markdown("---")

    with tab2:
        st.header(t['tab2'])
        
        # خيارات التحكم في التاب 2
        col1, col2 = st.columns([2, 1])
        with col1:
            selected_city = st.selectbox(t['select_city'], ["", "Sefrou (صفرو)", "Figuig (فكيك)", "Tangier (طنجة)"])
        with col2:
            if st.button(t['locate_me']):
                selected_city = "Sefrou (صفرو)" 
                st.info("Location detected: Sefrou")

        search_q = st.text_input(t['search_place'])

        # --- تفعيل محرك البحث الجغرافي ---
        target_coords = [33.8247, -4.8278] # الإحداثيات الافتراضية
        city_coords = {
            "Sefrou (صفرو)": [33.8247, -4.8278],
            "Figuig (فكيك)": [32.1083, -1.2283],
            "Tangier (طنجة)": [35.7595, -5.8340]
        }

        if search_q:
            try:
                geolocator = Nominatim(user_agent="balkiss_app")
                location = geolocator.geocode(search_q)
                if location:
                    target_coords = [location.latitude, location.longitude]
                    st.success(f"📍 {location.address}")
                else:
                    st.warning("Location not found, showing default.")
            except:
                st.error("Search service temporarily unavailable.")
        elif selected_city:
            target_coords = city_coords.get(selected_city, target_coords)

        # عرض الخريطة التفاعلية بناءً على البحث أو الاختيار
        m = folium.Map(location=target_coords, zoom_start=13)
        folium.Marker(target_coords, popup="Current Search", icon=folium.Icon(color='gold')).add_to(m)

        if selected_city or search_q:
            st.subheader(f"🗺️ {t['route_plan']}")
            
            # عرض الخريطة
            st_folium(m, width=900, height=450)
            
            # تفاصيل المسارات للمدن الـ 3 الرئيسية
            if "Sefrou" in (selected_city or search_q) or "صفرو" in (selected_city or search_q):
                st.markdown(f"### 📍 {t['route_plan']}")
                st.markdown("""
                * **Stop 1:** Waterfall Oued Aggai (Natural Heritage)
                * **Stop 2:** Historical Mellah (Cultural Heritage)
                * **Stop 3:** Cherry Cooperative (Local Craft & Economy)
                """)
            elif "Figuig" in (selected_city or search_q) or "فكيك" in (selected_city or search_q):
                st.markdown("""
                * **Stop 1:** Ksar Zenaga (Traditional Architecture)
                * **Stop 2:** Date Palm Oasis (Agriculture Heritage)
                * **Stop 3:** Traditional Irrigation System (Intelligence Heritage)
                """)

    with tab3:
        st.header(t['tab3'])
        st.write("Collect your Heritage Passport stamps here.")

    st.markdown("---")
    st.subheader(t['feedback'])
    st.text_area("Your Feedback...")
    st.button("Submit Feedback")
    st.markdown("<center>© 2026 MAISON BALKISS - Smart Tourism 4.0</center>", unsafe_allow_html=True)
