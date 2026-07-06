import streamlit as st
import pandas as pd
import datetime
import io
import sqlite3  # Maktaba ya SQLite Database
import plotly.express as px

# Maktaba za ReportLab kwa ajili ya PDF ya Kisasa
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


# 1. TAMBULISHA DATABASE HAPA JUU KABISA
DB_FILE = "database.db"

# 2. INITIALIZE SESSION STATE
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None
if 'username' not in st.session_state:
    st.session_state.username = None


#######################################################   LOGIN FORM LOPGISTICS   ############################################################

def login_form():
    st.markdown("<h1 style='text-align: center;'>🌳MPJ SCHOOL FINANCIALS MS</h1>", unsafe_allow_html=True)
    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Ingia", use_container_width=True)
        
        if submit:
            if username and password:
                # Tunafungua database na kutafuta mtumiaji
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                
                # Tunatumia .lower() kuhakikisha username inasoma hata kama aliandika kwa herufi kubwa
                cursor.execute("SELECT role FROM users WHERE username=? AND password=?", (username.lower(), password))
                user_data = cursor.fetchone()
                conn.close()
                
                if user_data:
                    # Kama amepatikana kwenye Database
                    st.session_state.logged_in = True
                    st.session_state.user_role = user_data[0]  # Inachukua cheo (Admin au User)
                    st.session_state.username = username.lower() # Inatunza jina lake kuzuia asijifute kimakosa
                    st.rerun()
                else:
                    st.error("❌ Username au Password siyo sahihi! Au mtumiaji huyu hayupo.")
            else:
                st.warning("⚠️ Tafadhali jaza Username na Password.")

# 2. Force Login check
if not st.session_state.logged_in:
    login_form()
    st.stop() # Hii inazuia page zingine zisionekane kabla ya login



# 1. Page Configuration
st.set_page_config(page_title="School Financial Management System", layout="centered")


#========================== Hii inasoma logo kutoka database kama BLOB na kuiweka kwenye sidebar ===========================#
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()
cursor.execute("SELECT Logo_Blob FROM system_settings LIMIT 1")
row = cursor.fetchone()
conn.close()

if row and row[0] is not None:
    logo_data = row[0]
    # Tunatumia st.sidebar.image moja kwa moja na data ya binary
    st.sidebar.image(logo_data, use_container_width=True)
else:
    st.sidebar.info("💡 Weka Logo ya Shule kwenye Settings")



################################### Custom CSS kwa ajili ya rangi ktk Sidebar ##############################################
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: ##0284C7; /* Hii ni rangi ya Light Blue */
    }
    </style>
""", unsafe_allow_html=True)


DB_FILE = "database.db"

# === KAZI YA KUANZISHA NA KUUNGANISHA DATABASE YA SQLITE ===
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()


    # 1. Jedwali la Usajili wa Wanafunzi
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            ID TEXT PRIMARY KEY,
            Name TEXT,
            Class TEXT,
            Gender TEXT,
            Hostel_Status TEXT,
            Address TEXT,
            Parent_Phone TEXT,
            Admission_Date TEXT
        )
    """)
    
    # 2. Jedwali la Ada
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fees (
            ID TEXT PRIMARY KEY,
            Name TEXT,
            Class TEXT,
            Gender TEXT,
            Hostel_Status TEXT,
            Address TEXT,
            Phone TEXT,
            Admission_Date TEXT,
            Q1 INTEGER,
            Q2 INTEGER,
            Q3 INTEGER,
            Q4 INTEGER,
            Total_Fee INTEGER,
            Total_Paid INTEGER,
            Status TEXT,
            Owings INTEGER
           
        )
    """)
    
    # 3. Jedwali la Michango Mingine
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS other_contributions (
            ID TEXT PRIMARY KEY,
            Name TEXT,
            Class TEXT,
            Gender TEXT,
            Hostel_Status TEXT,
            Address TEXT,
            Phone TEXT,
            Admission_Date TEXT,
            Tahadhari INTEGER,
            Kitambulisho INTEGER,
            Taaluma INTEGER,
            Michezo INTEGER,
            Ukarabati INTEGER,
            Mitihani_FII INTEGER,
            Mitihani_FIV INTEGER,
            Bima INTEGER,
            Total_Contribution INTEGER,
            Amount_Paid INTEGER,
            Status TEXT,
            Owings INTEGER
        )
    """)

    # 4. Jedwali la Matumizi
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            SN INTEGER PRIMARY KEY AUTOINCREMENT,
            Maelezo TEXT,
            Kiasi INTEGER,
            Tarehe TEXT
        )
    """)

    # 5. JEDWALI JIPYA: System Settings (Control Sheet Table) - Limeongezewa nguzo za michango mingine
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            id INTEGER PRIMARY KEY DEFAULT 1,
            School_Name TEXT,
            Location TEXT,
            Box_No TEXT,
            Phone TEXT,
            Fee_Hostel INTEGER,
            Fee_Day INTEGER,
            Req_Tahadhari INTEGER DEFAULT 10000,
            Req_Kitambulisho INTEGER DEFAULT 5000,
            Req_Taaluma INTEGER DEFAULT 20000,
            Req_Michezo INTEGER DEFAULT 5000,
            Req_Ukarabati INTEGER DEFAULT 10000,
            Req_Mitihani_FII INTEGER DEFAULT 0,
            Req_Mitihani_FIV INTEGER DEFAULT 0,
            Req_Bima INTEGER DEFAULT 54400
           
        )
    """)
    

    # Weka data za mwanzo kama jedwali lipo tupu au fanya uboreshaji (migration) kama nguzo mpya hazipo
    cursor.execute("SELECT COUNT(*) FROM system_settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO system_settings (id, School_Name, Location, Box_No, Phone, Fee_Hostel, Fee_Day, 
            Req_Tahadhari, Req_Kitambulisho, Req_Taaluma, Req_Michezo, Req_Ukarabati, Req_Mitihani_FII, Req_Mitihani_FIV, Req_Bima)
            VALUES (1, 'HOLLWOOD HIGH SCHOOL', 'SONGWE MBOZI', 'P.O.BOX xxxx MBOZI', '0655402558', 1100000, 400000,
            10000, 5000, 20000, 5000, 10000, 0, 0, 54400)
        """)
    else:
        # Kuzuia makosa kama unaupgrade kutoka database ya zamani, ongeza nguzo mpya kama hazipo
        try:
            cursor.execute("ALTER TABLE system_settings ADD COLUMN Req_Tahadhari INTEGER DEFAULT 10000")
            cursor.execute("ALTER TABLE system_settings ADD COLUMN Req_Kitambulisho INTEGER DEFAULT 5000")
            cursor.execute("ALTER TABLE system_settings ADD COLUMN Req_Taaluma INTEGER DEFAULT 20000")
            cursor.execute("ALTER TABLE system_settings ADD COLUMN Req_Michezo INTEGER DEFAULT 5000")
            cursor.execute("ALTER TABLE system_settings ADD COLUMN Req_Ukarabati INTEGER DEFAULT 10000")
            cursor.execute("ALTER TABLE system_settings ADD COLUMN Req_Mitihani_FII INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE system_settings ADD COLUMN Req_Mitihani_FIV INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE system_settings ADD COLUMN Req_Bima INTEGER DEFAULT 54400")
        except sqlite3.OperationalError:
            pass # Nguzo tayari zipo
        
    conn.commit()
    conn.close()


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # ... (jedwali zingine ulizokuwa nazo) ...
    
    # JEDWALI JIPYA LA WATUMIAJI
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            role TEXT
        )
    """)
    # Ongeza admin wa kwanza kama hayupo
    cursor.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?)", ("admin", "admin123", "Admin"))
    conn.commit()
    conn.close()

def check_login(username, password):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None

def add_user(username, password, role):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users VALUES (?, ?, ?)", (username, password, role))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()


# Anzisha database
init_db()

# Functions za kusoma settings kutoka kwenye database
def get_settings():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM system_settings WHERE id = 1", conn)
    conn.close()
    if not df.empty:
        return df.iloc[0].to_dict()
    return {
        "School_Name": "HOLLWOOD HIGH SCHOOL",
        "Location": "SONGWE MBOZI",
        "Box_No": "P.O.BOX xxxx MBOZI",
        "Phone": "0655402558",
        "Fee_Hostel": 1100000,
        "Fee_Day": 400000,
        "Req_Tahadhari": 10000,
        "Req_Kitambulisho": 5000,
        "Req_Taaluma": 20000,
        "Req_Michezo": 5000,
        "Req_Ukarabati": 10000,
        "Req_Mitihani_FII": 0,
        "Req_Mitihani_FIV": 0,
        "Req_Bima": 54400
    }

# Dynamic variables kutoka kwenye Control Sheet (Settings)
sys_settings = get_settings()
SCHOOL_NAME = sys_settings["School_Name"]
SCHOOL_LOCATION = sys_settings["Location"]
SCHOOL_BOX = sys_settings["Box_No"]
SCHOOL_PHONE = sys_settings["Phone"]
FEE_HOSTEL = sys_settings["Fee_Hostel"]
FEE_DAY = sys_settings["Fee_Day"]

# Maadili ya Kudumu ya Michango kutoka Control Sheet
REQ_TAHADHARI = sys_settings.get("Req_Tahadhari", 10000)
REQ_KITAMBULISHO = sys_settings.get("Req_Kitambulisho", 5000)
REQ_TAALUMA = sys_settings.get("Req_Taaluma", 20000)
REQ_MICHEZO = sys_settings.get("Req_Michezo", 5000)
REQ_UKARABATI = sys_settings.get("Req_Ukarabati", 10000)
REQ_MITIHANI_FII = sys_settings.get("Req_Mitihani_FII", 0)
REQ_MITIHANI_FIV = sys_settings.get("Req_Mitihani_FIV", 0)
REQ_BIMA = sys_settings.get("Req_Bima", 54400)

# Kazi za kusaidia kusoma data kutoka kwenye SQLite kwenda Pandas Dataframe
def get_students_df():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM students", conn)
    conn.close()
    return df

def get_fees_df():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM fees", conn)
    conn.close()
    return df

def get_other_df():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM other_contributions", conn)
    conn.close()
    return df

def get_expenses_df():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM expenses", conn)
    conn.close()
    return df

# Kuanzisha session state za kuediti
if 'edit_student_data' not in st.session_state:
    st.session_state.edit_student_data = None

# Custom CSS
st.markdown("""
    <style>
    .section-title { background-color: #000000; color: #ffffff; padding: 5px 10px; font-size: 14px; font-weight: bold; margin-bottom: 5px; }
    .institution-box { background-color: #FFFF00; color: #000000; padding: 15px; border-radius: 5px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# Helper function ya Excel download button
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Data')
    return output.getvalue()


  
####################################### Function ya PDF Receipt #######################################################

def generate_fee_pdf(student_info, q1, q2, q3, q4, tot_fee, tot_paid, owings, status_str):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=22, textColor=colors.HexColor('#1A365D'), alignment=1, spaceAfter=5, fontName="Helvetica-Bold")
    subtitle_style = ParagraphStyle('DocSub', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#4A5568'), alignment=1, spaceAfter=20)
    section_heading = ParagraphStyle('SectionHeading', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#2B6CB0'), spaceBefore=10, spaceAfter=10, fontName="Helvetica-Bold")
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#2D3748'), leading=14)
    
    story.append(Paragraph(SCHOOL_NAME, title_style))
    story.append(Paragraph(f"{SCHOOL_LOCATION} | {SCHOOL_BOX} | Simu: {SCHOOL_PHONE}", subtitle_style))
    story.append(Spacer(1, 10))
    
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    receipt_meta = [[Paragraph(f"<b>Namba ya Risiti:</b> EFT-{student_info['ID']}-{datetime.date.today().year}", body_style), Paragraph(f"<b>Tarehe ya Print:</b> {now}", body_style)]]
    t_meta = Table(receipt_meta, colWidths=[260, 260])
    story.append(t_meta)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("TAARIFA ZA MWANAFUNZI", section_heading))
    student_data = [
        [Paragraph("<b>Jina Kamili:</b>", body_style), Paragraph(str(student_info['Name']), body_style), Paragraph("<b>Namba ya Usajili (ID):</b>", body_style), Paragraph(str(student_info['ID']), body_style)],
        [Paragraph("<b>Darasa:</b>", body_style), Paragraph(str(student_info['Class']), body_style), Paragraph("<b>Jinsia:</b>", body_style), Paragraph(str(student_info['Gender']), body_style)],
        [Paragraph("<b>Hali ya Malazi:</b>", body_style), Paragraph(str(student_info['Hostel Status']), body_style), Paragraph("<b>Simu ya Mzazi:</b>", body_style), Paragraph(str(student_info['Parent Phone']), body_style)]
    ]
    t_student = Table(student_data, colWidths=[90, 170, 120, 140])
    t_student.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')), ('PADDING', (0,0), (-1,-1), 6), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0'))]))
    story.append(t_student)
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("MCHANGANUO WA MALIPO YA ADA", section_heading))
    fee_data = [
        [Paragraph("<b>Kipengele cha Muhula</b>", body_style), Paragraph("<b>Kiasi Kilicholipwa (TSHS)</b>", body_style)],
        [Paragraph("Ada ya Robo ya Kwanza (Q1)", body_style), Paragraph(f"{q1:,}", body_style)],
        [Paragraph("Ada ya Robo ya Pili (Q2)", body_style), Paragraph(f"{q2:,}", body_style)],
        [Paragraph("Ada ya Robo ya Tatu (Q3)", body_style), Paragraph(f"{q3:,}", body_style)],
        [Paragraph("Ada ya Robo ya Nne (Q4)", body_style), Paragraph(f"{q4:,}", body_style)],
        [Paragraph("<b>JUMLA YA ADA INAYOTAKIWA</b>", body_style), Paragraph(f"<b>{tot_fee:,}</b>", body_style)],
        [Paragraph("<b>JUMLA YA FEDHA ILIYOLIPWA</b>", body_style), Paragraph(f"<b>{tot_paid:,}</b>", body_style)],
        [Paragraph("<b>DENI / BALANSI INAYODAIWA</b>", body_style), Paragraph(f"<b>{owings:,}</b>", body_style)],
        [Paragraph("<b>HALI YA MALIPO (STATUS)</b>", body_style), Paragraph(f"<b>{status_str.upper()}</b>", body_style)]
    ]
    t_fee = Table(fee_data, colWidths=[300, 220])
    t_fee.setStyle(TableStyle([('BACKGROUND', (0,0), (1,0), colors.HexColor('#1A365D')), ('PADDING', (0,0), (-1,-1), 6), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')), ('BACKGROUND', (0,5), (1,5), colors.HexColor('#EDF2F7'))]))
    story.append(t_fee)
    story.append(Spacer(1, 40))
    
    sign_data = [[Paragraph("........................................................<br/><b>Saini ya Mhasibu</b>", body_style), Paragraph("........................................................<br/><b>Muhuri wa Taasisi</b>", body_style)]]
    t_sign = Table(sign_data, colWidths=[260, 260])
    story.append(t_sign)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def generate_expenses_pdf(expenses_df, jumla_matumizi, kuanzia, hadi):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=22, textColor=colors.HexColor('#1A365D'), alignment=1, spaceAfter=5, fontName="Helvetica-Bold")
    subtitle_style = ParagraphStyle('DocSub', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#4A5568'), alignment=1, spaceAfter=15)
    section_heading = ParagraphStyle('SectionHeading', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#2B6CB0'), spaceBefore=10, spaceAfter=10, fontName="Helvetica-Bold")
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#2D3748'), leading=14)
    header_table_style = ParagraphStyle('HeaderTable', parent=styles['Normal'], fontSize=10, textColor=colors.white, fontName="Helvetica-Bold")
    
    story.append(Paragraph(SCHOOL_NAME, title_style))
    story.append(Paragraph(f"{SCHOOL_LOCATION} | {SCHOOL_BOX} | Simu: {SCHOOL_PHONE}", subtitle_style))
    story.append(Spacer(1, 10))
    
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    report_meta = [
        [Paragraph(f"<b>Aina ya Ripoti:</b> Ripoti ya Matumizi ya Shule", body_style), Paragraph(f"<b>Tarehe ya Print:</b> {now}", body_style)],
        [Paragraph(f"<b>Kipindi kilichochujwa:</b> {kuanzia} hadi {hadi}", body_style), Paragraph("", body_style)]
    ]
    t_meta = Table(report_meta, colWidths=[280, 240])
    story.append(t_meta)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("MCHANGANUO WA MATUMIZI YALIYOFANYIKA", section_heading))
    
    table_data = [[Paragraph("<b>S/N</b>", header_table_style), Paragraph("<b>Maelezo ya Matumizi</b>", header_table_style), Paragraph("<b>Kiasi (TSHS)</b>", header_table_style), Paragraph("<b>Tarehe</b>", header_table_style)]]
    
    for _, row in expenses_df.iterrows():
        table_data.append([
            Paragraph(str(row['SN']), body_style),
            Paragraph(str(row['Maelezo']), body_style),
            Paragraph(f"{int(row['Kiasi']):,}", body_style),
            Paragraph(str(row['Tarehe']), body_style)
        ])
        
    table_data.append([
        Paragraph("<b>JUMLA KUU</b>", body_style),
        Paragraph("", body_style),
        Paragraph(f"<b>{jumla_matumizi:,}</b>", body_style),
        Paragraph("", body_style)
    ])
    
    t_expenses = Table(table_data, colWidths=[50, 250, 120, 100])
    t_expenses.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#EDF2F7')),
        ('SPAN', (0,-1), (1,-1)),
    ]))
    
    story.append(t_expenses)
    story.append(Spacer(1, 40))
    
    sign_data = [[Paragraph("........................................................<br/><b>Saini ya Mhasibu / Mkuu wa Shule</b>", body_style), Paragraph("........................................................<br/><b>Muhuri wa Taasisi</b>", body_style)]]
    t_sign = Table(sign_data, colWidths=[260, 260])
    story.append(t_sign)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def generate_general_report_pdf(jumla_ada_inayotakiwa, jumla_ada_iliyolipwa, deni_ada, jumla_mchango_inayotakiwa, jumla_mchango_iliyolipwa, deni_mchango, matumizi_yote, balansi, kuanzia, hadi):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=22, textColor=colors.HexColor('#1A365D'), alignment=1, spaceAfter=5, fontName="Helvetica-Bold")
    subtitle_style = ParagraphStyle('DocSub', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#4A5568'), alignment=1, spaceAfter=15)
    section_heading = ParagraphStyle('SectionHeading', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#1A365D'), spaceBefore=15, spaceAfter=10, fontName="Helvetica-Bold")
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#2D3748'), leading=14)
    header_table_style = ParagraphStyle('HeaderTable', parent=styles['Normal'], fontSize=10, textColor=colors.white, fontName="Helvetica-Bold")
    
    story.append(Paragraph(SCHOOL_NAME, title_style))
    story.append(Paragraph(f"{SCHOOL_LOCATION} | {SCHOOL_BOX} | Simu: {SCHOOL_PHONE}", subtitle_style))
    story.append(Spacer(1, 10))
    
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    story.append(Paragraph(f"<b>Aina ya Ripoti:</b> RIPOTI KUU YA MAPATO NA MATUMIZI (GENERAL FINANCIAL REPORT)", body_style))
    story.append(Paragraph(f"<b>Kipindi cha Ripoti:</b> Kuanzia {kuanzia} hadi {hadi}", body_style))
    story.append(Paragraph(f"<b>Tarehe ya Kuzalishwa:</b> {now}", body_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("1. TOKEO LA MAPATO (INCOME SUMMARY)", section_heading))
    income_data = [
        [Paragraph("<b>Chanzo cha Mapato</b>", header_table_style), Paragraph("<b>Kiasi Kinachotakiwa (TZS)</b>", header_table_style), Paragraph("<b>Kiasi Kilicholipwa (TZS)</b>", header_table_style), Paragraph("<b>Deni linalodaiwa (TZS)</b>", header_table_style)],
        [Paragraph("Michango ya Ada (Fees)", body_style), Paragraph(f"{jumla_ada_inayotakiwa:,}", body_style), Paragraph(f"{jumla_ada_iliyolipwa:,}", body_style), Paragraph(f"{deni_ada:,}", body_style)],
        [Paragraph("Michango Mingine (Other Inputs)", body_style), Paragraph(f"{jumla_mchango_inayotakiwa:,}", body_style), Paragraph(f"{jumla_mchango_iliyolipwa:,}", body_style), Paragraph(f"{deni_mchango:,}", body_style)],
        [Paragraph("<b>JUMLA YA MAPATO</b>", body_style), Paragraph(f"<b>{jumla_ada_inayotakiwa + jumla_mchango_inayotakiwa:,}</b>", body_style), Paragraph(f"<b>{jumla_ada_iliyolipwa + jumla_mchango_iliyolipwa:,}</b>", body_style), Paragraph(f"<b>{deni_ada + deni_mchango:,}</b>", body_style)]
    ]
    t_income = Table(income_data, colWidths=[160, 120, 120, 120])
    t_income.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#EDF2F7'))
    ]))
    story.append(t_income)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("2. MIZANI YA KIFEDHA (CASH FLOW STATEMENT)", section_heading))
    summary_data = [
        [Paragraph("<b>Kipengele cha Kifedha</b>", header_table_style), Paragraph("<b>Kiasi (TZS)</b>", header_table_style)],
        [Paragraph("Jumla Kuu ya Mapato Yaliyokusanywa (Actual Income)", body_style), Paragraph(f"{jumla_ada_iliyolipwa + jumla_mchango_iliyolipwa:,}", body_style)],
        [Paragraph("Jumla Kuu ya Matumizi (Total Expenses)", body_style), Paragraph(f"{matumizi_yote:,}", body_style)],
        [Paragraph("<b>SALIO / BALANSI ILIYOBAKI</b>", body_style), Paragraph(f"<b>{balansi:,}</b>", body_style)]
    ]
    t_summary = Table(summary_data, colWidths=[340, 180])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2B6CB0')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#D4EDDA') if balansi >= 0 else colors.HexColor('#F8D7DA'))
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 40))
    
    sign_data = [[Paragraph("........................................................<br/><b>Saini ya Mkuu wa Shule</b>", body_style), Paragraph("........................................................<br/><b>Muhuri wa Taasisi</b>", body_style)]]
    t_sign = Table(sign_data, colWidths=[260, 260])
    story.append(t_sign)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


###################################### FUNCTION NYINGEZA: STUDENT REPORT PDF #############################################################

def generate_individual_report_pdf(student_info, fee_info, other_info):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=22, textColor=colors.HexColor('#1A365D'), alignment=1, spaceAfter=5, fontName="Helvetica-Bold")
    subtitle_style = ParagraphStyle('DocSub', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#4A5568'), alignment=1, spaceAfter=15)
    section_heading = ParagraphStyle('SectionHeading', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#1A365D'), spaceBefore=12, spaceAfter=8, fontName="Helvetica-Bold")
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#2D3748'), leading=14)
    header_table_style = ParagraphStyle('HeaderTable', parent=styles['Normal'], fontSize=10, textColor=colors.white, fontName="Helvetica-Bold")
    
    story.append(Paragraph(SCHOOL_NAME, title_style))
    story.append(Paragraph(f"{SCHOOL_LOCATION} | {SCHOOL_BOX} | Simu: {SCHOOL_PHONE}", subtitle_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("<b>RIPOTI YA KIFEDHA YA MWANAFUNZI (INDIVIDUAL FINANCIAL REPORT)</b>", ParagraphStyle('RepType', parent=styles['Normal'], fontSize=12, alignment=1, fontName="Helvetica-Bold", textColor=colors.HexColor('#2B6CB0'))))
    story.append(Spacer(1, 10))
    
    # 1. Taarifa Binafsi
    story.append(Paragraph("TAARIFA BINAFSI", section_heading))
    personal_data = [
        [Paragraph("<b>Jina Kamili:</b>", body_style), Paragraph(str(student_info['Name']), body_style), Paragraph("<b>Namba ya Usajili (ID):</b>", body_style), Paragraph(str(student_info['ID']), body_style)],
        [Paragraph("<b>Darasa:</b>", body_style), Paragraph(str(student_info['Class']), body_style), Paragraph("<b>Jinsia:</b>", body_style), Paragraph(str(student_info['Gender']), body_style)],
        [Paragraph("<b>Hali ya Malazi:</b>", body_style), Paragraph(str(student_info['Hostel_Status']), body_style), Paragraph("<b>Simu ya Mzazi:</b>", body_style), Paragraph(str(student_info['Parent_Phone']), body_style)]
    ]
    t_personal = Table(personal_data, colWidths=[90, 170, 120, 140])
    t_personal.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')), ('PADDING', (0,0), (-1,-1), 6), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0'))]))
    story.append(t_personal)
    
    # 2. Muhtasari wa Ada
    story.append(Paragraph("1. REKODI YA MICHANGO YA ADA (FEES REPORT)", section_heading))
    f_required = fee_info.get("Total_Fee", 0) if fee_info else (FEE_HOSTEL if student_info['Hostel_Status'] == "Hostel Student" else FEE_DAY)
    f_paid = fee_info.get("Total_Paid", 0) if fee_info else 0
    f_owings = fee_info.get("Owings", 0) if fee_info else f_required
    f_status = fee_info.get("Status", "Hajalipa") if fee_info else "Hajalipa"
    
    fee_table = [
        [Paragraph("<b>Kipengele cha Ada</b>", header_table_style), Paragraph("<b>Kiasi (TZS)</b>", header_table_style)],
        [Paragraph("Ada Inayotakiwa kwa Mwaka", body_style), Paragraph(f"{f_required:,}", body_style)],
        [Paragraph("Jumla Kuu Iliyolipwa", body_style), Paragraph(f"{f_paid:,}", body_style)],
        [Paragraph("Salio linalodaiwa (Deni)", body_style), Paragraph(f"{f_owings:,}", body_style)],
        [Paragraph("Hali ya Malipo (Status)", body_style), Paragraph(f"<b>{f_status.upper()}</b>", body_style)]
    ]
    t_fee = Table(fee_table, colWidths=[300, 220])
    t_fee.setStyle(TableStyle([('BACKGROUND', (0,0), (1,0), colors.HexColor('#1A365D')), ('PADDING', (0,0), (-1,-1), 5), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0'))]))
    story.append(t_fee)
    
    # 3. Muhtasari wa Michango Mingine - Required Value inasoma kutoka Control Sheet
    story.append(Paragraph("2. REKODI YA MICHANGO MINGINE (OTHER CONTRIBUTIONS)", section_heading))
    # Jumla inayotakiwa inatoka kwenye Control Sheet
    total_required_other = REQ_TAHADHARI + REQ_KITAMBULISHO + REQ_TAALUMA + REQ_MICHEZO + REQ_UKARABATI + REQ_MITIHANI_FII + REQ_MITIHANI_FIV + REQ_BIMA
    
    o_paid = other_info.get("Amount_Paid", 0) if other_info else 0
    o_owings = total_required_other - o_paid
    o_status = "Amemaliza" if o_paid >= total_required_other else ("Hajalipa" if o_paid == 0 else "Anadaiwa")
    
    other_table = [
        [Paragraph("<b>Kipengele cha Mchango</b>", header_table_style), Paragraph("<b>Kiasi (TZS)</b>", header_table_style)],
        [Paragraph("Jumla ya Michango Inayotakiwa (Kutoka Settings)", body_style), Paragraph(f"{total_required_other:,}", body_style)],
        [Paragraph("Kiasi Kilicholipwa", body_style), Paragraph(f"{o_paid:,}", body_style)],
        [Paragraph("Salio linalodaiwa (Deni)", body_style), Paragraph(f"{o_owings:,}", body_style)],
        [Paragraph("Hali ya Malipo (Status)", body_style), Paragraph(f"<b>{o_status.upper()}</b>", body_style)]
    ]
    t_other = Table(other_table, colWidths=[300, 220])
    t_other.setStyle(TableStyle([('BACKGROUND', (0,0), (1,0), colors.HexColor('#2B6CB0')), ('PADDING', (0,0), (-1,-1), 5), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0'))]))
    story.append(t_other)
    
    # 4. Jumla Kuu Mwanafunzi
    story.append(Paragraph("3. MUHTASARI MKUU WA MADENI (TOTAL FINANCIAL SUMMARY)", section_heading))
    
    # HAPA NDIYO TUNAONGEZA ADA NA MICHANGO MINGINE KUPATA DENI LA JUMLA
    # f_owings inatoka kwenye ada, o_owings inatoka kwenye michango mingine
    tot_owings = f_owings + o_owings
    
    # Logic ya kuamua hali ya malipo ya jumla
    if tot_owings <= 0:
        overall_status = "AMEMALIZA MALIPO YOTE"
        status_color = colors.HexColor('#D4EDDA') # Kijani
    else:
        overall_status = f"ANADAIWA TZS {tot_owings:,}/="
        status_color = colors.HexColor('#F8D7DA') # Nyekundu
        
    summary_table = [
        [Paragraph("<b>Maelezo</b>", header_table_style), Paragraph("<b>Kiasi (TZS)</b>", header_table_style)],
        [Paragraph("Jumla Kuu ya Madeni Yote (Ada + Michango)", body_style), Paragraph(f"<b>{tot_owings:,}</b>", body_style)],
        [Paragraph("<b>HALI YA MWANAFUNZI</b>", body_style), Paragraph(f"<b>{overall_status}</b>", body_style)]
    ]
    
    t_summary = Table(summary_table, colWidths=[300, 220])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.HexColor('#2D3748')), 
        ('PADDING', (0,0), (-1,-1), 6), 
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')), 
        ('BACKGROUND', (1,2), (1,2), status_color) # Inabadilisha rangi kulingana na deni
    ]))
    story.append(t_summary)
    
    story.append(Spacer(1, 35))
    sign_data = [[Paragraph("........................................................<br/><b>Saini ya Mhasibu / Mkuu wa Shule</b>", body_style), Paragraph("........................................................<br/><b>Muhuri wa Taasisi</b>", body_style)]]
    t_sign = Table(sign_data, colWidths=[260, 260])
    story.append(t_sign)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


############################################################# Sidebar Navigation ##################################################################
# Ndani ya Sidebar yako, ongeza logic hii:
st.sidebar.title(f"👤 User: {st.session_state.user_role}")

if st.session_state.user_role == "Admin":
    # Admin anaona kila kitu
    pages = ["DASHBOARD",
 "USAJILI WA WANAFUNZI (Registration)",
 "MICHANGO YA ADA (Fees)", 
 "MICHANGO MINGINE (Other Inputs)",
 "MAPATO NA MATUMIZI (Cash Flow)", 
 "RIPOTI YA JUMLA (General Report)",
 "RIPOTI ZA WANAFUNZI (Student Reports)", 
 "⚙️ SYSTEM SETTINGS (Control Sheet)",
 "KUPROMOTE WANAFUNZI",
 "USER MANAGEMENT"]

else:
    # User wa kawaida haoni Settings
    pages = ["DASHBOARD",
 "MICHANGO YA ADA (Fees)",
 "MICHANGO MINGINE (Other Inputs)", 
 "RIPOTI ZA WANAFUNZI (Student Reports)"]

page = st.sidebar.radio("Chagua Ukurasa:", pages)



# --- LOGOUT NA DEVELOPER CONTACT ---
st.sidebar.markdown("---") # Mstari safi wa kutenganisha
col_out, col_dev = st.sidebar.columns(2) # Gawanya sidebar mara mbili

if col_out.button("🚪 Logout", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

if col_dev.button("📞developer", help="Piga 0655402558 kupata msaada wa kiufundi", use_container_width=True):
    st.sidebar.success("Mawasiliano ya Developer: 0655402558")


# === PAKIA DATA ZOTE TOKA SQLITE HAPA KWA PAMOJA ===
student_db = get_students_df()
fee_db = get_fees_df()
other_db = get_other_df()
expenses_db = get_expenses_df()


################################# ==================== 1. DASHBOARD ====================###########################################



################################# ==================== 1. DASHBOARD ====================###########################################

def render_modern_dashboard(student_db, fee_db, other_db):
    # ==================== 1. CHOTA JINA LA SHULE KUTOKA SYSTEM SETTING ====================
    shule_jina = None
    control_keys = ['REQ_SCHOOL_NAME', 'school_name', 'system_school_name', 'setting_school_name', 'SCHOOL_NAME']
    
    for key in control_keys:
        if key in st.session_state and st.session_state[key]:
            shule_jina = st.session_state[key]
            break
            
    if not shule_jina:
        shule_jina = globals().get('REQ_SCHOOL_NAME', globals().get('SCHOOL_NAME', "MFUMO WA MAPATO NA MICHANGO"))

    # ==================== 2. SEHEMU YA MATANGAZO YANAYOPITA (MARQUEE TEXT) ====================
    st.markdown(
        f"""
        <div style="background: linear-gradient(90deg, #1A365D 0%, #2A4365 100%); padding: 12px; border-radius: 10px; margin-bottom: 25px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1);">
            <marquee behavior="scroll" direction="left" scrollamount="6" style="color: #FFFFFF; font-family: 'Helvetica Neue', sans-serif; font-size: 16px; font-weight: bold; vertical-align: middle;">
                ✨ KARIBU KWENYE MFUMO WA KISASA WA ADA NA MICHANGO : 🏫 {shule_jina.upper()} 🏫 — Tarehe ya Leo: {datetime.date.today().strftime('%d/%m/%Y')} ✨
            </marquee>
        </div>
        """, 
        unsafe_allow_html=True
    )

    # ==================== 3. KADI: IDADI YA WANAFUNZI KWA KILA DARASA ====================
    st.markdown("### 🧑‍🎓 **IDADI YA WANAFUNZI KWA KILA DARASA**")
    
    if not student_db.empty and "Class" in student_db.columns:
        class_counts = student_db['Class'].value_counts().sort_index()
        # Tunatengeneza column kulingana na idadi ya madarasa yaliyopo
        cols = st.columns(len(class_counts))
        for i, (cls_name, count) in enumerate(class_counts.items()):
            with cols[i]:
                st.markdown(f'''
                    <div style="background-color: #F8FAFC; padding: 15px; border-radius: 10px; border-top: 4px solid #3182CE; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                        <h5 style="color: #64748B; font-size: 14px; margin-bottom: 5px;">{cls_name}</h5>
                        <h2 style="color: #0F172A; font-size: 26px; margin: 0; font-weight: 800;">{count}</h2>
                    </div>
                ''', unsafe_allow_html=True)
    else:
        st.info("Hakuna data za wanafunzi zilizopatikana bado.")

    st.write("")
    st.write("")

    # ==================== 4. KADI: MUHTASARI WA MAKUSANYO (MAPATO) ====================
    st.markdown("### 💰 **MUHTASARI WA MAKUSANYO YA KIFEDHA**")
    
    # Mahesabu salama (Kuzuia error kama database ni tupu)
    total_fee_paid = int(fee_db["Total_Paid"].sum()) if not fee_db.empty and "Total_Paid" in fee_db.columns else 0
    total_other_paid = int(other_db["Amount_Paid"].sum()) if not other_db.empty and "Amount_Paid" in other_db.columns else 0
    total_revenue = total_fee_paid + total_other_paid

    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f'''
            <div style="background-color: #F0FFF4; padding: 20px; border-radius: 12px; border-left: 5px solid #38A169; box-shadow: 0 2px 4px rgba(0,0,0,0.04);">
                <div style="font-size: 14px; color: #2F855A; font-weight: 600; margin-bottom: 5px;">🟢 JUMLA ADA ILIYOLIPWA</div>
                <div style="font-size: 24px; color: #1C4532; font-weight: 800;">TZS {total_fee_paid:,}/=</div>
            </div>
        ''', unsafe_allow_html=True)
    with m2:
        st.markdown(f'''
            <div style="background-color: #EBF8FF; padding: 20px; border-radius: 12px; border-left: 5px solid #3182CE; box-shadow: 0 2px 4px rgba(0,0,0,0.04);">
                <div style="font-size: 14px; color: #2B6CB0; font-weight: 600; margin-bottom: 5px;">📘 MICHANGO MINGINE</div>
                <div style="font-size: 24px; color: #2A4365; font-weight: 800;">TZS {total_other_paid:,}/=</div>
            </div>
        ''', unsafe_allow_html=True)
    with m3:
        st.markdown(f'''
            <div style="background-color: #FFFFF0; padding: 20px; border-radius: 12px; border-left: 5px solid #D69E2E; box-shadow: 0 2px 4px rgba(0,0,0,0.04);">
                <div style="font-size: 14px; color: #B7791F; font-weight: 600; margin-bottom: 5px;">🏆 JUMLA KUU YA MAPATO</div>
                <div style="font-size: 24px; color: #744210; font-weight: 800;">TZS {total_revenue:,}/=</div>
            </div>
        ''', unsafe_allow_html=True)

    st.write("")
    st.write("")

    # ==================== 5. GRAFU ZA KISASA (BAR GRAPHS KWA ZOTE MBILI) ====================
    st.markdown("### 📈 **MCHANGANUO WA MAPATO KWA GRAFU**")
    
    g1, g2 = st.columns(2)

    with g1:
        st.markdown("##### 📊 Makusanyo ya Ada kwa Darasa")
        if not fee_db.empty and "Class" in fee_db.columns and "Total_Paid" in fee_db.columns:
            fee_by_class = fee_db.groupby('Class')['Total_Paid'].sum().reset_index()
            fig1 = px.bar(
                fee_by_class, 
                x='Class', 
                y='Total_Paid', 
                color='Class',
                text_auto='.2s',
                labels={'Total_Paid': 'Kiasi cha Ada (TZS)', 'Class': 'Darasa'},
                template="plotly_white",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig1.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("Hakuna data za ada za kuchora grafu kwa sasa.")

    with g2:
        st.markdown("##### 📊 Michango Mingine kwa Darasa")
        if not other_db.empty and "Class" in other_db.columns and "Amount_Paid" in other_db.columns:
            other_by_class = other_db.groupby('Class')['Amount_Paid'].sum().reset_index()
            fig2 = px.bar(
                other_by_class, 
                x='Class', 
                y='Amount_Paid', 
                color='Class',
                text_auto='.2s',
                labels={'Amount_Paid': 'Kiasi cha Michango (TZS)', 'Class': 'Darasa'},
                template="plotly_white",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig2.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Hakuna data za michango mingine za kuchora grafu kwa sasa.")

    st.markdown("---")
    st.caption("💡 Dashboard hii inajichambua live kwa kila data mpya ikiongezwa. Kwa msaada tupigie 0655402558.")


# ========================================== LOGIC INAYOONYESHA DASHBOARD =============================================#

if page == "DASHBOARD":
    # Tunahakikisha data zote 3 (students, fees, other) zipo ndipo tunaiita function
    if all(var in locals() or var in globals() for var in ['student_db', 'fee_db', 'other_db']):
        render_modern_dashboard(student_db, fee_db, other_db)
    else:
        st.warning("⚠️ Mfumo unapakia kanzidata (database)... Tafadhali hakikisha umeingiza data kwanza.")



# ========================================== 2. USAJILI (USAJILI KWA MKONO + BULK UPLOAD YA EXCEL) =============================================#

elif page == "USAJILI WA WANAFUNZI (Registration)":
    st.header("📝 Student Registration Form")
    tab1, tab2 = st.tabs(["👤 Sajili / Hariri", "📂 Bulk Upload"])
    
    with tab1:
        default_id, default_name, default_class, default_gender = "", "", "Form I", "Male"
        default_hostel, default_addr, default_phone = "Hostel Student", "", ""
        default_date = datetime.date.today()
        
        if st.session_state.edit_student_data is not None:
            es = st.session_state.edit_student_data
            default_id, default_name, default_class, default_gender = es["ID"], es["Name"], es["Class"], es["Gender"]
            default_hostel, default_addr, default_phone, default_date = es["Hostel_Status"], es["Address"], es["Parent_Phone"], pd.to_datetime(es["Admission_Date"]).date()
            st.info(f"🔄 Unahariri: ID {default_id}")

        with st.form(key="registration_form"):
            col1, col2 = st.columns(2)
            with col1:
                r_id = st.text_input("ID (Registration Number)", value=default_id, disabled=(st.session_state.edit_student_data is not None))
                r_name = st.text_input("Full Name", value=default_name)
                r_class = st.selectbox("Class", ["Form I", "Form II", "Form III", "Form IV", "Form V", "Form VI"], index=["Form I", "Form II", "Form III", "Form IV", "Form V", "Form VI"].index(default_class))
                r_gender = st.selectbox("Gender", ["Male", "Female"], index=["Male", "Female"].index(default_gender))
            with col2:
                r_hostel = st.selectbox("Hostel Status", ["Hostel Student", "Day Student"], index=["Hostel Student", "Day Student"].index(default_hostel))
                r_address = st.text_input("Address", value=default_addr)
                r_phone = st.text_input("Parent Phone", value=default_phone)
                r_date = st.date_input("Admission Date", value=default_date)
            
            c_save, c_update = st.columns(2)
            btn_save = c_save.form_submit_button("💾 Save New Student", use_container_width=True)
            btn_update = c_update.form_submit_button("🔄 Update Student", use_container_width=True)
            
        if btn_save and r_id and r_name:
            if r_id in student_db["ID"].astype(str).values:
                st.error("ID tayari ipo!")
            else:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO students VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (r_id, r_name, r_class, r_gender, r_hostel, r_address, r_phone, str(r_date)))
                conn.commit()
                conn.close()
                st.success("Mwanafunzi amehifadhiwa kwenye database.db!")
                st.session_state.edit_student_data = None
                st.rerun()
                
        if btn_update and r_id and r_name:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("UPDATE students SET Name=?, Class=?, Gender=?, Hostel_Status=?, Address=?, Parent_Phone=?, Admission_Date=? WHERE ID=?", (r_name, r_class, r_gender, r_hostel, r_address, r_phone, str(r_date), r_id))
            conn.commit()
            conn.close()
            st.success("Mabadiliko yamehifadhiwa kwenye database.db!")
            st.session_state.edit_student_data = None
            st.rerun()

        search_id = st.text_input("Tafuta ID ya Mwanafunzi kuediti/kufuta:")
        if search_id:
            match = student_db[student_db["ID"].astype(str) == str(search_id)]
            if not match.empty:
                st.dataframe(match)
                b_edit, b_del = st.columns(2)
                if b_edit.button("✏️ Edit (Peleka Juu)"):
                    st.session_state.edit_student_data = match.iloc[0].to_dict()
                    st.rerun()
                if b_del.button("🗑️ Delete Mwanafunzi"):
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM students WHERE ID=?", (search_id,))
                    conn.commit()
                    conn.close()
                    st.success("Mwanafunzi amefutwa!")
                    st.rerun()

    with tab2:
        st.subheader("📂 Pakia Wanafunzi Wengi kwa Pamoja (Excel Bulk Upload)")
        st.markdown("""
        **Maelekezo:**
        1. Pakua template ya Excel hapo chini.
        2. Jaza taarifa za wanafunzi kulingana na safu (*columns*) zilizopo bila kubadilisha majina ya vichwa vya habari.
        3. Pakia (*Upload*) faili uloweka data ili kuhifadhi moja kwa moja kwenye mfumo.
        """)
        
        template_data = pd.DataFrame(columns=["ID", "Name", "Class", "Gender", "Hostel_Status", "Address", "Parent_Phone", "Admission_Date"])
        template_data.loc[0] = ["REG-001", "Meshack philipo", "Form I", "Male", "Hostel Student", "Mbeya", "0655402558", str(datetime.date.today())]
        
        template_excel = to_excel(template_data)
        st.download_button(
            label="📥 Download Excel Template Here",
            data=template_excel,
            file_name="student_registration_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.markdown("---")
        uploaded_file = st.file_uploader("Chagua faili la Excel ulilojaza data za wanafunzi:", type=["xlsx"])
        
        if uploaded_file is not None:
            try:
                df_upload = pd.read_excel(uploaded_file)
                df_upload = df_upload.astype(str)
                df_upload = df_upload.replace('nan', '')
                
                st.markdown("### 👀 Hakiki data uliyopakia kabla ya kuihifadhi:")
                st.dataframe(df_upload, use_container_width=True)
                
                if st.button("💾 Hifadhi Wanafunzi Hawa Kwenye Database", use_container_width=True):
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    
                    success_count = 0
                    duplicate_count = 0
                    
                    for _, row in df_upload.iterrows():
                        cursor.execute("SELECT COUNT(*) FROM students WHERE ID = ?", (row['ID'].strip(),))
                        if cursor.fetchone()[0] == 0:
                            cursor.execute("""
                                INSERT INTO students (ID, Name, Class, Gender, Hostel_Status, Address, Parent_Phone, Admission_Date) 
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (row['ID'].strip(), row['Name'].strip(), row['Class'].strip(), row['Gender'].strip(), 
                                  row['Hostel_Status'].strip(), row['Address'].strip(), row['Parent_Phone'].strip(), row['Admission_Date'].strip()))
                            success_count += 1
                        else:
                            duplicate_count += 1
                            
                    conn.commit()
                    conn.close()
                    
                    if success_count > 0:
                        st.success(f"🎉 Imefanikiwa! Wanafunzi {success_count} wameongezwa kwenye database kwa mkupuo.")
                    if duplicate_count > 0:
                        st.warning(f"⚠️ Wanafunzi {duplicate_count} hawajapakiwa kwa sababu ID zao tayari zipo kwenye mfumo.")
                        
                    st.rerun()
            except Exception as e:
                st.error(f"Kuna makosa yametokea wakati wa kusoma faili: {e}.")

    st.markdown("### 📋 Orodha Kamili ya Wanafunzi")
    st.dataframe(student_db, use_container_width=True)

# ======================================================== 3. ADA (FEES) ================================================================ #
elif page == "MICHANGO YA ADA (Fees)":
    st.header("💰 Fee Contribution Form")
    search_options = ["-- Chagua Mwanafunzi --"] + [f"{row['ID']} - {row['Name']}" for _, row in student_db.iterrows()]
    selected_student = st.selectbox("Andika au Chagua ID/Jina hapa...", search_options)
    
    auto_id, auto_name, auto_class, auto_gender, auto_hostel, auto_addr, auto_phone = "", "", "Form I", "Male", "Hostel Student", "", ""
    auto_date = datetime.date.today()
    q1_val, q2_val, q3_val, q4_val = 0, 0, 0, 0
    
    if selected_student != "-- Chagua Mwanafunzi --":
        sel_id = selected_student.split(" - ")[0]
        st_info = student_db[student_db["ID"].astype(str) == str(sel_id)].iloc[0]
        auto_id, auto_name, auto_class, auto_gender, auto_hostel = st_info["ID"], st_info["Name"], st_info["Class"], st_info["Gender"], st_info["Hostel_Status"]
        auto_addr, auto_phone = st_info["Address"], st_info["Parent_Phone"]
        
        fee_history = fee_db[fee_db["ID"].astype(str) == str(sel_id)]
        if not fee_history.empty:
            q1_val, q2_val, q3_val, q4_val = int(fee_history.iloc[0]["Q1"]), int(fee_history.iloc[0]["Q2"]), int(fee_history.iloc[0]["Q3"]), int(fee_history.iloc[0]["Q4"])

    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            f_class = st.selectbox("Class", ["Form I", "Form II", "Form III", "Form IV", "Form V", "Form VI"], index=["Form I", "Form II", "Form III", "Form IV", "Form V", "Form VI"].index(auto_class))
            f_id = st.text_input("ID", value=auto_id)
            f_name = st.text_input("Name", value=auto_name)
            f_address = st.text_input("Address", value=auto_addr)
            f_gender = st.selectbox("Gender", ["Male", "Female"], index=["Male", "Female"].index(auto_gender))
            f_hostel = st.selectbox("Hostel", ["Hostel Student", "Day Student"], index=["Hostel Student", "Day Student"].index(auto_hostel))
            f_phone = st.text_input("Phone", value=auto_phone)
        with col2:
            f_date = st.date_input("Date", value=auto_date)
            q1 = st.number_input("1st Quarter", value=q1_val, step=5000)
            q2 = st.number_input("2nd Quarter", value=q2_val, step=5000)
            q3 = st.number_input("3rd Quarter", value=q3_val, step=5000)
            q4 = st.number_input("4th Quarter", value=q4_val, step=5000)
            
            tot_fee = FEE_HOSTEL if f_hostel == "Hostel Student" else FEE_DAY
            tot_paid = q1 + q2 + q3 + q4
            owings = tot_fee - tot_paid
            status_str = "Amemaliza" if tot_paid >= tot_fee else ("Hajalipa" if tot_paid == 0 else "Anadaiwa")

    b1, b2, b3 = st.columns([1, 1, 2])
    if b1.button("💾 Save Record", use_container_width=True):
        if f_id and f_name:
            # Data Validation kwa upande wa ADA
            if tot_paid > tot_fee:
                st.error(f"❌ Imeshindikana! Kiasi ulichoingiza (TZS {tot_paid:,}) ni kikubwa kuliko ada inayotakiwa (TZS {tot_fee:,}) kwenye Control Sheet.")
            else:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("REPLACE INTO fees VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                               (f_id, f_name, f_class, f_gender, f_hostel, f_address, f_phone, str(f_date), q1, q2, q3, q4, tot_fee, tot_paid, status_str, owings))
                conn.commit()
                conn.close()
                st.success("Ada imehifadhiwa kwenye database.db!")
                st.rerun()
            
    if b2.button("🗑️ Delete Record", use_container_width=True):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM fees WHERE ID=?", (f_id,))
        conn.commit()
        conn.close()
        st.success("Rekodi imefutwa!")
        st.rerun()
        
    if selected_student != "-- Chagua Mwanafunzi --" and f_id:
        student_info_dict = {"ID": f_id, "Name": f_name, "Class": f_class, "Gender": f_gender, "Hostel Status": f_hostel, "Address": f_address, "Parent Phone": f_phone}
        pdf_data = generate_fee_pdf(student_info_dict, q1, q2, q3, q4, tot_fee, tot_paid, owings, status_str)
        b3.download_button(label="🖨️ Print PDF Receipt", data=pdf_data, file_name=f"Risiti_Ada_{f_id}.pdf", mime="application/pdf", use_container_width=True)

    st.dataframe(fee_db, use_container_width=True)

# ======================================= 4. MICHANGO MINGINE (DYNAMIC EXAM FEES BASED ON CLASS) =================================== #
elif page == "MICHANGO MINGINE (Other Inputs)":
    st.header("🎟️ Other Contribution Form")
    
    if 'edit_other_data' not in st.session_state:
        st.session_state.edit_other_data = None

    search_options_o = ["-- Chagua Mwanafunzi --"] + [f"{row['ID']} - {row['Name']}" for _, row in student_db.iterrows()]
    selected_student_o = st.selectbox("Andika au Chagua ID/Jina hapa...", search_options_o, key="other_box")
    
    o_auto_id, o_auto_name, o_auto_class, o_auto_gender, o_auto_hostel, o_auto_addr, o_auto_phone = "", "", "Form I", "Male", "Hostel Student", "", ""
    
    # Maadili ya kuanzia (Default Values) kutoka kwenye Control Sheet
    v_tah = REQ_TAHADHARI
    v_kit = REQ_KITAMBULISHO
    v_taal = REQ_TAALUMA
    v_mic = REQ_MICHEZO
    v_uka = REQ_UKARABATI
    v_f2 = REQ_MITIHANI_FII
    v_f4 = REQ_MITIHANI_FIV
    v_bim = REQ_BIMA
    o_auto_date = datetime.date.today()

    if selected_student_o != "-- Chagua Mwanafunzi --":
        sel_id_o = selected_student_o.split(" - ")[0]
        st_info_o = student_db[student_db["ID"].astype(str) == str(sel_id_o)].iloc[0]
        o_auto_id, o_auto_name, o_auto_class, o_auto_gender, o_auto_hostel = st_info_o["ID"], st_info_o["Name"], st_info_o["Class"], st_info_o["Gender"], st_info_o["Hostel_Status"]
        o_auto_addr, o_auto_phone = st_info_o["Address"], st_info_o["Parent_Phone"]
        
        oth_history = other_db[other_db["ID"].astype(str) == str(sel_id_o)]
        if not oth_history.empty:
            v_tah = int(oth_history.iloc[0]["Tahadhari"])
            v_kit = int(oth_history.iloc[0]["Kitambulisho"])
            v_taal = int(oth_history.iloc[0]["Taaluma"])
            v_mic = int(oth_history.iloc[0]["Michezo"])
            v_uka = int(oth_history.iloc[0]["Ukarabati"])
            v_f2 = int(oth_history.iloc[0]["Mitihani_FII"])
            v_f4 = int(oth_history.iloc[0]["Mitihani_FIV"])
            v_bim = int(oth_history.iloc[0]["Bima"])
            o_auto_date = pd.to_datetime(oth_history.iloc[0]["Admission_Date"]).date()

    if st.session_state.edit_other_data is not None:
        eo = st.session_state.edit_other_data
        o_auto_id, o_auto_name, o_auto_class, o_auto_gender, o_auto_hostel = eo["ID"], eo["Name"], eo["Class"], eo["Gender"], eo["Hostel_Status"]
        o_auto_addr, o_auto_phone = eo["Address"], eo["Phone"]
        v_tah = int(eo["Tahadhari"])
        v_kit = int(eo["Kitambulisho"])
        v_taal = int(eo["Taaluma"])
        v_mic = int(eo["Michezo"])
        v_uka = int(eo["Ukarabati"])
        v_f2 = int(eo["Mitihani_FII"])
        v_f4 = int(eo["Mitihani_FIV"])
        v_bim = int(eo["Bima"])
        o_auto_date = pd.to_datetime(eo["Admission_Date"]).date()
        st.info(f"🔄 Unahariri Michango ya: ID {o_auto_id} - {o_auto_name}")

    # Tunahitaji kujua darasa kabla ya kuingia kwenye st.form ili tuweze ku-control disabled state ya mitihani live
    # Ili st.selectbox ya darasa iweze ku-trigger mabadiliko live, tunaiweka nje au tunatumia session_state, lakini njia rahisi ndani ya form ni ku-render selectbox kwanza au kutumia st.selectbox ya kawaida kabla ya fomu kama unataka iwe reactive 100%.
    
    # Kufanya iwe live zaidi na ku-detect darasa kirahisi, tunatoa Selectbox ya Class nje ya form au tunatumia state:
    st.subheader("📝 Taarifa za Msingi")
    o_class = st.selectbox("Chagua Darasa la Mwanafunzi (Class)", ["Form I", "Form II", "Form III", "Form IV", "Form V", "Form VI"], index=["Form I", "Form II", "Form III", "Form IV", "Form V", "Form VI"].index(o_auto_class))

    # Logika ya kukagua darasa kwa ajili ya mitihani
    is_f2 = (o_class == "Form II")
    is_f4 = (o_class == "Form IV")

    with st.form(key="other_contributions_form"):
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"Darasa lililochaguliwa: {o_class}")
            o_id = st.text_input("ID", value=o_auto_id, disabled=(st.session_state.edit_other_data is not None))
            o_name = st.text_input("Name", value=o_auto_name)
            o_address = st.text_input("Address", value=o_auto_addr)
            o_gender = st.selectbox("Gender", ["Male", "Female"], index=["Male", "Female"].index(o_auto_gender))
            o_hostel = st.selectbox("Hostel Status", ["Hostel Student", "Day Student"], index=["Hostel Student", "Day Student"].index(o_auto_hostel))
            o_phone = st.text_input("Parent Phone", value=o_auto_phone)
        with col2:
            o_date = st.date_input("Admission Date", value=o_auto_date)
            
            tahadhari = st.number_input("Tahadhari", value=v_tah, help=f"Kiasi Halisi Control Sheet: {REQ_TAHADHARI:,}")
            kitambulisho = st.number_input("Kitambulisho", value=v_kit, help=f"Kiasi Halisi Control Sheet: {REQ_KITAMBULISHO:,}")
            taaluma = st.number_input("Taaluma", value=v_taal, help=f"Kiasi Halisi Control Sheet: {REQ_TAALUMA:,}")
            michezo = st.number_input("Michezo", value=v_mic, help=f"Kiasi Halisi Control Sheet: {REQ_MICHEZO:,}")
            ukarabati = st.number_input("Ukarabati", value=v_uka, help=f"Kiasi Halisi Control Sheet: {REQ_UKARABATI:,}")
            
            # --- SEHEMU YA MITIHANI INAKUWA FAINT KAMA SI DARASA HUSIKA ---
            mitihani_fii = st.number_input("Mitihani Form II", value=v_f2 if is_f2 else 0, disabled=not is_f2, help=f"Kiasi Halisi Control Sheet: {REQ_MITIHANI_FII:,}" if is_f2 else "Huruhusiwi kuchangia darasa hili.")
            mitihani_fiv = st.number_input("Mitihani Form IV", value=v_f4 if is_f4 else 0, disabled=not is_f4, help=f"Kiasi Halisi Control Sheet: {REQ_MITIHANI_FIV:,}" if is_f4 else "Huruhusiwi kuchangia darasa hili.")
            
            bima = st.number_input("Bima / NHIF", value=v_bim, help=f"Kiasi Halisi Control Sheet: {REQ_BIMA:,}")
            
            # Kipengele cha "Kiasi Kilicholipwa" kinajumlisha yaliyo hai tu
            tot_contribution = tahadhari + kitambulisho + taaluma + michezo + ukarabati + mitihani_fii + mitihani_fiv + bima
            amt_paid = st.number_input("Kiasi Kilicholipwa (Amount Paid)", value=tot_contribution, disabled=True)
            
            # Piga hesabu ya MAX ALLOWED kulingana na darasa ili mwanafunzi asidaiwe mitihani asiyohusika nayo
            req_f2_final = REQ_MITIHANI_FII if is_f2 else 0
            req_f4_final = REQ_MITIHANI_FIV if is_f4 else 0
            
            max_allowed_contribution = REQ_TAHADHARI + REQ_KITAMBULISHO + REQ_TAALUMA + REQ_MICHEZO + REQ_UKARABATI + req_f2_final + req_f4_final + REQ_BIMA
            o_owings = max_allowed_contribution - amt_paid
            o_status_str = "Amemaliza" if amt_paid >= max_allowed_contribution else ("Hajalipa" if amt_paid == 0 else "Anadaiwa")

        ob1, ob2 = st.columns(2)
        btn_save_other = ob1.form_submit_button("💾 Save / Update Record", use_container_width=True)
        btn_cancel = ob2.form_submit_button("❌ Cancel Edit", use_container_width=True)

    if btn_save_other and o_id and o_name:
        # VALIDATION KUTOKA CONTROL SHEET
        if tahadhari > REQ_TAHADHARI:
            st.error(f"❌ KOSA: Mchango wa Tahadhari (TZS {tahadhari:,}) ni mkubwa kuliko ule uliowekwa kwenye Control Sheet (TZS {REQ_TAHADHARI:,})!")
        elif kitambulisho > REQ_KITAMBULISHO:
            st.error(f"❌ KOSA: Mchango wa Kitambulisho (TZS {kitambulisho:,}) unazidi ukomo wa Control Sheet (TZS {REQ_KITAMBULISHO:,})!")
        elif taaluma > REQ_TAALUMA:
            st.error(f"❌ KOSA: Mchango wa Taaluma (TZS {taaluma:,}) unazidi ukomo wa Control Sheet (TZS {REQ_TAALUMA:,})!")
        elif michezo > REQ_MICHEZO:
            st.error(f"❌ KOSA: Mchango wa Michezo (TZS {michezo:,}) unazidi ukomo wa Control Sheet (TZS {REQ_MICHEZO:,})!")
        elif ukarabati > REQ_UKARABATI:
            st.error(f"❌ KOSA: Mchango wa Ukarabati (TZS {ukarabati:,}) unazidi ukomo wa Control Sheet (TZS {REQ_UKARABATI:,})!")
        elif is_f2 and mitihani_fii > REQ_MITIHANI_FII:
            st.error(f"❌ KOSA: Mchango wa Mitihani Form II (TZS {mitihani_fii:,}) unazidi ukomo wa Control Sheet (TZS {REQ_MITIHANI_FII:,})!")
        elif is_f4 and mitihani_fiv > REQ_MITIHANI_FIV:
            st.error(f"❌ KOSA: Mchango wa Mitihani Form IV (TZS {mitihani_fiv:,}) unazidi ukomo wa Control Sheet (TZS {REQ_MITIHANI_FIV:,})!")
        elif bima > REQ_BIMA:
            st.error(f"❌ KOSA: Mchango wa Bima / NHIF (TZS {bima:,}) unazidi ukomo wa Control Sheet (TZS {REQ_BIMA:,})!")
        else:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("REPLACE INTO other_contributions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                           (o_id, o_name, o_class, o_gender, o_hostel, o_address, o_phone, str(o_date), tahadhari, kitambulisho, taaluma, michezo, ukarabati, mitihani_fii, mitihani_fiv, bima, max_allowed_contribution, amt_paid, o_status_str, o_owings))
            conn.commit()
            conn.close()
            st.success("Michango imehifadhiwa vizuri kwa kuangalia darasa husika!")
            st.session_state.edit_other_data = None
            st.rerun()

    if btn_cancel:
        st.session_state.edit_other_data = None
        st.rerun()

    st.markdown("---")
    st.subheader("🔍 Tafuta, Hariri au Futa Michango")
    
    search_id_o = st.text_input("Andika ID ya Mwanafunzi kutafuta michango yake:")
    if search_id_o:
        match_o = other_db[other_db["ID"].astype(str) == str(search_id_o)]
        if not match_o.empty:
            st.dataframe(match_o)
            b_edit_o, b_del_o = st.columns(2)
            
            if b_edit_o.button("✏️ Edit Michango (Peleka Juu)"):
                st.session_state.edit_other_data = match_o.iloc[0].to_dict()
                st.rerun()
                
            if b_del_o.button("🗑️ Futa Michango Kabisa"):
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM other_contributions WHERE ID=?", (search_id_o,))
                conn.commit()
                conn.close()
                st.success("Rekodi ya michango imefutwa kabisa!")
                st.rerun()
        else:
            st.warning("ID hii haijatunza kumbukumbu zote za michango bado.")

    st.markdown("### 📊 Jedwali la Michango na Hali ya Malipo (Status)")
    
    def color_status(val):
        color = 'green' if val == 'Amemaliza' else ('red' if val == 'Hajalipa' else 'orange')
        return f'color: {color}; font-weight: bold;'

    if not other_db.empty:
       st.dataframe(other_db.style.map(color_status, subset=['Status']), use_container_width=True)
    else:
        st.info("Hakuna data ya michango mingine iliyosajiliwa kwa sasa.")

# ==================== 5. MAPATO NA MATUMIZI (CASH FLOW) ====================
elif page == "MAPATO NA MATUMIZI (Cash Flow)":
    st.header("📊 Usimamizi wa Mapato na Matumizi")
    
    jumla_ada = int(fee_db["Total_Paid"].sum()) if not fee_db.empty else 0
    jumla_michango_mingine = int(other_db["Amount_Paid"].sum()) if not other_db.empty else 0
    mapato_yote = jumla_ada + jumla_michango_mingine
    
    matumizi_yote = int(expenses_db["Kiasi"].sum()) if not expenses_db.empty else 0
    balansi_iliyobaki = mapato_yote - matumizi_yote

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div style="background-color:#D4EDDA; padding:15px; border-radius:5px;"><h4 style="color:#155724; margin:0;">💰 MAPATO YOTE YA SHULE</h4><h2 style="color:#155724; margin:5px 0 0 0;">TZS {:,}</h2><small>Ada: TZS {:,} | Michango: TZS {:,}</small></div>'.format(mapato_yote, jumla_ada, jumla_michango_mingine), unsafe_allow_html=True)
    with c2:
        st.markdown('<div style="background-color:#F8D7DA; padding:15px; border-radius:5px;"><h4 style="color:#721C24; margin:0;">📉 MATUMIZI YOTE (EXPENSES)</h4><h2 style="color:#721C24; margin:5px 0 0 0;">TZS {:,}</h2><small>Yaliyosajiliwa hadi sasa</small></div>'.format(matumizi_yote), unsafe_allow_html=True)
    with c3:
        bg_c = "#CCE5FF" if balansi_iliyobaki >= 0 else "#F8D7DA"
        text_c = "#004085" if balansi_iliyobaki >= 0 else "#721C24"
        st.markdown(f'<div style="background-color:{bg_c}; padding:15px; border-radius:5px;"><h4 style="color:{text_c}; margin:0;">🏦 BALANSI ILIYOBAKI (CASH IN HAND)</h4><h2 style="color:{text_c}; margin:5px 0 0 0;">TZS {balansi_iliyobaki:,}</h2><small>Mapato - Matumizi</small></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📝 Info (matumizi)")
    
    if 'edit_expense_sn' not in st.session_state:
        st.session_state.edit_expense_sn = None

    exp_maelezo, exp_kiasi = "", 0
    exp_tarehe = datetime.date.today()
    
    if st.session_state.edit_expense_sn is not None:
        match_exp = expenses_db[expenses_db["SN"] == st.session_state.edit_expense_sn].iloc[0]
        exp_maelezo = match_exp["Maelezo"]
        exp_kiasi = int(match_exp["Kiasi"])
        exp_tarehe = pd.to_datetime(match_exp["Tarehe"]).date()
        st.info(f"🔄 Unahariri Matumizi S/N: {st.session_state.edit_expense_sn}")

    with st.form(key="expense_form"):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            f_maelezo = st.text_input("MAELEZO:", value=exp_maelezo, placeholder="Mfano: Kununua Chaki, Kulipa Umeme, n.k.")
            f_kiasi = st.number_input("KIASI (TSHS):", value=exp_kiasi, step=1000)
        with col_f2:
            f_tarehe = st.date_input("TAREHE:", value=exp_tarehe)
        
        btn_col1, btn_col2 = st.columns(2)
        btn_save_exp = btn_col1.form_submit_button("💾 Save / Update Expense", use_container_width=True)
        btn_cancel_exp = btn_col2.form_submit_button("❌ Cancel Edit", use_container_width=True)

    if btn_save_exp and f_maelezo and f_kiasi > 0:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        if st.session_state.edit_expense_sn is None:
            cursor.execute("INSERT INTO expenses (Maelezo, Kiasi, Tarehe) VALUES (?, ?, ?)", (f_maelezo, f_kiasi, str(f_tarehe)))
        else:
            cursor.execute("UPDATE expenses SET Maelezo=?, Kiasi=?, Tarehe=? WHERE SN=?", (f_maelezo, f_kiasi, str(f_tarehe), st.session_state.edit_expense_sn))
        conn.commit()
        conn.close()
        st.success("Matumizi yamehifadhiwa vizuri!")
        st.session_state.edit_expense_sn = None
        st.rerun()

    if btn_cancel_exp:
        st.session_state.edit_expense_sn = None
        st.rerun()

    st.markdown("---")
    st.subheader("🔍 Tafuta na Uchuje Matumizi")
    
    col_search1, col_search2, col_search3 = st.columns([2, 1.5, 1.5])
    search_query = col_search1.text_input("Tafuta kwa Maelezo (Andika neno):", placeholder="Andika hapa kutafuta...")
    start_date = col_search2.date_input("Kuanzia Tarehe:", datetime.date(datetime.date.today().year, 1, 1))
    end_date = col_search3.date_input("Hadi Tarehe:", datetime.date.today())
    
    filtered_df = expenses_db.copy()
    if not filtered_df.empty:
        filtered_df["Tarehe_Parsed"] = pd.to_datetime(filtered_df["Tarehe"]).dt.date
        filtered_df = filtered_df[(filtered_df["Tarehe_Parsed"] >= start_date) & (filtered_df["Tarehe_Parsed"] <= end_date)]
        if search_query:
            filtered_df = filtered_df[filtered_df["Maelezo"].str.contains(search_query, case=False, na=False)]
        filtered_df = filtered_df.drop(columns=["Tarehe_Parsed"])

    if not filtered_df.empty:
        st.markdown(f"**Zimepatikana rekodi {len(filtered_df)} za matumizi:**")
        st.dataframe(filtered_df, use_container_width=True)
        
        st.markdown("##### ⚙️ Hariri (Edit) au Futa (Delete) kutoka kwenye Orodha")
        action_col1, action_col2 = st.columns([2, 3])
        select_sn = action_col1.selectbox("Chagua S/N ya matumizi unayotaka kubadili/kufuta:", ["-- Chagua S/N --"] + list(filtered_df["SN"].astype(str)))
        
        if select_sn != "-- Chagua S/N --":
            btn_edit_e, btn_del_e = action_col2.columns(2)
            if btn_edit_e.button("✏️ Edit (Peleka Kwenye Fomu)", use_container_width=True):
                st.session_state.edit_expense_sn = int(select_sn)
                st.rerun()
            if btn_del_e.button("🗑️ Futa Matumizi Haya", use_container_width=True):
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM expenses WHERE SN=?", (int(select_sn),))
                conn.commit()
                conn.close()
                st.success(f"Matumizi ya S/N {select_sn} yamefutwa kabisa!")
                st.rerun()

    if not filtered_df.empty:
        st.markdown("---")
        st.markdown("##### 🖨️ Print Ripoti Iliyochujwa")
        
        jumla_fil_matumizi = int(filtered_df["Kiasi"].sum())
        pdf_expenses_data = generate_expenses_pdf(filtered_df, jumla_fil_matumizi, str(start_date), str(end_date))
        st.download_button(
            label="📄 Download Safi & Print PDF Report",
            data=pdf_expenses_data,
            file_name=f"Ripoti_Matumizi_{start_date}_hadi_{end_date}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    else:
        st.info("Hakuna matumizi yaliyopatikana kulingana na vigezo ulivyoweka.")

# ==================== 6. RIPOTI YA JUMLA (SASA INASOMA UNIFIED REQUIRED VALUE) ====================
elif page == "RIPOTI YA JUMLA (General Report)":
    st.header("📊 Ripoti Kuu ya Mapato na Matumizi")
    
    # 1. Hesabu za ADA
    t_ada_inayotakiwa = int(fee_db["Total_Fee"].sum()) if not fee_db.empty else 0
    t_ada_iliyolipwa = int(fee_db["Total_Paid"].sum()) if not fee_db.empty else 0
    t_ada_madeni = int(fee_db["Owings"].sum()) if not fee_db.empty else 0
    
    # 2. Hesabu za MICHANGO MINGINE (Inasoma direct kwa kila mwanafunzi kulingana na muundo wa sasa wa control sheet)
    total_single_required_other = REQ_TAHADHARI + REQ_KITAMBULISHO + REQ_TAALUMA + REQ_MICHEZO + REQ_UKARABATI + REQ_MITIHANI_FII + REQ_MITIHANI_FIV + REQ_BIMA
    idadi_ya_wanafunzi_walioingizwa = len(other_db) if not other_db.empty else 0
    
    t_mchango_inayotakiwa = total_single_required_other * idadi_ya_wanafunzi_walioingizwa
    t_mchango_iliyolipwa = int(other_db["Amount_Paid"].sum()) if not other_db.empty else 0
    t_mchango_madeni = t_mchango_inayotakiwa - t_mchango_iliyolipwa
    
    st.subheader("🗓️ Filter Kipindi cha Ripoti")
    col_r1, col_r2 = st.columns(2)
    r_start = col_r1.date_input("Ripoti Kuanzia Tarehe:", datetime.date(datetime.date.today().year, 1, 1), key="rep_s")
    r_end = col_r2.date_input("Ripoti Hadi Tarehe:", datetime.date.today(), key="rep_e")
    
    rep_expenses_df = expenses_db.copy()
    if not rep_expenses_df.empty:
        rep_expenses_df["Tarehe_Parsed"] = pd.to_datetime(rep_expenses_df["Tarehe"]).dt.date
        rep_expenses_df = rep_expenses_df[(rep_expenses_df["Tarehe_Parsed"] >= r_start) & (rep_expenses_df["Tarehe_Parsed"] <= r_end)]
        t_matumizi = int(rep_expenses_df["Kiasi"].sum())
    else:
        t_matumizi = 0

    mapato_yote_yaliyokusanywa = t_ada_iliyolipwa + t_mchango_iliyolipwa
    balansi_kuu = mapato_yote_yaliyokusanywa - t_matumizi

    st.markdown("---")
    st.subheader("1. Muhtasari wa Mapato yote")
    data_mapato = {
        "Aina ya Mchango": ["Ada (Fees)", "Michango Mingine (Other)"],
        "Inayotakiwa (TSHS)": [f"{t_ada_inayotakiwa:,}", f"{t_mchango_inayotakiwa:,}"],
        "Iliyolipwa (TSHS)": [f"{t_ada_iliyolipwa:,}", f"{t_mchango_iliyolipwa:,}"],
        "Madeni / Owings (TSHS)": [f"{t_ada_madeni:,}", f"{t_mchango_madeni:,}"]
    }
    st.table(pd.DataFrame(data_mapato))

    st.subheader("2. Hali ya Mtiririko wa Pesa (Cash Flow)")
    col_summary1, col_summary2 = st.columns(2)
    with col_summary1:
        st.metric(label="💰 JUMLA YA MAPATO YALIYOKUSANYWA", value=f"TZS {mapato_yote_yaliyokusanywa:,}")
        st.metric(label="📉 JUMLA YA MATUMIZI YA KIPINDI HICHO", value=f"TZS {t_matumizi:,}")
    with col_summary2:
        st.metric(label="🏦 SALIO / BALANSI ILIYOBAKI", value=f"TZS {balansi_kuu:,}", delta=f" {balansi_kuu:,}")

    st.markdown("---")
    st.subheader("🖨️ Print Ripoti Rasmi ya Kifedha")
    
    pdf_general_data = generate_general_report_pdf(
        t_ada_inayotakiwa, t_ada_iliyolipwa, t_ada_madeni,
        t_mchango_inayotakiwa, t_mchango_iliyolipwa, t_mchango_madeni,
        t_matumizi, balansi_kuu, str(r_start), str(r_end)
    )
    
    st.download_button(
        label="📄 Pakua Ripoti Kuu ya Shule (PDF)",
        data=pdf_general_data,
        file_name=f"Ripoti_Kuu_ya_Fedha_{r_start}_hadi_{r_end}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

# ================================================ 7. RIPOTI ZA WANAFUNZI =======================================================#
# ================================================ 7. RIPOTI ZA WANAFUNZI =======================================================#

elif page == "RIPOTI ZA WANAFUNZI (Student Reports)":
    import zipfile
    
    # Kusoma taarifa za shule kwanza kwa ajili ya Kichwa Kikuu
    conn = sqlite3.connect(DB_FILE)
    df_set = pd.read_sql_query("SELECT * FROM system_settings LIMIT 1", conn)
    conn.close()
    
    school_name = df_set['School_Name'].iloc[0] if not df_set.empty else "SCHOOL FINANCIAL SYSTEM"
    school_location = df_set['Location'].iloc[0] if not df_set.empty else ""
    school_box = df_set['Box_No'].iloc[0] if not df_set.empty else ""
    school_phone = df_set['Phone'].iloc[0] if not df_set.empty else ""

    # Custom CSS kwa ajili ya Layout
    st.markdown("""
        <style>
        .school-header { background-color: #1E3A8A; padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .school-header h1 { margin: 0; font-size: 26px; font-weight: bold; color: #FFFFFF !important; }
        .school-header p { margin: 5px 0 0 0; font-size: 14px; opacity: 0.9; }
        .report-card { background-color: #F8FAFC; padding: 15px; border-radius: 8px; border-left: 5px solid #3B82F6; margin-bottom: 20px; }
        </style>
    """, unsafe_allow_html=True)

    # 1. Kuonyesha Taarifa za Shule kwenye Header ya Ukurasa (UI)
    st.markdown(f"""
        <div class="school-header">
            <h1>🏫 {school_name.upper()}</h1>
            <p>📍 P.O. Box {school_box}, {school_location} | 📞 Simu: {school_phone}</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.subheader("🖨️ Student Statement & Official Receipt")

    # --- FUNCTION YA KUTENGENEZA PDF ILI ITUMIKE KOTE ---
    def create_receipt_pdf(st_details, table_rows, jumla_imelipwa, jumla_inayodaiwa):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=30, bottomMargin=30)
        story = []
        styles = getSampleStyleSheet()
        
        style_school = ParagraphStyle('PdfSchool', parent=styles['Title'], fontSize=16, textColor=colors.HexColor("#1E3A8A"), spaceAfter=4)
        style_sub = ParagraphStyle('PdfSub', parent=styles['Normal'], fontSize=9, alignment=1, textColor=colors.HexColor("#475569"), spaceAfter=15)
        style_normal = ParagraphStyle('PdfNorm', parent=styles['Normal'], fontSize=10, spaceAfter=4)
        
        # Header
        story.append(Paragraph(f"<b>{school_name.upper()}</b>", style_school))
        story.append(Paragraph(f"P.O. Box {school_box}, {school_location} | Tel: {school_phone}", style_sub))
        story.append(Paragraph("<b><u>RISITI NA TAARIFA YA MALIPO (OFFICIAL STATEMENT)</u></b>", ParagraphStyle('Title2', parent=styles['Normal'], alignment=1, fontSize=12, spaceAfter=15)))
        
        # Taarifa za Mwanafunzi
        story.append(Paragraph(f"<b>Jina la Mwanafunzi:</b> {st_details['Name']}", style_normal))
        story.append(Paragraph(f"<b>Darasa / Kidato:</b> {st_details['Class']} ({st_details['Hostel_Status']})", style_normal))
        story.append(Paragraph(f"<b>Namba ya Usajili (ID):</b> {st_details['ID']}", style_normal))
        
        status_pdf_text = "AMEMALIZA MALIPO YOTE" if jumla_inayodaiwa <= 0 else f"ANADAIWA JUMLA YA TZS {jumla_inayodaiwa:,}"
        color_status = colors.HexColor("#16A34A") if jumla_inayodaiwa <= 0 else colors.HexColor("#DC2626")
        story.append(Paragraph(f"<b>Hali ya Jumla ya Malipo:</b> <font color='{color_status}'><b>{status_pdf_text}</b></font>", style_normal))
        story.append(Spacer(1, 15))
        
        # Jedwali
        pdf_table_data = [["Aina ya Mchango / Kipengele", "Kiasi Kilicholipwa", "Hali (Status & Deni)"]]
        for row in table_rows:
            clean_status = row[2].replace("🟢 ", "").replace("🔴 ", "")
            pdf_table_data.append([row[0], f"{row[1]:,} TZS", clean_status])
            
        pdf_table_data.append(["JUMLA KUU ILIYOLIPWA", f"{jumla_imelipwa:,} TZS", ""])
        pdf_table_data.append(["JUMLA KUU INAYODAIWA", f"{jumla_inayodaiwa:,} TZS", ""])
        
        t = Table(pdf_table_data, colWidths=[240, 120, 160])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E3A8A")), 
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('BACKGROUND', (0,1), (-1,-3), colors.HexColor("#F8FAFC")), 
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
            ('FONTNAME', (0,-2), (-1,-1), 'Helvetica-Bold'),
            ('BACKGROUND', (0,-2), (-1,-1), colors.HexColor("#E2E8F0")),
            ('TOPPADDING', (0,1), (-1,-1), 6),
            ('BOTTOMPADDING', (0,1), (-1,-1), 6),
        ]))
        story.append(t)
        
        # Saini
        story.append(Spacer(1, 40))
        story.append(Paragraph("____________________________&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;____________________________", style_normal))
        story.append(Paragraph("Saini ya Mhasibu / Mkuu wa Shule&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Tarehe ya Kutoa Risiti", style_normal))
        
        doc.build(story)
        return buffer.getvalue()

    # --- FUNCTION YA KUFANYA MAHESABU KWA MWANAFUNZI ---
    def calculate_student_data(st_details, df_fees, df_other, df_set):
        req_ada = int(df_set['Fee_Hostel'].iloc[0]) if st_details['Hostel_Status'] == 'Hostel Student' else int(df_set['Fee_Day'].iloc[0])
        
        if not df_fees.empty:
            paid_ada = int(df_fees['Total_Paid'].iloc[0] or 0)
            deni_ada = int(df_fees['Owings'].iloc[0] or 0)
        else:
            paid_ada, deni_ada = 0, req_ada

        r = df_other.iloc[0] if not df_other.empty else None
        
        req_t = int(df_set['Req_Tahadhari'].iloc[0]) if not df_set.empty else 0
        req_k = int(df_set['Req_Kitambulisho'].iloc[0]) if not df_set.empty else 0
        req_ta = int(df_set['Req_Taaluma'].iloc[0]) if not df_set.empty else 0
        req_m = int(df_set['Req_Michezo'].iloc[0]) if not df_set.empty else 0
        req_u = int(df_set['Req_Ukarabati'].iloc[0]) if not df_set.empty else 0
        req_b = int(df_set['Req_Bima'].iloc[0]) if not df_set.empty else 0
        req_f2 = int(df_set['Req_Mitihani_FII'].iloc[0]) if not df_set.empty else 0
        req_f4 = int(df_set['Req_Mitihani_FIV'].iloc[0]) if not df_set.empty else 0
        
        p_t = int(r["Tahadhari"]) if r is not None else 0
        p_k = int(r["Kitambulisho"]) if r is not None else 0
        p_ta = int(r["Taaluma"]) if r is not None else 0
        p_m = int(r["Michezo"]) if r is not None else 0
        p_u = int(r["Ukarabati"]) if r is not None else 0
        p_b = int(r["Bima"]) if r is not None else 0
        p_f2 = int(r["Mitihani_FII"]) if r is not None else 0
        p_f4 = int(r["Mitihani_FIV"]) if r is not None else 0

        paid_michango = p_t + p_k + p_ta + p_m + p_u + p_b
        req_michango = req_t + req_k + req_ta + req_m + req_u + req_b
        
        if st_details['Class'] == "Form II":
            paid_michango += p_f2
            req_michango += req_f2
        if st_details['Class'] == "Form IV":
            paid_michango += p_f4
            req_michango += req_f4
            
        deni_michango = max(0, req_michango - paid_michango)
        jumla_kuu_imelipwa = paid_ada + paid_michango
        jumla_kuu_inayodaiwa = deni_ada + deni_michango

        def get_item_status(paid, required):
            owed = required - paid
            return "🟢 KAMALIZA" if owed <= 0 else f"🔴 ANADAIWA ({owed:,})"

        table_rows = [
            ["Ada ya Shule", paid_ada, get_item_status(paid_ada, req_ada)],
            ["Mchango wa Tahadhari", p_t, get_item_status(p_t, req_t)],
            ["Mchango wa Kitambulisho", p_k, get_item_status(p_k, req_k)],
            ["Mchango wa Taaluma", p_ta, get_item_status(p_ta, req_ta)],
            ["Mchango wa Michezo", p_m, get_item_status(p_m, req_m)],
            ["Mchango wa Ukarabati", p_u, get_item_status(p_u, req_u)],
            ["Mchango wa Bima / NHIF", p_b, get_item_status(p_b, req_b)]
        ]

        if st_details['Class'] == "Form II": table_rows.append(["Mitihani Form II", p_f2, get_item_status(p_f2, req_f2)])
        if st_details['Class'] == "Form IV": table_rows.append(["Mitihani Form IV", p_f4, get_item_status(p_f4, req_f4)])

        return table_rows, paid_ada, paid_michango, jumla_kuu_imelipwa, jumla_kuu_inayodaiwa

    # TABS ZA KUTENGANISHA MOJA MOJA NA BULK
    tab_single, tab_bulk = st.tabs(["👤 Ripoti ya Mwanafunzi Mmoja", "📂 Bulk Export (Wanafunzi Wote)"])

    with tab_single:
        report_options = ["-- Chagua Mwanafunzi --"] + [f"{row['ID']} - {row['Name']}" for _, row in student_db.iterrows()]
        selected_report_student = st.selectbox("Tafuta au Chagua Mwanafunzi kutoa Ripoti:", report_options)

        if selected_report_student != "-- Chagua Mwanafunzi --":
            report_id = selected_report_student.split(" - ")[0]
            st_details = student_db[student_db["ID"].astype(str) == str(report_id)].iloc[0]
            
            conn = sqlite3.connect(DB_FILE)
            df_fees = pd.read_sql_query(f"SELECT * FROM fees WHERE ID='{report_id}'", conn)
            df_other = pd.read_sql_query(f"SELECT * FROM other_contributions WHERE ID='{report_id}'", conn)
            conn.close()

            table_rows, paid_ada, paid_michango, jumla_kuu_imelipwa, jumla_kuu_inayodaiwa = calculate_student_data(st_details, df_fees, df_other, df_set)

            # Card ya Taarifa za Mwanafunzi
            st.markdown(f"""
                <div class="report-card">
                    <h4>👤 TAARIFA ZA MWANAFUNZI</h4>
                    <b>Jina Kamili:</b> {st_details['Name']} &nbsp;|&nbsp; <b>Darasa:</b> {st_details['Class']} &nbsp;|&nbsp; 
                    <b>Hali ya Malazi:</b> {st_details['Hostel_Status']} &nbsp;|&nbsp; <b>ID:</b> {st_details['ID']}
                </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric(label="💰 Jumla Ada Iliyolipwa", value=f"{paid_ada:,} TZS")
            with col2: st.metric(label="📦 Michango Mingine Iliyolipwa", value=f"{paid_michango:,} TZS")
            with col3:
                delta_val = f"-{jumla_kuu_inayodaiwa:,} TZS" if jumla_kuu_inayodaiwa > 0 else "0 TZS"
                st.metric(label="🚨 Jumla Kuu Inayodaiwa", value=f"{jumla_kuu_inayodaiwa:,} TZS", delta=delta_val, delta_color="inverse")
            with col4:
                if jumla_kuu_inayodaiwa <= 0: st.success("🟢 STATUS KUU: AMEMALIZA")
                else: st.error("🔴 STATUS KUU: ANADAIWA")

            st.markdown("#### 📋 Mchanganuo wa Kila Kipengele na Hali ya Deni")
            df_display = pd.DataFrame(table_rows, columns=["Aina ya Kipengele", "Kiasi Kilicholipwa", "Hali (Status & Deni)"])
            df_display["Kiasi Kilicholipwa"] = df_display["Kiasi Kilicholipwa"].apply(lambda x: f"{x:,} TZS")
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            if st.button("🖨️ Zalisha Risiti Halisi (Generate PDF Receipt)", use_container_width=True):
                pdf_bytes = create_receipt_pdf(st_details, table_rows, jumla_kuu_imelipwa, jumla_kuu_inayodaiwa)
                st.download_button(
                    label="📥 Bofya Hapa Kupakua Risiti Rasmi (PDF)", 
                    data=pdf_bytes, 
                    file_name=f"Risiti_{st_details['Name'].replace(' ', '_')}.pdf", 
                    mime="application/pdf",
                    use_container_width=True
                )

    with tab_bulk:
        st.markdown("### 📥 Pakua Ripoti za Wanafunzi Wote (ZIP File)")
        st.info("Kipengele hiki kitachakata na kutengeneza faili la ZIP lenye risiti za PDF kwa KILA mwanafunzi aliye kwenye mfumo wako. Utapata PDF zote zikiwa zimepangwa kwa majina na ID.")
        
        if st.button("🚀 Tengeneza ZIP ya Wanafunzi Wote", use_container_width=True):
            with st.spinner("Inachakata data na kutengeneza PDFs... Tafadhali subiri (Inaweza kuchukua muda kidogo kulingana na idadi ya wanafunzi)."):
                
                # Fetch all data once to avoid repeated DB calls
                conn = sqlite3.connect(DB_FILE)
                df_all_students = pd.read_sql_query("SELECT * FROM students", conn)
                df_all_fees = pd.read_sql_query("SELECT * FROM fees", conn)
                df_all_other = pd.read_sql_query("SELECT * FROM other_contributions", conn)
                conn.close()

                zip_buffer = io.BytesIO()
                
                with zipfile.ZipFile(zip_buffer, "w") as zf:
                    for idx, st_row in df_all_students.iterrows():
                        report_id = str(st_row['ID'])
                        st_df_fees = df_all_fees[df_all_fees['ID'] == report_id]
                        st_df_other = df_all_other[df_all_other['ID'] == report_id]
                        
                        # Generate calculation for this student
                        t_rows, p_ada, p_michango, j_imelipwa, j_inayodaiwa = calculate_student_data(st_row, st_df_fees, st_df_other, df_set)
                        
                        # Generate PDF bytes
                        pdf_data = create_receipt_pdf(st_row, t_rows, j_imelipwa, j_inayodaiwa)
                        
                        # Add PDF to ZIP
                        safe_name = str(st_row['Name']).replace(" ", "_").replace("/", "-")
                        zf.writestr(f"Risiti_{safe_name}_{report_id}.pdf", pdf_data)

                zip_buffer.seek(0)
                st.success(f"✅ Faili la ZIP lenye ripoti za wanafunzi {len(df_all_students)} limekamilika!")
                
                st.download_button(
                    label="⬇️ Pakua Risiti Zote (.zip)",
                    data=zip_buffer,
                    file_name="Risiti_Zote_Wanafunzi.zip",
                    mime="application/zip",
                    use_container_width=True
                )


    # ========================================================================================================
    # KIPENGELE KIPYA: ORODHA YA WANAODAIWA KIVIDATO CHENYE PDF YA KISASA NA YA KIJANJA
    # ========================================================================================================
    st.markdown("---")
    st.subheader("📊 Orodha ya Wanafunzi Wanaodaiwa")
    st.write("Chagua kidato kisha bofya kitufe kutazama na kupakua orodha ya wanaodaiwa.")

    # 1. Chagua Kidato na Kitufe kinachojitegemea
    col_sel1, col_sel2 = st.columns([2, 1])
    with col_sel1:
        deni_class = st.selectbox(
            "Chagua Kidato cha Kuangalia Madeni:", 
            ["Form I", "Form II", "Form III", "Form IV", "Form V", "Form VI"],
            key="deni_class_select"
        )
    with col_sel2:
        st.markdown("<br>", unsafe_allow_html=True)
        tafuta_btn = st.button("🔍 Tafuta Wanaodaiwa", use_container_width=True)

    # 2. Tunatumia session_state kuhifadhi darasa lililotafutwa ili ukidownload PDF data isipotee
    if tafuta_btn:
        st.session_state['active_deni_class'] = deni_class

    # 3. Kama kuna darasa limeshatafutwa, onyesha data
    if 'active_deni_class' in st.session_state:
        current_class = st.session_state['active_deni_class']
        
        conn = sqlite3.connect(DB_FILE)
        query = """
            SELECT 
                s.ID AS [ID ya Mwanafunzi],
                s.Name AS [Jina Kamili],
                s.Class AS [Kidato],
                COALESCE(f.Owings, 0) AS [Deni la Ada],
                COALESCE(o.Owings, 0) AS [Deni la Michango Mingine]
            FROM students s
            LEFT JOIN fees f ON s.ID = f.ID
            LEFT JOIN other_contributions o ON s.ID = o.ID
            WHERE s.Class = ?
        """
        df_madeni = pd.read_sql_query(query, conn, params=(current_class,))
        conn.close()

        # Tunachuja wale wanaodaiwa tu
        df_wanaodaiwa = df_madeni[
            (df_madeni["Deni la Ada"] > 0) | (df_madeni["Deni la Michango Mingine"] > 0)
        ]

        if not df_wanaodaiwa.empty:
            jumla_ada = df_wanaodaiwa["Deni la Ada"].sum()
            jumla_michango = df_wanaodaiwa["Deni la Michango Mingine"].sum()

            # INTERNAL FUNCTION: Kutengeneza PDF ya Kijanja inayosona Jina la Shule
            def tengeneza_pdf_ya_kijanja(df, kidato, j_ada, j_michango):
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=35, leftMargin=35, topMargin=35, bottomMargin=35)
                story = []
                styles = getSampleStyleSheet()
                
                # Mitindo ya Kichwa inayotumia data za Shule
                title_style = ParagraphStyle(
                    'DocTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=28, 
                    textColor=colors.HexColor("#1E3A8A"), spaceAfter=15, alignment=1
                )
                school_info_style = ParagraphStyle(
                    'DocSub', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, 
                    textColor=colors.HexColor("#4B5563"), spaceAfter=15, alignment=1
                )
                report_title_style = ParagraphStyle(
                    'RepTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=22, 
                    textColor=colors.HexColor("#B91C1C"), spaceAfter=20, alignment=1 # Nyekundu iliyoiva
                )
                meta_style = ParagraphStyle(
                    'DocMeta', parent=styles['Normal'], fontName='Helvetica', fontSize=10, 
                    textColor=colors.HexColor("#374151"), spaceAfter=5
                )
                th_style = ParagraphStyle(
                    'TableHeaderStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, 
                    textColor=colors.white, alignment=0
                )
                td_style = ParagraphStyle(
                    'TableCellStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=9, 
                    textColor=colors.HexColor("#1F2937")
                )
                
                # CHOTA JINA NA TAARIFA ZA SHULE KUTOKA KWENYE GLOBAL VARIABLES ZAKO
                shule_jina = globals().get('SCHOOL_NAME', 'SHULE YETU HIGH SCHOOL')
                shule_box = globals().get('SCHOOL_BOX', 'P.O BOX XXXX')
                shule_mahali = globals().get('SCHOOL_LOCATION', 'TANZANIA')
                shule_simu = globals().get('SCHOOL_PHONE', '')

                story.append(Paragraph(f"{shule_jina.upper()}", title_style))
                story.append(Paragraph(f"{shule_box}, {shule_mahali} | Simu: {shule_simu}", school_info_style))
                story.append(Paragraph(f"RIPOTI RASMI YA WANAODAIWA — {kidato.upper()}", report_title_style))
                
                # Kipengele cha Muhtasari wa Kipato na Tarehe
                tarehe_sasa = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                story.append(Paragraph(f"<b>Tarehe ya Kuchapishwa:</b> {tarehe_sasa}", meta_style))
                story.append(Paragraph(f"<b>Jumla Kuu ya Ada Inayodaiwa:</b> TZS {j_ada:,.2f}", meta_style))
                story.append(Paragraph(f"<b>Jumla Kuu ya Michango Inayodaiwa:</b> TZS {j_michango:,.2f}", meta_style))
                story.append(Spacer(1, 15))
                
                # Maandalizi ya data za Jedwali la PDF
                table_data = [[
                    Paragraph("<b>ID ya Mwanafunzi</b>", th_style),
                    Paragraph("<b>Jina Kamili</b>", th_style),
                    Paragraph("<b>Deni la Ada (TZS)</b>", th_style),
                    Paragraph("<b>Michango Mingine (TZS)</b>", th_style)
                ]]
                
                for _, row in df.iterrows():
                    table_data.append([
                        Paragraph(str(row["ID ya Mwanafunzi"]), td_style),
                        Paragraph(str(row["Jina Kamili"]), td_style),
                        Paragraph(f"{row['Deni la Ada']:,.2f}", td_style),
                        Paragraph(f"{row['Deni la Michango Mingine']:,.2f}", td_style)
                    ])
                
                pdf_table = Table(table_data, colWidths=[90, 210, 115, 125])
                pdf_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E3A8A")), 
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, 0), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")), 
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]), 
                    ('TOPPADDING', (0, 1), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ]))
                
                story.append(pdf_table)
                doc.build(story)
                buffer.seek(0)
                return buffer.getvalue()

            # Onyesha kadi za muhtasari
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.metric(f"Jumla ya Madeni ya Ada ({current_class})", f"TZS {jumla_ada:,.2f}")
            with col_d2:
                st.metric(f"Jumla ya Michango Mingine ({current_class})", f"TZS {jumla_michango:,.2f}")

            # =========================================================================
            # VITUFE VYA KUDOWNLOAD VIPO JUU YA JEDWALI LA MAJINA SASA
            # =========================================================================
            st.markdown("#### 📥 Pakua Ripoti")
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                pdf_bytes = tengeneza_pdf_ya_kijanja(df_wanaodaiwa, current_class, jumla_ada, jumla_michango)
                st.download_button(
                    label=f"📄 Pakua PDF ya Wanaodaiwa ({current_class})",
                    data=pdf_bytes,
                    file_name=f"ripoti_madeni_{current_class.replace(' ', '_').lower()}.pdf",
                    mime='application/pdf',
                    use_container_width=True
                )
                
            with col_btn2:
                csv = df_wanaodaiwa.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"📥 Pakua Excel/CSV ({current_class})",
                    data=csv,
                    file_name=f"wanaodaiwa_{current_class.replace(' ', '_').lower()}.csv",
                    mime='text/csv',
                    use_container_width=True
                )

            # JEDWALI LINAWEKWA HAPA CHINI YA VITUFE VYA DOWNLOAD
            st.markdown(f"#### 📋 Orodha ya Majina ya {current_class}")
            st.dataframe(df_wanaodaiwa, use_container_width=True)
            
        else:
            st.success(f"🎉 Safi kabisa! Hakuna mwanafunzi anayedaiwa katika {current_class} kwa sasa.")


# ======================================= 8. SYSTEM SETTINGS (CONTROL SHEET - SASA INA MICHANGO YOTE) ==============================================
elif page == "⚙️ SYSTEM SETTINGS (Control Sheet)":
    st.header("⚙️ System Control Sheet")
    st.markdown("Hapa ndipo unapoweza kubadili data za msingi zinazo-control kurasa zote za mfumo mzima ikiwemo ada na **maadili ya lazima ya michango mingine**.")
    
    current_settings = get_settings()
    
    with st.form("settings_form"):
        st.subheader("🏢 Taarifa za Shule / Taasisi")
        col_s1, col_s2 = st.columns(2)
        set_name = col_s1.text_input("Jina la Shule (School Name):", value=current_settings["School_Name"])
        set_location = col_s2.text_input("Mahali (Location):", value=current_settings["Location"])
        
        col_s3, col_s4 = st.columns(2)
        set_box = col_s3.text_input("Sanduku la Posta (P.O. Box):", value=current_settings["Box_No"])
        set_phone = col_s4.text_input("Namba ya Simu ya Shule:", value=current_settings["Phone"])
        
        st.markdown("---")
        st.subheader("💰 Muundo wa Ada kwa Mwaka (Fee Structures)")
        col_s5, col_s6 = st.columns(2)
        set_fee_hostel = col_s5.number_input("Ada ya Wanafunzi wa Hostel (Hostel Student Fee):", value=int(current_settings["Fee_Hostel"]), step=50000)
        set_fee_day = col_s6.number_input("Ada ya Wanafunzi wa Kutwa (Day Student Fee):", value=int(current_settings["Fee_Day"]), step=50000)
        
        st.markdown("---")
        st.subheader("🎟️ Muundo wa Michango Mingine ya Kudumu (Required Fixed Other Contributions)")
        col_o1, col_o2 = st.columns(2)
        set_tahadhari = col_o1.number_input("Mchango wa Tahadhari:", value=int(current_settings.get("Req_Tahadhari", 10000)), step=1000)
        set_kitambulisho = col_o2.number_input("Mchango wa Kitambulisho:", value=int(current_settings.get("Req_Kitambulisho", 5000)), step=1000)
        
        col_o3, col_o4 = st.columns(2)
        set_taaluma = col_o3.number_input("Mchango wa Taaluma:", value=int(current_settings.get("Req_Taaluma", 20000)), step=1000)
        set_michezo = col_o4.number_input("Mchango wa Michezo:", value=int(current_settings.get("Req_Michezo", 5000)), step=1000)
        
        col_o5, col_o6 = st.columns(2)
        set_ukarabati = col_o5.number_input("Mchango wa Ukarabati:", value=int(current_settings.get("Req_Ukarabati", 10000)), step=1000)
        set_mitihani_fii = col_o6.number_input("Mitihani Form II:", value=int(current_settings.get("Req_Mitihani_FII", 0)), step=1000)
        
        col_o7, col_o8 = st.columns(2)
        set_mitihani_fiv = col_o7.number_input("Mitihani Form IV:", value=int(current_settings.get("Req_Mitihani_FIV", 0)), step=1000)
        set_bima = col_o8.number_input("Bima / NHIF:", value=int(current_settings.get("Req_Bima", 54400)), step=1000)
        
        btn_save_settings = st.form_submit_button("💾 Hifadhi Mabadiliko ya Mfumo", use_container_width=True)
        
    if btn_save_settings:
      conn = sqlite3.connect(DB_FILE)
      cursor = conn.cursor()
      cursor.execute("""
            UPDATE system_settings 
            SET School_Name=?, Location=?, Box_No=?, Phone=?, Fee_Hostel=?, Fee_Day=?,
                Req_Tahadhari=?, Req_Kitambulisho=?, Req_Taaluma=?, Req_Michezo=?, 
                Req_Ukarabati=?, Req_Mitihani_FII=?, Req_Mitihani_FIV=?, Req_Bima=?
            WHERE id=1
        """, (set_name, set_location, set_box, set_phone, set_fee_hostel, set_fee_day,
              set_tahadhari, set_kitambulisho, set_taaluma, set_michezo,
              set_ukarabati, set_mitihani_fii, set_mitihani_fiv, set_bima))
      conn.commit()
      conn.close()
      st.success("Mabadiliko yamehifadhiwa kiwanda! Mfumo mzima umehuishwa na vizuizi vya makosa vimesasishwa.")
      st.rerun()


# === SEHEMU YA BACKUP NA RESTORE ===
    st.markdown("---")
    st.subheader("💾 Backup & Restore ya Mfumo")
    col_b1, col_b2 = st.columns(2)

    # 1. Kitufe cha kudownload Backup
    with col_b1:
        st.markdown("**Pakua Backup ya Sasa:**")
        with open(DB_FILE, "rb") as f:
            st.download_button(
                label="📥 Download Backup (.db)",
                data=f,
                file_name=f"backup_database_{datetime.date.today()}.db",
                mime="application/octet-stream",
                use_container_width=True
            )

    # 2. Uploader ya kurudisha Backup
    with col_b2:
        st.markdown("**Rejesha Backup (Upload):**")
        uploaded_file = st.file_uploader("Chagua faili la backup (.db)", type=["db"])
        if uploaded_file is not None:
            if st.button("🔄 Thibitisha Urejeshaji (Restore)", use_container_width=True):
                try:
                    # Tunafunga connection kwanza ili tuweze ku-overwrite
                    with open(DB_FILE, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    st.success("✅ Backup imerejeshwa kikamilifu! Mfumo utajirudia (rerun) sasa hivi.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Imeshindikana kurejesha backup: {e}")

    st.warning("⚠️ Tahadhari: Urejeshaji (Restore) utafuta data zote za sasa na kuweka data za kwenye faili unaloli-upload.")


# ============================================= SEHEMU YA LOGO (UPLOAD TO DB) =========================================================#
    st.subheader("🖼️ Logo ya Shule")
    uploaded_logo = st.file_uploader("Upload Logo ya Shule (PNG/JPG)", type=["png", "jpg", "jpeg"])
    
    if uploaded_logo is not None:
        # Soma picha kama bytes
        logo_bytes = uploaded_logo.getvalue()
        
        # Hifadhi kwenye database
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE system_settings SET Logo_Blob=?", (logo_bytes,))
        conn.commit()
        conn.close()
        st.success("✅ Logo imehifadhiwa kwenye Database!")
        st.rerun()


# ==================================== SEHEMU YA SYSTEM RESET (WEKA CHINI YA SYSTEM SETTINGS) ===================================================== #
    st.markdown("---")
    st.markdown("### ⚠️ SEHEMU YA KUREJESHA MFUMO UPYA (SYSTEM RESET)")
    
    st.error(
        """
        🚨 **ONYO LA HATARI KUU:** Kitendo hiki kitafuta kabisa taarifa zifuatazo kutoka kwenye mfumo:
        1. Majina ya Wanafunzi wote na Madarasa yao (`students`).
        2. Kumbukumbu zote za malipo ya Ada (`fees`).
        3. Kumbukumbu zote za malipo ya Michango Mingine (`other_contributions`).
        
        **Kumbuka:** Ukishafuta, data hizi hazitoweza kurudishwa tena kwa namna yoyote ile!
        """
    )
    
    # Njia ya Usalama: Kulazimisha mtumiaji athibitishe kwa kuandika neno maalum
    thibitisho = st.text_input(
        "Ili kuzuia makosa ya bahati mbaya, tafadhali andika neno **RESET** kwa herufi kubwa hapa chini ili kuruhusu kitufe:", 
        value=""
    )
    
    if thibitisho == "RESET":
        st.warning("🔒 Kitufe kipo tayari sasa. Hakikisha una nakala (backup) ya data zako kabla ya kubonyeza!")
        
        # Kitufe chekundu cha hatari (type="primary")
        if st.button("🔴 FUTA DATA ZOTE NA URUDISHE MFUMO UPYA", type="primary", use_container_width=True):
            with st.spinner("Mfumo unasafishwa... Tafadhali subiri..."):
                try:
                    # Fungua connection ya database
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    
                    # 1. Futa data za wanafunzi
                    cursor.execute("DELETE FROM students")
                    
                    # 2. Futa data za ada
                    cursor.execute("DELETE FROM fees")
                    
                    # 3. Futa data za michango mingine
                    cursor.execute("DELETE FROM other_contributions")
                    
                    # === REKEBISHO LIPO HAPA ===
                    # Lazima tuthibitishe (commit) kufuta kwanza ili kufunga 'transaction' ya sasa
                    conn.commit()
                    
                    # Sasa hapa miamala (transactions) yote imefungwa, tunaruhusiwa ku-VACUUM bila error
                    cursor.execute("VACUUM")
                    
                    # Funga connection kabisa
                    conn.close()
                    
                    st.success("🎉 Mfumo umerudishwa upya kwa mafanikio! Data zote zimesafishwa kikamilifu.")
                    
                    # Mfumo unajirefresh ili dashboard na kurasa zingine zisomeke tupu kabisa
                    st.rerun()
                    
                except sqlite3.Error as e:
                    st.error(f"❌ Hitilafu imetokea kwenye Kanzidata (Database Error): {e}")
                except Exception as e:
                    st.error(f"❌ Hitilafu isiyotarajiwa imetokea: {e}")
    else:
        st.info("💡 Kitendo hiki ni cha hatari mno. Ili kuwasha kitufe cha kufuta, andika neno **RESET** kwa usahihi kwenye sanduku la maandishi hapo juu.")




# ================================================= SEHEMU YA PROMOTION YA WANAFUNZI ====================================================#
# ======================================================== 9. KUPROMOTE WANAFUNZI =======================================================#
elif page == "KUPROMOTE WANAFUNZI":
    st.header("🎓 Kupromote Wanafunzi (Mwaka Mpya)")
    st.warning("⚠️ ONYO: Kipengele hiki kitapandisha wanafunzi madarasa na KUFUTA rekodi zao zote za ada na michango ili kuanza mwaka mpya (majina na taarifa za msingi zitabaki). Hakikisha umepakua ripoti (backup) za mwaka ulioisha kabla ya kufanya hivi.")

    st.markdown("---")
    
    with st.form("promotion_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            from_class = st.selectbox("Kutoka Darasa (Darasa la Sasa):", ["Form I", "Form II", "Form III", "Form IV", "Form V", "Form VI"])
            
        with col2:
            to_class = st.selectbox("Kwenda Darasa Jipya:", ["Form I", "Form II", "Form III", "Form IV", "Form V", "Form VI", "Alumni (Wamehitimu)"])
            
        st.markdown("<br>", unsafe_allow_html=True)
        submit_promote = st.form_submit_button("🚀 PANDISHA DARASA NA FUTA MADENI", use_container_width=True)

    if submit_promote:
        if from_class == to_class:
            st.error("❌ Darasa la sasa na darasa jipya haviwezi kufanana. Tafadhali chagua kwa usahihi.")
        else:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()

            # Pata ID za wanafunzi wa darasa husika
            cursor.execute("SELECT ID FROM students WHERE Class=?", (from_class,))
            students_to_promote = cursor.fetchall()
            
            if not students_to_promote:
                st.info(f"ℹ️ Hakuna wanafunzi waliokutwa katika darasa la {from_class}.")
            else:
                # Tengeneza list ya IDs
                student_ids = [row[0] for row in students_to_promote]
                
                # Tengeneza placeholders (?, ?, ?) kulingana na idadi ya wanafunzi
                placeholders = ','.join('?' for _ in student_ids)

                try:
                    # 1. Update darasa kwenye table ya students (Majina yanabaki)
                    cursor.execute(f"UPDATE students SET Class=? WHERE ID IN ({placeholders})", [to_class] + student_ids)

                    # 2. Futa kumbu kumbu zote za ada (fees)
                    cursor.execute(f"DELETE FROM fees WHERE ID IN ({placeholders})", student_ids)

                    # 3. Futa kumbu kumbu zote za michango mingine (other_contributions)
                    cursor.execute(f"DELETE FROM other_contributions WHERE ID IN ({placeholders})", student_ids)

                    conn.commit()
                    
                    st.success(f"✅ KIKAMILIFU! Wanafunzi {len(student_ids)} wamepandishwa kutoka {from_class} kwenda {to_class}. Rekodi zao za ada na michango zimefutwa na mfumo upo tayari kwa mwaka mpya.")
                    
                except Exception as e:
                    st.error(f"❌ Kuna kosa limetokea: {e}")
                finally:
                    conn.close()




# ======================================================= 10. USER MANAGEMENT ==================================================================#

elif page == "USER MANAGEMENT":
    # 1. Ulinzi wa Ukurasa: Admin pekee ndiye anayeruhusiwa hapa
    if st.session_state.user_role != "Admin":
        st.error("🚫 Huna ruhusa ya kuingia kwenye ukurasa huu. Ni kwa ajili ya Admin pekee.")
    else:
        st.header("👥 Usimamizi wa Watumiaji (User Management)")
        st.markdown("Hapa unaweza kuongeza, kuhariri, na kufuta watumiaji wanaotumia mfumo huu.")

        # Gawanya kwenye Tabs ili iwe safi na ya kisasa
        tab_add, tab_manage = st.tabs(["➕ Ongeza User Mpya", "⚙️ Hariri / Futa Watumiaji (Manage)"])

        # ================= TAB 1: KUONGEZA USER =================
        with tab_add:
            st.subheader("Sajili Mtumiaji Mpya")
            with st.form("add_user_form"):
                col1, col2 = st.columns(2)
                with col1:
                    new_user = st.text_input("Jina la Mtumiaji (Username)")
                with col2:
                    new_role = st.selectbox("Cheo (Role)", ["User", "Admin"])
                
                new_pass = st.text_input("Nenosiri (Password)", type="password")
                submit_add = st.form_submit_button("💾 Hifadhi Mtumiaji", use_container_width=True)

                if submit_add:
                    if new_user and new_pass:
                        conn = sqlite3.connect(DB_FILE)
                        cursor = conn.cursor()
                        # Angalia kama mtumiaji tayari yupo
                        cursor.execute("SELECT * FROM users WHERE username=?", (new_user.lower(),))
                        if cursor.fetchone():
                            st.error(f"❌ Mtumiaji mwenye jina '{new_user}' yupo tayari kwenye mfumo!")
                        else:
                            cursor.execute("INSERT INTO users VALUES (?, ?, ?)", (new_user.lower(), new_pass, new_role))
                            conn.commit()
                            st.success(f"✅ Mtumiaji '{new_user}' ameongezwa kikamilifu!")
                        conn.close()
                    else:
                        st.warning("⚠️ Tafadhali jaza Username na Password.")

        # ================= TAB 2: EDIT, UPDATE NA DELETE =================
        with tab_manage:
            st.subheader("📋 Orodha ya Watumiaji Wote")

            # Vuta data zote za watumiaji
            conn = sqlite3.connect(DB_FILE)
            df_users = pd.read_sql_query("SELECT username AS 'Username', role AS 'Cheo (Role)', password AS 'Nenosiri' FROM users", conn)
            conn.close()

            # Onyesha Jedwali la Watumiaji
            st.dataframe(df_users, use_container_width=True)

            st.markdown("---")
            st.markdown("#### ✏️ Hariri (Update) au 🗑️ Futa (Delete) Mtumiaji")
            
            # Sanduku la kuchagua mtumiaji wa kumfanyia mabadiliko
            user_list = df_users["Username"].tolist()
            user_to_edit = st.selectbox("Tafuta au Chagua Username unayotaka kuhariri/kufuta:", ["-- Chagua Mtumiaji --"] + user_list)

            if user_to_edit != "-- Chagua Mtumiaji --":
                # Pata taarifa za sasa za mtumiaji aliyechaguliwa
                current_details = df_users[df_users["Username"] == user_to_edit].iloc[0]
                
                with st.form("edit_delete_user_form"):
                    st.info(f"Unahariri taarifa za mtumiaji: **{user_to_edit}**")
                    
                    # Username inakuwa disabled kwa sababu ni Primary Key (Haikubali kubadilishwa hovyo)
                    edit_user = st.text_input("Username (Huwezi kubadili jina hili)", value=current_details["Username"], disabled=True)
                    
                    e_col1, e_col2 = st.columns(2)
                    with e_col1:
                        edit_pass = st.text_input("Nenosiri Jipya (Password)", value=current_details["Nenosiri"], type="password")
                    with e_col2:
                        role_index = 0 if current_details["Cheo (Role)"] == "User" else 1
                        edit_role = st.selectbox("Badili Cheo (Role)", ["User", "Admin"], index=role_index)

                    # Vifungo vya Update na Delete
                    btn_col1, btn_col2 = st.columns(2)
                    btn_update = btn_col1.form_submit_button("🔄 Badili Taarifa (Update)", use_container_width=True)
                    btn_delete = btn_col2.form_submit_button("🗑️ Futa Mtumiaji (Delete)", use_container_width=True)

                    # ==== LOGIC YA UPDATE ====
                    if btn_update:
                        if user_to_edit == "admin" and edit_role == "User":
                            st.error("❌ KOSA LAKIUSALAMA: Huwezi kumshusha cheo Admin mkuu (Default Admin) kuwa User wa kawaida!")
                        else:
                            conn = sqlite3.connect(DB_FILE)
                            cursor = conn.cursor()
                            cursor.execute("UPDATE users SET password=?, role=? WHERE username=?", (edit_pass, edit_role, user_to_edit))
                            conn.commit()
                            conn.close()
                            st.success(f"✅ Taarifa za '{user_to_edit}' zimesasishwa kikamilifu!")
                            st.rerun()

                    # ==== LOGIC YA DELETE ====
                    if btn_delete:
                        if user_to_edit == "admin":
                            st.error("❌ KOSA LAKIUSALAMA: Huwezi kumfuta Admin mkuu (Default Admin) kwenye mfumo!")
                        elif user_to_edit == st.session_state.username if 'username' in st.session_state else "":
                            st.warning("⚠️ Huwezi kujifuta mwenyewe ukiwa ndani ya mfumo.")
                        else:
                            conn = sqlite3.connect(DB_FILE)
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM users WHERE username=?", (user_to_edit,))
                            conn.commit()
                            conn.close()
                            st.success(f"🗑️ Mtumiaji '{user_to_edit}' amefutwa kabisa kutoka kwenye kanzidata!")
                            st.rerun()