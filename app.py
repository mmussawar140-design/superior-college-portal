import streamlit as st
from datetime import date, datetime
import json
import os
import pandas as pd
from fpdf import FPDF
import tempfile

# --- FIREBASE MODULES ---
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# --- Page Config ---
st.set_page_config(page_title="Superior College Okara Portal", layout="wide", page_icon="image_500c0a.png")

# ==========================================
# FIREBASE DATABASE CONNECTION
# ==========================================
FIREBASE_URL = "https://superior-college-okara-9efbc-default-rtdb.firebaseio.com/" 

if not firebase_admin._apps:
    try:
        # راز (Secret) سے چابی پڑھنا
        key_dict = json.loads(st.secrets["firebase_secret"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred, {
            'databaseURL': FIREBASE_URL
        })
    except Exception as e:
        st.error(f"Firebase Connection Error: {e}")

def load_data(node_name, default_val=[]):
    try:
        data = db.reference(node_name).get()
        return data if data is not None else default_val
    except:
        return default_val

def save_data(node_name, data):
    try:
        db.reference(node_name).set(data)
    except Exception as e:
        st.error(f"Save Error: {e}")

# ==========================================
# SAFE CSS FOR PREMIUM LOOK
# ==========================================
st.markdown("""
<style>
.stApp { background-color: #083b3c !important; }
.stSidebar { background-color: #062b2b !important; }
h1, h2, h3, h4, h5, h6, p, label, li, div[data-testid="stMarkdownContainer"] {
    color: #ffffff !important;
    font-family: 'Arial', sans-serif !important;
    font-weight: bold !important;
}
h1 { font-size: 36px !important; }
h2 { font-size: 30px !important; }
h3 { font-size: 24px !important; }
input, textarea, div[data-baseweb="select"] > div, div[data-baseweb="select"] span {
    background-color: #f0f8f8 !important;
    color: #000000 !important;
    border-radius: 5px !important;
    border: none !important;
    font-size: 14px !important;
    font-weight: bold !important;
}
input::placeholder, textarea::placeholder { color: #555555 !important; }
ul[data-baseweb="menu"] { background-color: #ffffff !important; }
ul[data-baseweb="menu"] li, ul[data-baseweb="menu"] span { 
    color: #000000 !important; font-weight: bold !important; background-color: transparent !important;
}
button[data-baseweb="tab"] {
    background-color: #115e5e !important;
    border-radius: 8px 8px 0px 0px !important;
    margin-right: 5px !important;
    padding: 10px 20px !important;
    border: 2px solid #0d4a4a !important; border-bottom: none !important;
    box-shadow: 2px -2px 5px rgba(0,0,0,0.3) !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    background-color: #f7b731 !important; border-color: #c28c11 !important;
}
button[data-baseweb="tab"] p { font-size: 16px !important; font-weight: bold !important; color: #ffffff !important; }
button[data-baseweb="tab"][aria-selected="true"] p { color: #000000 !important; }
div[data-baseweb="tab-highlight"] { display: none !important; }
.reg-box {
    background-color: #0a494a; padding: 30px; border-radius: 12px;
    border: 2px solid #115e5e; box-shadow: 0px 8px 16px rgba(0,0,0,0.6); margin-top: 20px;
}
div[data-testid="metric-container"] {
    background: linear-gradient(145deg, #115e5e, #0d4a4a) !important;
    border-left: 6px solid #f7b731 !important; padding: 15px !important;
    border-radius: 8px !important; box-shadow: 4px 4px 10px rgba(0,0,0,0.5) !important;
}
[data-testid="stDataFrame"] { background-color: #ffffff !important; border-radius: 5px; overflow: hidden; }
[data-testid="stDataFrame"] div, [data-testid="stDataFrame"] span { color: #000000 !important; }
[data-testid="stDataFrame"] th, [data-testid="stDataFrame"] th span { background-color: #115e5e !important; color: #ffffff !important; font-size: 12px !important;}
</style>
""", unsafe_allow_html=True)

if os.path.exists("image_500c0a.png"):
    st.sidebar.image("image_500c0a.png", use_container_width=True)

# ==========================================
# INITIALIZE CLOUD DATA
# ==========================================
default_settings = {
    "classes": ["11th", "12th"],
    "courses": ["F.Sc (Pre-Medical)", "F.Sc (Pre-Engineering)", "ICS", "F.A", "F.A (IT)", "DIT"],
    "branches": ["Boys", "Girls"],
    "sections": ["RMEB", "PMEB", "RMEG", "PMEG", "RBICS-I", "RBICS-II", "RBICS-III", "RGICS-I", "RGICS-II", "RGICS-III", "RBFA", "RGFA", "RBDIT", "RGDIT", "SMEB", "SMEG", "SBICS", "SGICS", "SBFA", "SGFA", "SBDIT", "SGDIT"],
    "subjects": ["Urdu", "English", "Islamyat", "Tarjmatul Quran", "Pakistan Studies", "Physics", "Chemistry", "Mathematics", "Biology", "Computer", "Economics", "Statistics", "Education", "Civics", "Sociology", "Physical Education", "Fine Arts", "Psychology"],
    "months": ["August", "September", "October", "November", "December", "January", "February", "March", "April", "May"]
}

for key in ['settings_db', 'users_db', 'students_db', 'attendance_db', 'tests_db', 'marks_db', 'followup_db', 'syllabus_db']:
    if key not in st.session_state:
        st.session_state[key] = load_data(key, default_settings if key == 'settings_db' else [])

if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False
    st.session_state.current_user = None

def check_single_role_exists(role): return any(user['role'] == role for user in st.session_state.users_db)
def get_class_incharge(class_name, course, branch, section):
    for user in st.session_state.users_db:
        if user['role'] == 'Class Incharge' and user.get('incharge_class') == class_name and user.get('incharge_course') == course and user.get('incharge_branch') == branch and user.get('incharge_section') == section:
            return user['name']
    return "Not Assigned"

def get_section_options(cls_name, crs_name, br_name):
    if cls_name == "11th":
        if crs_name in ["F.Sc (Pre-Medical)", "F.Sc (Pre-Engineering)"]: return ["RMEB", "PMEB"] if br_name == "Boys" else ["RMEG", "PMEG"]
        elif crs_name == "ICS": return ["RBICS-I", "RBICS-II", "RBICS-III"] if br_name == "Boys" else ["RGICS-I", "RGICS-II", "RGICS-III"]
        elif crs_name in ["F.A", "F.A (IT)"]: return ["RBFA"] if br_name == "Boys" else ["RGFA"]
        elif crs_name == "DIT": return ["RBDIT"] if br_name == "Boys" else ["RGDIT"]
    elif cls_name == "12th":
        if crs_name in ["F.Sc (Pre-Medical)", "F.Sc (Pre-Engineering)"]: return ["SMEB"] if br_name == "Boys" else ["SMEG"]
        elif crs_name == "ICS": return ["SBICS"] if br_name == "Boys" else ["SGICS"]
        elif crs_name in ["F.A", "F.A (IT)"]: return ["SBFA"] if br_name == "Boys" else ["SGFA"]
        elif crs_name == "DIT": return ["SBDIT"] if br_name == "Boys" else ["SGDIT"]
    return ["N/A"]

# ==========================================
# EXPORT GENERATORS
# ==========================================
def generate_csv_with_header_utf8(df, title, meta_info=""):
    # utf-8-sig ensures Excel reads Urdu perfectly
    header = f'"SUPERIOR COLLEGE OKARA"\n"{title}"\n"{meta_info}"\n'
    return header.encode('utf-8-sig') + b'\n' + df.to_csv(index=False).encode('utf-8-sig')

def generate_basic_pdf(df, title, meta_info=""):
    # Basic PDF (Does not support connected Urdu characters properly)
    pdf = FPDF(orientation='L')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 8, "SUPERIOR COLLEGE OKARA", 0, 1, 'C')
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, title, 0, 1, 'C')
    pdf.set_font("Arial", '', 10)
    if meta_info: pdf.cell(0, 6, meta_info, 0, 1, 'C')
    pdf.ln(8)
    
    col_widths = [15] + [(260)/len(df.columns)] * (len(df.columns)-1)
    pdf.set_font("Arial", 'B', 8)
    for i, h in enumerate(df.columns): pdf.cell(col_widths[i], 8, str(h)[:15], 1, 0, 'C')
    pdf.ln()
    pdf.set_font("Arial", '', 8)
    for idx, row in df.iterrows():
        for i, val in enumerate(row):
            t_val = str(val)[:45] + '...' if len(str(val))>45 else str(val)
            pdf.cell(col_widths[i], 8, t_val, 1, 0, 'C')
        pdf.ln()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name)
    with open(tmp.name, "rb") as f: return f.read()

# ==========================================
# SYLLABUS MODULE
# ==========================================
def render_syllabus_tracker(user, is_admin=False):
    st.subheader("📚 Syllabus Progress Tracker")
    
    if not is_admin:
        assignments = user.get('teaching_assignments', [])
        if not assignments:
            st.warning("Please setup teaching assignments first.")
            return
        
        assg_opts = [f"{a['class_name']} | {a['course']} | {a['branch']} | {a['section']} -> {a['subject']}" for a in assignments]
        sel_assg = st.selectbox("Select Subject", assg_opts)
        parts = sel_assg.split(" -> ")
        meta = parts[0].split(" | ")
        c_cls, c_crs, c_br, c_sec, c_subj = meta[0], meta[1], meta[2], meta[3], parts[1]
        
        with st.expander("➕ Add Syllabus Breakup"):
            with st.form("add_syllabus_form"):
                sc1, sc2 = st.columns(2)
                s_month = sc1.selectbox("Select Month", st.session_state.settings_db.get('months', default_settings['months']))
                s_week = sc2.selectbox("Select Week", ["Week 1", "Week 2", "Week 3", "Week 4"])
                s_topic = st.text_area("Syllabus / Topics to Teach (اردو میں بھی لکھ سکتے ہیں)")
                if st.form_submit_button("Save Syllabus Plan"):
                    entry = {
                        "id": f"{c_cls}_{c_sec}_{c_subj}_{s_month}_{s_week}".replace(" ", ""),
                        "teacher": user['name'], "class_name": c_cls, "course": c_crs, "branch": c_br, "section": c_sec, "subject": c_subj,
                        "month": s_month, "week": s_week, "topic": s_topic, "completed": False
                    }
                    st.session_state.syllabus_db = [s for s in st.session_state.syllabus_db if s['id'] != entry['id']] # Overwrite if same week
                    st.session_state.syllabus_db.append(entry)
                    save_data('syllabus_db', st.session_state.syllabus_db)
                    st.success("Syllabus Added!")
                    st.rerun()
        
        # Display & Track
        my_syl = [s for s in st.session_state.syllabus_db if s['teacher']==user['name'] and s['class_name']==c_cls and s['section']==c_sec and s['subject']==c_subj]
        
    else:
        st.markdown("#### Admin Syllabus View")
        ac1, ac2, ac3, ac4 = st.columns(4)
        a_cls = ac1.selectbox("Class", st.session_state.settings_db['classes'], key="as1")
        a_crs = ac2.selectbox("Course", st.session_state.settings_db['courses'], key="as2")
        a_br = ac3.selectbox("Branch", st.session_state.settings_db['branches'], key="as3")
        a_sec = ac4.selectbox("Section", get_section_options(a_cls, a_crs, a_br), key="as4")
        a_subj = st.selectbox("Subject", st.session_state.settings_db['subjects'], key="as5")
        
        my_syl = [s for s in st.session_state.syllabus_db if s['class_name']==a_cls and s['section']==a_sec and s['subject']==a_subj]

    if my_syl:
        # Sort properly
        month_order = {m: i for i, m in enumerate(st.session_state.settings_db.get('months', default_settings['months']))}
        my_syl.sort(key=lambda x: (month_order.get(x['month'], 99), x['week']))
        
        total_weeks = len(my_syl)
        completed_weeks = sum(1 for s in my_syl if s['completed'])
        prog_perc = int((completed_weeks / total_weeks) * 100) if total_weeks > 0 else 0
        
        st.markdown(f"#### Progress: {prog_perc}% Completed")
        st.progress(prog_perc)
        st.markdown(f"**{completed_weeks} out of {total_weeks} Weeks Completed**")
        
        df_syl = pd.DataFrame(my_syl)[['month', 'week', 'topic', 'completed', 'id']]
        df_syl.columns = ['MONTH', 'WEEK', 'SYLLABUS / TOPICS', 'COMPLETED', 'ID']
        
        if not is_admin:
            st.info("💡 Check the 'COMPLETED' box below when you finish teaching a week's syllabus.")
            edited_df = st.data_editor(
                df_syl.drop(columns=['ID']),
                column_config={"COMPLETED": st.column_config.CheckboxColumn("COMPLETED", default=False)},
                disabled=["MONTH", "WEEK", "SYLLABUS / TOPICS"], hide_index=True, use_container_width=True
            )
            if st.button("Update Progress"):
                for i, row in edited_df.iterrows():
                    orig_id = df_syl.iloc[i]['ID']
                    for s in st.session_state.syllabus_db:
                        if s['id'] == orig_id: s['completed'] = row['COMPLETED']
                save_data('syllabus_db', st.session_state.syllabus_db)
                st.success("Progress Updated!")
                st.rerun()
        else:
            teacher_name = my_syl[0]['teacher'] if my_syl else "Unknown"
            st.write(f"**Teacher:** {teacher_name}")
            st.dataframe(df_syl.drop(columns=['ID']), hide_index=True, use_container_width=True)
            
        st.divider()
        csv_data = generate_csv_with_header_utf8(df_syl.drop(columns=['ID']), "SYLLABUS BREAKUP", f"Progress: {prog_perc}%")
        pdf_data = generate_basic_pdf(df_syl.drop(columns=['ID', 'COMPLETED']), "SYLLABUS BREAKUP", f"Progress: {prog_perc}%")
        
        d1, d2 = st.columns(2)
        d1.download_button("📥 Download Excel/CSV (Best for Urdu)", data=csv_data, file_name="Syllabus.csv", mime="text/csv")
        d2.download_button("📥 Download PDF (English Only)", data=pdf_data, file_name="Syllabus.pdf", mime="application/pdf")
    else:
        st.info("No syllabus data available for this selection yet.")

# ==========================================
# MAIN UI & AUTH
# ==========================================
col_logo, col_title = st.columns([1, 10])
with col_logo:
    if os.path.exists("image_500c0a.png"): st.image("image_500c0a.png", width=70)
with col_title:
    st.title("🎓 Superior College Okara - Management System")

if 'saved_username' not in st.session_state:
    st.session_state.saved_username = load_data('saved_username_db', "")

if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["Login", "Admin Sign Up"])
    with tab1:
        l1, l2, l3 = st.columns([1, 2, 1])
        with l2:
            st.markdown('<div class="reg-box">', unsafe_allow_html=True)
            st.subheader("Login to Portal")
            msg_log = st.empty()
            l_user = st.text_input("Username", value=st.session_state.saved_username)
            l_pass = st.text_input("Password", type="password")
            rem = st.checkbox("Remember Me", value=bool(st.session_state.saved_username))
            
            if st.button("Login", use_container_width=True):
                found = False
                for u in st.session_state.users_db:
                    if u.get('username') == l_user and u.get('password') == l_pass:
                        st.session_state.logged_in = True
                        st.session_state.current_user = u
                        found = True
                        if rem: save_data('saved_username_db', l_user)
                        else: save_data('saved_username_db', "")
                        st.rerun()
                if not found: msg_log.error("Invalid Credentials!")
            st.markdown('</div>', unsafe_allow_html=True)
            
    with tab2:
        r1, r2, r3 = st.columns([1, 2, 1])
        with r2:
            st.markdown('<div class="reg-box">', unsafe_allow_html=True)
            st.subheader("Admin Only Registration")
            msg_reg = st.empty()
            
            existing_admin_roles = [u.get('role') for u in st.session_state.users_db if u.get('role') in ["Principal", "Vice Principal", "Controller of Examinations"]]
            available_roles = [r for r in ["Principal", "Vice Principal", "Controller of Examinations"] if r not in existing_admin_roles]
            
            if not available_roles:
                st.success("✔️ تمام ایڈمن اکاؤنٹس بن چکے ہیں۔ اب کوئی نیا ایڈمن اکاؤنٹ نہیں بن سکتا۔")
            else:
                role = st.selectbox("Role", available_roles)
                c_n, c_u = st.columns(2)
                r_name = c_n.text_input("Name")
                r_usr = c_u.text_input("Username", key="r_usr")
                c_p, c_cp = st.columns(2)
                r_pwd = c_p.text_input("Password", type="password", key="r_pwd")
                c_pwd = c_cp.text_input("Confirm Password", type="password")
                
                if st.button("Register Admin", use_container_width=True):
                    if not r_name or not r_usr or not r_pwd: msg_reg.error("Fill all fields.")
                    elif r_pwd != c_pwd: msg_reg.error("Passwords mismatch.")
                    else:
                        if role in [u.get('role') for u in st.session_state.users_db]:
                            msg_reg.error(f"{role} account already exists!")
                        else:
                            user = {"name": r_name, "username": r_usr, "password": r_pwd, "role": role, "profile_setup": True}
                            st.session_state.users_db.append(user)
                            save_data('users_db', st.session_state.users_db)
                            msg_reg.success("Admin registered! Please Login.")
                            st.rerun() 
            st.markdown('</div>', unsafe_allow_html=True)

else:
    user = st.session_state.current_user
    c1, c2 = st.columns([9, 1])
    c1.write(f"### Welcome, {user['name'].upper()} ({user['role']})")
    if c2.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.rerun()
    st.divider()
    
    # --- ADMIN DASHBOARD ---
    if user['role'] in ["Principal", "Vice Principal", "Controller of Examinations"]:
        t_usr, t_stu, t_str, t_teach, t_syl, t_rep = st.tabs(["👥 Users", "🎓 Students", "🏗️ Structure", "📚 My Teaching", "📖 Syllabus Tracking", "📈 Reports"])
        with t_syl: render_syllabus_tracker(user, is_admin=True)
        # (Other tabs functionality logic hidden for brevity - add them if needed below)
        with t_teach: st.write("Teacher features inside Admin.")
        
    # --- TEACHER DASHBOARD ---
    elif user['role'] == "Teacher":
        st.markdown("### 📊 My Teacher Dashboard")
        t_teach, t_marks, t_stu, t_abs, t_syl, t_prof = st.tabs(["📝 Tests/Marks", "📈 Results", "🎓 Students", "📅 Absentees", "📖 Syllabus Progress", "⚙️ Setup"])
        with t_syl: render_syllabus_tracker(user, is_admin=False)

    # --- CLASS INCHARGE DASHBOARD ---
    elif user['role'] == "Class Incharge":
        st.markdown(f"### 📊 Incharge Dashboard")
        t_reg, t_att, t_teach, t_syl, t_rep, t_prof = st.tabs(["📝 Students", "📅 Attendance", "📚 Tests/Marks", "📖 Syllabus Progress", "📈 Results", "⚙️ Setup"])
        with t_syl: render_syllabus_tracker(user, is_admin=False)
