import streamlit as st
import pandas as pd
import os
from datetime import datetime
import requests
import folium 
from streamlit_folium import st_folium 
from geopy.geocoders import Nominatim 
from streamlit_gsheets import GSheetsConnection

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

# --- الربط مع Google Sheets (طريقة آمنة) ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except:
    st.error("Please configure Google Sheets Secrets.")

# --- وظائف قاعدة البيانات المحلية ---
def save_user_to_db(name, email, password):
    df = pd.DataFrame([[datetime.now(), name, email, password]], columns=['Date', 'Name', 'Email', 'Password'])
    df.to_csv('visitors_log.csv', mode='a', header=not os.path.exists('visitors_log.csv'), index=False)

def check_login(email, password):
    if os.path.exists('visitors_log.csv'):
        df = pd.read_csv('visitors_log.csv', on_bad_lines='skip')
        user = df[df['Email'] == email]
        if not user.empty:
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

# 4. القائمة الجانبية
with st.sidebar:
    st.title("MAISON BALKISS")
    lang = st.selectbox("🌐 Language", ['English', 'العربية'])
    t = lang_dict[lang]
    st.markdown("---")
    with st.expander("🔐 Admin Area"):
        if st.text_input("Password", type="password", key="admin_key") == "BALKISS2024":
            st.success("Admin Verified")
            if os.path.exists('visitors_log.csv'):
                st.subheader("👥 Visitors")
                st.dataframe(pd.read_csv('visitors_log.csv', on_bad_lines='skip'))

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
        # استخدام سيكريت للـ API Key بدلا من وضعه في الكود
        gemini_api = st.secrets.get("GEMINI_API_KEY", "")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_api}"
        user_query = st.chat_input("Ask Maison Balkiss AI...")
        if user_query:
            payload = {"contents": [{"parts": [{"text": f"You are a professional Moroccan Virtual Guide for Maison Balkiss. Answer in {lang}: {user_query}"}]}]}
            try:
                response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=15)
                res_json = response.json()
                answer = res_json['candidates'][0]['content']['parts'][0]['text'] if 'candidates' in res_json else "Guide is busy, try again!"
                st.session_state.chat_history.append({"u": user_query, "a": answer})
            except:
                st.error("AI is temporarily offline.")
        for chat in reversed(st.session_state.chat_history):
            st.markdown(f"**👤 You:** {chat['u']}\n\n**🏛️ Maison Balkiss:** {chat['a']}\n---")

    with tab2:
        st.header(t['tab2'])
        if os.path.exists('landmarks_data.csv'):
            df_geo = pd.read_csv('landmarks_data.csv')
            c1, c2 = st.columns(2)
            with c1:
                sel_reg = st.selectbox("📍 الجهة", [""] + sorted(df_geo['Region'].unique().tolist()))
            if sel_reg:
                with c2:
                    cities = sorted(df_geo[df_geo['Region'] == sel_reg]['City'].unique().tolist())
                    sel_city = st.selectbox("🏙️ المدينة", [""] + cities)
                if sel_city:
                    city_info = df_geo[df_geo['City'] == sel_city].iloc[0]
                    st.info(f"✨ {city_info['Description']}")
                    m = folium.Map(location=[city_info['Lat'], city_info['Lon']], zoom_start=12)
                    folium.Marker([city_info['Lat'], city_info['Lon']], popup=city_info['Place']).add_to(m)
                    st_folium(m, width=700, height=450, key="map_"+sel_city)
        else: st.warning("⚠️ Data file missing!")

    with tab3:
        st.header(f"📜 {t['tab3']}")
        user_stamps = load_user_stamps(st.session_state.visitor_email)
        stamps_count = len(user_stamps)
        st.markdown(f"""
            <div style="border: 3px double #D4AF37; padding: 25px; border-radius: 15px; background: #111; text-align: center;">
                <h2 style="color: #D4AF37;">HERITAGE AMBASSADOR PASSPORT</h2>
                <p style="color: white;">HOLDER: {st.session_state.visitor_name} | STAMPS: {stamps_count}/10</p>
            </div>
        """, unsafe_allow_html=True)

        st.subheader("🌟 Exclusive Eco-Travel Services")
        with st.expander("Get your Personalized Green Itinerary (15€)"):
            with st.form("purchase_form"):
                cust_name = st.text_input("Full Name", value=st.session_state.visitor_name)
                cust_email = st.text_input("Email", value=st.session_state.visitor_email)
                submit_order = st.form_submit_button("Confirm & Pay via WhatsApp 💬")
                
                if submit_order:
                    order_data = pd.DataFrame([{
                        "Timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Guest Name": cust_name, "City": cust_email,
                        "Passport Type": "PURCHASE: Green Itinerary", "Notes": "Pending"
                    }])
                    try:
                        existing_data = conn.read()
                        updated_df = pd.concat([existing_data, order_data], ignore_index=True)
                        conn.update(data=updated_df)
                        wa_url = f"https://wa.me/212667920412?text=I%20ordered%20the%20Green%20Itinerary"
                        st.markdown(f'<meta http-equiv="refresh" content="0;url={wa_url}">', unsafe_allow_html=True)
                    except: st.error("Check your internet or Secrets.")

    st.markdown("---")
    st.markdown("<center>© 2026 MAISON BALKISS - Smart Tourism 4.0</center>", unsafe_allow_html=True)
