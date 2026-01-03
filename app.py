import streamlit as st
import pandas as pd
import os
from datetime import datetime
import requests
import folium 
from streamlit_folium import st_folium 
from geopy.geocoders import Nominatim 

# 1. إعدادات الصفحة والهوية البصرية
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
        user = df[df['Email'] == email]
        if not user.empty:
            if 'Password' not in df.columns:
                return user.iloc[0]['Name']
            actual_password = str(user.iloc[0].get('Password', '')).strip()
            if actual_password == "nan" or actual_password == "" or actual_password == str(password):
                return user.iloc[0]['Name']
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

def save_feedback(name, email, message):
    if message:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        df = pd.DataFrame([[now, name, email, message]], columns=['Date', 'Name', 'Email', 'Message'])
        df.to_csv('feedback_log.csv', mode='a', header=not os.path.exists('feedback_log.csv'), index=False)
        return True
    return False

# 2. قاموس اللغات
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

# 4. القائمة الجانبية
with st.sidebar:
    st.title("MAISON BALKISS")
    lang = st.selectbox("🌐 Language", ['English', 'العربية'])
    t = lang_dict[lang]
    st.markdown("---")
    with st.expander("🔐 Admin Area"):
        if st.text_input("Password", type="password", key="admin_key") == "BALKISS2024":
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
            if os.path.exists('visitors_log.csv'):
                df_vis = pd.read_csv('visitors_log.csv')
                st.download_button(
                    label="📥 تحميل قائمة الزوار (CSV)",
                    data=df_vis.to_csv(index=False).encode('utf-8'),
                    file_name='balkiss_visitors.csv',
                    mime='text/csv', )

# 5. واجهة الدخول
if not st.session_state.logged_in:
    tab_log, tab_reg = st.tabs([t['login_title'], "📝 New Account"])
    with tab_reg:
        v_name = st.text_input(t['name'], key="reg_name")
        v_email = st.text_input(t['email'], key="reg_email")
        v_pass = st.text_input(t['pass'], type="password", key="reg_pass")
        if st.button("Create Account"):
            if v_name and v_email and v_pass:
                save_user_to_db(v_name, v_email, v_pass)
                st.success("Account created!")
    with tab_log:
        log_email = st.text_input(t['email'], key="log_email")
        log_pass = st.text_input(t['pass'], type="password", key="log_pass")
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
        api_key = "AIzaSyBN9cmExKPo5Mn9UAtvdYKohgODPf8hwbA"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        user_query = st.chat_input("Ask Maison Balkiss AI...")
        if user_query:
            payload = {"contents": [{"parts": [{"text": f"You are a professional Moroccan Virtual Guide for Maison Balkiss. Answer in {lang}: {user_query}"}]}]}
            try:
                response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=15)
                res_json = response.json()
                if 'candidates' in res_json:
                    answer = res_json['candidates'][0]['content']['parts'][0]['text']
                else:
                    answer = "I'm here to help! Could you please repeat?"
                st.session_state.chat_history.append({"u": user_query, "a": answer})
            except:
                st.error("Offline Mode")
        for chat in reversed(st.session_state.chat_history):
            st.markdown(f"**👤 You:** {chat['u']}\n\n**🏛️ Maison Balkiss:** {chat['a']}\n---")

    with tab2:
        st.header(t['tab2'])
        
        # التأكد من وجود ملف البيانات
        if os.path.exists('landmarks_data.csv'):
            df_geo = pd.read_csv('landmarks_data.csv')
            
            # تقسيم الشاشة لـ 2 أعمدة
            c1, c2 = st.columns(2)
            with c1:
                # اختيار الجهة
                sel_reg = st.selectbox("📍 الجهة", [""] + sorted(df_geo['Region'].unique().tolist()))
            
            if sel_reg:
                with c2:
                    # اختيار المدينة
                    cities = sorted(df_geo[df_geo['Region'] == sel_reg]['City'].unique().tolist())
                    sel_city = st.selectbox("🏙️ المدينة", [""] + cities)
                
                if sel_city:
                    # جلب معلومات المدينة
                    city_info = df_geo[df_geo['City'] == sel_city].iloc[0]
                    st.info(f"✨ {city_info['Description']}")
                    
                    # الخريطة (هادي هي اللي خاصها تكون محاذية للـ if)
                    m = folium.Map(location=[city_info['Lat'], city_info['Lon']], zoom_start=12)
                    folium.Marker([city_info['Lat'], city_info['Lon']], popup=city_info['Place']).add_to(m)
                    st_folium(m, width=900, height=450, key="map_"+sel_city)
        else:
            st.warning("⚠️ ملف landmarks_data.csv مفقود!")

    with tab3:
        st.header(f"📜 {t['tab3']}")
        user_stamps = load_user_stamps(st.session_state.visitor_email)
        stamps_count = len(user_stamps)

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
        c_scan1, c_scan2 = st.columns([2, 1])
        with c_scan1:
            loc_to_scan = st.selectbox("Current Location:", ["Dar El Ghezl", "Bab El Maqam", "The Mellah", "Oued Aggai Falls"])
        with c_scan2:
            qr_verify = st.text_input("Verification Code", placeholder="Code from QR", key="qr_input_code")
        
        if st.button("🌟 Verify & Stamp"):
            if qr_verify == "1234":
                save_stamp_to_db(st.session_state.visitor_name, st.session_state.visitor_email, loc_to_scan)
                st.success(f"Verified! Stamp added for {loc_to_scan}")
                st.rerun()
            else:
                st.error("Invalid Code!")

        st.markdown("---")
        st.subheader("🏺 Your Digital Heritage Stamps")
        cols = st.columns(2)
        for i, visit in enumerate(reversed(user_stamps)):
            with cols[i % 2]:
                st.markdown(f'''
                    <div style="background-color: #fdf5e6; padding: 15px; border: 3px dashed #b8860b; border-radius: 2px; margin-bottom: 20px; position: relative; box-shadow: 5px 5px 15px rgba(0,0,0,0.3); font-family: 'Courier New', Courier, monospace; min-height: 180px;">
                        <div style="border: 1px solid #d2b48c; padding: 10px;">
                            <span style="float: right; color: #b8860b; font-weight: bold; font-size: 18px;">10<br><small>DH</small></span>
                            <h3 style="margin:0; color: #333; text-transform: uppercase;">{visit['Place']}</h3>
                            <p style="font-size: 10px; color: #8b4513; margin: 5px 0; font-weight: bold;">ROYAUME DU MAROC - HERITAGE</p>
                            <hr style="border-top: 1px solid #d2b48c; margin: 10px 0;">
                            <p style="font-size: 13px; color: #000; margin: 5px 0;"><b>HOLDER:</b> {visit['Name']}</p>
                            <p style="font-size: 11px; color: #000; margin: 0;"><b>DATE:</b> {visit['Date']}</p>
                        </div>
                        <div style="position: absolute; bottom: 10px; right: 10px; width: 85px; height: 85px; border: 4px double rgba(139, 0, 0, 0.7); border-radius: 50%; display: flex; flex-direction: column; align-items: center; justify-content: center; transform: rotate(-15deg); background: rgba(255, 255, 255, 0.1);">
                            <div style="border: 1px solid rgba(139, 0, 0, 0.4); border-radius: 50%; width: 70px; height: 70px; display: flex; flex-direction: column; align-items: center; justify-content: center; line-height: 1.1;">
                                <span style="font-size: 6px; color: rgba(139, 0, 0, 0.7); font-weight: bold; margin-bottom: 2px;">★ ★ ★</span>
                                <span style="font-size: 10px; color: rgba(139, 0, 0, 0.8); font-weight: 900; text-align: center;">MAISON<br>BALKISS</span>
                                <span style="font-size: 6px; color: rgba(139, 0, 0, 0.7); font-weight: bold; margin-top: 2px;">OFFICIAL</span>
                            </div>
                        </div>
                    </div>
                ''', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader(t['feedback'])
    user_msg = st.text_area("Your Feedback...", key="feedback_area_unique")
    if st.button("Submit Feedback"):
        if save_feedback(st.session_state.visitor_name, st.session_state.visitor_email, user_msg):
            st.success("Success! Feedback recorded.")
# --- تزيديه فآخر الملف ---
st.write("---") # خط فاصل
st.markdown(f'''
    <div style="background-color: #ffffff; padding: 25px; border-radius: 15px; border: 2px solid #e0e0e0; text-align: center; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
        <h2 style="color: #2e7d32;">🌟 Exclusive Eco-Travel Services</h2>
        <p style="font-size: 18px; color: #555;">Support Maison Balkiss and get your Personalized Green Itinerary!</p>
        <p style="font-weight: bold; font-size: 20px;">Price: 15€</p>
        <br>
        <a href="https://wa.me/2126XXXXXXXX?text=Hello%20Maison%20Balkiss,%20I%20want%20to%20order%20my%20Eco-Travel%20Plan" 
           target="_blank" 
           style="background-color: #25D366; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block; font-size: 18px;">
           Order Now via WhatsApp 💬
        </a>
        <p style="margin-top: 15px; font-size: 12px; color: #888;">Payments via PayPal or Bank Transfer</p>
    </div>
''', unsafe_allow_html=True)
    st.markdown("<center>© 2026 MAISON BALKISS - Smart Tourism 4.0</center>", unsafe_allow_html=True)
