import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import os
from datetime import datetime, date, timedelta

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="Rattlesnake ERP | Control Operativo Ejecutivo",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_PATH = "database/control_ejecutivo.db"

# ==========================================
# ESTILOS CSS - CORRECCIÓN DE CONTRASTE & TEMA CLARO
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
        
        /* Typography General */
        label, p, span, h1, h2, h3, h4, h5, h6, div {
            color: #0F172A !important;
        }

        /* Inputs y Campos deTexto */
        div[data-baseweb="input"] input, div[data-baseweb="select"] {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 6px !important;
        }

        /* Sidebar Elegante Oscuro / Ejecutivo */
        section[data-testid="stSidebar"] {
            background-color: #0F172A !important;
        }
        
        section[data-testid="stSidebar"] * {
            color: #F8FAFC !important;
        }

        section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
            background-color: #1E293B !important;
            border-radius: 6px;
        }
        
        /* Tarjetas de Métricas Ejecutivas */
        div[data-testid="stMetric"] {
            background-color: #FFFFFF !important;
            padding: 18px;
            border-radius: 10px;
            border-left: 5px solid #0284C7;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
        }
        
        div[data-testid="stMetricValue"] * {
            font-size: 26px !important;
            font-weight: 800 !important;
            color: #0F172A !important;
        }

        /* Botones Principales */
        .stButton>button {
            border-radius: 6px;
            font-weight: 600;
            background: #0284C7 !important;
            color: #FFFFFF !important;
            border: none;
            padding: 8px 16px;
            width: 100%;
        }
        
        .stButton>button * {
            color: #FFFFFF !important;
        }
        
        .stButton>button:hover {
            background: #0369A1 !important;
        }

        /* Expander y Tablas */
        div[data-aria-expanded="true"] {
            background-color: #FFFFFF !important;
            border-radius: 8px;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# INICIALIZACIÓN DE BASE DE DATOS
# ==========================================
def init_db():
    os.makedirs("database", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Clientes
    c.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            contacto TEXT,
            telefono TEXT,
            email TEXT
        )
    ''')

    # Catálogo de Servicios
    c.execute('''
        CREATE TABLE IF NOT EXISTS servicios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concepto TEXT NOT NULL,
            precio_base REAL NOT NULL
        )
    ''')

    # Órdenes de Trabajo / Control Operativo
    c.execute('''
        CREATE TABLE IF NOT EXISTS ordenes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            servicio_id INTEGER,
            estatus TEXT DEFAULT 'En Proceso',
            fecha_inicio DATE,
            fecha_fin DATE,
            monto REAL NOT NULL,
            pagado REAL DEFAULT 0.0,
            FOREIGN KEY (cliente_id) REFERENCES clientes (id),
            FOREIGN KEY (servicio_id) REFERENCES servicios (id)
        )
    ''')

    # Gastos y Finanzas
    c.execute('''
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            orden_id INTEGER,
            categoria TEXT NOT NULL,
            concepto TEXT NOT NULL,
            monto REAL NOT NULL,
            fecha DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY (orden_id) REFERENCES ordenes (id)
        )
    ''')

    # Datos Demo
    c.execute("SELECT count(*) FROM clientes")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO clientes (nombre, contacto, telefono, email) VALUES ('Residencial Guadix', 'Ing. Carlos', '6671234567', 'carlos@guadix.com')")
        c.execute("INSERT INTO clientes (nombre, contacto, telefono, email) VALUES ('Comercial Plaza del Sol', 'Lic. Sofía', '6677654321', 'sofia@plazasol.com')")
        
        c.execute("INSERT INTO servicios (concepto, precio_base) VALUES ('Instalación Eléctrica Comercial', 25000)")
        c.execute("INSERT INTO servicios (concepto, precio_base) VALUES ('Mantenimiento Plomería e Hidráulico', 12000)")

        c.execute("INSERT INTO ordenes (cliente_id, servicio_id, estatus, fecha_inicio, fecha_fin, monto, pagado) VALUES (1, 1, 'En Proceso', '2026-09-01', '2026-09-30', 25000, 15000)")
        c.execute("INSERT INTO ordenes (cliente_id, servicio_id, estatus, fecha_inicio, fecha_fin, monto, pagado) VALUES (2, 2, 'Completado', '2026-08-15', '2026-08-28', 12000, 12000)")

        c.execute("INSERT INTO gastos (orden_id, categoria, concepto, monto, fecha) VALUES (1, 'Materiales', 'Cableado y Breakers', 8500, '2026-09-05')")

    conn.commit()
    conn.close()

init_db()

# ==========================================
# MENÚ LATERAL DE NAVEGACIÓN
# ==========================================
st.sidebar.markdown("<h2 style='color:#FFFFFF;'>⚡ Rattlesnake ERP</h2>", unsafe_allow_html=True)
st.sidebar.caption("Control Ejecutivo & Gestión Operativa")
st.sidebar.markdown("---")

menu = st.sidebar.radio("Navegación / Módulos", [
    "📋 Control Operativo",
    "👥 Clientes",
    "🛠️ Servicios / Catálogo",
    "💰 Finanzas & CxC",
    "📦 Inventario",
    "📊 Reportes & Gantt"
])

# ==========================================
# CONSULTAS DE DATOS
# ==========================================
def fetch_control_operativo():
    conn = sqlite3.connect(DB_PATH)
    query = '''
        SELECT 
            o.id as 'ID Órden',
            c.nombre as 'Cliente',
            s.concepto as 'Servicio',
            o.estatus as 'Estatus',
            o.fecha_inicio as 'Fecha Inicio',
            o.fecha_fin as 'Fecha Término',
            o.monto as 'Monto Total',
            o.pagado as 'Monto Pagado',
            (o.monto - o.pagado) as 'Pendiente'
        FROM ordenes o
        JOIN clientes c ON o.cliente_id = c.id
        JOIN servicios s ON o.servicio_id = s.id
        ORDER BY o.id DESC
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# ==========================================
# VISTA 1: CONTROL OPERATIVO CENTRAL
# ==========================================
if menu == "📋 Control Operativo":
    st.markdown("<h2>Tablero de Control Operativo</h2>", unsafe_allow_html=True)
    st.caption("Visión integrada de proyectos activos, montos contratados, cobranza y estatus de obras.")

    df_op = fetch_control_operativo()

    # 1. RESUMEN EJECUTIVO (KPIs TOP)
    ingresos_totales = df_op['Monto Total'].sum()
    cobrado_total = df_op['Monto Pagado'].sum()
    cuentas_pendientes = df_op['Pendiente'].sum()
    trabajos_activos = len(df_op[df_op['Estatus'] == 'En Proceso'])

    st.markdown("---")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Ingresos Contratados", f"${ingresos_totales:,.2f}")
    kpi2.metric("Cobrado Real", f"${cobrado_total:,.2f}")
    kpi3.metric("Pendiente por Cobrar", f"${cuentas_pendientes:,.2f}", delta="-CxC", delta_color="inverse")
    kpi4.metric("Trabajos Activos", f"{trabajos_activos} Proyectos")

    st.markdown("---")

    # 2. FILTROS Y BÚSQUEDA SUPERIOR
    st.subheader("🔍 Filtros & Búsqueda Operativa")
    f_col1, f_col2, f_col3 = st.columns([1.5, 1, 1.5])

    with f_col1:
        clientes_lista = ["Todos"] + list(df_op['Cliente'].unique())
        sel_cliente = st.selectbox("Cliente", clientes_lista)

    with f_col2:
        estatus_lista = ["Todos", "En Proceso", "Completado", "Pausado"]
        sel_estatus = st.selectbox("Estatus del Trabajo", estatus_lista)

    with f_col3:
        fechas = st.date_input("Rango de Fechas", [date(2026, 1, 1), date(2026, 12, 31)])

    # Aplicación de Filtros
    df_filtered = df_op.copy()
    if sel_cliente != "Todos":
        df_filtered = df_filtered[df_filtered['Cliente'] == sel_cliente]
    if sel_estatus != "Todos":
        df_filtered = df_filtered[df_filtered['Estatus'] == sel_estatus]

    # 3. TABLA CENTRAL TIPO "CONTROL OPERATIVO"
    st.markdown("### 📊 Tabla de Control de Trabajos y Obras")
    st.dataframe(
        df_filtered[['ID Órden', 'Cliente', 'Servicio', 'Estatus', 'Fecha Inicio', 'Fecha Término', 'Monto Total', 'Monto Pagado', 'Pendiente']],
        use_container_width=True,
        height=280
    )

    # 4. ACCIONES RÁPIDAS
    st.markdown("### ⚡ Acciones Operativas")
    acc_col1, acc_col2 = st.columns(2)

    with acc_col1:
        with st.expander("💳 Registrar Cobro / Abono a Órden"):
            orden_id_pago = st.number_input("ID de la Órden", min_value=1, step=1)
            monto_abono = st.number_input("Monto Recibido ($)", min_value=100.0, step=500.0)
            if st.button("Aplicar Abono"):
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("UPDATE ordenes SET pagado = pagado + ? WHERE id = ?", (monto_abono, orden_id_pago))
                conn.commit()
                conn.close()
                st.success("Cobro registrado exitosamente.")
                st.rerun()

    with acc_col2:
        with st.expander("📌 Cambiar Estado de Obra / Trabajo"):
            orden_id_estatus = st.number_input("ID de Órden a Editar", min_value=1, step=1)
            nuevo_estatus = st.selectbox("Estado Nuevo", ["En Proceso", "Completado", "Pausado", "Cancelado"])
            if st.button("Guardar Cambio de Estado"):
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("UPDATE ordenes SET estatus = ? WHERE id = ?", (nuevo_estatus, orden_id_estatus))
                conn.commit()
                conn.close()
                st.success("Estatus actualizado.")
                st.rerun()

# ==========================================
# VISTA 2: CLIENTES
# ==========================================
elif menu == "👥 Clientes":
    st.markdown("<h2>Directorio de Clientes</h2>", unsafe_allow_html=True)
    
    col_c1, col_c2 = st.columns([1.2, 1])
    with col_c1:
        conn = sqlite3.connect(DB_PATH)
        df_c = pd.read_sql_query("SELECT * FROM clientes", conn)
        conn.close()
        st.dataframe(df_c, use_container_width=True)

    with col_c2:
        st.subheader("➕ Registrar Nuevo Cliente")
        with st.form("form_cliente"):
            nombre_c = st.text_input("Empresa / Nombre Cliente")
            contacto_c = st.text_input("Persona de Contacto")
            tel_c = st.text_input("Teléfono")
            email_c = st.text_input("Correo Electrónico")
            
            if st.form_submit_button("Guardar Cliente"):
                if nombre_c:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute("INSERT INTO clientes (nombre, contacto, telefono, email) VALUES (?, ?, ?, ?)", 
                              (nombre_c, contacto_c, tel_c, email_c))
                    conn.commit()
                    conn.close()
                    st.success("Cliente agregado exitosamente.")
                    st.rerun()

# ==========================================
# VISTA 3: SERVICIOS / CATÁLOGO
# ==========================================
elif menu == "🛠️ Servicios / Catálogo":
    st.markdown("<h2>Catálogo de Servicios</h2>", unsafe_allow_html=True)
    
    col_s1, col_s2 = st.columns([1.2, 1])
    with col_s1:
        conn = sqlite3.connect(DB_PATH)
        df_s = pd.read_sql_query("SELECT * FROM servicios", conn)
        conn.close()
        st.dataframe(df_s, use_container_width=True)

    with col_s2:
        st.subheader("➕ Agregar Concepto al Catálogo")
        with st.form("form_servicio"):
            concepto_s = st.text_input("Concepto / Descripción del Servicio")
            precio_s = st.number_input("Precio Base Estimado ($)", min_value=0.0, step=1000.0)
            
            if st.form_submit_button("Guardar en Catálogo"):
                if concepto_s:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute("INSERT INTO servicios (concepto, precio_base) VALUES (?, ?)", (concepto_s, precio_s))
                    conn.commit()
                    conn.close()
                    st.success("Servicio registrado.")
                    st.rerun()

# ==========================================
# VISTA 4: FINANZAS & REPORTES GANTT
# ==========================================
elif menu == "📊 Reportes & Gantt":
    st.markdown("<h2>Reportes Ejecutivos & Cronogramas</h2>", unsafe_allow_html=True)
    
    df_op = fetch_control_operativo()
    if not df_op.empty:
        fig_gantt = px.timeline(
            df_op, 
            x_start="Fecha Inicio", 
            x_end="Fecha Término", 
            y="Cliente", 
            color="Estatus",
            title="Cronograma de Trabajos y Proyectos Activos"
        )
        fig_gantt.update_yaxes(autorange="reversed")
        fig_gantt.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#0F172A')
        st.plotly_chart(fig_gantt, use_container_width=True)

elif menu in ["💰 Finanzas & CxC", "📦 Inventario"]:
    st.markdown(f"<h2>{menu}</h2>", unsafe_allow_html=True)
    st.info("Módulo operativo integrado al motor de datos principal.")
