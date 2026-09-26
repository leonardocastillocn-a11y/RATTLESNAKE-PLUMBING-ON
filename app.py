import hashlib
import json
import os
import secrets
import sqlite3
import urllib.parse
import urllib.request
from datetime import datetime, date

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
import streamlit as st

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="Rattlesnake System",
    page_icon="🐍",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = "database/erp_local.db"

# ==========================================
# ESTILOS CSS (TEMA CLARO / LIGHT MODE)
# ==========================================
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }
        
        .stApp {
            background-color: #F8FAFC;
            color: #0F172A;
        }
        
        section[data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            border-right: 1px solid #E2E8F0;
        }
        
        section[data-testid="stSidebar"] * {
            color: #1E293B !important;
        }
        
        section[data-testid="stSidebar"] div[role="radiogroup"] label {
            padding: 8px 12px;
            border-radius: 6px;
            transition: background 0.2s;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
            background-color: #F1F5F9 !important;
        }
        
        .main-header {
            font-size: 28px;
            font-weight: 800;
            color: #0F172A;
            letter-spacing: -0.5px;
            margin-bottom: 20px;
        }
        
        .brand-header {
            font-size: 22px;
            font-weight: 800;
            color: #0284C7 !important;
            margin-bottom: 0px;
        }

        .kpi-card {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            padding: 16px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        
        .stButton>button {
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.2s ease-in-out;
            background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%);
            color: white !important;
            border: none;
            padding: 8px 16px;
        }
        
        .stButton>button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.25);
        }
        
        div[data-testid="stMetricValue"] {
            font-size: 26px !important;
            font-weight: 700 !important;
            color: #0284C7 !important;
        }
        div[data-testid="stMetricLabel"] {
            color: #475569 !important;
        }
    </style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# DICCIONARIO BILINGÜE (i18n)
# ==========================================
TEXTS = {
    "ES": {
        "app_title": "Rattlesnake System",
        "app_subtitle": "Gestión Ejecutiva & Control de Obra",
        "login_title": "Acceso al Sistema",
        "user_label": "Usuario Maestro",
        "pass_label": "Contraseña",
        "btn_login": "Ingresar al Sistema",
        "err_login": "Usuario o contraseña incorrectos.",
        "demo_info": "🔑 Acceso Maestro Inicial:",
        "nav_title": "MENÚ PRINCIPAL",
        "nav_director": "🎯 Tablero Operativo Director",
        "nav_balance": "📊 Balance Financiero",
        "nav_obras": "🏗️ Obras & Ubicaciones",
        "nav_workers": "👷 Personal & Trabajadores",
        "nav_costos": "💰 Registro de Costos",
        "nav_cxp": "💳 Cuentas por Pagar (CxP)",
        "nav_req": "📋 Requisiciones de Campo",
        "nav_users": "👑 Usuarios Maestros",
        "btn_logout": "Cerrar Sesión",
        "lang_selector": "🌐 Idioma / Language",
        "dir_title": "🎯 Tablero Operativo Directivo - Resumen Ejecutivo",
        "dir_kpi_total_proj": "Proyectos Activos",
        "dir_kpi_goal_prog": "Meta Avance Físico Promedio",
        "dir_kpi_real_prog": "Avance Físico Real Promedio",
        "dir_kpi_efficiency": "Eficiencia Presupuestal Global",
        "dir_status_summary": "Estatus Operativo de Proyectos",
        "dir_scurve_title": "Curva S Acumulada de Ejecución Financiera",
        "dir_alerts_title": "⚠️ Alerta de Desvíos Presupuestales u Operativos",
        "bal_title": "📊 Dashboard Financiero & Rendimiento de Obra",
        "metric_budget": "Presupuesto Contratado",
        "metric_executed": "Costo Real Ejecutado",
        "metric_pending": "Cuentas por Pagar (CxP)",
        "metric_available": "Margen / Disponible",
        "chart_cat": "Desglose de Costos por Categoría",
        "chart_comp": "Presupuesto vs Costo Real por Proyecto",
        "obras_title": "🏗️ Gestión de Obras, Edición & Avance Físico",
        "tab_map": "🗺️ Mapa & Listado de Obras",
        "tab_new_obra": "➕ Registrar Nueva Obra",
        "tab_edit_obra": "✏️ Editar Obra & Avance Físico",
        "tab_del_obra": "🗑️ Eliminar Obra",
        "lbl_code": "Código de Obra",
        "lbl_name": "Nombre de la Obra / Proyecto",
        "lbl_client": "Cliente / Empresa",
        "lbl_calle": "Calle y Número",
        "lbl_cp": "Código Postal (CP)",
        "lbl_city": "Ciudad / Municipio",
        "lbl_state": "Estado",
        "lbl_budget": "Presupuesto Contratado ($)",
        "lbl_target_prog": "Meta de Avance Esperado (%)",
        "lbl_real_prog": "Avance Real Actual (%)",
        "lbl_lat": "Latitud GPS (Opcional)",
        "lbl_lon": "Longitud GPS (Opcional)",
        "btn_save_obra": "Guardar Proyecto",
        "msg_obra_success": "Obra guardada exitosamente.",
        "workers_title": "👷 Control de Personal & Asignación a Obras",
        "tab_workers_list": "📌 Lista & Asignación de Personal",
        "tab_new_worker": "➕ Registrar Nuevo Trabajador",
        "lbl_worker_name": "Nombre Completo del Trabajador",
        "lbl_position": "Puesto / Especialidad (ej. Albañil, Plomero, Residente)",
        "lbl_phone": "Teléfono de Contacto",
        "lbl_assign_obra": "Asignar a Obra",
        "btn_save_worker": "Registrar Trabajador",
        "msg_worker_success": "Trabajador registrado exitosamente.",
        "costos_title": "💰 Captura & Control Metódico de Costos",
        "lbl_select_obra": "Seleccionar Obra",
        "lbl_cat": "Categoría de Costo",
        "lbl_concept": "Concepto / Descripción del Gasto",
        "lbl_amount": "Monto Total ($)",
        "lbl_date": "Fecha del Gasto",
        "lbl_obs": "Notas / Referencia de Factura",
        "btn_save_costo": "Registrar Costo",
        "msg_costo_success": "Costo registrado exitosamente.",
        "costos_history": "Historial de Costos Registrados",
        "cxp_title": "💳 Cuentas por Pagar & Compromisos Financieros",
        "tab_active_cxp": "📌 Cuentas Pendientes",
        "tab_new_cxp": "➕ Nueva Cuenta por Pagar",
        "lbl_provider": "Proveedor / Subcontratista",
        "lbl_due": "Fecha Límite de Pago",
        "btn_save_cxp": "Crear Cuenta por Pagar",
        "msg_cxp_success": "Cuenta por pagar registrada exitosamente.",
        "btn_pay": "Aplicar Pago / Abono",
        "lbl_cxp_id": "ID Cuenta por Pagar",
        "lbl_pay_amount": "Monto a Abonar ($)",
        "msg_pay_success": "Abono/Pago aplicado correctamente y reflejado en costos.",
        "req_title": "📋 Requisiciones de Insumos & Materiales de Campo",
        "tab_active_req": "📌 Requisiciones Solicitadas",
        "tab_new_req": "➕ Nueva Requisición",
        "lbl_item": "Insumo / Material Requerido",
        "lbl_qty": "Cantidad",
        "lbl_unit": "Unidad",
        "lbl_priority": "Prioridad",
        "btn_send_req": "Enviar Requisición",
        "msg_req_success": "Requisición enviada con éxito.",
        "users_title": "👑 Control & Alta de Usuarios Maestros",
        "lbl_new_username": "Nombre de Usuario (Login)",
        "lbl_new_password": "Contraseña",
        "lbl_fullname": "Nombre Completo",
        "btn_create_user": "Dar de Alta Usuario Maestro",
        "msg_user_success": "Usuario Maestro creado con éxito.",
        "users_list": "Usuarios Registrados en el Sistema",
    },
    "EN": {
        "app_title": "Rattlesnake System",
        "app_subtitle": "Executive Management & Site Control",
        "login_title": "System Access",
        "user_label": "Master User",
        "pass_label": "Password",
        "btn_login": "Sign In",
        "err_login": "Invalid username or password.",
        "demo_info": "🔑 Initial Master Access:",
        "nav_title": "MAIN MENU",
        "nav_director": "🎯 Director Operational Dashboard",
        "nav_balance": "📊 Financial Balance",
        "nav_obras": "🏗️ Projects & Locations",
        "nav_workers": "👷 Personnel & Workers",
        "nav_costos": "💰 Cost Tracking",
        "nav_cxp": "💳 Accounts Payable",
        "nav_req": "📋 Field Requisitions",
        "nav_users": "👑 Master Users",
        "btn_logout": "Sign Out",
        "lang_selector": "🌐 Language / Idioma",
        "dir_title": "🎯 Director Operational Dashboard - Executive Overview",
        "dir_kpi_total_proj": "Active Projects",
        "dir_kpi_goal_prog": "Target Physical Progress Avg",
        "dir_kpi_real_prog": "Actual Physical Progress Avg",
        "dir_kpi_efficiency": "Overall Budget Efficiency",
        "dir_status_summary": "Project Operational Status",
        "dir_scurve_title": "S-Curve Cumulative Financial Execution",
        "dir_alerts_title": "⚠️ Budget & Operational Variance Alerts",
        "bal_title": "📊 Financial Dashboard & Site Performance",
        "metric_budget": "Contracted Budget",
        "metric_executed": "Actual Cost Executed",
        "metric_pending": "Accounts Payable (AP)",
        "metric_available": "Margin / Available",
        "chart_cat": "Cost Breakdown by Category",
        "chart_comp": "Budget vs Actual Cost per Project",
        "obras_title": "🏗️ Project Management, Editing & Progress",
        "tab_map": "MAP & Project List",
        "tab_new_obra": "➕ Register New Project",
        "tab_edit_obra": "✏️ Edit Project & Progress",
        "tab_del_obra": "🗑️ Delete Project",
        "lbl_code": "Project Code",
        "lbl_name": "Project Name",
        "lbl_client": "Client / Company",
        "lbl_calle": "Street & Number",
        "lbl_cp": "Zip Code",
        "lbl_city": "City",
        "lbl_state": "State",
        "lbl_budget": "Contracted Budget ($)",
        "lbl_target_prog": "Target Expected Progress (%)",
        "lbl_real_prog": "Actual Current Progress (%)",
        "lbl_lat": "GPS Latitude (Optional)",
        "lbl_lon": "GPS Longitude (Optional)",
        "btn_save_obra": "Save Project",
        "msg_obra_success": "Project saved successfully.",
        "workers_title": "👷 Personnel Control & Site Assignment",
        "tab_workers_list": "📌 Staff List & Assignment",
        "tab_new_worker": "➕ Register New Worker",
        "lbl_worker_name": "Worker Full Name",
        "lbl_position": "Role / Specialty (e.g. Mason, Plumber, Supervisor)",
        "lbl_phone": "Phone Number",
        "lbl_assign_obra": "Assign to Site",
        "btn_save_worker": "Register Worker",
        "msg_worker_success": "Worker registered successfully.",
        "costos_title": "💰 Systematic Cost Tracking",
        "lbl_select_obra": "Select Project",
        "lbl_cat": "Cost Category",
        "lbl_concept": "Concept / Expense Description",
        "lbl_amount": "Total Amount ($)",
        "lbl_date": "Expense Date",
        "lbl_obs": "Notes / Invoice Ref",
        "btn_save_costo": "Register Expense",
        "msg_costo_success": "Expense registered successfully.",
        "costos_history": "Expense Log History",
        "cxp_title": "💳 Accounts Payable & Financial Commitments",
        "tab_active_cxp": "📌 Pending Accounts",
        "tab_new_cxp": "➕ New Payable Account",
        "lbl_provider": "Vendor / Subcontractor",
        "lbl_due": "Due Date",
        "btn_save_cxp": "Create Payable Account",
        "msg_cxp_success": "Payable account created successfully.",
        "btn_pay": "Apply Payment / Partial",
        "lbl_cxp_id": "AP Account ID",
        "lbl_pay_amount": "Amount to Pay ($)",
        "msg_pay_success": "Payment applied successfully and recorded under expenses.",
        "req_title": "📋 Field Materials & Supply Requisitions",
        "tab_active_req": "📌 Active Requisitions",
        "tab_new_req": "➕ New Requisition",
        "lbl_item": "Material / Supply Needed",
        "lbl_qty": "Quantity",
        "lbl_unit": "Unit",
        "lbl_priority": "Priority Level",
        "btn_send_req": "Submit Requisition",
        "msg_req_success": "Requisition submitted successfully.",
        "users_title": "👑 Master User Access Control",
        "lbl_new_username": "Username",
        "lbl_new_password": "Password",
        "lbl_fullname": "Full Name",
        "btn_create_user": "Register Master User",
        "msg_user_success": "Master User registered successfully.",
        "users_list": "Registered System Users",
    },
}

# ==========================================
# GEOCODIFICACIÓN (DIRECCIÓN -> GPS LAT/LON)
# ==========================================
def geocode_address(calle, cp, ciudad, estado):
    partes = [p.strip() for p in [calle, cp, ciudad, estado] if p and p.strip()]
    direccion_completa = ", ".join(partes)

    if not direccion_completa:
        return None, None
    try:
        encoded = urllib.parse.quote(direccion_completa)
        url = f"https://nominatim.openstreetmap.org/search?q={encoded}&format=json&limit=1"
        req = urllib.request.Request(
            url, headers={"User-Agent": "RattlesnakeERP/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass
    return None, None

# ==========================================
# BASE DE DATOS & SEGURIDAD
# ==========================================
def make_hashes(password, salt=None):
    if not salt:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
    )
    return f"{salt}${key.hex()}"

def check_hashes(password, hashed_text):
    try:
        if "$" not in hashed_text:
            return hashlib.sha256(password.encode()).hexdigest() == hashed_text
        salt, _ = hashed_text.split("$")
        return make_hashes(password, salt) == hashed_text
    except Exception:
        return False

def ensure_columns(cursor, table_name, columns_dict):
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_cols = [col[1] for col in cursor.fetchall()]
    for col_name, col_def in columns_dict.items():
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_def}")

def init_db():
    os.makedirs("database", exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()

        # 1. Usuarios
        c.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                nombre_completo TEXT NOT NULL,
                rol TEXT DEFAULT 'Usuario Maestro'
            )
        """)
        ensure_columns(
            c,
            "usuarios",
            {
                "username": "TEXT DEFAULT ''",
                "password": "TEXT DEFAULT ''",
                "nombre_completo": "TEXT DEFAULT ''",
                "rol": "TEXT DEFAULT 'Usuario Maestro'",
            },
        )

        c.execute("SELECT * FROM usuarios WHERE username = 'admin'")
        if not c.fetchone():
            c.execute(
                "INSERT INTO usuarios (username, password, nombre_completo, rol) VALUES (?, ?, ?, ?)",
                ("admin", make_hashes("admin123"), "Usuario Maestro", "Usuario Maestro"),
            )
        else:
            c.execute(
                "UPDATE usuarios SET password = ? WHERE username = 'admin'",
                (make_hashes("admin123"),),
            )

        # 2. Proyectos
        c.execute("""
            CREATE TABLE IF NOT EXISTS proyectos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                cliente TEXT DEFAULT '',
                calle TEXT DEFAULT '',
                codigo_postal TEXT DEFAULT '',
                ciudad TEXT DEFAULT '',
                estado_provincia TEXT DEFAULT '',
                presupuesto_total REAL DEFAULT 0.0,
                avance_meta REAL DEFAULT 0.0,
                avance_real REAL DEFAULT 0.0,
                latitud REAL DEFAULT 0.0,
                longitud REAL DEFAULT 0.0,
                estado TEXT DEFAULT 'En Proceso',
                fecha_inicio DATE DEFAULT CURRENT_DATE
            )
        """)
        ensure_columns(
            c,
            "proyectos",
            {
                "codigo": "TEXT DEFAULT ''",
                "nombre": "TEXT DEFAULT ''",
                "cliente": "TEXT DEFAULT ''",
                "calle": "TEXT DEFAULT ''",
                "codigo_postal": "TEXT DEFAULT ''",
                "ciudad": "TEXT DEFAULT ''",
                "estado_provincia": "TEXT DEFAULT ''",
                "presupuesto_total": "REAL DEFAULT 0.0",
                "avance_meta": "REAL DEFAULT 0.0",
                "avance_real": "REAL DEFAULT 0.0",
                "latitud": "REAL DEFAULT 0.0",
                "longitud": "REAL DEFAULT 0.0",
                "estado": "TEXT DEFAULT 'En Proceso'",
                "fecha_inicio": "DATE DEFAULT CURRENT_DATE",
            },
        )

        # 3. Trabajadores
        c.execute("""
            CREATE TABLE IF NOT EXISTS trabajadores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_completo TEXT NOT NULL,
                puesto TEXT NOT NULL,
                telefono TEXT,
                proyecto_id INTEGER,
                estatus TEXT DEFAULT 'Activo',
                fecha_registro DATE DEFAULT CURRENT_DATE,
                FOREIGN KEY (proyecto_id) REFERENCES proyectos (id)
            )
        """)
        ensure_columns(
            c,
            "trabajadores",
            {
                "nombre_completo": "TEXT DEFAULT ''",
                "puesto": "TEXT DEFAULT ''",
                "telefono": "TEXT DEFAULT ''",
                "proyecto_id": "INTEGER",
                "estatus": "TEXT DEFAULT 'Activo'",
                "fecha_registro": "DATE DEFAULT CURRENT_DATE",
            },
        )

        # 4. Costos
        c.execute("""
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
        """)
        ensure_columns(
            c,
            "costos",
            {
                "proyecto_id": "INTEGER",
                "categoria": "TEXT DEFAULT ''",
                "concepto": "TEXT DEFAULT ''",
                "monto": "REAL DEFAULT 0.0",
                "fecha": "DATE DEFAULT CURRENT_DATE",
                "registrado_por": "TEXT DEFAULT ''",
                "observaciones": "TEXT DEFAULT ''",
            },
        )

        # 5. Cuentas por pagar
        c.execute("""
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
        """)
        ensure_columns(
            c,
            "cuentas_por_pagar",
            {
                "proyecto_id": "INTEGER",
                "proveedor": "TEXT DEFAULT ''",
                "concepto": "TEXT DEFAULT ''",
                "monto_total": "REAL DEFAULT 0.0",
                "monto_pagado": "REAL DEFAULT 0.0",
                "estatus": "TEXT DEFAULT 'Pendiente'",
                "fecha_vencimiento": "DATE",
                "registrado_por": "TEXT DEFAULT ''",
            },
        )

        # 6. Requisiciones
        c.execute("""
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
        """)
        ensure_columns(
            c,
            "requisiciones",
            {
                "proyecto_id": "INTEGER",
                "insumo": "TEXT DEFAULT ''",
                "cantidad": "REAL DEFAULT 0.0",
                "unidad": "TEXT DEFAULT ''",
                "prioridad": "TEXT DEFAULT 'Normal'",
                "solicitado_por": "TEXT DEFAULT ''",
                "estatus": "TEXT DEFAULT 'Pendiente'",
                "fecha": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            },
        )

        conn.commit()

init_db()

# ==========================================
# FUNCIONES DE CONSULTA A BASE DE DATOS
# ==========================================
@st.cache_data(ttl=60)
def get_proyectos_df():
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query("SELECT * FROM proyectos ORDER BY id DESC", conn)

@st.cache_data(ttl=60)
def get_trabajadores_df(proyecto_id=None):
    with sqlite3.connect(DB_PATH) as conn:
        if proyecto_id:
            return pd.read_sql_query(
                "SELECT t.*, p.nombre as proyecto FROM trabajadores t LEFT JOIN proyectos p ON t.proyecto_id = p.id WHERE t.proyecto_id = ? ORDER BY t.id DESC",
                conn, params=(proyecto_id,)
            )
        return pd.read_sql_query(
            "SELECT t.*, coalesce(p.nombre, 'Sin Asignar / Oficina') as proyecto FROM trabajadores t LEFT JOIN proyectos p ON t.proyecto_id = p.id ORDER BY t.id DESC",
            conn,
        )

@st.cache_data(ttl=60)
def get_costos_df(proyecto_id=None):
    with sqlite3.connect(DB_PATH) as conn:
        if proyecto_id:
            return pd.read_sql_query(
                "SELECT c.*, p.nombre as proyecto FROM costos c JOIN proyectos p ON c.proyecto_id = p.id WHERE c.proyecto_id = ? ORDER BY c.id DESC",
                conn, params=(proyecto_id,)
            )
        return pd.read_sql_query(
            "SELECT c.*, p.nombre as proyecto FROM costos c JOIN proyectos p ON c.proyecto_id = p.id ORDER BY c.id DESC",
            conn,
        )

@st.cache_data(ttl=60)
def get_cxp_df(proyecto_id=None):
    with sqlite3.connect(DB_PATH) as conn:
        if proyecto_id:
            return pd.read_sql_query(
                "SELECT cxp.*, p.nombre as proyecto FROM cuentas_por_pagar cxp JOIN proyectos p ON cxp.proyecto_id = p.id WHERE cxp.proyecto_id = ? ORDER BY cxp.id DESC",
                conn, params=(proyecto_id,)
            )
        return pd.read_sql_query(
            "SELECT cxp.*, p.nombre as proyecto FROM cuentas_por_pagar cxp JOIN proyectos p ON cxp.proyecto_id = p.id ORDER BY cxp.id DESC",
            conn,
        )

@st.cache_data(ttl=60)
def get_requisiciones_df(proyecto_id=None):
    with sqlite3.connect(DB_PATH) as conn:
        if proyecto_id:
            return pd.read_sql_query(
                "SELECT r.*, p.nombre as proyecto FROM requisiciones r JOIN proyectos p ON r.proyecto_id = p.id WHERE r.proyecto_id = ? ORDER BY r.id DESC",
                conn, params=(proyecto_id,)
            )
        return pd.read_sql_query(
            "SELECT r.*, p.nombre as proyecto FROM requisiciones r JOIN proyectos p ON r.proyecto_id = p.id ORDER BY r.id DESC",
            conn,
        )

@st.cache_data(ttl=60)
def get_usuarios_df():
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query("SELECT id, username, nombre_completo, rol FROM usuarios ORDER BY id DESC", conn)

def clear_data_cache():
    st.cache_data.clear()

# ==========================================
# MANEJO DE SESIÓN
# ==========================================
if "lang" not in st.session_state:
    st.session_state["lang"] = "ES"

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_info"] = None

t = TEXTS[st.session_state["lang"]]

# ==========================================
# PANTALLA DE LOGIN
# ==========================================
if not st.session_state["logged_in"]:
    st.markdown(
        f"<h1 style='text-align: center; margin-top: 50px; color: #0F172A;'>🐍 {t['app_title']}</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='text-align: center; color: #64748B;'>{t['app_subtitle']}</p>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.subheader(t["login_title"])
        username = st.text_input(t["user_label"])
        password = st.text_input(t["pass_label"], type="password")

        if st.button(t["btn_login"], use_container_width=True):
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute("SELECT username, password, nombre_completo, rol FROM usuarios WHERE username = ?", (username,))
                data = c.fetchone()

            if data and check_hashes(password, data[1]):
                st.session_state["logged_in"] = True
                st.session_state["user_info"] = {
                    "username": data[0],
                    "nombre": data[2],
                    "rol": data[3],
                }
                st.rerun()
            else:
                st.error(t["err_login"])

        st.info(f"{t['demo_info']}\n- User: `admin`\n- Password: `admin123`")
    st.stop()

# ==========================================
# BARRA LATERAL (Navegación & Filtros Globales)
# ==========================================
user = st.session_state["user_info"]

st.sidebar.markdown(f"<h2 class='brand-header'>🐍 {t['app_title']}</h2>", unsafe_allow_html=True)
st.sidebar.caption(f"{t['app_subtitle']}")
st.sidebar.markdown("---")

opciones_menu = [
    t["nav_director"],
    t["nav_balance"],
    t["nav_obras"],
    t["nav_workers"],
    t["nav_costos"],
    t["nav_cxp"],
    t["nav_req"],
    t["nav_users"],
]

menu_sel = st.sidebar.radio(t["nav_title"], opciones_menu)

st.sidebar.markdown("---")

# FILTRO GLOBAL POR OBRA EN LA SIDEBAR
all_proyectos_df = get_proyectos_df()
proyectos_dict_global = dict(zip(all_proyectos_df['nombre'], all_proyectos_df['id'])) if not all_proyectos_df.empty else {}

st.sidebar.markdown("### 🎯 Filtro Global de Obra")
global_obra_sel = st.sidebar.selectbox(
    "Seleccionar Obra para Filtrar Todo:",
    ["Todas las Obras"] + list(proyectos_dict_global.keys()),
    key="global_obra_filter"
)

st.sidebar.markdown("---")

lang_choice = st.sidebar.selectbox(
    t["lang_selector"],
    ["Español (ES)", "English (EN)"],
    index=0 if st.session_state["lang"] == "ES" else 1,
)
new_lang = "ES" if "Español" in lang_choice else "EN"

if new_lang != st.session_state["lang"]:
    st.session_state["lang"] = new_lang
    st.rerun()

st.sidebar.markdown(f"👤 **{user['nombre']}** \n<small style='color:#64748B;'>👑 {user['rol']}</small>", unsafe_allow_html=True)

if st.sidebar.button(t["btn_logout"], use_container_width=True):
    st.session_state["logged_in"] = False
    st.session_state["user_info"] = None
    st.rerun()

# ==========================================
# 0. TABLERO OPERATIVO DIRECTOR
# ==========================================
if menu_sel == t["nav_director"]:
    st.markdown(f"<div class='main-header'>{t['dir_title']}</div>", unsafe_allow_html=True)

    proyectos_df = get_proyectos_df()
    
    # Aplicar filtro global si no es 'Todas las Obras'
    if global_obra_sel != "Todas las Obras":
        proyectos_df = proyectos_df[proyectos_df['nombre'] == global_obra_sel]
        selected_p_id = proyectos_dict_global.get(global_obra_sel)
        costos_df = get_costos_df(selected_p_id)
    else:
        costos_df = get_costos_df()

    if proyectos_df.empty:
        st.info("No hay obras que coincidan con los criterios de filtrado seleccionados.")
    else:
        total_proyectos = len(proyectos_df)
        meta_promedio = proyectos_df["avance_meta"].mean()
        real_promedio = proyectos_df["avance_real"].mean()

        presupuesto_global = proyectos_df["presupuesto_total"].sum()
        costo_global = costos_df["monto"].sum() if not costos_df.empty else 0.0

        eficiencia_presupuestal = (
            ((presupuesto_global - costo_global) / presupuesto_global * 100)
            if presupuesto_global > 0 else 100.0
        )

        k1, k2, k3, k4 = st.columns(4)
        k1.metric(t["dir_kpi_total_proj"], f"{total_proyectos}")
        k2.metric(t["dir_kpi_goal_prog"], f"{meta_promedio:.1f}%")
        k3.metric(t["dir_kpi_real_prog"], f"{real_promedio:.1f}%", delta=f"{real_promedio - meta_promedio:.1f}%")
        k4.metric(
            t["dir_kpi_efficiency"],
            f"{eficiencia_presupuestal:.1f}%",
            delta="En Presupuesto" if eficiencia_presupuestal >= 0 else "Sobrecosto",
            delta_color="normal" if eficiencia_presupuestal >= 0 else "inverse",
        )

        st.markdown("---")

        col_dir1, col_dir2 = st.columns([1.3, 1])

        with col_dir1:
            st.subheader(t["dir_scurve_title"])

            if not costos_df.empty:
                costos_df["fecha_dt"] = pd.to_datetime(costos_df["fecha"])
                costos_df["periodo"] = costos_df["fecha_dt"].dt.to_period("M").astype(str)
                df_acum = costos_df.groupby("periodo")["monto"].sum().reset_index()
                df_acum["acumulado"] = df_acum["monto"].cumsum()
                df_acum["pct_ejecutado"] = (
                    (df_acum["acumulado"] / presupuesto_global * 100)
                    if presupuesto_global > 0 else 0
                )

                fig_curva = go.Figure()
                fig_curva.add_trace(go.Scatter(
                    x=df_acum["periodo"],
                    y=df_acum["pct_ejecutado"],
                    mode="lines+markers",
                    name="Gasto Real Acumulado (%)",
                    line=dict(color="#0284C7", width=3),
                ))
                fig_curva.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#0F172A",
                    yaxis=dict(title="% Presupuesto Ejecutado", range=[0, max(105, df_acum["pct_ejecutado"].max() + 5)], gridcolor="#E2E8F0"),
                    xaxis=dict(gridcolor="#E2E8F0"),
                    margin=dict(l=20, r=20, t=30, b=20),
                )
                st.plotly_chart(fig_curva, use_container_width=True)
            else:
                st.info("Sin suficientes datos históricos de costos para generar la curva acumulada.")

        with col_dir2:
            st.subheader(t["dir_status_summary"])
            df_status = proyectos_df.copy()
            costo_por_obra = (
                costos_df.groupby("proyecto_id")["monto"].sum().reset_index()
                if not costos_df.empty
                else pd.DataFrame(columns=["proyecto_id", "monto"])
            )
            df_status = df_status.merge(costo_por_obra, left_on="id", right_on="proyecto_id", how="left").fillna({"monto": 0})

            df_status["Semaforo"] = np.where(df_status["avance_real"] >= df_status["avance_meta"], "🟢 En Tiempo", "🔴 Con Retraso")
            df_status["Consumido ($)"] = df_status["monto"]

            st.dataframe(
                df_status[["nombre", "avance_meta", "avance_real", "Semaforo", "presupuesto_total", "Consumido ($)"]],
                column_config={
                    "nombre": "Obra",
                    "avance_meta": st.column_config.NumberColumn("Meta %", format="%.1f%%"),
                    "avance_real": st.column_config.NumberColumn("Real %", format="%.1f%%"),
                    "presupuesto_total": st.column_config.NumberColumn("Presupuesto", format="$%,.2f"),
                    "Consumido ($)": st.column_config.NumberColumn("Gasto Real", format="$%,.2f"),
                },
                use_container_width=True,
            )

        st.subheader(t["dir_alerts_title"])
        alertas = []
        for _, row in df_status.iterrows():
            if row["avance_real"] < row["avance_meta"]:
                desvio = row["avance_meta"] - row["avance_real"]
                alertas.append(f"🚨 **{row['nombre']}**: Retraso en avance físico de **{desvio:.1f}%** respecto a la meta.")
            if row["Consumido ($)"] > row["presupuesto_total"]:
                exceso = row["Consumido ($)"] - row["presupuesto_total"]
                alertas.append(f"💸 **{row['nombre']}**: Presupuesto excedido por **${exceso:,.2f}**.")

        if alertas:
            for al in alertas:
                st.warning(al)
        else:
            st.success("✅ Todos los proyectos seleccionados avanzan conforme a metas y dentro del presupuesto programado.")

# ==========================================
# 1. BALANCE FINANCIERO
# ==========================================
elif menu_sel == t["nav_balance"]:
    st.markdown(f"<div class='main-header'>{t['bal_title']}</div>", unsafe_allow_html=True)

    proyectos_df = get_proyectos_df()
    
    if global_obra_sel != "Todas las Obras":
        proyectos_df = proyectos_df[proyectos_df['nombre'] == global_obra_sel]
        selected_p_id = proyectos_dict_global.get(global_obra_sel)
        costos_df = get_costos_df(selected_p_id)
        cxp_df = get_cxp_df(selected_p_id)
    else:
        costos_df = get_costos_df()
        cxp_df = get_cxp_df()

    if proyectos_df.empty:
        st.info("Sin proyectos registrados aún en la base de datos o que coincidan con la búsqueda.")
    else:
        presupuesto_total = proyectos_df["presupuesto_total"].sum()
        costo_total_ejecutado = costos_df["monto"].sum() if not costos_df.empty else 0
        pagos_pendientes_total = (
            (cxp_df["monto_total"] - cxp_df["monto_pagado"]).sum() if not cxp_df.empty else 0
        )
        balance_disponible = presupuesto_total - costo_total_ejecutado

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(t["metric_budget"], f"${presupuesto_total:,.2f}")
        c2.metric(
            t["metric_executed"],
            f"${costo_total_ejecutado:,.2f}",
            delta=f"-{(costo_total_ejecutado/presupuesto_total*100) if presupuesto_total>0 else 0:.1f}%",
            delta_color="inverse",
        )
        c3.metric(t["metric_pending"], f"${pagos_pendientes_total:,.2f}")
        c4.metric(
            t["metric_available"],
            f"${balance_disponible:,.2f}",
            delta=f"{(balance_disponible/presupuesto_total*100) if presupuesto_total>0 else 0:.1f}%",
        )

        st.markdown("---")

        col_graf1, col_graf2 = st.columns(2)

        with col_graf1:
            st.subheader(t["chart_cat"])
            if not costos_df.empty:
                fig_cat = px.pie(
                    costos_df,
                    names="categoria",
                    values="monto",
                    hole=0.45,
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                )
                fig_cat.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#0F172A", margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig_cat, use_container_width=True)
            else:
                st.info("No hay gastos registrados para graficar.")

        with col_graf2:
            st.subheader(t["chart_comp"])
            if not costos_df.empty:
                costo_por_obra = costos_df.groupby("proyecto_id")["monto"].sum().reset_index()
                df_comp = proyectos_df.merge(costo_por_obra, left_on="id", right_on="proyecto_id", how="left").fillna(0)

                fig_bar = go.Figure(data=[
                    go.Bar(name="Presupuesto", x=df_comp["nombre"], y=df_comp["presupuesto_total"], marker_color="#0284C7"),
                    go.Bar(name="Ejecutado", x=df_comp["nombre"], y=df_comp["monto"], marker_color="#EF4444"),
                ])
                fig_bar.update_layout(
                    barmode="group",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#0F172A",
                    yaxis=dict(gridcolor="#E2E8F0"),
                    margin=dict(l=20, r=20, t=30, b=20),
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("Sin datos comparativos de obra.")

# ==========================================
# 2. OBRAS, MAPA, EDICIÓN & AVANCES
# ==========================================
elif menu_sel == t["nav_obras"]:
    st.markdown(f"<div class='main-header'>{t['obras_title']}</div>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        t["tab_map"],
        t["tab_new_obra"],
        t["tab_edit_obra"],
        t["tab_del_obra"],
    ])

    with tab1:
        st.subheader("🔍 Filtros de Obras")
        f_col1, f_col2 = st.columns([1, 2])
        with f_col1:
            filtro_estatus_obra = st.multiselect(
                "Filtrar por Estatus:",
                ["En Proceso", "Pausado", "Concluido", "Cancelado"],
                default=["En Proceso", "Pausado", "Concluido"]
            )
        with f_col2:
            buscar_obra = st.text_input("🔎 Buscar Obra por Nombre, Cliente o Código:", "")

        df_obras = get_proyectos_df()
        
        if not df_obras.empty:
            # Aplicar filtros locales de la pestaña
            if filtro_estatus_obra:
                df_obras = df_obras[df_obras['estado'].isin(filtro_estatus_obra)]
            if buscar_obra:
                search_term = buscar_obra.lower()
                df_obras = df_obras[
                    df_obras['nombre'].str.lower().str.contains(search_term) |
                    df_obras['cliente'].str.lower().str.contains(search_term) |
                    df_obras['codigo'].str.lower().str.contains(search_term)
                ]

            df_mapa = df_obras.dropna(subset=["latitud", "longitud"]).copy()
            df_mapa = df_mapa[(df_mapa["latitud"] != 0.0) & (df_mapa["longitud"] != 0.0)]

            if not df_mapa.empty:
                st.pydeck_chart(
                    pdk.Deck(
                        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
                        initial_view_state=pdk.ViewState(
                            latitude=df_mapa["latitud"].mean(),
                            longitude=df_mapa["longitud"].mean(),
                            zoom=10,
                            pitch=30,
                        ),
                        layers=[
                            pdk.Layer(
                                "ScatterplotLayer",
                                data=df_mapa,
                                get_position="[longitud, latitud]",
                                get_color="[2, 132, 199, 230]",
                                get_radius=400,
                                pickable=True,
                                auto_highlight=True,
                            ),
                        ],
                        tooltip={
                            "html": (
                                "<b>🏗️ Obra:</b> {nombre}<br/><b>👤 Cliente:</b> {cliente}<br/><b>📍 Dirección:</b> {calle}, CP {codigo_postal}, {ciudad}, {estado_provincia}<br/><b>💰 Presupuesto:</b> ${presupuesto_total}<br/><b>📊 Avance Real:</b> {avance_real}%"
                            ),
                            "style": {"backgroundColor": "#0F172A", "color": "white", "fontSize": "13px", "borderRadius": "6px"},
                        },
                    )
                )
            else:
                st.info("📍 No se encontraron coordenadas GPS válidas para las obras filtradas.")

            st.markdown("---")
            st.dataframe(
                df_obras[["codigo", "nombre", "cliente", "calle", "codigo_postal", "ciudad", "estado_provincia", "presupuesto_total", "avance_meta", "avance_real", "estado"]],
                column_config={
                    "presupuesto_total": st.column_config.NumberColumn("Presupuesto", format="$%,.2f"),
                    "avance_meta": st.column_config.NumberColumn("Meta %", format="%.1f%%"),
                    "avance_real": st.column_config.NumberColumn("Real %", format="%.1f%%"),
                },
                use_container_width=True,
            )
        else:
            st.info("No hay proyectos registrados que coincidan con la búsqueda.")

    with tab2:
        with st.form("form_nueva_obra"):
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                codigo = st.text_input(t["lbl_code"])
                nombre = st.text_input(t["lbl_name"])
                cliente = st.text_input(t["lbl_client"])
                presupuesto = st.number_input(t["lbl_budget"], min_value=0.0, step=10000.0)

            with col_b2:
                calle = st.text_input(t["lbl_calle"])
                c_cp, c_city, c_st = st.columns(3)
                with c_cp:
                    cp = st.text_input(t["lbl_cp"])
                with c_city:
                    ciudad = st.text_input(t["lbl_city"])
                with c_st:
                    estado_prov = st.text_input(t["lbl_state"])

            c_meta, c_real = st.columns(2)
            with c_meta:
                avance_meta = st.number_input(t["lbl_target_prog"], min_value=0.0, max_value=100.0, value=0.0, step=5.0)
            with c_real:
                avance_real = st.number_input(t["lbl_real_prog"], min_value=0.0, max_value=100.0, value=0.0, step=5.0)

            c_lat, c_lon = st.columns(2)
            with c_lat:
                latitud_manual = st.number_input(t["lbl_lat"], format="%.6f", value=0.0)
            with c_lon:
                longitud_manual = st.number_input(t["lbl_lon"], format="%.6f", value=0.0)

            if st.form_submit_button(t["btn_save_obra"]):
                if codigo and nombre and cliente:
                    lat_final, lon_final = latitud_manual, longitud_manual

                    if lat_final == 0.0 and lon_final == 0.0:
                        lat_geo, lon_geo = geocode_address(calle, cp, ciudad, estado_prov)
                        if lat_geo and lon_geo:
                            lat_final, lon_final = lat_geo, lon_geo
                            st.info(f"📍 Coordenadas encontradas automáticamente: Lat {lat_final}, Lon {lon_final}")

                    try:
                        with sqlite3.connect(DB_PATH) as conn:
                            c = conn.cursor()
                            c.execute(
                                "INSERT INTO proyectos (codigo, nombre, cliente, calle, codigo_postal, ciudad, estado_provincia, presupuesto_total, avance_meta, avance_real, latitud, longitud) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (codigo, nombre, cliente, calle, cp, ciudad, estado_prov, presupuesto, avance_meta, avance_real, lat_final, lon_final),
                            )
                            conn.commit()
                        clear_data_cache()
                        st.success(t["msg_obra_success"])
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    with tab3:
        st.subheader("✏️ Editar Datos de Obra & Actualizar Avance Físico")
        df_obras_edit = get_proyectos_df()

        if not df_obras_edit.empty:
            proyectos_dict_edit = dict(zip(df_obras_edit["nombre"] + " (" + df_obras_edit["cliente"] + ")", df_obras_edit["id"]))
            obra_sel_edit = st.selectbox("Seleccionar Proyecto a Editar", list(proyectos_dict_edit.keys()))
            id_edit = proyectos_dict_edit[obra_sel_edit]
            row_edit = df_obras_edit[df_obras_edit["id"] == id_edit].iloc[0]

            with st.form("form_editar_obra"):
                c_e1, c_e2 = st.columns(2)
                with c_e1:
                    e_nombre = st.text_input("Nombre de la Obra", value=str(row_edit["nombre"]))
                    e_cliente = st.text_input("Cliente", value=str(row_edit["cliente"]))
                    e_presupuesto = st.number_input("Presupuesto Contratado ($)", value=float(row_edit["presupuesto_total"]), step=10000.0)
                    e_estado = st.selectbox(
                        "Estatus de Obra",
                        ["En Proceso", "Pausado", "Concluido", "Cancelado"],
                        index=["En Proceso", "Pausado", "Concluido", "Cancelado"].index(row_edit["estado"]) if row_edit["estado"] in ["En Proceso", "Pausado", "Concluido", "Cancelado"] else 0,
                    )

                with c_e2:
                    e_calle = st.text_input("Calle y Número", value=str(row_edit["calle"]))
                    e_cp = st.text_input("Código Postal", value=str(row_edit["codigo_postal"]))
                    e_ciudad = st.text_input("Ciudad", value=str(row_edit["ciudad"]))
                    e_estado_prov = st.text_input("Estado", value=str(row_edit["estado_provincia"]))

                st.markdown("---")
                st.markdown("### 📊 Actualizar Avance Físico (%)")
                c_av1, c_av2 = st.columns(2)
                with c_av1:
                    e_avance_meta = st.number_input("Meta Avance Físico (%)", min_value=0.0, max_value=100.0, value=float(row_edit["avance_meta"]), step=1.0)
                with c_av2:
                    e_avance_real = st.number_input("Avance Físico Real Actual (%)", min_value=0.0, max_value=100.0, value=float(row_edit["avance_real"]), step=1.0)

                if st.form_submit_button("💾 Guardar Cambios"):
                    lat_edit, lon_edit = float(row_edit["latitud"]), float(row_edit["longitud"])
                    if e_calle != row_edit["calle"] or e_ciudad != row_edit["ciudad"] or e_estado_prov != row_edit["estado_provincia"] or (lat_edit == 0.0 and lon_edit == 0.0):
                        new_lat, new_lon = geocode_address(e_calle, e_cp, e_ciudad, e_estado_prov)
                        if new_lat and new_lon:
                            lat_edit, lon_edit = new_lat, new_lon

                    with sqlite3.connect(DB_PATH) as conn:
                        c = conn.cursor()
                        c.execute(
                            "UPDATE proyectos SET nombre = ?, cliente = ?, calle = ?, codigo_postal = ?, ciudad = ?, estado_provincia = ?, presupuesto_total = ?, avance_meta = ?, avance_real = ?, estado = ?, latitud = ?, longitud = ? WHERE id = ?",
                            (e_nombre, e_cliente, e_calle, e_cp, e_ciudad, e_estado_prov, e_presupuesto, e_avance_meta, e_avance_real, e_estado, lat_edit, lon_edit, id_edit),
                        )
                        conn.commit()
                    clear_data_cache()
                    st.success("✅ ¡Obra y avances actualizados correctamente!")
                    st.rerun()
        else:
            st.info("No hay proyectos registrados para editar.")

    with tab4:
        st.subheader("🗑️ Eliminar Obra")
        df_obras_del = get_proyectos_df()

        if not df_obras_del.empty:
            proyectos_dict_del = dict(zip(df_obras_del["nombre"] + " (" + df_obras_del["cliente"] + ")", df_obras_del["id"]))
            obra_sel_del = st.selectbox("Seleccionar Proyecto a Borrar", list(proyectos_dict_del.keys()))
            id_borrar = proyectos_dict_del[obra_sel_del]

            st.error("⚠️ **ATENCIÓN**: Esta acción eliminará permanentemente la obra seleccionada y **todos sus registros asociados** (Trabajadores, Costos, CxP y Requisiciones).")

            if st.button("❌ Confirmar y Borrar Obra", type="primary"):
                try:
                    with sqlite3.connect(DB_PATH) as conn:
                        c = conn.cursor()
                        c.execute("UPDATE trabajadores SET proyecto_id = NULL WHERE proyecto_id = ?", (id_borrar,))
                        c.execute("DELETE FROM costos WHERE proyecto_id = ?", (id_borrar,))
                        c.execute("DELETE FROM cuentas_por_pagar WHERE proyecto_id = ?", (id_borrar,))
                        c.execute("DELETE FROM requisiciones WHERE proyecto_id = ?", (id_borrar,))
                        c.execute("DELETE FROM proyectos WHERE id = ?", (id_borrar,))
                        conn.commit()
                    clear_data_cache()
                    st.success("La obra se eliminó correctamente.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al eliminar la obra: {e}")
        else:
            st.info("No hay proyectos registrados para eliminar.")

# ==========================================
# 3. TRABAJADORES & PERSONAL POR OBRA
# ==========================================
elif menu_sel == t["nav_workers"]:
    st.markdown(f"<div class='main-header'>{t['workers_title']}</div>", unsafe_allow_html=True)

    proyectos_df = get_proyectos_df()
    proyectos_dict = dict(zip(proyectos_df["nombre"], proyectos_df["id"])) if not proyectos_df.empty else {}

    tab1, tab2 = st.tabs([t["tab_workers_list"], t["tab_new_worker"]])

    with tab1:
        st.subheader("🔍 Filtros de Personal")
        col_wf1, col_wf2, col_wf3 = st.columns([1, 1, 1.5])
        
        with col_wf1:
            filtro_obra_worker = st.selectbox(
                "Filtrar por Obra:",
                ["Todas las Obras"] + list(proyectos_dict.keys()),
                index=0 if global_obra_sel == "Todas las Obras" else (list(proyectos_dict.keys()).index(global_obra_sel) + 1 if global_obra_sel in proyectos_dict else 0)
            )
        with col_wf2:
            filtro_estatus_worker = st.selectbox("Estatus del Trabajador:", ["Todos", "Activo", "Inactivo"])
        with col_wf3:
            buscar_worker = st.text_input("🔎 Buscar Trabajador o Puesto:", "")

        trabajadores_df = get_trabajadores_df()

        if not trabajadores_df.empty:
            df_mostrar = trabajadores_df.copy()
            if filtro_obra_worker != "Todas las Obras":
                df_mostrar = df_mostrar[df_mostrar["proyecto"] == filtro_obra_worker]
            if filtro_estatus_worker != "Todos":
                df_mostrar = df_mostrar[df_mostrar["estatus"] == filtro_estatus_worker]
            if buscar_worker:
                term_w = buscar_worker.lower()
                df_mostrar = df_mostrar[
                    df_mostrar["nombre_completo"].str.lower().str.contains(term_w) |
                    df_mostrar["puesto"].str.lower().str.contains(term_w)
                ]

            st.dataframe(
                df_mostrar[["id", "nombre_completo", "puesto", "telefono", "proyecto", "estatus", "fecha_registro"]],
                column_config={
                    "id": "ID",
                    "nombre_completo": "Trabajador",
                    "puesto": "Puesto / Especialidad",
                    "telefono": "Teléfono",
                    "proyecto": "Obra Asignada",
                    "estatus": "Estatus",
                },
                use_container_width=True,
            )

            st.markdown("---")
            st.subheader("🔄 Reasignar Trabajador a Otra Obra")

            with st.form("form_reasignar_trabajador"):
                trabajador_dict = dict(zip(trabajadores_df["nombre_completo"] + " (" + trabajadores_df["puesto"] + ")", trabajadores_df["id"]))
                trabajador_sel = st.selectbox("Seleccionar Trabajador", list(trabajador_dict.keys()))
                nueva_obra_sel = st.selectbox("Nueva Obra Asignada", ["Sin Asignar / Oficina"] + list(proyectos_dict.keys()))

                if st.form_submit_button("Guardar Cambios de Asignación"):
                    trab_id = trabajador_dict[trabajador_sel]
                    nueva_obra_id = proyectos_dict[nueva_obra_sel] if nueva_obra_sel != "Sin Asignar / Oficina" else None

                    with sqlite3.connect(DB_PATH) as conn:
                        c = conn.cursor()
                        c.execute("UPDATE trabajadores SET proyecto_id = ? WHERE id = ?", (nueva_obra_id, trab_id))
                        conn.commit()
                    clear_data_cache()
                    st.success("Reasignación completada correctamente.")
                    st.rerun()
        else:
            st.info("No hay trabajadores registrados en la base de datos.")

    with tab2:
        with st.form("form_nuevo_trabajador"):
            w_nombre = st.text_input(t["lbl_worker_name"])
            w_puesto = st.text_input(t["lbl_position"])
            w_telefono = st.text_input(t["lbl_phone"])

            opciones_obra = ["Sin Asignar / Oficina"] + list(proyectos_dict.keys())
            w_obra = st.selectbox(t["lbl_assign_obra"], opciones_obra)

            if st.form_submit_button(t["btn_save_worker"]):
                if w_nombre and w_puesto:
                    obra_id_val = proyectos_dict[w_obra] if w_obra != "Sin Asignar / Oficina" else None
                    try:
                        with sqlite3.connect(DB_PATH) as conn:
                            c = conn.cursor()
                            c.execute(
                                "INSERT INTO trabajadores (nombre_completo, puesto, telefono, proyecto_id) VALUES (?, ?, ?, ?)",
                                (w_nombre, w_puesto, w_telefono, obra_id_val),
                            )
                            conn.commit()
                        clear_data_cache()
                        st.success(t["msg_worker_success"])
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar trabajador: {e}")

# ==========================================
# 4. COSTOS
# ==========================================
elif menu_sel == t["nav_costos"]:
    st.markdown(f"<div class='main-header'>{t['costos_title']}</div>", unsafe_allow_html=True)

    proyectos_df = get_proyectos_df()
    if proyectos_df.empty:
        st.warning("Registra una obra o proyecto primero.")
    else:
        proyectos_dict = dict(zip(proyectos_df["nombre"], proyectos_df["id"]))
        col_sel, col_form = st.columns([1, 1.2])

        with col_sel:
            # Sincronizado con la barra lateral
            idx_obra = list(proyectos_dict.keys()).index(global_obra_sel) if global_obra_sel in proyectos_dict else 0
            obra_sel = st.selectbox(t["lbl_select_obra"], list(proyectos_dict.keys()), index=idx_obra)
            obra_id = proyectos_dict[obra_sel]

            with st.form("form_costo"):
                categoria = st.selectbox(
                    t["lbl_cat"],
                    [
                        "Materiales / Materials",
                        "Mano de Obra / Labor",
                        "Equipos / Equipment",
                        "Subcontratos / Subcontracts",
                        "Gastos Indirectos / Indirects",
                    ],
                )
                concepto = st.text_input(t["lbl_concept"])
                monto = st.number_input(t["lbl_amount"], min_value=0.01, step=500.0)
                fecha_costo = st.date_input(t["lbl_date"], datetime.now())
                observaciones = st.text_area(t["lbl_obs"])

                if st.form_submit_button(t["btn_save_costo"]):
                    if concepto and monto > 0:
                        with sqlite3.connect(DB_PATH) as conn:
                            c = conn.cursor()
                            c.execute(
                                "INSERT INTO costos (proyecto_id, categoria, concepto, monto, fecha, registrado_por, observaciones) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (obra_id, categoria, concepto, monto, fecha_costo, user["nombre"], observaciones),
                            )
                            conn.commit()
                        clear_data_cache()
                        st.success(t["msg_costo_success"])
                        st.rerun()

        with col_form:
            st.subheader(t["costos_history"])
            costos_df = get_costos_df(obra_id)

            if not costos_df.empty:
                st.markdown("##### 🔍 Filtros de Historial")
                fc1, fc2 = st.columns(2)
                with fc1:
                    f_cats = st.multiselect("Categorías:", costos_df['categoria'].unique().tolist(), default=costos_df['categoria'].unique().tolist())
                with fc2:
                    f_busqueda_c = st.text_input("🔎 Buscar Concepto / Usuario:", "")

                df_costos_filtrados = costos_df.copy()
                if f_cats:
                    df_costos_filtrados = df_costos_filtrados[df_costos_filtrados['categoria'].isin(f_cats)]
                if f_busqueda_c:
                    term_c = f_busqueda_c.lower()
                    df_costos_filtrados = df_costos_filtrados[
                        df_costos_filtrados['concepto'].str.lower().str.contains(term_c) |
                        df_costos_filtrados['registrado_por'].str.lower().str.contains(term_c)
                    ]

                st.dataframe(
                    df_costos_filtrados[["id", "categoria", "concepto", "monto", "fecha", "registrado_por"]],
                    column_config={"monto": st.column_config.NumberColumn("Monto", format="$%,.2f")},
                    use_container_width=True,
                )

                st.markdown("---")
                with st.expander("🗑️ Eliminar Registro de Costo Erróneo"):
                    costo_del_id = st.selectbox("Selecciona el ID del costo a eliminar", costos_df["id"].tolist())
                    if st.button("Eliminar Costo"):
                        with sqlite3.connect(DB_PATH) as conn:
                            c = conn.cursor()
                            c.execute("DELETE FROM costos WHERE id = ?", (costo_del_id,))
                            conn.commit()
                        clear_data_cache()
                        st.success("Costo eliminado.")
                        st.rerun()
            else:
                st.info("Sin registros de costos para esta obra.")

# ==========================================
# 5. CUENTAS POR PAGAR (CxP)
# ==========================================
elif menu_sel == t["nav_cxp"]:
    st.markdown(f"<div class='main-header'>{t['cxp_title']}</div>", unsafe_allow_html=True)

    proyectos_df = get_proyectos_df()
    if proyectos_df.empty:
        st.warning("Registra una obra o proyecto primero.")
    else:
        proyectos_dict = dict(zip(proyectos_df["nombre"], proyectos_df["id"]))
        tab1, tab2 = st.tabs([t["tab_active_cxp"], t["tab_new_cxp"]])

        with tab1:
            st.subheader("🔍 Filtros de Cuentas por Pagar")
            c_f1, c_f2, c_f3 = st.columns([1, 1, 1.5])
            with c_f1:
                filtro_estatus_cxp = st.multiselect("Estatus:", ["Pendiente", "Parcial", "Pagado"], default=["Pendiente", "Parcial"])
            with c_f2:
                filtro_obra_cxp = st.selectbox("Obra:", ["Todas las Obras"] + list(proyectos_dict.keys()), index=0 if global_obra_sel == "Todas las Obras" else (list(proyectos_dict.keys()).index(global_obra_sel) + 1 if global_obra_sel in proyectos_dict else 0))
            with c_f3:
                buscar_proveedor = st.text_input("🔎 Buscar Proveedor o Concepto:", "")

            cxp_df = get_cxp_df()
            if not cxp_df.empty:
                cxp_df["saldo_pendiente"] = cxp_df["monto_total"] - cxp_df["monto_pagado"]
                
                df_cxp_filtrada = cxp_df.copy()
                if filtro_estatus_cxp:
                    df_cxp_filtrada = df_cxp_filtrada[df_cxp_filtrada["estatus"].isin(filtro_estatus_cxp)]
                if filtro_obra_cxp != "Todas las Obras":
                    df_cxp_filtrada = df_cxp_filtrada[df_cxp_filtrada["proyecto"] == filtro_obra_cxp]
                if buscar_proveedor:
                    term_p = buscar_proveedor.lower()
                    df_cxp_filtrada = df_cxp_filtrada[
                        df_cxp_filtrada["proveedor"].str.lower().str.contains(term_p) |
                        df_cxp_filtrada["concepto"].str.lower().str.contains(term_p)
                    ]

                st.dataframe(
                    df_cxp_filtrada[["id", "proyecto", "proveedor", "concepto", "monto_total", "monto_pagado", "saldo_pendiente", "estatus", "fecha_vencimiento"]],
                    column_config={
                        "monto_total": st.column_config.NumberColumn("Total", format="$%,.2f"),
                        "monto_pagado": st.column_config.NumberColumn("Pagado", format="$%,.2f"),
                        "saldo_pendiente": st.column_config.NumberColumn("Saldo", format="$%,.2f"),
                    },
                    use_container_width=True,
                )

                st.markdown("---")
                st.subheader(t["btn_pay"])

                pendientes = df_cxp_filtrada[df_cxp_filtrada["saldo_pendiente"] > 0]
                if not pendientes.empty:
                    with st.form("form_pago_cxp"):
                        cxp_id_sel = st.selectbox(t["lbl_cxp_id"], pendientes["id"].tolist())
                        monto_abono = st.number_input(t["lbl_pay_amount"], min_value=0.01, step=1000.0)

                        if st.form_submit_button(t["btn_pay"]):
                            row = pendientes[pendientes["id"] == cxp_id_sel].iloc[0]
                            nuevo_pagado = row["monto_pagado"] + monto_abono
                            nuevo_estatus = "Pagado" if nuevo_pagado >= row["monto_total"] else "Parcial"

                            with sqlite3.connect(DB_PATH) as conn:
                                c = conn.cursor()
                                c.execute("UPDATE cuentas_por_pagar SET monto_pagado = ?, estatus = ? WHERE id = ?", (nuevo_pagado, nuevo_estatus, cxp_id_sel))
                                c.execute(
                                    "INSERT INTO costos (proyecto_id, categoria, concepto, monto, fecha, registrado_por, observaciones) VALUES (?, ?, ?, ?, CURRENT_DATE, ?, ?)",
                                    (
                                        row["proyecto_id"],
                                        "Subcontratos / Subcontracts",
                                        f"Pago CxP #{cxp_id_sel}: {row['proveedor']} - {row['concepto']}",
                                        monto_abono,
                                        user["nombre"],
                                        f"Abono CxP Ref {cxp_id_sel}",
                                    ),
                                )
                                conn.commit()
                            clear_data_cache()
                            st.success(t["msg_pay_success"])
                            st.rerun()
                else:
                    st.success("🎉 ¡No hay cuentas pendientes por pagar para el filtro actual!")
            else:
                st.info("No hay cuentas por pagar registradas.")

        with tab2:
            with st.form("form_nueva_cxp"):
                obra_cxp = st.selectbox(t["lbl_select_obra"], list(proyectos_dict.keys()))
                proveedor = st.text_input(t["lbl_provider"])
                concepto_cxp = st.text_input(t["lbl_concept"])
                monto_total = st.number_input(t["lbl_amount"], min_value=0.01, step=1000.0)
                fecha_venc = st.date_input(t["lbl_due"], datetime.now())

                if st.form_submit_button(t["btn_save_cxp"]):
                    if proveedor and concepto_cxp and monto_total > 0:
                        with sqlite3.connect(DB_PATH) as conn:
                            c = conn.cursor()
                            c.execute(
                                "INSERT INTO cuentas_por_pagar (proyecto_id, proveedor, concepto, monto_total, fecha_vencimiento, registrado_por) VALUES (?, ?, ?, ?, ?, ?)",
                                (proyectos_dict[obra_cxp], proveedor, concepto_cxp, monto_total, fecha_venc, user["nombre"]),
                            )
                            conn.commit()
                        clear_data_cache()
                        st.success(t["msg_cxp_success"])
                        st.rerun()

# ==========================================
# 6. REQUISICIONES DE CAMPO
# ==========================================
elif menu_sel == t["nav_req"]:
    st.markdown(f"<div class='main-header'>{t['req_title']}</div>", unsafe_allow_html=True)

    proyectos_df = get_proyectos_df()
    if proyectos_df.empty:
        st.warning("Registra una obra o proyecto primero.")
    else:
        proyectos_dict = dict(zip(proyectos_df["nombre"], proyectos_df["id"]))
        tab1, tab2 = st.tabs([t["tab_active_req"], t["tab_new_req"]])

        with tab1:
            st.subheader("🔍 Filtros de Requisiciones")
            rf_col1, rf_col2, rf_col3 = st.columns([1, 1, 1.5])
            with rf_col1:
                filtro_prio_req = st.multiselect("Prioridad:", ["Baja", "Normal", "Alta", "Urgente"], default=["Baja", "Normal", "Alta", "Urgente"])
            with rf_col2:
                filtro_estatus_req = st.multiselect("Estatus:", ["Pendiente", "Aprobado", "Entregado", "Rechazado"], default=["Pendiente", "Aprobado"])
            with rf_col3:
                buscar_req = st.text_input("🔎 Buscar Insumo o Solicitante:", "")

            req_df = get_requisiciones_df()
            if not req_df.empty:
                df_req_filtrada = req_df.copy()
                if filtro_prio_req:
                    df_req_filtrada = df_req_filtrada[df_req_filtrada["prioridad"].isin(filtro_prio_req)]
                if filtro_estatus_req:
                    df_req_filtrada = df_req_filtrada[df_req_filtrada["estatus"].isin(filtro_estatus_req)]
                if global_obra_sel != "Todas las Obras":
                    df_req_filtrada = df_req_filtrada[df_req_filtrada["proyecto"] == global_obra_sel]
                if buscar_req:
                    term_r = buscar_req.lower()
                    df_req_filtrada = df_req_filtrada[
                        df_req_filtrada["insumo"].str.lower().str.contains(term_r) |
                        df_req_filtrada["solicitado_por"].str.lower().str.contains(term_r)
                    ]

                st.dataframe(
                    df_req_filtrada[["id", "proyecto", "insumo", "cantidad", "unidad", "prioridad", "solicitado_por", "estatus", "fecha"]],
                    use_container_width=True,
                )

                st.markdown("---")
                st.subheader("🔄 Cambiar Estatus de Requisición")
                with st.form("form_estatus_req"):
                    req_id_sel = st.selectbox("ID Requisición", df_req_filtrada["id"].tolist())
                    nuevo_estatus_req = st.selectbox("Nuevo Estatus", ["Pendiente", "Aprobado", "Entregado", "Rechazado"])

                    if st.form_submit_button("Actualizar Estatus"):
                        with sqlite3.connect(DB_PATH) as conn:
                            c = conn.cursor()
                            c.execute("UPDATE requisiciones SET estatus = ? WHERE id = ?", (nuevo_estatus_req, req_id_sel))
                            conn.commit()
                        clear_data_cache()
                        st.success("Estatus de la requisición actualizado.")
                        st.rerun()
            else:
                st.info("No hay requisiciones generadas.")

        with tab2:
            with st.form("form_nueva_req"):
                obra_req = st.selectbox(t["lbl_select_obra"], list(proyectos_dict.keys()))
                insumo = st.text_input(t["lbl_item"])
                c_cant, c_uni, c_prio = st.columns(3)
                with c_cant:
                    cantidad = st.number_input(t["lbl_qty"], min_value=0.01, value=1.0)
                with c_uni:
                    unidad = st.text_input(t["lbl_unit"], value="Pza / M2 / Ton")
                with c_prio:
                    prioridad = st.selectbox(t["lbl_priority"], ["Baja", "Normal", "Alta", "Urgente"])

                if st.form_submit_button(t["btn_send_req"]):
                    if insumo and cantidad > 0:
                        with sqlite3.connect(DB_PATH) as conn:
                            c = conn.cursor()
                            c.execute(
                                "INSERT INTO requisiciones (proyecto_id, insumo, cantidad, unidad, prioridad, solicitado_por, estatus) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (proyectos_dict[obra_req], insumo, cantidad, unidad, prioridad, user["nombre"], "Pendiente"),
                            )
                            conn.commit()
                        clear_data_cache()
                        st.success(t["msg_req_success"])
                        st.rerun()

# ==========================================
# 7. USUARIOS MAESTROS
# ==========================================
elif menu_sel == t["nav_users"]:
    st.markdown(f"<div class='main-header'>{t['users_title']}</div>", unsafe_allow_html=True)

    col_user1, col_user2 = st.columns([1, 1.2])

    with col_user1:
        with st.form("form_nuevo_usuario"):
            new_username = st.text_input(t["lbl_new_username"])
            new_password = st.text_input(t["lbl_new_password"], type="password")
            fullname = st.text_input(t["lbl_fullname"])

            if st.form_submit_button(t["btn_create_user"]):
                if new_username and new_password and fullname:
                    try:
                        with sqlite3.connect(DB_PATH) as conn:
                            c = conn.cursor()
                            c.execute(
                                "INSERT INTO usuarios (username, password, nombre_completo, rol) VALUES (?, ?, ?, ?)",
                                (new_username, make_hashes(new_password), fullname, "Usuario Maestro"),
                            )
                            conn.commit()
                        clear_data_cache()
                        st.success(t["msg_user_success"])
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("El nombre de usuario ya existe en el sistema.")
                    except Exception as e:
                        st.error(f"Error: {e}")

    with col_user2:
        st.subheader(t["users_list"])
        users_df = get_usuarios_df()
        st.dataframe(users_df, use_container_width=True)
