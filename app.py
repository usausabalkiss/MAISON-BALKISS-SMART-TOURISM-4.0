
import streamlit as st
import sqlite3
import pandas as pd

# قاعدة البيانات
conn = sqlite3.connect('maison_balkiss_pro.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS ai_projects 
             (id INTEGER PRIMARY KEY, client TEXT, service TEXT, deadline TEXT, 
              total REAL, advance REAL, status TEXT)''')
conn.commit()

st.set_page_config(page_title="Maison Balkiss AI Business", layout="wide")

tech_services = ["AI & INNOVATION", "BRANDING & AI", "SMART TOURISM 4.0", "TECH ACADEMY 4.0", "ATELIERS", "Consulting"]

st.sidebar.title("👑 Maison Balkiss AI")
admin_mode = st.sidebar.checkbox("🔒 Admin Dashboard")

st.title("⚜️ AI Business Management System")
tab1, tab2, tab3 = st.tabs(["🚀 New Project", "📅 Project Pipeline", "📊 Finance & Admin"])

with tab1:
    st.subheader("📩 تسجيل مشروع جديد")
    with st.form("tech_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            client = st.text_input("👤 اسم العميل")
            service = st.selectbox("🛠️ الخدمة", tech_services)
            total = st.number_input("💰 الميزانية", min_value=0.0)
        with c2:
            deadline = st.date_input("📅 التسليم")
            advance = st.number_input("💵 العربون", min_value=0.0)
            curr = st.selectbox("💱 العملة", ["USD", "EUR", "MAD"])
        
        if st.form_submit_button("✅ حفظ المشروع"):
            if client:
                c.execute("INSERT INTO ai_projects (client, service, deadline, total, advance, status) VALUES (?, ?, ?, ?, ?, ?)",
                          (client, service, deadline.strftime("%Y-%m-%d"), total, advance, "In Progress"))
                conn.commit()
                st.success(f"✅ تم تسجيل مشروع {service}!")

with tab2:
    st.subheader("📅 Project Pipeline")
    df = pd.read_sql_query("SELECT client, service, deadline, status FROM ai_projects", conn)
    st.dataframe(df, use_container_width=True)

with tab3:
    if admin_mode:
        pwd = st.text_input("Password", type="password")
        if pwd == "12345678ouafaa@":
            full_df = pd.read_sql_query("SELECT * FROM ai_projects", conn)
            st.dataframe(full_df, use_container_width=True)
            st.metric("📈 إجمالي الأرباح", f"{full_df['total'].sum()} {curr}")
