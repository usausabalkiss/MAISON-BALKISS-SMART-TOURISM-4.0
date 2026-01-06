from streamlit_js_eval import streamlit_js_eval
import streamlit as st
import pandas as pd
import os
from datetime import datetime
import requests
import folium 
from streamlit_folium import st_folium 

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
    new_data = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d %H:%M"), name, email, str(password)]], 
                            columns=['Date', 'Name', 'Email', 'Password'])
    new_data.to_csv('visitors_log.csv', mode='a', header=not os.path.exists('visitors_log.csv'), index=False)

def check_login(email, password):
    if os.path.exists('visitors_log.csv'):
        df = pd.read_csv('visitors_log.csv')
        user = df[(df['Email'].astype(str) == str(email)) & (df['Password'].astype(str) == str(password))]
        if not user.empty: return user.iloc[0]['Name']
    return None

def save_stamp_to_db(name, email, place):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    df = pd.DataFrame([[name, email, place, now]], columns=['Name', 'Email', 'Place', 'Date'])
    df.to_csv('stamps_log.csv', mode='a', header=not os.path.exists('stamps_log.csv'), index=False)

def load_user_stamps(email):
    if os.path.exists('stamps_log.csv'):
        df = pd.read_csv('stamps_log.csv')
        user_stamps = df[df['Email'].astype(str) == str(email)]
        return user_stamps.to_dict('records')
    return []

# 2. قاموس اللغات
lang_dict = {
    'English': {
        'welcome': 'Welcome to Maison Balkiss', 'subtitle': 'SMART TOURISM 4.0', 'login_title': 'Visitor Registration',
        'name': 'Full Name', 'email': 'Email / Phone', 'pass': 'Password', 'start': 'Start Discovery', 
        'tab1': '💬 Heritage Hubs', 'tab2': '🗺️ Smart Trail', 'tab3': '📜 Heritage Passport',
        'gps_btn': '🛰️ Claim Local Stamp', 'gps_wait': 'Locating you...'
    },
    'العربية': {
        'welcome': 'مرحباً بكم في ميزون بلقيس', 'subtitle': 'السياحة الذكية 4.0', 'login_title': 'تسجيل الزوار',
        'name': 'الاسم الكامل', 'email': 'البريد الإلكتروني / الهاتف', 'pass': 'كلمة المرور', 'start': 'ابدأ الاكتشاف', 
        'tab1': '💬 الأقطاب التراثية', 'tab2': '🗺️ المسار الذكي', 'tab3': '📜 الجواز التراثي',
        'gps_btn': '🛰️ أحصل على ختم الموقع', 'gps_wait': 'جاري تحديد موقعك...'
    }
}

# 3. إدارة الجلسة
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# 4. القائمة الجانبية
with st.sidebar:
    st.title("MAISON BALKISS")
    lang = st.selectbox("🌐 Language", ['English', 'العربية'])
    t = lang_dict[lang]
    st.markdown("---")
    with st.expander("🔐 Admin"):
        if st.text_input("Password", type="password") == "BALKISS2024":
            if os.path.exists('stamps_log.csv'): st.dataframe(pd.read_csv('stamps_log.csv'))

# 5. واجهة الدخول
if not st.session_state.logged_in:
    tab_log, tab_reg = st.tabs([t['login_title'], "New Account"])
    with tab_reg:
        v_name = st.text_input(t['name'], key="reg_n")
        v_email = st.text_input(t['email'], key="reg_e")
        v_pass = st.text_input(t['pass'], type="password", key="reg_p")
        if st.button("Register"):
            save_user_to_db(v_name, v_email, v_pass)
            st.success("Account created!")
    with tab_log:
        log_e = st.text_input(t['email'], key="log_e")
        log_p = st.text_input(t['pass'], type="password", key="log_p")
        if st.button(t['start']):
            name = check_login(log_e, log_p)
            if name:
                st.session_state.logged_in, st.session_state.visitor_name, st.session_state.visitor_email = True, name, log_e
                st.rerun()

# 6. الواجهة الرئيسية
else:
    st.title(f"👑 {t['welcome']}")
    tab1, tab2, tab3 = st.tabs([t['tab1'], t['tab2'], t['tab3']])

    with tab1:
        # --- كود الأقطاب المغربية (North, Center, South, Desert, Coast) ---
        hubs_data = {
            "North": {"en": "Mediterranean Soul", "ar": "روح المتوسط", "img": "https://images.unsplash.com/photo-1548013146-72479768bbaa?w=800"},
            "Center": {"en": "Spiritual Heartland", "ar": "القلب الروحاني", "img": "https://images.unsplash.com/photo-1549944850-84e00be4203b?w=800"},
            "South": {"en": "Red Oasis", "ar": "واحة البهجة", "img": "https://images.unsplash.com/photo-1597212618440-806262de496b?w=800"},
            "Desert": {"en": "Golden Sahara", "ar": "الصحراء الذهبية", "img": "https://images.unsplash.com/photo-1505051508008-923feaf90180?w=800"},
            "Coast": {"en": "Atlantic Breeze", "ar": "نسيم المحيط", "img": "https://images.unsplash.com/photo-1539129790410-d0124747b290?w=800"}
        }
        cols = st.columns(5)
        if 'active_hub' not in st.session_state: st.session_state.active_hub = "Center"
        for i, k in enumerate(hubs_data.keys()):
            if cols[i].button(hubs_data[k][('en' if lang == 'English' else 'ar')], key=f"h_{k}"):
                st.session_state.active_hub = k
        st.image(hubs_data[st.session_state.active_hub]['img'], use_container_width=True)

    with tab2:
        st.header(t['tab2'])
        if os.path.exists('landmarks_data.csv'):
            df_geo = pd.read_csv('landmarks_data.csv')
            sel_city = st.selectbox("Select City", df_geo['City'].unique())
            city_info = df_geo[df_geo['City'] == sel_city].iloc[0]
            m = folium.Map(location=[city_info['Lat'], city_info['Lon']], zoom_start=12)
            folium.Marker([city_info['Lat'], city_info['Lon']], popup=city_info['Place']).add_to(m)
            st_folium(m, width=800, height=450, key="map")

    with tab3:
        # --- حلينا فضيحة صفرو والتكرار هنا ---
        st.header(t['tab3'])
        
        # كارت الجواز
        user_stamps = load_user_stamps(st.session_state.visitor_email)
        st.markdown(f"""
            <div style="border: 3px double #D4AF37; padding: 20px; border-radius: 15px; background: #111; text-align: center;">
                <h2 style="color: #D4AF37;">HERITAGE AMBASSADOR PASSPORT</h2>
                <p style="color: white;">Holder: {st.session_state.visitor_name} | Stamps: {len(user_stamps)}</p>
            </div>
        """, unsafe_allow_html=True)

        st.divider()
        
        # نظام تحديد الموقع الذكي: لا كود، لا صفرو مفروضة
        st.subheader("📍 Verify Your Current Location")
        if st.button(t['gps_btn']):
            loc = streamlit_js_eval(js_expressions="window.navigator.geolocation.getCurrentPosition(pos => { return pos.coords })", key="gps_p")
            if loc:
                u_lat, u_lon = loc['latitude'], loc['longitude']
                # سؤل الخريطة عن اسم المدينة
                try:
                    res = requests.get(f"https://nominatim.openstreetmap.org/reverse?lat={u_lat}&lon={u_lon}&format=json", headers={'User-Agent': 'BalkissApp/1.0'}).json()
                    current_city = res.get('address', {}).get('city') or res.get('address', {}).get('town') or "Morocco Landmark"
                except: current_city = "Morocco Explorer"
                
                # إضافة الطابع بناءً على الموقع الفعلي
                save_stamp_to_db(st.session_state.visitor_name, st.session_state.visitor_email, current_city)
                st.success(f"Verified! Stamp for {current_city} added.")
                st.balloons()
                st.rerun()

        # عرض الطوابع الحقيقية فقط
        st.subheader("🏺 Collected Stamps")
        if user_stamps:
            cols = st.columns(2)
            for i, visit in enumerate(reversed(user_stamps)):
                with cols[i % 2]:
                    st.markdown(f'''
                        <div style="background-color: #fdf5e6; padding: 10px; border: 2px dashed #b8860b; color: black; border-radius: 5px; margin-bottom: 10px;">
                            <h4 style="margin:0;">📮 {visit['Place']}</h4>
                            <p style="font-size: 11px; margin:0;"><b>DATE:</b> {visit['Date']}</p>
                        </div>
                    ''', unsafe_allow_html=True)
        else: st.info("Passport empty. Verify location to get stamps.")

st.markdown("<center>© 2026 MAISON BALKISS - Smart Tourism 4.0</center>", unsafe_allow_html=True)
