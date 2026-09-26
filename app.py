import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import hashlib
import os
from datetime import datetime, timedelta

# ==========================================
# CONFIGURACIÓN PÁGINA & THEME
# ==========================================
st.set_page_config(
    page_title="Rattlesnake System",
    page_icon="🐍",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_PATH = "database/erp_local.db"

# ==========================================
# ESTILOS CSS - CONTRASTE ALTO & PALETA EJECUTIVA CLARA
# ==========================================
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }
        
        /* Fondo Principal Claro */
        .stApp {
            background-color: #F8FAFC !important;
            color: #0F172A !important;
        }
        
        /* Forzar texto oscuro en todas las etiquetas e inputs */
        label, p, span, h1, h2, h3, h4, h5, h6, div {
            color: #0F172A !important;
        }

        /* Input fields y labels en formularios */
        div[data-baseweb="input"] {
            background-color: #FFFFFF !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 8px !important;
        }
        
        div[data-baseweb="input"] input {
            color: #0F172A !important;
            background-color: #FFFFFF !important;
        }

        /* Sidebar con contraste claro */
        section[data-testid="stSidebar"] {
            background-color: #E2E8F0 !important;
            border-right: 1px solid #CBD5E1;
        }
        
        section[data-testid="stSidebar"] * {
            color: #1E293B !important;
        }
        
        section[data-testid="stSidebar"] div[role="radiogroup"] label {
            padding: 8px 12px;
            border-radius: 8px;
            transition: all 0.2s ease;
        }
        
        section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
            background-color: #CBD5E1 !important;
        }
        
        /* Encabezados y Marcas */
        .main-header {
            font-size: 26px;
            font-weight: 800;
            color: #0F172A !important;
            letter-spacing: -0.5px;
            margin-bottom: 20px;
        }
        
        .brand-header {
            font-size: 22px;
            font-weight: 800;
            color: #0284C7 !important;
        }
        
        /* Botones de Acción */
        .stButton>button {
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.2s ease-in-out;
            background: #0284C7 !important;
            color: #FFFFFF !important;
            border: none;
            padding: 8px 16px;
        }
        
        .stButton>button * {
            color: #FFFFFF !important;
        }
        
        .stButton>button:hover {
            background: #0369A1 !important;
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.25);
        }
        
        /* Tarjetas de Métricas */
        div[data-testid="stMetric"] {
            background-color: #FFFFFF !important;
            padding: 16px;
            border-radius: 10px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }
        
        div[data-testid="stMetricValue"] * {
            font-size: 24px !important;
            font-weight: 700 !important;
            color: #0284C7 !important;
        }

        /* Cajas de alerta e Info */
        div[data-testid="stAlert"] {
            background-color: #F1F5F9 !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 8px !important;
        }
        div[data-testid="stAlert"] * {
            color: #1E293B !important;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# DICCIONARIO BILINGÜE (i18n)
# ==========================================
TEXTS = {
    "ES": {
        "app_title": "Rattlesnake System",
        "app_subtitle": "Control Ejecutivo de Obra & Gestión Financiera",
        "login_title": "Acceso al Sistema",
        "user_label": "Usuario Maestro",
        "pass_label": "Contraseña",
        "btn_login": "Ingresar al Sistema",
        "err_login": "Usuario o contraseña incorrectos.",
        "demo_info": "🔑 Acceso Maestro Inicial:",
        "nav_title": "MENÚ PRINCIPAL",
        "nav_balance": "📊 Balance Financiero",
        "nav_obras": "🏗️ Obras & Ubicaciones",
        "nav_gantt": "📅 Calendario de Trabajo (Gantt)",
        "nav_pagos": "🗓️ Calendario de Pagos (CxP)",
        "nav_costos": "💰 Registro de Costos",
        "nav_req": "📋 Requisiciones de Campo",
        "nav_users": "👑 Usuarios Maestros",
        "btn_logout": "Cerrar Sesión",
        "lang_selector": "🌐 Idioma / Language",
        # Balance
        "bal_title": "📊 Dashboard Financiero Ejecutivo",
        "metric_budget": "Presupuesto Contratado",
        "metric_executed": "Costo Real Ejecutado",
        "metric_pending": "Cuentas por Pagar (CxP)",
        "metric_available": "Margen / Disponible",
        "chart_cat": "Desglose de Costos por Categoría",
        "chart_comp": "Presupuesto vs Costo Real por Proyecto",
        # Cronograma
        "gantt_title": "📅 Cronograma de Trabajo & Plan de Obra",
        "lbl_task": "Actividad / Etapa de Obra",
        "lbl_start": "Fecha de Inicio",
        "lbl_end": "Fecha de Término",
        "btn_add_task": "Agregar Tarea al Cronograma",
        # Pagos
        "pagos_title": "🗓️ Programación & Calendario de Pagos",
        "tab_calendar": "📅 Calendario de Vencimientos",
        "tab_new_cxp": "➕ Programar Nuevo Pago",
        "lbl_provider": "Proveedor / Subcontratista",
        "lbl_due": "Fecha Límite de Pago",
        "btn_save_cxp": "Registrar Compromiso de Pago",
        # Obras
        "obras_title": "🏗️ Gestión de Obras & Coordenadas GPS",
        "tab_map": "🗺️ Mapa & Listado de Obras",
        "tab_new_obra": "➕ Registrar Nueva Obra",
        "lbl_code": "Código de Obra",
        "lbl_name": "Nombre de la Obra / Proyecto",
        "lbl_client": "Cliente / Empresa",
        "lbl_budget": "Presupuesto Contratado ($)",
        "lbl_lat": "Latitud GPS",
        "lbl_lon": "Longitud GPS",
        "btn_save_obra": "Guardar Proyecto",
        # Costos
        "costos_title": "💰 Captura & Control Metódico de Costos",
        "lbl_select_obra": "Seleccionar Obra",
        "lbl_cat": "Categoría de Costo",
        "lbl_concept": "Concepto / Descripción del Gasto",
        "lbl_amount": "Monto Total ($)",
        "lbl_date": "Fecha del Gasto",
        "btn_save_costo": "Registrar Costo",
        "costos_history": "Historial de Costos Registrados",
        # Requisiciones
        "req_title": "📋 Requisiciones de Insumos & Campo",
        "lbl_item": "Insumo / Material Requerido",
        "lbl_qty": "Cantidad",
        "lbl_unit": "Unidad",
        "lbl_priority": "Prioridad",
        "btn_send_req": "Enviar Requisición",
        # Usuarios
        "users_title": "👑 Control & Alta de Usuarios Maestros",
        "lbl_fullname": "Nombre Completo",
        "btn_create_user": "Dar de Alta Usuario Maestro"
    },
    "EN": {
        "app_title": "Rattlesnake System",
        "app_subtitle": "Executive Site Control & Financial Management",
        "login_title": "System Access",
        "user_label": "Master User",
        "pass_label": "Password",
        "btn_login": "Sign In",
        "err_login": "Invalid username or password.",
        "demo_info": "🔑 Initial Master Access:",
        "nav_title": "MAIN MENU",
        "nav_balance": "📊 Financial Balance",
        "nav_obras": "🏗️ Projects & Locations",
        "nav_gantt": "📅 Work Schedule (Gantt)",
        "nav_pagos": "🗓️ Payment Schedule (AP)",
        "nav_costos": "💰 Cost Tracking",
        "nav_req": "📋 Field Requisitions",
        "nav_users": "👑 Master Users",
        "btn_logout": "Sign Out",
        "lang_selector": "🌐 Language / Idioma",
        # Balance
        "bal_title": "📊 Executive Financial Dashboard",
        "metric_budget": "Contracted Budget",
        "metric_executed": "Actual Cost Executed",
        "metric_pending": "Accounts Payable (AP)",
        "metric_available": "Margin / Available",
        "chart_cat": "Cost Breakdown by Category",
        "chart_comp": "Budget vs Actual Cost per Project",
        # Cronograma
        "gantt_title": "📅 Project Schedule & Gantt Chart",
        "lbl_task": "Activity / Site Phase",
        "lbl_start": "Start Date",
        "lbl_end": "End Date",
        "btn_add_task": "Add Task to Schedule",
        # Pagos
        "pagos_title": "🗓️ Payment Schedule & AP Calendar",
        "tab_calendar": "📅 Due Dates Calendar",
        "tab_new_cxp": "➕ Schedule New Payment",
        "lbl_provider": "Vendor / Subcontractor",
        "lbl_due": "Payment Due Date",
        "btn_save_cxp": "Save Payment Commitment",
        # Obras
        "obras_title": "🏗️ Project Management & GPS Coordinates",
        "tab_map": "🗺️ Map & Project List",
        "tab_new_obra": "➕ Register New Project",
        "lbl_code": "Project Code",
        "lbl_name": "Project Name",
        "lbl_client": "Client / Company",
        "lbl_budget": "Contracted Budget ($)",
        "lbl_lat": "GPS Latitude",
        "lbl_lon": "GPS Longitude",
        "btn_save_obra": "Save Project",
        # Costos
        "costos_title": "💰 Systematic Cost Tracking",
        "lbl_select_obra": "Select Project",
        "lbl_cat": "Cost Category",
        "lbl_concept": "Concept / Expense Description",
        "lbl_amount": "Total Amount ($)",
        "lbl_date": "Expense Date",
        "btn_save_costo": "Register Expense",
        "costos_history": "Expense Log History",
        # Requisiciones
        "req_title": "📋 Field Requisitions & Supplies",
        "lbl_item": "Material / Supply Needed",
        "lbl_qty": "Quantity",
        "lbl_unit": "Unit",
        "lbl_priority": "Priority Level",
        "btn_send_req": "Submit Requisition",
        # Usuarios
        "users_title": "👑 Master User Access Control",
        "lbl_fullname": "Full Name",
        "btn_create_user": "Register Master User"
    }
}

# ==========================================
# BASE DE DATOS & SEGURIDAD
# ==========================================
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

def init_db():
    os.makedirs("database", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nombre_completo TEXT NOT NULL,
            rol TEXT DEFAULT 'Usuario Maestro'
        )
    ''')
    
    c.execute("SELECT * FROM usuarios WHERE username = 'admin'")
    if not c.fetchone():
        c.execute(
            "INSERT INTO usuarios (username, password, nombre_completo, rol) VALUES (?, ?, ?, ?)",
            ("admin", make_hashes("admin123"), "Usuario Maestro", "Usuario Maestro")
        )

    c.execute('''
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            cliente TEXT NOT NULL,
            presupuesto_total REAL NOT NULL,
            latitud REAL,
            longitud REAL,
            estado TEXT DEFAULT 'En Proceso',
            fecha_inicio DATE DEFAULT CURRENT_DATE
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS costos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proyecto_id INTEGER,
            categoria TEXT NOT NULL,
            concepto TEXT NOT NULL,
            monto REAL NOT NULL,
            fecha DATE DEFAULT CURRENT_DATE,
            registrado_por TEXT NOT NULL,
            observaciones TEXT,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos (id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS cronograma (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proyecto_id INTEGER,
            actividad TEXT NOT NULL,
            fecha_inicio DATE NOT NULL,
            fecha_fin DATE NOT NULL,
            avance INTEGER DEFAULT 0,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos (id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS cuentas_por_pagar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proyecto_id INTEGER,
            proveedor TEXT NOT NULL,
            concepto TEXT NOT NULL,
            monto_total REAL NOT NULL,
            monto_pagado REAL DEFAULT 0,
            estatus TEXT DEFAULT 'Pendiente',
            fecha_vencimiento DATE,
            registrado_por TEXT NOT NULL,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos (id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS requisiciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proyecto_id INTEGER,
            insumo TEXT NOT NULL,
            cantidad REAL NOT NULL,
            unidad TEXT NOT NULL,
            prioridad TEXT DEFAULT 'Normal',
            solicitado_por TEXT NOT NULL,
            estatus TEXT DEFAULT 'Pendiente',
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos (id)
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# ==========================================
# MANEJO DE SESIÓN
# ==========================================
if 'lang' not in st.session_state:
    st.session_state['lang'] = 'ES'

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_info'] = None

t = TEXTS[st.session_state['lang']]

# ==========================================
# PANTALLA DE LOGIN
# ==========================================
if not st.session_state['logged_in']:
    st.markdown(f"<h1 style='text-align: center; margin-top: 40px;'>🐍 {t['app_title']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center;'>{t['app_subtitle']}</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.subheader(t["login_title"])
        username = st.text_input(t["user_label"], key="login_u")
        password = st.text_input(t["pass_label"], type="password", key="login_p")
        
        if st.button(t["btn_login"], use_container_width=True):
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('SELECT username, password, nombre_completo, rol FROM usuarios WHERE username = ?', (username,))
            data = c.fetchone()
            conn.close()
            
            if data and check_hashes(password, data[1]):
                st.session_state['logged_in'] = True
                st.session_state['user_info'] = {"username": data[0], "nombre": data[2], "rol": data[3]}
                st.rerun()
            else:
                st.error(t["err_login"])
        
        st.info(f"{t['demo_info']}\n- User: **admin**\n- Password: **admin123**")
    st.stop()

# ==========================================
# BARRA LATERAL (UX/UI ESTRUCTURA)
# ==========================================
user = st.session_state['user_info']

st.sidebar.markdown(f"<h2 class='brand-header'>🐍 {t['app_title']}</h2>", unsafe_allow_html=True)
st.sidebar.caption(f"{t['app_subtitle']}")
st.sidebar.markdown("---")

opciones_menu = [
    t["nav_balance"],
    t["nav_obras"],
    t["nav_gantt"],
    t["nav_pagos"],
    t["nav_costos"],
    t["nav_req"],
    t["nav_users"]
]

menu_sel = st.sidebar.radio(t["nav_title"], opciones_menu)
st.sidebar.markdown("---")

lang_choice = st.sidebar.selectbox(
    t["lang_selector"], 
    ["Español (ES)", "English (EN)"], 
    index=0 if st.session_state['lang'] == 'ES' else 1
)
new_lang = "ES" if "Español" in lang_choice else "EN"

if new_lang != st.session_state['lang']:
    st.session_state['lang'] = new_lang
    st.rerun()

st.sidebar.markdown(f"👤 **{user['nombre']}**  \n<small>👑 {user['rol']}</small>", unsafe_allow_html=True)

if st.sidebar.button(t["btn_logout"], use_container_width=True):
    st.session_state['logged_in'] = False
    st.session_state['user_info'] = None
    st.rerun()

# ==========================================
# CONSULTAS A BASE DE DATOS
# ==========================================
def get_proyectos_df():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM proyectos ORDER BY id DESC", conn)
    conn.close()
    return df

def get_costos_df(proyecto_id=None):
    conn = sqlite3.connect(DB_PATH)
    if proyecto_id:
        df = pd.read_sql_query("SELECT c.*, p.nombre as proyecto FROM costos c JOIN proyectos p ON c.proyecto_id = p.id WHERE c.proyecto_id = ?", conn, params=(proyecto_id,))
    else:
        df = pd.read_sql_query("SELECT c.*, p.nombre as proyecto FROM costos c JOIN proyectos p ON c.proyecto_id = p.id", conn)
    conn.close()
    return df

def get_cxp_df(proyecto_id=None):
    conn = sqlite3.connect(DB_PATH)
    if proyecto_id:
        df = pd.read_sql_query("SELECT cxp.*, p.nombre as proyecto FROM cuentas_por_pagar cxp JOIN proyectos p ON cxp.proyecto_id = p.id WHERE cxp.proyecto_id = ?", conn, params=(proyecto_id,))
    else:
        df = pd.read_sql_query("SELECT cxp.*, p.nombre as proyecto FROM cuentas_por_pagar cxp JOIN proyectos p ON cxp.proyecto_id = p.id", conn)
    conn.close()
    return df

def get_cronograma_df(proyecto_id=None):
    conn = sqlite3.connect(DB_PATH)
    if proyecto_id:
        df = pd.read_sql_query("SELECT cr.*, p.nombre as proyecto FROM cronograma cr JOIN proyectos p ON cr.proyecto_id = p.id WHERE cr.proyecto_id = ?", conn, params=(proyecto_id,))
    else:
        df = pd.read_sql_query("SELECT cr.*, p.nombre as proyecto FROM cronograma cr JOIN proyectos p ON cr.proyecto_id = p.id", conn)
    conn.close()
    return df

# ==========================================
# 1. BALANCE FINANCIERO PREDETERMINADO
# ==========================================
if menu_sel == t["nav_balance"]:
    st.markdown(f"<div class='main-header'>{t['bal_title']}</div>", unsafe_allow_html=True)
    
    proyectos_df = get_proyectos_df()
    costos_df = get_costos_df()
    cxp_df = get_cxp_df()

    if proyectos_df.empty:
        st.info("Sin proyectos registrados aún en el sistema.")
    else:
        presupuesto_total = proyectos_df['presupuesto_total'].sum()
        costo_total_ejecutado = costos_df['monto'].sum() if not costos_df.empty else 0
        pagos_pendientes_total = (cxp_df['monto_total'] - cxp_df['monto_pagado']).sum() if not cxp_df.empty else 0
        balance_disponible = presupuesto_total - costo_total_ejecutado

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(t["metric_budget"], f"${presupuesto_total:,.2f}")
        c2.metric(t["metric_executed"], f"${costo_total_ejecutado:,.2f}", delta=f"-{(costo_total_ejecutado/presupuesto_total*100) if presupuesto_total>0 else 0:.1f}%", delta_color="inverse")
        c3.metric(t["metric_pending"], f"${pagos_pendientes_total:,.2f}")
        c4.metric(t["metric_available"], f"${balance_disponible:,.2f}", delta=f"{(balance_disponible/presupuesto_total*100) if presupuesto_total>0 else 0:.1f}%")

        st.markdown("---")
        
        col_graf1, col_graf2 = st.columns(2)

        with col_graf1:
            st.subheader(t["chart_cat"])
            if not costos_df.empty:
                fig_cat = px.pie(costos_df, names='categoria', values='monto', hole=0.45,
                                 color_discrete_sequence=px.colors.qualitative.Set2)
                fig_cat.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#0F172A')
                st.plotly_chart(fig_cat, use_container_width=True)
            else:
                st.info("No hay gastos registrados para graficar.")

        with col_graf2:
            st.subheader(t["chart_comp"])
            if not costos_df.empty:
                costo_por_obra = costos_df.groupby('proyecto_id')['monto'].sum().reset_index()
                df_comp = proyectos_df.merge(costo_por_obra, left_on='id', right_on='proyecto_id', how='left').fillna(0)
                
                fig_bar = go.Figure(data=[
                    go.Bar(name='Presupuesto', x=df_comp['nombre'], y=df_comp['presupuesto_total'], marker_color='#0284C7'),
                    go.Bar(name='Ejecutado', x=df_comp['nombre'], y=df_comp['monto'], marker_color='#EF4444')
                ])
                fig_bar.update_layout(barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#0F172A')
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("Sin datos comparativos de obra.")

# ==========================================
# 2. CALENDARIO DE TRABAJO (GANTT)
# ==========================================
elif menu_sel == t["nav_gantt"]:
    st.markdown(f"<div class='main-header'>{t['gantt_title']}</div>", unsafe_allow_html=True)
    
    proyectos_df = get_proyectos_df()
    if proyectos_df.empty:
        st.warning("Registra una obra o proyecto primero.")
    else:
        proyectos_dict = dict(zip(proyectos_df['nombre'], proyectos_df['id']))
        obra_sel = st.selectbox(t["lbl_select_obra"], list(proyectos_dict.keys()), key="gantt_p_sel")
        obra_id = proyectos_dict[obra_sel]

        col_gantt1, col_gantt2 = st.columns([1.2, 1])

        with col_gantt2:
            st.subheader("➕ Agregar Tarea al Cronograma")
            with st.form("form_gantt"):
                actividad = st.text_input(t["lbl_task"])
                c_f1, c_f2 = st.columns(2)
                with c_f1:
                    f_inc = st.date_input(t["lbl_start"], datetime.now())
                with c_f2:
                    f_fin = st.date_input(t["lbl_end"], datetime.now() + timedelta(days=7))
                avance = st.slider("% Avance", 0, 100, 0)

                if st.form_submit_button(t["btn_add_task"]):
                    if actividad and f_fin >= f_inc:
                        conn = sqlite3.connect(DB_PATH)
                        c = conn.cursor()
                        c.execute(
                            "INSERT INTO cronograma (proyecto_id, actividad, fecha_inicio, fecha_fin, avance) VALUES (?, ?, ?, ?, ?)",
                            (obra_id, actividad, f_inc, f_fin, avance)
                        )
                        conn.commit()
                        conn.close()
                        st.success("Actividad agregada.")
                        st.rerun()

        with col_gantt1:
            st.subheader("📊 Diagrama de Gantt")
            c_df = get_cronograma_df(obra_id)
            if not c_df.empty:
                fig_gantt = px.timeline(
                    c_df, 
                    x_start="fecha_inicio", 
                    x_end="fecha_fin", 
                    y="actividad", 
                    color="avance",
                    color_continuous_scale="Blues",
                    title=f"Planificación de Obra: {obra_sel}"
                )
                fig_gantt.update_yaxes(autorange="reversed")
                fig_gantt.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#0F172A')
                st.plotly_chart(fig_gantt, use_container_width=True)
            else:
                st.info("Sin tareas en el cronograma para este proyecto.")

# ==========================================
# 3. CALENDARIO DE PAGOS Y PROGRAMACIÓN (CXP)
# ==========================================
elif menu_sel == t["nav_pagos"]:
    st.markdown(f"<div class='main-header'>{t['pagos_title']}</div>", unsafe_allow_html=True)
    
    proyectos_df = get_proyectos_df()
    if proyectos_df.empty:
        st.warning("Registra una obra o proyecto primero.")
    else:
        proyectos_dict = dict(zip(proyectos_df['nombre'], proyectos_df['id']))

        tab_cal, tab_form = st.tabs([t["tab_calendar"], t["tab_new_cxp"]])

        with tab_cal:
            cxp_df = get_cxp_df()
            if not cxp_df.empty:
                cxp_df['Pendiente'] = cxp_df['monto_total'] - cxp_df['monto_pagado']
                
                # Gráfico de Vencimiento de Pagos por Mes
                cxp_df['fecha_vencimiento'] = pd.to_datetime(cxp_df['fecha_vencimiento'])
                fig_pagos = px.bar(
                    cxp_df, 
                    x="fecha_vencimiento", 
                    y="Pendiente", 
                    color="proveedor", 
                    title="Programación de Vencimientos de Pagos",
                    labels={"fecha_vencimiento": "Fecha de Vencimiento", "Pendiente": "Monto Por Pagar ($)"}
                )
                fig_pagos.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#0F172A')
                st.plotly_chart(fig_pagos, use_container_width=True)
                
                st.markdown("---")
                st.dataframe(cxp_df[['id', 'proyecto', 'proveedor', 'concepto', 'monto_total', 'monto_pagado', 'Pendiente', 'estatus', 'fecha_vencimiento']], use_container_width=True)

                c1, c2 = st.columns(2)
                with c1:
                    cxp_id = st.number_input(t["lbl_cxp_id"], min_value=1, step=1)
                with c2:
                    monto_abono = st.number_input(t["lbl_pay_amount"], min_value=0.01, step=500.0)

                if st.button(t["btn_pay"]):
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute("SELECT monto_total, monto_pagado FROM cuentas_por_pagar WHERE id = ?", (cxp_id,))
                    row = c.fetchone()
                    if row:
                        total, pagado = row
                        nuevo_pagado = pagado + monto_abono
                        nuevo_estatus = "Pagado" if nuevo_pagado >= total else "Parcial"
                        c.execute("UPDATE cuentas_por_pagar SET monto_pagado = ?, estatus = ? WHERE id = ?", (nuevo_pagado, nuevo_estatus, cxp_id))
                        conn.commit()
                        st.success("Pago/Abono registrado.")
                        st.rerun()
                    conn.close()

        with tab_form:
            with st.form("form_cxp_new"):
                obra_sel = st.selectbox(t["lbl_select_obra"], list(proyectos_dict.keys()), key="cxp_p_sel")
                obra_id = proyectos_dict[obra_sel]
                proveedor = st.text_input(t["lbl_provider"])
                concepto = st.text_input(t["lbl_concept"])
                monto_total = st.number_input(t["lbl_amount"], min_value=0.01, step=1000.0)
                vencimiento = st.date_input(t["lbl_due"], datetime.now())

                if st.form_submit_button(t["btn_save_cxp"]):
                    if proveedor and concepto and monto_total > 0:
                        conn = sqlite3.connect(DB_PATH)
                        c = conn.cursor()
                        c.execute(
                            "INSERT INTO cuentas_por_pagar (proyecto_id, proveedor, concepto, monto_total, fecha_vencimiento, registrado_por) VALUES (?, ?, ?, ?, ?, ?)",
                            (obra_id, proveedor, concepto, monto_total, vencimiento, user['nombre'])
                        )
                        conn.commit()
                        conn.close()
                        st.success("Compromiso de pago programado.")
                        st.rerun()

# ==========================================
# 4. OBRAS Y UBICACIONES GPS
# ==========================================
elif menu_sel == t["nav_obras"]:
    st.markdown(f"<div class='main-header'>{t['obras_title']}</div>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs([t["tab_map"], t["tab_new_obra"]])

    with tab1:
        df_obras = get_proyectos_df()
        if not df_obras.empty:
            df_mapa = df_obras.dropna(subset=['latitud', 'longitud'])
            if not df_mapa.empty:
                st.map(df_mapa, latitude='latitud', longitude='longitud', size=25)
            st.markdown("---")
            st.dataframe(df_obras[['codigo', 'nombre', 'cliente', 'presupuesto_total', 'estado', 'latitud', 'longitud']], use_container_width=True)
        else:
            st.info("No hay proyectos registrados.")

    with tab2:
        with st.form("form_nueva_obra"):
            codigo = st.text_input(t["lbl_code"])
            nombre = st.text_input(t["lbl_name"])
            cliente = st.text_input(t["lbl_client"])
            presupuesto = st.number_input(t["lbl_budget"], min_value=0.0, step=10000.0)
            
            c_lat, c_lon = st.columns(2)
            with c_lat:
                latitud = st.number_input(t["lbl_lat"], format="%.6f", value=24.8091)
            with c_lon:
                longitud = st.number_input(t["lbl_lon"], format="%.6f", value=-107.3940)

            if st.form_submit_button(t["btn_save_obra"]):
                if codigo and nombre and cliente:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    try:
                        c.execute(
                            "INSERT INTO proyectos (codigo, nombre, cliente, presupuesto_total, latitud, longitud) VALUES (?, ?, ?, ?, ?, ?)",
                            (codigo, nombre, cliente, presupuesto, latitud, longitud)
                        )
                        conn.commit()
                        st.success("Proyecto registrado.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                    finally:
                        conn.close()

# ==========================================
# 5. REGISTRO DE COSTOS
# ==========================================
elif menu_sel == t["nav_costos"]:
    st.markdown(f"<div class='main-header'>{t['costos_title']}</div>", unsafe_allow_html=True)
    
    proyectos_df = get_proyectos_df()
    if proyectos_df.empty:
        st.warning("Registra una obra o proyecto primero.")
    else:
        proyectos_dict = dict(zip(proyectos_df['nombre'], proyectos_df['id']))
        col_sel, col_form = st.columns([1, 1.2])

        with col_sel:
            obra_sel = st.selectbox(t["lbl_select_obra"], list(proyectos_dict.keys()), key="costos_p_sel")
            obra_id = proyectos_dict[obra_sel]

            with st.form("form_costo"):
                categoria = st.selectbox(t["lbl_cat"], [
                    "Materiales / Materials",
                    "Mano de Obra / Labor",
                    "Equipos / Equipment",
                    "Subcontratos / Subcontracts",
                    "Gastos Indirectos / Indirects"
                ])
                concepto = st.text_input(t["lbl_concept"])
                monto = st.number_input(t["lbl_amount"], min_value=0.01, step=500.0)
                fecha_costo = st.date_input(t["lbl_date"], datetime.now())

                if st.form_submit_button(t["btn_save_costo"]):
                    if concepto and monto > 0:
                        conn = sqlite3.connect(DB_PATH)
                        c = conn.cursor()
                        c.execute(
                            "INSERT INTO costos (proyecto_id, categoria, concepto, monto, fecha, registrado_por) VALUES (?, ?, ?, ?, ?, ?)",
                            (obra_id, categoria, concepto, monto, fecha_costo, user['nombre'])
                        )
                        conn.commit()
                        conn.close()
                        st.success("Gasto registrado correctamente.")
                        st.rerun()

        with col_form:
            st.subheader(f"{t['costos_history']}: {obra_sel}")
            costos_obra = get_costos_df(obra_id)
            if not costos_obra.empty:
                st.dataframe(costos_obra[['fecha', 'categoria', 'concepto', 'monto', 'registrado_por']], use_container_width=True)

# ==========================================
# 6. REQUISICIONES DE CAMPO
# ==========================================
elif menu_sel == t["nav_req"]:
    st.markdown(f"<div class='main-header'>{t['req_title']}</div>", unsafe_allow_html=True)
    
    proyectos_df = get_proyectos_df()
    if proyectos_df.empty:
        st.warning("Registra una obra o proyecto primero.")
    else:
        proyectos_dict = dict(zip(proyectos_df['nombre'], proyectos_dict.keys()))
        c_req1, c_req2 = st.columns([1, 1.2])

        with c_req1:
            obra_sel = st.selectbox(t["lbl_select_obra"], list(proyectos_dict.keys()), key="req_p_sel")
            obra_id = proyectos_dict[obra_sel]

            with st.form("form_req"):
                insumo = st.text_input(t["lbl_item"])
                col_cant, col_uni = st.columns(2)
                with col_cant:
                    cantidad = st.number_input(t["lbl_qty"], min_value=0.1, step=1.0)
                with col_uni:
                    unidad = st.text_input(t["lbl_unit"], value="Pza")
                prioridad = st.selectbox(t["lbl_priority"], ["Normal", "Urgente / Urgent", "Crítica / Critical"])

                if st.form_submit_button(t["btn_send_req"]):
                    if insumo:
                        conn = sqlite3.connect(DB_PATH)
                        c = conn.cursor()
                        c.execute(
                            "INSERT INTO requisiciones (proyecto_id, insumo, cantidad, unidad, prioridad, solicitado_por) VALUES (?, ?, ?, ?, ?, ?)",
                            (obra_id, insumo, cantidad, unidad, prioridad, user['nombre'])
                        )
                        conn.commit()
                        conn.close()
                        st.success("Requisición enviada.")
                        st.rerun()

        with c_req2:
            conn = sqlite3.connect(DB_PATH)
            req_df = pd.read_sql_query("SELECT r.*, p.nombre as proyecto FROM requisiciones r JOIN proyectos p ON r.proyecto_id = p.id WHERE r.proyecto_id = ?", conn, params=(obra_id,))
            conn.close()
            if not req_df.empty:
                st.dataframe(req_df[['fecha', 'insumo', 'cantidad', 'unidad', 'prioridad', 'solicitado_por', 'estatus']], use_container_width=True)

# ==========================================
# 7. USUARIOS MAESTROS
# ==========================================
elif menu_sel == t["nav_users"]:
    st.markdown(f"<div class='main-header'>{t['users_title']}</div>", unsafe_allow_html=True)
    
    conn = sqlite3.connect(DB_PATH)
    users_df = pd.read_sql_query("SELECT id, username, nombre_completo, rol FROM usuarios", conn)
    conn.close()

    st.dataframe(users_df, use_container_width=True)

    st.markdown("---")
    with st.form("form_user"):
        new_username = st.text_input(t["user_label"], key="new_u")
        new_password = st.text_input(t["pass_label"], type="password", key="new_p")
        new_nombre = st.text_input(t["lbl_fullname"])

        if st.form_submit_button(t["btn_create_user"]):
            if new_username and new_password and new_nombre:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                try:
                    c.execute(
                        "INSERT INTO usuarios (username, password, nombre_completo, rol) VALUES (?, ?, ?, ?)",
                        (new_username, make_hashes(new_password), new_nombre, "Usuario Maestro")
                    )
                    conn.commit()
                    st.success("Usuario creado con éxito.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    conn.close()
