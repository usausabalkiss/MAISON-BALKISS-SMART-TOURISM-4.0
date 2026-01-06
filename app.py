from streamlit_js_eval import streamlit_js_eval
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

# --- وظائف قاعدة البيانات المحلية ---
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

def save_feedback(name, email, message):
    if message:
        df = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d %H:%M"), name, email, message]], columns=['Date', 'Name', 'Email', 'Message'])
        df.to_csv('feedback_log.csv', mode='a', header=not os.path.exists('feedback_log.csv'), index=False)
        return True
    return False

# 2. قاموس اللغات (تم تبديل سمية التاب 1)
lang_dict = {
    'English': {
        'welcome': 'Welcome to Maison Balkiss', 'subtitle': 'SMART TOURISM 4.0', 'login_title': 'Visitor Registration',
        'name': 'Full Name', 'email': 'Email / Phone', 'pass': 'Password', 'start': 'Start Discovery', 
        'tab1': '🏛️ Heritage Hubs', 'tab2': '🗺️ Smart Trail', 'tab3': '📜 Heritage Passport', 'feedback': 'Your Opinion Matters',
        'gps_btn': '🛰️ Claim Local Stamp'
    },
    'العربية': {
        'welcome': 'مرحباً بكم في ميزون بلقيس', 'subtitle': 'السياحة الذكية 4.0', 'login_title': 'تسجيل الزوار',
        'name': 'الاسم الكامل', 'email': 'البريد الإلكتروني / الهاتف', 'pass': 'كلمة المرور', 'start': 'ابدأ الاكتشاف', 
        'tab1': '🏛️ الأقطاب التراثية', 'tab2': '🗺️ المسار الذكي', 'tab3': '📜 الجواز التراثي', 'feedback': 'رأيكم يهمنا',
        'gps_btn': '🛰️ أحصل على ختم الموقع الحالي'
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
    with st.expander("🔐 Admin Area"):
        if st.text_input("Password", type="password", key="admin_key") == "BALKISS2024":
            if os.path.exists('stamps_log.csv'):
                st.subheader("📍 Stamps Activity")
                st.dataframe(pd.read_csv('stamps_log.csv'))

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
                st.session_state.logged_in, st.session_state.visitor_name, st.session_state.visitor_email = True, name, log_email
                st.rerun()
            else: st.error("Invalid Login")

# 6. الواجهة الرئيسية
else:
    st.title(f"👑 {t['welcome']}")
    st.subheader(t['subtitle'])
    tab1, tab2, tab3 = st.tabs([t['tab1'], t['tab2'], t['tab3']])

    with tab1:
        hub_lang = st.radio("🌐 Language / اللغة", ("English", "العربية"), horizontal=True, key="h_lang")
        hubs_data = {
            "North": {"en": {"title": "The Mediterranean Soul", "desc": "A dream of blue and white.", "highlights": "• Chefchaouen • Tangier"}, "ar": {"title": "روح المتوسط", "desc": "حلم من الأزرق والأبيض.", "highlights": "• شفشاون • طنجة"}, "img": "https://images.unsplash.com/photo-1548013146-72479768bbaa?w=800"},
            "Center": {"en": {"title": "The Spiritual Heartland", "desc": "The cradle of history.", "highlights": "• Fes • Sefrou Falls"}, "ar": {"title": "القلب الروحاني", "desc": "مهد التاريخ.", "highlights": "• فاس • شلالات صفرو"}, "img": "https://images.unsplash.com/photo-1549944850-84e00be4203b?w=800"},
            "South": {"en": {"title": "The Red Oasis", "desc": "Vibrant souks.", "highlights": "• Marrakech"}, "ar": {"title": "واحة البهجة", "desc": "الأسواق النابضة.", "highlights": "• مراكش"}, "img": "https://images.unsplash.com/photo-1597212618440-806262de496b?w=800"},
            "Desert": {"en": {"title": "The Golden Sahara", "desc": "Golden dunes.", "highlights": "• Merzouga"}, "ar": {"title": "الصحراء الذهبية", "desc": "كثبان ذهبية.", "highlights": "• مرزوكة"}, "img": "https://images.unsplash.com/photo-1505051508008-923feaf90180?w=800"},
            "Coast": {"en": {"title": "The Atlantic Breeze", "desc": "Artistic wind city.", "highlights": "• Essaouira • Dakhla"}, "ar": {"title": "نسيم المحيط", "desc": "مدينة الرياح والفنون.", "highlights": "• الصويرة • الداخلة"}, "img": "https://images.unsplash.com/photo-1539129790410-d0124747b290?w=800"}
        }
        cols = st.columns(5)
        if 'active_hub' not in st.session_state: st.session_state.active_hub = "Center"
        for i, k in enumerate(hubs_data.keys()):
            label = hubs_data[k]['en' if hub_lang == 'English' else 'ar']['title']
            if cols[i].button(label, key=f"btn_{k}"): st.session_state.active_hub = k; st.rerun()
        sel = hubs_data[st.session_state.active_hub]
        c1, c2 = st.columns([1.5, 1])
        with c1: st.image(sel['img'], use_container_width=True)
        with c2: 
            txt = sel['en' if hub_lang == 'English' else 'ar']
            st.header(txt['title']); st.write(txt['desc']); st.info(txt['highlights'])

    with tab2:
        st.header(t['tab2'])
        if os.path.exists('landmarks_data.csv'):
            df_geo = pd.read_csv('landmarks_data.csv')
            c1, c2 = st.columns(2)
            with c1: sel_reg = st.selectbox("📍 Region", [""] + sorted(df_geo['Region'].unique().tolist()), key="r_map")
            with c2: 
                cities = sorted(df_geo[df_geo['Region'] == sel_reg]['City'].unique().tolist()) if sel_reg else sorted(df_geo['City'].unique().tolist())
                sel_city = st.selectbox("🏙️ City", [""] + cities, key="c_map")
            if sel_city:
                city_info = df_geo[df_geo['City'] == sel_city].iloc[0]
                st.success(city_info['Description'])
                m = folium.Map(location=[city_info['Lat'], city_info['Lon']], zoom_start=12)
                folium.Marker([city_info['Lat'], city_info['Lon']], popup=city_info['Place']).add_to(m)
                st_folium(m, width=800, height=450, key="map")

    with tab3:
            st.header(t['tab3'])
            user_stamps = load_user_stamps(st.session_state.visitor_email)
            stamps_count = len(user_stamps)
            
            # 1. باسبور الأمباسادور (Ambassador Passport) - الديكور ديالك
            st.markdown(f"""
                <div style="border: 3px double #D4AF37; padding: 25px; border-radius: 15px; background: linear-gradient(145deg, #111, #000); text-align: center;">
                    <h2 style="color: #D4AF37; margin-bottom: 5px;">HERITAGE AMBASSADOR PASSPORT</h2>
                    <div style="display: flex; justify-content: space-around; margin-top: 20px;">
                        <div><p style="color: #D4AF37; font-size: 12px;">HOLDER</p><h3 style="color: white;">{st.session_state.visitor_name}</h3></div>
                        <div><p style="color: #D4AF37; font-size: 12px;">STAMPS</p><h3 style="color: white;">{stamps_count} / 10</h3></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            st.progress(min(stamps_count / 10, 1.0))
            if stamps_count >= 10:
                st.success("🎖️ Congratulations! You are now a Gold Heritage Ambassador!")

            st.write("---")
            
            # 2. اللوكايشن والبحث التلقائي - هاد الجزء هو اللي زدت فيه "البحث اليدوي"
            st.subheader("📍 Verify Your Visit")
            
            # خيار البحث اليدوي (باش السائح ما يحصلش إيلا الـ GPS تعطل)
            # لستة المدن (تقدري تزيدي فيها اللي بغيتي)
            cities_list = ["Fez", "Marrakech", "Chefchaouen", "Tanger", "Casablanca", "Rabat", "Essaouira", "Agadir", "Meknes", "Ouarzazate", "Ifrane", "Merzouga"]
            
            # زدت خيار "أخرى" في اللخر
            selected_city = st.selectbox("Search your current city | ابحث عن مدينتك", ["--- Select City ---"] + cities_list + ["Other City... / مدينة أخرى..."])
            
            # إيلا اختار "أخرى"، كيبان ليه مربع يكتب فيه
            custom_city = ""
            if selected_city == "Other City... / مدينة أخرى...":
                custom_city = st.text_input("Enter your city name | اكتب اسم مدينتك")
            
            st.write("OR") 
            
            # (نفس الكود ديال اللوكايشن كيبقى من بعد)
            current_loc = streamlit_js_eval(js_expressions="window.navigator.geolocation.getCurrentPosition(pos => { return pos.coords })", key="gps_ready")

            if st.button("🛰️ Claim Local Heritage Stamp"):
                # تحديد سمية المدينة النهائية
                final_city = custom_city if selected_city == "Other City... / مدينة أخرى..." else selected_city
                
                if final_city and final_city != "--- Select City ---":
                    save_stamp_to_db(st.session_state.visitor_name, st.session_state.visitor_email, final_city)
                    st.success(f"Stamp for {final_city} added!")
                    st.balloons()
                    st.rerun()
                # (الباقي ديال الكود كيبقى هو هو)
                
                # الخيار 2: إيلا السائح بغا يخدم بالـ GPS
                elif current_loc:
                    try:
                        res = requests.get(f"https://nominatim.openstreetmap.org/reverse?lat={current_loc['latitude']}&lon={current_loc['longitude']}&format=json", headers={'User-Agent': 'BalkissApp/1.0'}).json()
                        city_name = res.get('address', {}).get('city') or res.get('address', {}).get('town') or res.get('address', {}).get('village') or "Morocco Landmark"
                        
                        save_stamp_to_db(st.session_state.visitor_name, st.session_state.visitor_email, city_name)
                        st.success(f"Verified by GPS! Stamp for {city_name} added.")
                        st.balloons()
                        st.rerun()
                    except:
                        st.error("GPS error. Please select city manually from the list above.")
                else:
                    st.warning("Please select a city from the list or wait for GPS to respond!")

            st.write("---")
            
            # 3. الطابع البريدي بالكاشي ديال الماركة (Maison Balkiss Official) - بـ 10 دراهم
            st.subheader("🏺 Your Digital Collection")
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
    # --- الخدمة ديال 15 دولار (بقات كيف ما هي) ---
    st.write("---")
    st.subheader("🌟 Exclusive Eco-Travel Services")
    with st.expander("Get your Personalized Green Itinerary (15€)"):
        with st.form("purchase_form"):
            cn, ce = st.text_input("Full Name"), st.text_input("Email")
            if st.form_submit_button("Confirm & Pay via WhatsApp 💬"):
                wa_url = f"https://wa.me/212667920412?text=Order%20Itinerary%20for%20{cn}"
                st.markdown(f'<meta http-equiv="refresh" content="0;url={wa_url}">', unsafe_allow_html=True)

    # --- الفيدباك (مكانه الصحيح داخل الـ else) ---
    st.write("---")
    st.subheader(t['feedback'])
    user_msg = st.text_area("Your Feedback...", key="feedback_area")
    if st.button("Submit Feedback"):
        if save_feedback(st.session_state.visitor_name, st.session_state.visitor_email, user_msg):
            st.success("Success! Feedback recorded.")

st.markdown("<center>© 2026 MAISON BALKISS - Smart Tourism 4.0</center>", unsafe_allow_html=True)
