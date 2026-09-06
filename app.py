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

# --- Custom CSS for Professional Look & Cards ---
st.markdown("""
<style>
div[data-testid="metric-container"] {
    background-color: #F8FAFA;
    border: 1px solid #E0E6E6;
    padding: 15px 20px;
    border-radius: 10px;
    box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    border-left: 5px solid #0A7E7B;
}
.center-text { text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- UI Global Logo ---
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
    "subjects": ["Urdu", "English", "Islamyat", "Tarjmatul Quran", "Pakistan Studies", "Physics", "Chemistry", "Mathematics", "Biology", "Computer", "Economics", "Statistics", "Education", "Civics", "Sociology", "Physical Education", "Fine Arts", "Psychology"]
}

if 'settings_db' not in st.session_state: st.session_state.settings_db = load_data('settings_db', default_settings)
if 'users_db' not in st.session_state: st.session_state.users_db = load_data('users_db', [])
if 'students_db' not in st.session_state: st.session_state.students_db = load_data('students_db', [])
if 'attendance_db' not in st.session_state: st.session_state.attendance_db = load_data('attendance_db', [])
if 'tests_db' not in st.session_state: st.session_state.tests_db = load_data('tests_db', [])
if 'marks_db' not in st.session_state: st.session_state.marks_db = load_data('marks_db', [])
if 'followup_db' not in st.session_state: st.session_state.followup_db = load_data('followup_db', [])

if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False
    st.session_state.current_user = None

def check_single_role_exists(role): return any(user['role'] == role for user in st.session_state.users_db)
def get_class_incharge(class_name, course, branch, section):
    for user in st.session_state.users_db:
        if user['role'] == 'Class Incharge' and user.get('incharge_class') == class_name and user.get('incharge_course') == course and user.get('incharge_branch') == branch and user.get('incharge_section') == section:
            return user['name']
    return "Not Assigned"

def fmt_mark(val):
    if val is None or val == "-": return val
    v_str = str(val)
    return v_str[:-2] if v_str.endswith(".0") else v_str
def format_date_ddmmyyyy(date_val):
    if not date_val: return ""
    try: return date.fromisoformat(str(date_val)).strftime("%d-%m-%Y") if "-" in str(date_val) else str(date_val)
    except: return str(date_val)
def get_month_year(date_val):
    if not date_val: return "Unknown"
    try: return date.fromisoformat(str(date_val)).strftime("%B %Y") if "-" in str(date_val) else str(date_val)
    except: return str(date_val)

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

def get_mandatory_subjects(cls_name, crs_name):
    mand = ["Urdu", "English", "Tarjmatul Quran"]
    if cls_name == "11th": mand.append("Islamyat")
    elif cls_name == "12th": mand.append("Pakistan Studies")
    if crs_name == "F.Sc (Pre-Medical)": mand.extend(["Biology", "Physics", "Chemistry"])
    elif crs_name == "F.Sc (Pre-Engineering)": mand.extend(["Physics", "Chemistry", "Mathematics"])
    elif crs_name in ["ICS", "F.A (IT)"]: mand.append("Computer")
    seen = set()
    return [x for x in mand if not (x in seen or seen.add(x))]

def get_all_possible_subjects(cls_name, crs_name):
    mand = get_mandatory_subjects(cls_name, crs_name)
    opt = [s for s in st.session_state.settings_db['subjects'] if s not in mand]
    return mand + opt

# ==========================================
# EXPORT GENERATORS WITH LOGO
# ==========================================
def generate_csv_with_header(df, title, date_str="", class_name="", section="", incharge=""):
    date_f = format_date_ddmmyyyy(date_str) if "-" in str(date_str) and len(str(date_str)) <= 10 else date_str
    header = f'"SUPERIOR COLLEGE OKARA"\n"{title}"\n'
    meta = []
    if date_f: meta.append(f"Date/Session: {date_f}")
    if class_name: meta.append(f"Class: {class_name}")
    if section: meta.append(f"Section: {section}")
    if incharge and incharge != "Not Assigned": meta.append(f"Class Incharge: {incharge}")
    if meta: header += '"' + " | ".join(meta) + '"\n'
    return header.encode('utf-8') + b'\n' + df.to_csv(index=False).encode('utf-8')

def generate_pdf(df, title, date_str="", class_name="", section="", incharge=""):
    pdf = FPDF(orientation='L')
    pdf.add_page()
    if os.path.exists("image_500c0a.png"): pdf.image("image_500c0a.png", x=10, y=8, w=22)
        
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 8, "SUPERIOR COLLEGE OKARA", 0, 1, 'C')
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, title, 0, 1, 'C')
    pdf.set_font("Arial", '', 10)
    meta = []
    if date_str: meta.append(f"Date/Session: {format_date_ddmmyyyy(date_str)}")
    if class_name: meta.append(f"Class: {class_name}")
    if section: meta.append(f"Section: {section}")
    if incharge and incharge != "Not Assigned": meta.append(f"Class Incharge: {incharge}")
    if meta: pdf.cell(0, 6, " | ".join(meta), 0, 1, 'C')
    pdf.ln(8)
    
    col_widths = []
    rem_w = 270
    dyn_cols = 0
    for h in df.columns:
        hu = str(h).upper()
        if hu in ["STUDENT NAME", "NAME"]: col_widths.append(40); rem_w -= 40
        elif hu in ["ROLL NO"]: col_widths.append(20); rem_w -= 20
        elif hu in ["SR. NO."]: col_widths.append(15); rem_w -= 15
        else: col_widths.append(0); dyn_cols += 1
    if dyn_cols > 0:
        dyn_w = rem_w / dyn_cols
        col_widths = [dyn_w if w==0 else w for w in col_widths]

    pdf.set_font("Arial", 'B', 8)
    for i, h in enumerate(df.columns): pdf.cell(col_widths[i], 8, str(h)[:15], 1, 0, 'C')
    pdf.ln()
    pdf.set_font("Arial", '', 8)
    for idx, row in df.iterrows():
        for i, val in enumerate(row):
            t_val = str(val)[:35] + '...' if len(str(val))>35 else str(val)
            pdf.cell(col_widths[i], 8, t_val, 1, 0, 'L' if str(df.columns[i]).upper() in ["STUDENT NAME", "NAME"] else 'C')
        pdf.ln()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name)
    with open(tmp.name, "rb") as f: return f.read()

def draw_single_report_card(pdf, student_info, marks_df, totals):
    pdf.add_page()
    if os.path.exists("image_500c0a.png"): pdf.image("image_500c0a.png", x=10, y=8, w=22)
        
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 8, "SUPERIOR COLLEGE OKARA", 0, 1, 'C')
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "STUDENT REPORT CARD", 0, 1, 'C')
    pdf.set_font("Arial", '', 10)
    meta = []
    if student_info.get('test_month'): meta.append(f"Session: {student_info['test_month']}")
    meta.append(f"Class: {student_info['class']}")
    meta.append(f"Section: {student_info['section']}")
    if student_info['incharge'] != "Not Assigned": meta.append(f"Class Incharge: {student_info['incharge']}")
    pdf.cell(0, 6, " | ".join(meta), 0, 1, 'C')
    pdf.ln(8)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(90, 8, f"STUDENT NAME: {student_info['name']}", 0, 0)
    pdf.cell(90, 8, f"FATHER NAME: {student_info['father_name']}", 0, 1)
    pdf.cell(90, 8, f"ROLL NO: {student_info['roll_no']}", 0, 0)
    pdf.cell(90, 8, f"COURSE: {student_info['course']}", 0, 1)
    pdf.cell(90, 8, f"TEST NAME: {student_info['test_name']}", 0, 1)
    pdf.ln(4)
    
    cols = ['SR. NO.', 'SUBJECT', 'TEACHER', 'TOTAL MARKS', 'OBTAINED MARKS', 'PERCENTAGE']
    col_widths = [15, 45, 45, 25, 30, 30]
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("Arial", 'B', 9)
    for i, header in enumerate(cols): pdf.cell(col_widths[i], 8, header, 1, 0, 'C', fill=True)
    pdf.ln()
    pdf.set_font("Arial", '', 9)
    for _, row in marks_df.iterrows():
        pdf.cell(col_widths[0], 8, str(row['SR. NO.']), 1, 0, 'C')
        pdf.cell(col_widths[1], 8, str(row['SUBJECT']).upper(), 1, 0, 'L')
        pdf.cell(col_widths[2], 8, str(row['TEACHER']).upper(), 1, 0, 'L')
        pdf.cell(col_widths[3], 8, str(row['TOTAL MARKS']), 1, 0, 'C')
        pdf.cell(col_widths[4], 8, str(row['OBTAINED MARKS']), 1, 0, 'C')
        pdf.cell(col_widths[5], 8, str(row['PERCENTAGE']), 1, 1, 'C')
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(col_widths[0]+col_widths[1]+col_widths[2], 8, "GRAND TOTAL", 1, 0, 'R', fill=True)
    pdf.cell(col_widths[3], 8, str(totals['TOTAL MARKS']), 1, 0, 'C', fill=True)
    pdf.cell(col_widths[4], 8, str(totals['OBTAINED MARKS']), 1, 0, 'C', fill=True)
    pdf.cell(col_widths[5], 8, str(totals['PERCENTAGE']), 1, 1, 'C', fill=True)

def generate_bulk_report_cards(roll_nos, marks_list, class_name, course, branch, section, test_name, test_month):
    pdf = FPDF()
    for roll in roll_nos:
        st_marks = [m for m in marks_list if m['roll_no'] == roll]
        if not st_marks: continue
        st_info_db = next((s for s in st.session_state.students_db if s['roll_no'] == roll and s.get('class_name')==class_name), {})
        incharge_name = get_class_incharge(class_name, course, branch, section)
        
        df = pd.DataFrame(st_marks)
        df.rename(columns={'subject': 'SUBJECT', 'teacher': 'TEACHER', 'total_marks': 'TOTAL MARKS', 'obtained_marks': 'OBTAINED MARKS'}, inplace=True)
        df['TOTAL MARKS'] = df['TOTAL MARKS'].apply(fmt_mark)
        df['OBTAINED MARKS'] = df['OBTAINED MARKS'].apply(fmt_mark)
        df.insert(0, 'SR. NO.', range(1, len(df) + 1))
        
        grand_total = sum([m['total_marks'] for m in st_marks])
        grand_obt = sum([m['obtained_marks'] for m in st_marks])
        overall_perc = round((grand_obt / grand_total) * 100, 2) if grand_total > 0 else 0
        df['PERCENTAGE'] = [f"{round((m['obtained_marks']/m['total_marks'])*100, 2)}%" if m['total_marks']>0 else "0%" for m in st_marks]
        
        s_info = {
            "name": st_marks[0]['student_name'].upper(), "father_name": st_info_db.get('father_name', 'N/A').upper(),
            "roll_no": roll, "class": class_name, "course": course, "section": section,
            "test_name": test_name.upper(), "test_month": test_month, "incharge": incharge_name.upper()
        }
        totals = {'TOTAL MARKS': fmt_mark(grand_total), 'OBTAINED MARKS': fmt_mark(grand_obt), 'PERCENTAGE': f"{overall_perc}%"}
        draw_single_report_card(pdf, s_info, df[['SR. NO.', 'SUBJECT', 'TEACHER', 'TOTAL MARKS', 'OBTAINED MARKS', 'PERCENTAGE']], totals)
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp_file.name)
    with open(tmp_file.name, "rb") as f: return f.read()

# ==========================================
# REPORT CARDS LOGIC
# ==========================================
def render_report_card_module(marks_list, class_name, course, branch, section):
    st.subheader("Class Result & Report Cards")
    if not marks_list:
        st.info("No marks data available.")
        return
        
    test_groups = list(set([f"{m['test_type']} ({get_month_year(m.get('date', ''))})" for m in marks_list]))
    c_sel1, c_sel2 = st.columns([1, 2])
    selected_test = c_sel1.selectbox("Select Test Session", test_groups)
    
    if selected_test:
        t_type = selected_test.split(" (")[0]
        t_month = selected_test.split(" (")[1].replace(")", "")
        f_marks = [m for m in marks_list if m['test_type'] == t_type and get_month_year(m.get('date', '')) == t_month]
        rolls = list(set([m['roll_no'] for m in f_marks]))
        s_dict = {m['roll_no']: m['student_name'] for m in f_marks}
        incharge_name = get_class_incharge(class_name, course, branch, section)
        all_subj = sorted(list(set([m['subject'].upper() for m in f_marks])))
        
        sum_data = []
        for r in rolls:
            r_marks = [m for m in f_marks if m['roll_no'] == r]
            tot = sum([m['total_marks'] for m in r_marks])
            obt = sum([m['obtained_marks'] for m in r_marks])
            perc = round((obt/tot)*100, 2) if tot > 0 else 0
            
            row = {"SELECT": False, "ROLL NO": str(r), "STUDENT NAME": s_dict[r].upper()}
            for subj in all_subj:
                sm = next((m for m in r_marks if m['subject'].upper() == subj), None)
                row[subj] = f"{fmt_mark(sm['obtained_marks'])}/{fmt_mark(sm['total_marks'])}" if sm else "-"
            row["TOTAL (MAX)"] = fmt_mark(tot)
            row["TOTAL (OBT)"] = fmt_mark(obt)
            row["PERCENTAGE"] = f"{perc}%"
            sum_data.append(row)
        
        sum_df = pd.DataFrame(sum_data)
        sum_df = sum_df.sort_values(by='ROLL NO').reset_index(drop=True)
        sum_df.insert(1, 'SR. NO.', range(1, len(sum_df) + 1))
        sum_df.columns = sum_df.columns.str.upper()
        
        st.markdown("#### Complete Class Result Table")
        dis_cols = ["SR. NO.", "ROLL NO", "STUDENT NAME", "TOTAL (MAX)", "TOTAL (OBT)", "PERCENTAGE"] + all_subj
        edited_df = st.data_editor(sum_df, column_config={"SELECT": st.column_config.CheckboxColumn("SELECT", default=False)}, disabled=dis_cols, hide_index=True, use_container_width=True)
        
        sel_rolls = edited_df[edited_df["SELECT"] == True]["ROLL NO"].tolist()
        c1, c2, c3 = st.columns(3)
        with c1: st.download_button("Download Result (PDF)", data=generate_pdf(sum_df.drop(columns=["SELECT"]), "CLASS RESULT", t_month, class_name, section, incharge_name), file_name=f"Result_{class_name}_{section}.pdf", mime="application/pdf")
        with c2: st.download_button("Download Result (Excel)", data=generate_csv_with_header(sum_df.drop(columns=["SELECT"]), "CLASS RESULT", t_month, class_name, section, incharge_name), file_name=f"Result_{class_name}_{section}.csv", mime="text/csv")
        with c3:
            if sel_rolls:
                bulk_pdf = generate_bulk_report_cards(sel_rolls, f_marks, class_name, course, branch, section, t_type, t_month)
                st.download_button(f"Download Selected Report Cards (PDF)", data=bulk_pdf, file_name="Selected_ReportCards.pdf", mime="application/pdf", type="primary")
            else: st.button("Select checkboxes to bulk download", disabled=True)

        st.divider()
        st.markdown("#### 📄 View Individual Student Report Card")
        rolls_sorted = sorted(rolls, key=lambda x: str(x))
        cr1, cr2 = st.columns([1, 2])
        view_roll = cr1.selectbox("Select Student", ["-- Select Student --"] + rolls_sorted, format_func=lambda x: f"{x} - {s_dict[x]}" if x != "-- Select Student --" else x)
        
        if view_roll != "-- Select Student --":
            st_marks = [m for m in f_marks if m['roll_no'] == view_roll]
            st_info_db = next((s for s in st.session_state.students_db if s['roll_no'] == view_roll and s.get('class_name')==class_name), {})
            
            c_d1, c_d2 = st.columns(2)
            c_d1.write(f"**STUDENT NAME:** {s_dict[view_roll].upper()}")
            c_d1.write(f"**ROLL NO:** {view_roll}")
            c_d1.write(f"**TEST NAME:** {t_type.upper()}")
            c_d2.write(f"**FATHER NAME:** {st_info_db.get('father_name', 'N/A').upper()}")
            c_d2.write(f"**CLASS & SECTION:** {class_name} - {section}")
            c_d2.write(f"**CLASS INCHARGE:** {incharge_name.upper()}")
            
            df_ind = pd.DataFrame(st_marks)
            df_ind.rename(columns={'subject': 'SUBJECT', 'teacher': 'TEACHER', 'total_marks': 'TOTAL MARKS', 'obtained_marks': 'OBTAINED MARKS'}, inplace=True)
            df_ind['SUBJECT'] = df_ind['SUBJECT'].str.upper()
            df_ind['TEACHER'] = df_ind['TEACHER'].str.upper()
            g_tot = df_ind['TOTAL MARKS'].sum()
            g_obt = df_ind['OBTAINED MARKS'].sum()
            o_perc = round((g_obt / g_tot) * 100, 2) if g_tot > 0 else 0
            df_ind['PERCENTAGE'] = df_ind.apply(lambda r: f"{round((r['OBTAINED MARKS'] / r['TOTAL MARKS']) * 100, 2)}%" if r['TOTAL MARKS']>0 else "0%", axis=1)
            df_ind['TOTAL MARKS'] = df_ind['TOTAL MARKS'].apply(fmt_mark)
            df_ind['OBTAINED MARKS'] = df_ind['OBTAINED MARKS'].apply(fmt_mark)
            
            df_ind.insert(0, 'SR. NO.', range(1, len(df_ind) + 1))
            df_ind.columns = df_ind.columns.str.upper()
            st.table(df_ind[['SR. NO.', 'SUBJECT', 'TEACHER', 'TOTAL MARKS', 'OBTAINED MARKS', 'PERCENTAGE']])
            
            t1, t2, t3 = st.columns([2, 1, 1])
            t1.markdown("<h5 style='text-align: right;'>GRAND TOTAL:</h5>", unsafe_allow_html=True)
            t2.markdown(f"**{fmt_mark(g_tot)}** (Total) | **{fmt_mark(g_obt)}** (Obtained)")
            t3.markdown(f"**{o_perc}%**")
            
            col_b1, col_b2, _ = st.columns([1, 1, 2])
            with col_b1:
                csv_data = df_ind[['SR. NO.', 'SUBJECT', 'TEACHER', 'TOTAL MARKS', 'OBTAINED MARKS', 'PERCENTAGE']].copy()
                csv_data.loc[len(csv_data)] = ['-', 'GRAND TOTAL', '', fmt_mark(g_tot), fmt_mark(g_obt), f"{o_perc}%"]
                st.download_button("Download Report (CSV)", data=generate_csv_with_header(csv_data, f"STUDENT REPORT CARD - {s_dict[view_roll].upper()}", t_month, class_name, section, incharge_name), file_name=f"ReportCard_{view_roll}.csv", mime="text/csv")
            with col_b2:
                single_pdf = generate_bulk_report_cards([view_roll], f_marks, class_name, course, branch, section, t_type, t_month)
                st.download_button("Download Report (PDF)", data=single_pdf, file_name=f"ReportCard_{view_roll}.pdf", mime="application/pdf", type="primary")

# ==========================================
# MODULE: MY TEACHING SETUP & PROFILE
# ==========================================
def update_user_in_db(user_dict):
    for i, u in enumerate(st.session_state.users_db):
        if u['username'] == user_dict['username']:
            st.session_state.users_db[i] = user_dict
            break
    save_data('users_db', st.session_state.users_db)
    st.session_state.current_user = user_dict

def render_profile_setup(user):
    st.subheader("⚙️ Complete Your Profile & Teaching Setup")
    is_incharge = user['role'] == "Class Incharge"
    
    with st.container(): 
        with st.form("profile_setup_form"):
            if is_incharge:
                st.markdown("#### 1. Incharge Jurisdiction (Your Class)")
                c1, c2, c3, c4 = st.columns(4)
                with c1: inc_cls = st.selectbox("Class", st.session_state.settings_db['classes'])
                with c2: inc_crs = st.selectbox("Course", st.session_state.settings_db['courses'])
                with c3: inc_br = st.selectbox("Branch", st.session_state.settings_db['branches'])
                with c4: inc_sec = st.selectbox("Section", st.session_state.settings_db['sections'])
                st.divider()

            st.markdown("#### Teaching Assignments (Add subjects you teach)")
            tc1, tc2, tc3, tc4 = st.columns(4)
            with tc1: t_cls = st.selectbox("Select Class", st.session_state.settings_db['classes'], key="t1")
            with tc2: t_crs = st.selectbox("Select Course", st.session_state.settings_db['courses'], key="t2")
            with tc3: t_br = st.selectbox("Select Branch", st.session_state.settings_db['branches'], key="t3")
            with tc4: t_sec = st.selectbox("Select Section", st.session_state.settings_db['sections'], key="t4")
            t_subjs = st.multiselect("Select Subjects You Teach Here", st.session_state.settings_db['subjects'])
            
            if st.form_submit_button("Save & Complete Setup"):
                user['profile_setup'] = True
                if is_incharge:
                    user['incharge_class'] = inc_cls
                    user['incharge_course'] = inc_crs
                    user['incharge_branch'] = inc_br
                    user['incharge_section'] = inc_sec
                if 'teaching_assignments' not in user: user['teaching_assignments'] = []
                for s in t_subjs:
                    assg = {"class_name": t_cls, "course": t_crs, "branch": t_br, "section": t_sec, "subject": s}
                    if assg not in user['teaching_assignments']: user['teaching_assignments'].append(assg)
                update_user_in_db(user)
                st.success("Profile Setup Complete! Redirecting...")
                st.rerun()

    if user.get('teaching_assignments'):
        st.markdown("#### Current Teaching Assignments")
        df_a = pd.DataFrame(user['teaching_assignments']).rename(columns={'class_name':'CLASS', 'course':'COURSE', 'branch':'BRANCH', 'section':'SECTION', 'subject':'SUBJECT'})
        df_a.columns = df_a.columns.str.upper()
        st.table(df_a)
        if st.button("Clear All Assignments (Reset)"):
            user['teaching_assignments'] = []
            update_user_in_db(user)
            st.rerun()

# ==========================================
# MODULE: TEST CREATION & MARKS ENTRY
# ==========================================
def render_test_and_marks_module(user):
    assignments = user.get('teaching_assignments', [])
    if not assignments:
        st.warning("Please add teaching assignments in 'My Teaching Setup' to create tests.")
        return

    tab_create, tab_marks = st.tabs(["Create New Test", "Enter Marks"])
    with tab_create:
        msg_c = st.empty()
        assg_opts = [f"{a['class_name']} | {a['course']} | {a['branch']} | {a['section']} -> {a['subject']}" for a in assignments]
        fc1, fc2 = st.columns([2, 1])
        with fc1:
            with st.form("create_test_form", clear_on_submit=True):
                sel_assg = st.selectbox("Select Class & Subject", assg_opts)
                
                c_1, c_2 = st.columns(2)
                t_type = c_1.selectbox("Test Type", ["Monthly Test", "Weekly Test", "Class Test", "Mid Term", "Final Term"])
                t_marks = c_2.number_input("Total Marks", min_value=1.0, value=None)
                
                d1, d2 = st.columns(2)
                with d1: t_date = st.date_input("Test Date", date.today())
                with d2: st.info(f"**Day:** {t_date.strftime('%A')}")
                
                t_syl = st.text_area("Syllabus")
                
                if st.form_submit_button("Create Test"):
                    if t_marks is None: msg_c.error("Enter Total Marks.")
                    else:
                        parts = sel_assg.split(" -> ")
                        meta = parts[0].split(" | ")
                        test_data = {
                            "test_id": f"{meta[0]}_{meta[1]}_{meta[3]}_{meta[2]}_{parts[1]}_{t_date}_{t_type}",
                            "class_name": meta[0], "course": meta[1], "branch": meta[2], "section": meta[3],
                            "subject": parts[1], "test_type": t_type, "syllabus": t_syl, 
                            "date": str(t_date), "day": t_date.strftime('%A'), "total_marks": t_marks, "teacher": user['name']
                        }
                        st.session_state.tests_db.append(test_data)
                        save_data('tests_db', st.session_state.tests_db)
                        msg_c.success("Test Created Successfully!")

    with tab_marks:
        msg_m = st.empty()
        my_tests = [t for t in st.session_state.tests_db if t['teacher'] == user['name']]
        if my_tests:
            mc1, mc2 = st.columns([1, 2])
            t_opts = [f"{t['class_name']} - {t['section']} | {t['test_type']} - {t['subject']} ({format_date_ddmmyyyy(t['date'])})" for t in my_tests]
            sel_t_str = mc1.selectbox("Select Test", t_opts)
            
            t_meta = sel_t_str.split(" | ")
            c_s = t_meta[0].split(" - ")
            t_s = t_meta[1].split(" - ")
            date_s = t_s[1].split(" (")[1].replace(")", "")
            
            sel_test = next(t for t in my_tests if t['class_name']==c_s[0] and t['section']==c_s[1] and t['test_type']==t_s[0] and t['subject']==t_s[1].split(" (")[0] and format_date_ddmmyyyy(t['date'])==date_s)
            sec_st = [s for s in st.session_state.students_db if s['section'] == sel_test['section'] and s['class_name'] == sel_test['class_name'] and s['course'] == sel_test['course'] and s['branch'] == sel_test['branch']]
            
            if sec_st:
                sec_st = sorted(sec_st, key=lambda x: str(x['roll_no']))
                st.write(f"**Total Marks:** {fmt_mark(sel_test['total_marks'])}")
                
                fm1, fm2 = st.columns([1, 1])
                with fm1:
                    with st.form("marks_entry_form"):
                        md_list = []
                        for s in sec_st:
                            c_n, c_m = st.columns([3, 2])
                            c_n.write(f"{s['roll_no']} - {s['name'].upper()}")
                            obt = c_m.number_input("Obtained", min_value=0.0, max_value=float(sel_test['total_marks']), value=None, label_visibility="collapsed", key=f"m_{s['roll_no']}")
                            md_list.append({"roll_no": s['roll_no'], "name": s['name'], "obtained": obt})
                        
                        if st.form_submit_button("Save Marks"):
                            if any(md['obtained'] is None for md in md_list): msg_m.error("Enter marks for all students.")
                            else:
                                st.session_state.marks_db = [m for m in st.session_state.marks_db if m.get('test_id') != sel_test['test_id']]
                                for md in md_list:
                                    perc = (md['obtained'] / sel_test['total_marks']) * 100
                                    st.session_state.marks_db.append({
                                        "test_id": sel_test['test_id'], "class_name": sel_test['class_name'], "course": sel_test['course'], "section": sel_test['section'], "branch": sel_test['branch'],
                                        "subject": sel_test['subject'], "test_type": sel_test['test_type'], "date": sel_test['date'],
                                        "roll_no": md['roll_no'], "student_name": md['name'], "total_marks": sel_test['total_marks'], 
                                        "obtained_marks": md['obtained'], "percentage": round(perc, 2), "teacher": user['name']
                                    })
                                save_data('marks_db', st.session_state.marks_db)
                                msg_m.success("Marks saved!")
            else: msg_m.warning("No students in this section.")
        else: msg_m.info("No tests created yet.")

# ==========================================
# MAIN UI & AUTH
# ==========================================
col_logo, col_title = st.columns([1, 10])
with col_logo:
    if os.path.exists("image_500c0a.png"): st.image("image_500c0a.png", width=70)
with col_title:
    st.title("🎓 Superior College Okara - Management System")

if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["Login", "Admin Sign Up"])
    with tab1:
        l1, l2, l3 = st.columns([1, 2, 1])
        with l2:
            st.subheader("Login to Portal")
            msg_log = st.empty()
            l_user = st.text_input("Username")
            l_pass = st.text_input("Password", type="password")
            if st.button("Login", use_container_width=True):
                found = False
                for u in st.session_state.users_db:
                    if u.get('username') == l_user and u.get('password') == l_pass:
                        st.session_state.logged_in = True
                        st.session_state.current_user = u
                        found = True
                        st.rerun()
                if not found: msg_log.error("Invalid Credentials!")
            
    with tab2:
        r1, r2 = st.columns([2, 1])
        with r1:
            st.subheader("Admin Only Registration")
            msg_reg = st.empty()
            role = st.selectbox("Role", ["Principal", "Vice Principal", "Controller of Examinations"])
            
            c_n, c_u = st.columns(2)
            r_name = c_n.text_input("Name")
            r_usr = c_u.text_input("Username", key="r_usr")
            
            c_p, c_cp = st.columns(2)
            r_pwd = c_p.text_input("Password", type="password", key="r_pwd")
            c_pwd = c_cp.text_input("Confirm Password", type="password")
            if c_pwd and r_pwd != c_pwd: st.error("Passwords do not match!")
            
            if st.button("Register Admin", use_container_width=True):
                if not r_name or not r_usr or not r_pwd: msg_reg.error("Fill all fields.")
                elif r_pwd != c_pwd: msg_reg.error("Passwords mismatch.")
                elif check_single_role_exists(role): msg_reg.error(f"{role} already exists.")
                else:
                    user = {"name": r_name, "username": r_usr, "password": r_pwd, "role": role, "profile_setup": True}
                    st.session_state.users_db.append(user)
                    save_data('users_db', st.session_state.users_db)
                    msg_reg.success("Admin registered! Please Login.")

else:
    user = st.session_state.current_user
    c1, c2 = st.columns([9, 1])
    c1.write(f"### Welcome, {user['name'].upper()} ({user['role']})")
    if c2.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.rerun()
    st.divider()

    if user['role'] in ["Teacher", "Class Incharge"] and not user.get('profile_setup'):
        render_profile_setup(user)
    
    # --- MANAGEMENT DASHBOARD ---
    elif user['role'] in ["Principal", "Vice Principal", "Controller of Examinations"]:
        st.markdown("### 📊 College Daily Attendance Overview")
        od1, od2 = st.columns([1, 3])
        ov_date_m = od1.date_input("Select Date", date.today(), key="ov_m")
        
        tot_b = len([s for s in st.session_state.students_db if s.get('branch')=='Boys'])
        tot_g = len([s for s in st.session_state.students_db if s.get('branch')=='Girls'])
        abs_b, abs_g, abs_all = 0, 0, 0
        for r in [a for a in st.session_state.attendance_db if a['date'] == str(ov_date_m)]:
            for roll in r.get('absent_students', []):
                st_db = next((s for s in st.session_state.students_db if str(s['roll_no'])==str(roll) and s.get('class_name')==r['class_name']), None)
                if st_db:
                    abs_all += 1
                    if st_db.get('branch') == 'Boys': abs_b += 1
                    elif st_db.get('branch') == 'Girls': abs_g += 1
        
        m_c1, m_c2, m_c3 = st.columns(3)
        m_c1.metric("TOTAL STUDENTS", len(st.session_state.students_db))
        m_c2.metric("TOTAL PRESENT", len(st.session_state.students_db) - abs_all)
        m_c3.metric("TOTAL ABSENT", abs_all)
        
        m_d1, m_d2, m_d3, m_d4 = st.columns(4)
        m_d1.metric("BOYS TOTAL", tot_b)
        m_d2.metric("BOYS ABSENT", abs_b)
        m_d3.metric("GIRLS TOTAL", tot_g)
        m_d4.metric("GIRLS ABSENT", abs_g)
        st.divider()
        
        t_usr, t_stu, t_str, t_teach, t_rep = st.tabs(["👥 User Credentials", "🎓 Student Management", "🏗️ College Structure", "📚 My Teaching (Admin)", "📈 Reports"])
        with t_usr:
            st.subheader("Manage Teacher & Incharge Accounts")
            u1, u2 = st.columns([2, 1])
            with u1:
                with st.form("add_user_form", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    new_role = c1.selectbox("Role", ["Teacher", "Class Incharge"])
                    new_name = c2.text_input("Name")
                    c3, c4 = st.columns(2)
                    new_usr = c3.text_input("Username")
                    new_pwd = c4.text_input("Temp Password")
                    if st.form_submit_button("Create User"):
                        if not new_name or not new_usr or not new_pwd: st.error("Fill all fields.")
                        else:
                            st.session_state.users_db.append({"name": new_name, "username": new_usr, "password": new_pwd, "role": new_role, "profile_setup": False})
                            save_data('users_db', st.session_state.users_db)
                            st.success("User created!")
                            st.rerun()
            st.markdown("#### Edit Existing Users")
            edited_u = st.data_editor(pd.DataFrame(st.session_state.users_db), num_rows="dynamic", use_container_width=True)
            if st.button("Save User Changes"):
                st.session_state.users_db = edited_u.to_dict('records')
                save_data('users_db', st.session_state.users_db)
                st.success("Updated!")

        with t_stu:
            st.subheader("Student Database (Edit / Delete / Promote)")
            if st.session_state.students_db:
                edited_stu = st.data_editor(pd.DataFrame(st.session_state.students_db), num_rows="dynamic", use_container_width=True)
                if st.button("Save Student Changes"):
                    st.session_state.students_db = edited_stu.to_dict('records')
                    save_data('students_db', st.session_state.students_db)
                    st.success("Updated!")
            else: st.info("No students registered.")

        with t_str:
            st.subheader("Manage College Structure")
            sc1, sc2, sc3 = st.columns(3)
            cols_map = [sc1, sc2, sc3, sc1, sc2]
            for i, k in enumerate(st.session_state.settings_db.keys()):
                with cols_map[i % 5]:
                    st.markdown(f"**{k.upper()}**")
                    ed_set = st.data_editor(pd.DataFrame({k: st.session_state.settings_db[k]}), num_rows="dynamic", key=f"set_{k}")
                    st.session_state.settings_db[k] = ed_set[k].dropna().tolist()
            if st.button("Save Structure Changes"):
                save_data('settings_db', st.session_state.settings_db)
                st.success("Structure Updated!")

        with t_teach:
            render_profile_setup(user)
            st.divider()
            render_test_and_marks_module(user)

        with t_rep:
            rt1, rt2, rt3, rt4 = st.tabs(["Class Results", "Absentee Report", "Transport Users", "Student Lists"])
            with rt1:
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                with col_m1: sel_class = st.selectbox("Class", st.session_state.settings_db['classes'])
                with col_m2: sel_course = st.selectbox("Course", st.session_state.settings_db['courses'])
                with col_m3: sel_branch = st.selectbox("Branch", st.session_state.settings_db['branches'])
                with col_m4: sel_sec = st.selectbox("Section", get_section_options(sel_class, sel_course, sel_branch))
                section_marks = [m for m in st.session_state.marks_db if m.get('class_name') == sel_class and m.get('course') == sel_course and m.get('section') == sel_sec and m.get('branch') == sel_branch]
                render_report_card_module(section_marks, sel_class, sel_course, sel_branch, sel_sec)
            with rt2:
                ra1, ra2 = st.columns([1, 2])
                rep_date = ra1.date_input("Select Date", date.today(), key="r_dt")
                rep_data = []
                for a in [r for r in st.session_state.attendance_db if r['date'] == str(rep_date)]:
                    for roll in a.get('absent_students', []):
                        s = next((st for st in st.session_state.students_db if str(st['roll_no'])==str(roll) and st.get('class_name')==a['class_name']), None)
                        if s:
                            fu = next((f for f in st.session_state.followup_db if f['date']==str(rep_date) and str(f['roll_no'])==str(roll)), {})
                            inc = get_class_incharge(a['class_name'], a['course'], a['branch'], a['section'])
                            rep_data.append({"ROLL NO": str(roll), "NAME": s['name'].upper(), "CLASS": a['class_name'], "SECTION": a['section'], "INCHARGE": inc.upper(), "ATTENDED BY": fu.get('spoke_to', 'N/A').upper(), "REASON": fu.get('reason', 'N/A')})
                if rep_data:
                    df_rep = pd.DataFrame(rep_data)
                    df_rep = df_rep.sort_values(by='ROLL NO').reset_index(drop=True)
                    df_rep.insert(0, 'SR. NO.', range(1, len(df_rep) + 1))
                    df_rep.columns = df_rep.columns.str.upper()
                    st.dataframe(df_rep, use_container_width=True)
                    c_am1, c_am2 = st.columns(2)
                    with c_am1: st.download_button("Download Report (CSV)", data=generate_csv_with_header(df_rep, "COLLEGE ABSENTEE REPORT", rep_date), file_name=f"Absentee_{rep_date}.csv", mime="text/csv")
                    with c_am2: st.download_button("Download Report (PDF)", data=generate_pdf(df_rep, "COLLEGE ABSENTEE REPORT", rep_date), file_name=f"Absentee_{rep_date}.pdf", mime="application/pdf")
                else: st.info("No absentees.")
            with rt3:
                tr_st = [s for s in st.session_state.students_db if s.get('transport') == 'Yes']
                if tr_st: 
                    df_t = pd.DataFrame(tr_st).rename(columns={'name': 'NAME', 'roll_no': 'ROLL NO', 'class_name': 'CLASS', 'course': 'COURSE', 'section': 'SECTION', 'branch': 'BRANCH', 'contact1': 'CONTACT'})
                    display_t = df_t[['ROLL NO', 'NAME', 'CLASS', 'COURSE', 'SECTION', 'BRANCH', 'CONTACT']]
                    display_t['ROLL NO'] = display_t['ROLL NO'].astype(str)
                    display_t = display_t.sort_values(by='ROLL NO').reset_index(drop=True)
                    display_t.insert(0, 'SR. NO.', range(1, len(display_t) + 1))
                    display_t.columns = display_t.columns.str.upper()
                    st.dataframe(display_t, use_container_width=True)
                    c_tm1, c_tm2 = st.columns(2)
                    with c_tm1: st.download_button("Download Transport List (CSV)", data=generate_csv_with_header(display_t, "COLLEGE TRANSPORT USERS", date.today()), file_name="Transport.csv", mime="text/csv")
                    with c_tm2: st.download_button("Download Transport List (PDF)", data=generate_pdf(display_t, "COLLEGE TRANSPORT USERS", date.today()), file_name="Transport.pdf", mime="application/pdf")
                else: st.info("No transport users.")
            with rt4:
                st.subheader("Section-wise Student List")
                col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                with col_s1: sel_s_class = st.selectbox("Class", st.session_state.settings_db['classes'], key="s_cls")
                with col_s2: sel_s_course = st.selectbox("Course", st.session_state.settings_db['courses'], key="s_crs")
                with col_s3: sel_s_branch = st.selectbox("Branch", st.session_state.settings_db['branches'], key="s_br")
                with col_s4: sel_s_sec = st.selectbox("Section", get_section_options(sel_s_class, sel_s_course, sel_s_branch), key="s_sec")
                s_list = [s for s in st.session_state.students_db if s.get('class_name')==sel_s_class and s.get('course')==sel_s_course and s.get('section')==sel_s_sec and s.get('branch')==sel_s_branch]
                if s_list:
                    df_s = pd.DataFrame(s_list).rename(columns={'name': 'NAME', 'father_name': 'FATHER NAME', 'roll_no': 'ROLL NO', 'contact1': 'CONTACT', 'transport': 'TRANSPORT'})
                    display_s = df_s[['ROLL NO', 'NAME', 'FATHER NAME', 'CONTACT', 'TRANSPORT']]
                    display_s['ROLL NO'] = display_s['ROLL NO'].astype(str)
                    display_s = display_s.sort_values(by='ROLL NO').reset_index(drop=True)
                    display_s.insert(0, 'SR. NO.', range(1, len(display_s) + 1))
                    display_s.columns = display_s.columns.str.upper()
                    st.dataframe(display_s, use_container_width=True)
                    inc_n = get_class_incharge(sel_s_class, sel_s_course, sel_s_branch, sel_s_sec)
                    c_sl1, c_sl2 = st.columns(2)
                    with c_sl1: st.download_button("Download List (CSV)", data=generate_csv_with_header(display_s, "STUDENT LIST", date.today(), sel_s_class, sel_s_sec, inc_n), file_name=f"Students_{sel_s_class}_{sel_s_sec}.csv", mime="text/csv")
                    with c_sl2: st.download_button("Download List (PDF)", data=generate_pdf(display_s, "STUDENT LIST", date.today(), sel_s_class, sel_s_sec, inc_n), file_name=f"Students_{sel_s_class}_{sel_s_sec}.pdf", mime="application/pdf")
                else: st.info("No students found in this section.")

    # --- TEACHER DASHBOARD ---
    elif user['role'] == "Teacher":
        st.markdown("### 📊 My Teacher Dashboard")
        t_teach, t_marks, t_stu, t_abs, t_prof = st.tabs(["📝 Create Test/Marks", "📈 My Results", "🎓 Class Students", "📅 Absentee Report", "⚙️ Setup"])
        with t_teach: render_test_and_marks_module(user)
        with t_marks: 
            my_m = [m for m in st.session_state.marks_db if m.get('teacher') == user['name']]
            st.subheader("My Uploaded Results")
            if not my_m: st.info("No marks data available. Please enter marks for a test first.")
            else:
                t_groups = list(set([f"{m['class_name']} - {m['section']} | {m['test_type']} - {m['subject']} ({m.get('date', 'N/A')})" for m in my_m]))
                tr1, tr2 = st.columns([1, 2])
                s_test = tr1.selectbox("Select Test to View", t_groups)
                if s_test:
                    cls_sec = s_test.split(" | ")[0]
                    t_cls = cls_sec.split(" - ")[0]
                    t_sec = cls_sec.split(" - ")[1]
                    t_type = s_test.split(" | ")[1].split(" - ")[0]
                    t_subj = s_test.split(" - ")[2].split(" (")[0]
                    t_date = s_test.split(" (")[1].replace(")", "")
                    f_marks = [m for m in my_m if m['test_type'] == t_type and m['subject'] == t_subj and m.get('date', 'N/A') == t_date and m['class_name'] == t_cls and m['section'] == t_sec]
                    if f_marks:
                        inc_name = get_class_incharge(t_cls, f_marks[0]['course'], f_marks[0]['branch'], t_sec)
                        data = []
                        for m in f_marks:
                            data.append({"ROLL NO": str(m['roll_no']), "STUDENT NAME": m['student_name'].upper(), "TOTAL MARKS": fmt_mark(m['total_marks']), "OBTAINED MARKS": fmt_mark(m['obtained_marks']), "PERCENTAGE": f"{m['percentage']}%"})
                        df = pd.DataFrame(data)
                        df['ROLL NO'] = pd.to_numeric(df['ROLL NO'], errors='coerce')
                        df = df.sort_values(by='ROLL NO').reset_index(drop=True)
                        df['ROLL NO'] = df['ROLL NO'].astype(str).str.replace(".0", "", regex=False)
                        df.insert(0, 'SR. NO.', range(1, len(df) + 1))
                        df.columns = df.columns.str.upper()
                        st.dataframe(df, use_container_width=True)
                        st.divider()
                        c1, c2 = st.columns(2)
                        title = f"SUBJECT RESULT: {t_subj.upper()} - {t_type.upper()}"
                        with c1: st.download_button("Download Result (CSV)", data=generate_csv_with_header(df, title, t_date, t_cls, t_sec, inc_name), file_name=f"Result_{t_subj}_{t_cls}.csv", mime="text/csv")
                        with c2: st.download_button("Download Result (PDF)", data=generate_pdf(df, title, t_date, t_cls, t_sec, inc_name), file_name=f"Result_{t_subj}_{t_cls}.pdf", mime="application/pdf")

        with t_stu:
            st.subheader("My Class Students")
            assignments = user.get('teaching_assignments', [])
            if assignments:
                assg_opts = list(set([f"{a['class_name']} | {a['course']} | {a['branch']} | {a['section']}" for a in assignments]))
                cs1, cs2 = st.columns([1, 2])
                sel_assg = cs1.selectbox("Select Class", assg_opts)
                if sel_assg:
                    c, crs, br, sec = sel_assg.split(" | ")
                    st_list = [s for s in st.session_state.students_db if s.get('class_name')==c and s.get('course')==crs and s.get('branch')==br and s.get('section')==sec]
                    if st_list:
                        df = pd.DataFrame(st_list)[['roll_no', 'name', 'father_name', 'contact1', 'transport']]
                        df.rename(columns={'roll_no':'ROLL NO', 'name':'NAME', 'father_name':'FATHER NAME', 'contact1':'CONTACT', 'transport':'TRANSPORT'}, inplace=True)
                        df['ROLL NO'] = df['ROLL NO'].astype(str)
                        df = df.sort_values(by='ROLL NO').reset_index(drop=True)
                        df.insert(0, 'SR. NO.', range(1, len(df) + 1))
                        df.columns = df.columns.str.upper()
                        st.dataframe(df, use_container_width=True)
                    else: st.info("No students in this class.")
            else: st.warning("No assignments setup yet.")
            
        with t_abs:
            st.subheader("Absentee Report (My Classes)")
            if assignments:
                assg_opts = list(set([f"{a['class_name']} | {a['course']} | {a['branch']} | {a['section']}" for a in assignments]))
                ca1, ca2, ca3 = st.columns([1, 1, 1])
                sel_assg_a = ca1.selectbox("Select Class", assg_opts, key="t_abs_sel")
                rep_date_t = ca2.date_input("Select Date", date.today(), key="t_abs_dt")
                if sel_assg_a:
                    c, crs, br, sec = sel_assg_a.split(" | ")
                    rep_data_t = []
                    att_rec = next((r for r in st.session_state.attendance_db if r['date'] == str(rep_date_t) and r.get('class_name')==c and r.get('section')==sec and r.get('branch')==br), None)
                    if att_rec:
                        for roll in att_rec.get('absent_students', []):
                            student = next((s for s in st.session_state.students_db if str(s['roll_no'])==str(roll) and s.get('class_name')==c and s.get('section')==sec), None)
                            if student:
                                fu = next((f for f in st.session_state.followup_db if f['date']==str(rep_date_t) and str(f['roll_no'])==str(roll)), {})
                                rep_data_t.append({"ROLL NO": str(roll), "NAME": student['name'].upper(), "ATTENDED BY": fu.get('spoke_to', 'Pending').upper(), "REASON": fu.get('reason', 'Pending')})
                        if rep_data_t: 
                            df_rep = pd.DataFrame(rep_data_t)
                            df_rep['ROLL NO'] = pd.to_numeric(df_rep['ROLL NO'], errors='coerce')
                            df_rep = df_rep.sort_values(by='ROLL NO').reset_index(drop=True)
                            df_rep['ROLL NO'] = df_rep['ROLL NO'].astype(str).str.replace(".0", "", regex=False)
                            df_rep.insert(0, 'SR. NO.', range(1, len(df_rep) + 1))
                            df_rep.columns = df_rep.columns.str.upper()
                            st.dataframe(df_rep, use_container_width=True)
                        else: st.info("No absentees.")
                    else: st.info("Attendance not marked for this date.")
            else: st.warning("No assignments setup yet.")
            
        with t_prof: render_profile_setup(user)

    # --- CLASS INCHARGE DASHBOARD ---
    elif user['role'] == "Class Incharge":
        my_cls, my_crs, my_br, my_sec = user.get('incharge_class'), user.get('incharge_course'), user.get('incharge_branch'), user.get('incharge_section')
        incharge_name = user['name']
        
        st.markdown(f"### 📊 Incharge Overview: {my_cls} | {my_sec} ({my_br})")
        od1, od2 = st.columns([1, 3])
        ov_date = od1.date_input("Select Date", date.today(), key="ov_inc")
        my_st = [s for s in st.session_state.students_db if s.get('class_name')==my_cls and s.get('section')==my_sec and s.get('branch')==my_br]
        att_r = next((r for r in st.session_state.attendance_db if r['date']==str(ov_date) and r.get('class_name')==my_cls and r.get('section')==my_sec), None)
        
        abs_n = len(att_r['absent_students']) if att_r else 0
        c1, c2, c3 = st.columns(3)
        c1.metric("TOTAL STUDENTS", len(my_st))
        c2.metric("PRESENT", len(my_st) - abs_n if att_r else 0)
        c3.metric("ABSENT", abs_n)
        st.divider()
        
        t_reg, t_att, t_teach, t_rep, t_prof = st.tabs(["📝 Students (Add/Edit)", "📅 Attendance & Absentees", "📚 Tests & Marks", "📈 Results", "⚙️ Setup"])
        
        with t_reg:
            rg1, rg2 = st.columns([1, 1])
            with rg1:
                st.subheader("Add New Student")
                msg_reg = st.empty()
                with st.form("student_registration_form", clear_on_submit=True):
                    c_1, c_2 = st.columns(2)
                    s_n = c_1.text_input("Student Name")
                    s_f = c_2.text_input("Father's Name")
                    c_3, c_4 = st.columns(2)
                    s_r = c_3.text_input("Roll Number")
                    s_tr = c_4.checkbox("Uses Transport")
                    
                    c_5, c_6 = st.columns(2)
                    s_c1 = c_5.text_input("Contact 1", max_chars=11)
                    s_c2 = c_6.text_input("Contact 2", max_chars=11)
                    
                    if st.form_submit_button("Add Student"):
                        if s_n and s_r:
                            st.session_state.students_db.append({"class_name": my_cls, "course": my_crs, "branch": my_br, "section": my_sec, "name": s_n, "father_name": s_f, "roll_no": s_r, "contact1": s_c1, "contact2": s_c2, "transport": "Yes" if s_tr else "No"})
                            save_data('students_db', st.session_state.students_db)
                            msg_reg.success(f"{s_n.upper()} Added!")
                            st.rerun()
                        else: msg_reg.error("Name and Roll required.")
            
            st.markdown("#### Edit Class Students")
            if my_st:
                df_my = pd.DataFrame(my_st)
                ed_my = st.data_editor(df_my, num_rows="dynamic")
                if st.button("Save Edits"):
                    st.session_state.students_db = [s for s in st.session_state.students_db if not (s.get('class_name')==my_cls and s.get('section')==my_sec and s.get('branch')==my_br)]
                    st.session_state.students_db.extend(ed_my.to_dict('records'))
                    save_data('students_db', st.session_state.students_db)
                    st.success("Changes saved!")
                
                df_dl = pd.DataFrame(my_st).rename(columns={'name': 'NAME', 'father_name': 'FATHER NAME', 'roll_no': 'ROLL NO', 'contact1': 'CONTACT', 'transport': 'TRANSPORT'})
                display_dl = df_dl[['ROLL NO', 'NAME', 'FATHER NAME', 'CONTACT', 'TRANSPORT']]
                display_dl['ROLL NO'] = pd.to_numeric(display_dl['ROLL NO'], errors='coerce')
                display_dl = display_dl.sort_values(by='ROLL NO').reset_index(drop=True)
                display_dl['ROLL NO'] = display_dl['ROLL NO'].astype(str).str.replace(".0", "", regex=False)
                display_dl.insert(0, 'SR. NO.', range(1, len(display_dl) + 1))
                display_dl.columns = display_dl.columns.str.upper()
                
                c_sdl1, c_sdl2 = st.columns(2)
                with c_sdl1: st.download_button("Download Class List (CSV)", data=generate_csv_with_header(display_dl, "REGISTERED STUDENTS LIST", date.today(), my_cls, my_sec, incharge_name), file_name=f"Students_{my_cls}_{my_sec}.csv", mime="text/csv")
                with c_sdl2: st.download_button("Download Class List (PDF)", data=generate_pdf(display_dl, "REGISTERED STUDENTS LIST", date.today(), my_cls, my_sec, incharge_name), file_name=f"Students_{my_cls}_{my_sec}.pdf", mime="application/pdf")

        with t_att:
            at1, at2 = st.columns([1, 1])
            with at1:
                st.subheader("Mark Daily Attendance")
                msg_att = st.empty()
                att_d = st.date_input("Attendance Date", date.today())
                if my_st:
                    my_st_sorted = sorted(my_st, key=lambda x: str(x['roll_no']))
                    with st.form("att_f"):
                        abs_rolls = []
                        for s in my_st_sorted:
                            if st.checkbox(f"{s['roll_no']} - {s['name'].upper()}", key=f"att_{s['roll_no']}"): abs_rolls.append(s['roll_no'])
                        if st.form_submit_button("Save Attendance", use_container_width=True):
                            st.session_state.attendance_db.append({"date": str(att_d), "class_name": my_cls, "course": my_crs, "section": my_sec, "branch": my_br, "absent_students": abs_rolls})
                            save_data('attendance_db', st.session_state.attendance_db)
                            msg_att.success("Attendance saved successfully!")
                            st.rerun()
            st.divider()
            st.subheader("Absentee Follow-up")
            msg_follow = st.empty()
            fud1, fud2 = st.columns([1, 2])
            fu_d = fud1.date_input("Follow-up Date", date.today(), key="fu_inc")
            fu_r = next((r for r in st.session_state.attendance_db if r['date']==str(fu_d) and r.get('class_name')==my_cls and r.get('section')==my_sec), None)
            
            if fu_r and fu_r['absent_students']:
                fu_c1, fu_c2 = st.columns(2)
                with fu_c1:
                    for roll in sorted(fu_r['absent_students'], key=lambda x: str(x)):
                        s = next((st for st in my_st if str(st['roll_no'])==str(roll)), None)
                        if s:
                            with st.expander(f"📞 Call: {s['name'].upper()} (Roll: {roll})"):
                                st.write(f"**Primary Contact:** {s['contact1']}")
                                with st.form(f"fu_{roll}"):
                                    spoke = st.text_input("Attended By")
                                    rsn = st.text_area("Reason")
                                    if st.form_submit_button("Save"):
                                        st.session_state.followup_db.append({"date": str(fu_d), "class_name": my_cls, "section": my_sec, "branch": my_br, "roll_no": roll, "spoke_to": spoke, "reason": rsn})
                                        save_data('followup_db', st.session_state.followup_db)
                                        msg_follow.success("Done!")
                
                st.markdown("#### Today's Follow-up Summary")
                sum_d = []
                for roll in fu_r['absent_students']:
                    s = next((st for st in my_st if str(st['roll_no'])==str(roll)), None)
                    if s:
                        f_rec = next((f for f in st.session_state.followup_db if f['date']==str(fu_d) and str(f['roll_no'])==str(roll) and f.get('class_name')==my_cls), {})
                        sum_d.append({"ROLL NO": str(roll), "NAME": s['name'].upper(), "CONTACT": s['contact1'], "ATTENDED BY": f_rec.get('spoke_to', 'Pending').upper(), "REASON": f_rec.get('reason', 'Pending')})
                if sum_d:
                    df_sum = pd.DataFrame(sum_d)
                    df_sum['ROLL NO'] = pd.to_numeric(df_sum['ROLL NO'], errors='coerce')
                    df_sum = df_sum.sort_values(by='ROLL NO').reset_index(drop=True)
                    df_sum['ROLL NO'] = df_sum['ROLL NO'].astype(str).str.replace(".0", "", regex=False)
                    df_sum.insert(0, 'SR. NO.', range(1, len(df_sum) + 1))
                    df_sum.columns = df_sum.columns.str.upper()
                    st.dataframe(df_sum, use_container_width=True)
                    c_f1, c_f2 = st.columns(2)
                    with c_f1: st.download_button("Download Summary (CSV)", data=generate_csv_with_header(df_sum, "ABSENTEE FOLLOW-UP SUMMARY", fu_d, my_cls, my_sec, incharge_name), file_name=f"Followup_{fu_d}.csv", mime="text/csv")
                    with c_f2: st.download_button("Download Summary (PDF)", data=generate_pdf(df_sum, "ABSENTEE FOLLOW-UP SUMMARY", fu_d, my_cls, my_sec, incharge_name), file_name=f"Followup_{fu_d}.pdf", mime="application/pdf")
            elif fu_r: st.success("No absentees!")
            else: st.warning("Attendance not marked.")
            
        with t_teach: render_test_and_marks_module(user)
        with t_rep: 
            sec_m = [m for m in st.session_state.marks_db if m.get('class_name')==my_cls and m.get('section')==my_sec and m.get('branch')==my_br]
            render_report_card_module(sec_m, my_cls, my_crs, my_br, my_sec)
        with t_prof: render_profile_setup(user)
