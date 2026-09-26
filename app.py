import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import hashlib
import os
from datetime import datetime

# ==========================================
# CONFIGURACIÓN DE PÁGINA Y ESTILOS PRO
# ==========================================
st.set_page_config(
    page_title="Rattlesnake Plumbing ERP",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_PATH = "database/erp_local.db"

# Estilos CSS personalizados
st.markdown("""
    <style>
        .main-header {
            font-size: 26px;
            font-weight: 700;
            color: #1E293B;
            margin-bottom: 10px;
        }
        .metric-card {
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }
        .metric-title {
            font-size: 13px;
            color: #64748B;
            font-weight: 600;
            text-transform: uppercase;
        }
        .metric-value {
            font-size: 22px;
            font-weight: 700;
            color: #0F172A;
        }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# BASE DE DATOS Y AUTENTICACIÓN
# ==========================================
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

def init_db():
    os.makedirs("database", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. Tabla de Usuarios (Único Rol: Usuario Maestro)
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nombre_completo TEXT NOT NULL,
            rol TEXT DEFAULT 'Usuario Maestro'
        )
    ''')
    
    # Usuario Maestro por defecto (admin / admin123)
    c.execute("SELECT * FROM usuarios WHERE username = 'admin'")
    if not c.fetchone():
        c.execute(
            "INSERT INTO usuarios (username, password, nombre_completo, rol) VALUES (?, ?, ?, ?)",
            ("admin", make_hashes("admin123"), "Usuario Maestro", "Usuario Maestro")
        )

    # 2. Tabla de Proyectos / Obras
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

    # 3. Tabla de Costos (Materiales, Mano de Obra, etc.)
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

    # 4. Tabla de Cuentas por Pagar (Pagos Pendientes)
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

    # 5. Tabla de Requisiciones de Campo
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
# FUNCIONES AUXILIARES DE CONSULTA
# ==========================================
def login_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT username, password, nombre_completo, rol FROM usuarios WHERE username = ?', (username,))
    data = c.fetchone()
    conn.close()
    if data and check_hashes(password, data[1]):
        return {"username": data[0], "nombre": data[2], "rol": data[3]}
    return None

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

def get_requisiciones_df(proyecto_id=None):
    conn = sqlite3.connect(DB_PATH)
    if proyecto_id:
        df = pd.read_sql_query("SELECT r.*, p.nombre as proyecto FROM requisiciones r JOIN proyectos p ON r.proyecto_id = p.id WHERE r.proyecto_id = ?", conn, params=(proyecto_id,))
    else:
        df = pd.read_sql_query("SELECT r.*, p.nombre as proyecto FROM requisiciones r JOIN proyectos p ON r.proyecto_id = p.id", conn)
    conn.close()
    return df


# ==========================================
# MANEJO DE SESIÓN Y LOGIN
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_info'] = None

if not st.session_state['logged_in']:
    st.markdown("<h2 style='text-align: center;'>⚡ Rattlesnake ERP - Control de Obra</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.subheader("Acceso al Sistema")
        username = st.text_input("Usuario Maestro")
        password = st.text_input("Contraseña", type="password")
        
        if st.button("Iniciar Sesión", use_container_width=True):
            user = login_user(username, password)
            if user:
                st.session_state['logged_in'] = True
                st.session_state['user_info'] = user
                st.success(f"Bienvenido {user['nombre']}")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
        
        st.info("🔑 **Acceso Inicial Maestro:**\n- Usuario: `admin`\n- Contraseña: `admin123`")
    st.stop()


# ==========================================
# BARRA LATERAL (MENÚ Y USUARIO)
# ==========================================
user = st.session_state['user_info']
st.sidebar.title("⚡ Rattlesnake ERP")
st.sidebar.caption(f"👤 **{user['nombre']}**\n👑 *Usuario Maestro*")

if st.sidebar.button("Cerrar Sesión"):
    st.session_state['logged_in'] = False
    st.session_state['user_info'] = None
    st.rerun()

st.sidebar.markdown("---")

# Menú principal completo
opciones_menu = [
    "📊 Balance Financiero",
    "🏗️ Obras y Ubicaciones",
    "💰 Registro de Costos",
    "💳 Pagos Pendientes (CxP)",
    "📋 Requisiciones de Campo",
    "👑 Gestión de Usuarios Maestros"
]

menu_sel = st.sidebar.radio("Navegación", opciones_menu)


# ==========================================
# VISTA 1: BALANCE FINANCIERO (DASHBOARD)
# ==========================================
if menu_sel == "📊 Balance Financiero":
    st.markdown("<div class='main-header'>📊 Balance Financiero & Control Ejecutivo</div>", unsafe_allow_html=True)
    
    proyectos_df = get_proyectos_df()
    costos_df = get_costos_df()
    cxp_df = get_cxp_df()

    if proyectos_df.empty:
        st.warning("No hay obras registradas. Registra tu primera obra en el menú de 'Obras y Ubicaciones'.")
    else:
        # Métricas Globales
        presupuesto_total = proyectos_df['presupuesto_total'].sum()
        costo_total_ejecutado = costos_df['monto'].sum() if not costos_df.empty else 0
        pagos_pendientes_total = (cxp_df['monto_total'] - cxp_df['monto_pagado']).sum() if not cxp_df.empty else 0
        balance_disponible = presupuesto_total - costo_total_ejecutado

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Presupuesto Contratado", f"${presupuesto_total:,.2f}")
        c2.metric("Costo Real Ejecutado", f"${costo_total_ejecutado:,.2f}", delta=f"-{(costo_total_ejecutado/presupuesto_total*100) if presupuesto_total>0 else 0:.1f}% del total", delta_color="inverse")
        c3.metric("Pagos Pendientes (CxP)", f"${pagos_pendientes_total:,.2f}")
        c4.metric("Margen / Disponible", f"${balance_disponible:,.2f}", delta=f"{(balance_disponible/presupuesto_total*100) if presupuesto_total>0 else 0:.1f}% disponible")

        st.markdown("---")
        
        col_graf1, col_graf2 = st.columns(2)

        with col_graf1:
            st.subheader("Desglose de Costos por Categoría")
            if not costos_df.empty:
                fig_cat = px.pie(costos_df, names='categoria', values='monto', hole=0.4,
                                 color_discrete_sequence=px.colors.qualitative.Bold)
                st.plotly_chart(fig_cat, use_container_width=True)
            else:
                st.info("Sin registros de costos aún.")

        with col_graf2:
            st.subheader("Presupuesto vs Costo por Obra")
            if not costos_df.empty:
                costo_por_obra = costos_df.groupby('proyecto_id')['monto'].sum().reset_index()
                df_comp = proyectos_df.merge(costo_por_obra, left_on='id', right_on='proyecto_id', how='left').fillna(0)
                
                fig_bar = go.Figure(data=[
                    go.Bar(name='Presupuesto', x=df_comp['nombre'], y=df_comp['presupuesto_total'], marker_color='#2563EB'),
                    go.Bar(name='Costo Ejecutado', x=df_comp['nombre'], y=df_comp['monto'], marker_color='#EF4444')
                ])
                fig_bar.update_layout(barmode='group')
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("Sin costos registrados para comparar.")


# ==========================================
# VISTA 2: OBRAS Y UBICACIONES (MAPA)
# ==========================================
elif menu_sel == "🏗️ Obras y Ubicaciones":
    st.markdown("<div class='main-header'>🏗️ Gestión de Obras y Mapas de Ubicación</div>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🗺️ Mapa y Lista de Obras", "➕ Registrar Nueva Obra"])

    with tab1:
        df_obras = get_proyectos_df()
        if not df_obras.empty:
            st.subheader("Ubicación Geográfica de Proyectos")
            
            df_mapa = df_obras.dropna(subset=['latitud', 'longitud'])
            if not df_mapa.empty:
                st.map(df_mapa, latitude='latitud', longitude='longitud', size=20)
            else:
                st.info("Las obras registradas no tienen coordenadas GPS agregadas.")

            st.markdown("---")
            st.subheader("Listado de Obras Activas")
            st.dataframe(df_obras[['codigo', 'nombre', 'cliente', 'presupuesto_total', 'estado', 'latitud', 'longitud']], use_container_width=True)
        else:
            st.info("No hay obras registradas.")

    with tab2:
        st.subheader("Alta de Nuevo Proyecto")
        with st.form("form_nueva_obra"):
            codigo = st.text_input("Código de Obra (ej. OBRA-2026-01)")
            nombre = st.text_input("Nombre de la Obra")
            cliente = st.text_input("Cliente / Empresa")
            presupuesto = st.number_input("Presupuesto Total ($)", min_value=0.0, step=10000.0)
            
            c_lat, c_lon = st.columns(2)
            with c_lat:
                latitud = st.number_input("Latitud GPS (ej. 24.8091)", format="%.6f", value=24.8091)
            with c_lon:
                longitud = st.number_input("Longitud GPS (ej. -107.3940)", format="%.6f", value=-107.3940)

            if st.form_submit_button("Guardar Obra"):
                if codigo and nombre and cliente:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    try:
                        c.execute(
                            "INSERT INTO proyectos (codigo, nombre, cliente, presupuesto_total, latitud, longitud) VALUES (?, ?, ?, ?, ?, ?)",
                            (codigo, nombre, cliente, presupuesto, latitud, longitud)
                        )
                        conn.commit()
                        st.success(f"Obra '{nombre}' creada exitosamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")
                    finally:
                        conn.close()
                else:
                    st.error("Completa los campos obligatorios.")


# ==========================================
# VISTA 3: REGISTRO DE COSTOS (MATERIALES Y MANO DE OBRA)
# ==========================================
elif menu_sel == "💰 Registro de Costos":
    st.markdown("<div class='main-header'>💰 Carga y Desglose de Costos de Obra</div>", unsafe_allow_html=True)
    
    proyectos_df = get_proyectos_df()
    if proyectos_df.empty:
        st.warning("Primero debes dar de alta una obra en el sistema.")
    else:
        proyectos_dict = dict(zip(proyectos_df['nombre'], proyectos_df['id']))
        
        col_sel, col_form = st.columns([1, 1.2])

        with col_sel:
            st.subheader("Captura de Costo")
            obra_sel = st.selectbox("Selecciona la Obra", list(proyectos_dict.keys()))
            obra_id = proyectos_dict[obra_sel]

            with st.form("form_costo"):
                categoria = st.selectbox("Categoría de Costo", [
                    "Materiales",
                    "Mano de Obra",
                    "Equipos y Herramientas",
                    "Subcontratos",
                    "Gastos Indirectos / Gastos de Campo"
                ])
                concepto = st.text_input("Concepto / Descripción del Gasto")
                monto = st.number_input("Monto Total ($)", min_value=0.01, step=500.0)
                fecha_costo = st.date_input("Fecha de Gasto", datetime.now())
                observaciones = st.text_area("Notas / Número de Factura o Nota")

                if st.form_submit_button("Registrar Costo"):
                    if concepto and monto > 0:
                        conn = sqlite3.connect(DB_PATH)
                        c = conn.cursor()
                        c.execute(
                            "INSERT INTO costos (proyecto_id, categoria, concepto, monto, fecha, registrado_por, observaciones) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (obra_id, categoria, concepto, monto, fecha_costo, user['nombre'], observaciones)
                        )
                        conn.commit()
                        conn.close()
                        st.success("Costo registrado correctamente.")
                        st.rerun()
                    else:
                        st.error("Ingresa el concepto y un monto válido.")

        with col_form:
            st.subheader(f"Historial de Costos: {obra_sel}")
            costos_obra = get_costos_df(obra_id)
            if not costos_obra.empty:
                st.dataframe(costos_obra[['fecha', 'categoria', 'concepto', 'monto', 'registrado_por']], use_container_width=True)
                st.metric("Total Acumulado en esta Obra", f"${costos_obra['monto'].sum():,.2f}")
            else:
                st.info("Esta obra no tiene costos cargados aún.")


# ==========================================
# VISTA 4: PAGOS PENDIENTES (CXP)
# ==========================================
elif menu_sel == "💳 Pagos Pendientes (CxP)":
    st.markdown("<div class='main-header'>💳 Cuentas por Pagar & Pagos Pendientes</div>", unsafe_allow_html=True)
    
    proyectos_df = get_proyectos_df()
    if proyectos_df.empty:
        st.warning("Debes registrar obras primero.")
    else:
        proyectos_dict = dict(zip(proyectos_df['nombre'], proyectos_df['id']))

        tab_cxp1, tab_cxp2 = st.tabs(["📌 Cuentas por Pagar Activas", "➕ Registrar Factura / Cuenta"])

        with tab_cxp1:
            cxp_df = get_cxp_df()
            if not cxp_df.empty:
                cxp_df['Pendiente'] = cxp_df['monto_total'] - cxp_df['monto_pagado']
                st.dataframe(
                    cxp_df[['id', 'proyecto', 'proveedor', 'concepto', 'monto_total', 'monto_pagado', 'Pendiente', 'estatus', 'fecha_vencimiento', 'registrado_por']],
                    use_container_width=True
                )

                st.markdown("---")
                st.subheader("Registrar Abono o Pago")
                c1, c2 = st.columns(2)
                with c1:
                    cxp_id = st.number_input("ID de la Cuenta por Pagar", min_value=1, step=1)
                with c2:
                    monto_abono = st.number_input("Monto a Abonar ($)", min_value=0.01, step=500.0)

                if st.button("Aplicar Pago"):
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
                        st.success(f"Abono de ${monto_abono:,.2f} aplicado correctamente.")
                        st.rerun()
                    else:
                        st.error("ID de Cuenta por Pagar no encontrado.")
                    conn.close()
            else:
                st.info("No hay cuentas por pagar registradas.")

        with tab_cxp2:
            with st.form("form_cxp"):
                obra_sel = st.selectbox("Obra Asociada", list(proyectos_dict.keys()))
                obra_id = proyectos_dict[obra_sel]
                proveedor = st.text_input("Proveedor o Subcontratista")
                concepto = st.text_input("Concepto de la Factura / Servicio")
                monto_total = st.number_input("Monto Total de la Factura ($)", min_value=0.01, step=1000.0)
                vencimiento = st.date_input("Fecha Limite de Pago", datetime.now())

                if st.form_submit_button("Guardar Cuenta por Pagar"):
                    if proveedor and concepto and monto_total > 0:
                        conn = sqlite3.connect(DB_PATH)
                        c = conn.cursor()
                        c.execute(
                            "INSERT INTO cuentas_por_pagar (proyecto_id, proveedor, concepto, monto_total, fecha_vencimiento, registrado_por) VALUES (?, ?, ?, ?, ?, ?)",
                            (obra_id, proveedor, concepto, monto_total, vencimiento, user['nombre'])
                        )
                        conn.commit()
                        conn.close()
                        st.success("Cuenta por pagar creada correctamente.")
                        st.rerun()


# ==========================================
# VISTA 5: REQUISICIONES DE CAMPO
# ==========================================
elif menu_sel == "📋 Requisiciones de Campo":
    st.markdown("<div class='main-header'>📋 Requisiciones de Insumos desde Obra</div>", unsafe_allow_html=True)
    
    proyectos_df = get_proyectos_df()
    if proyectos_df.empty:
        st.warning("No hay obras registradas.")
    else:
        proyectos_dict = dict(zip(proyectos_df['nombre'], proyectos_df['id']))

        c_req1, c_req2 = st.columns([1, 1.2])

        with c_req1:
            st.subheader("Nueva Requisición")
            obra_sel = st.selectbox("Obra", list(proyectos_dict.keys()))
            obra_id = proyectos_dict[obra_sel]

            with st.form("form_req"):
                insumo = st.text_input("Material / Insumo Solicitado")
                col_cant, col_uni = st.columns(2)
                with col_cant:
                    cantidad = st.number_input("Cantidad", min_value=0.1, step=1.0)
                with col_uni:
                    unidad = st.text_input("Unidad", value="Pza")
                prioridad = st.selectbox("Prioridad", ["Normal", "Urgente", "Crítica"])

                if st.form_submit_button("Enviar Solicitud"):
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
            st.subheader("Solicitudes Activas")
            req_df = get_requisiciones_df(obra_id)
            if not req_df.empty:
                st.dataframe(req_df[['fecha', 'insumo', 'cantidad', 'unidad', 'prioridad', 'solicitado_por', 'estatus']], use_container_width=True)
            else:
                st.info("Sin requisiciones pendientes.")


# ==========================================
# VISTA 6: GESTIÓN DE USUARIOS MAESTROS
# ==========================================
elif menu_sel == "👑 Gestión de Usuarios Maestros":
    st.markdown("<div class='main-header'>👑 Alta y Control de Usuarios Maestros</div>", unsafe_allow_html=True)
    
    conn = sqlite3.connect(DB_PATH)
    users_df = pd.read_sql_query("SELECT id, username, nombre_completo FROM usuarios", conn)
    conn.close()

    st.subheader("Usuarios Maestros Registrados")
    st.dataframe(users_df, use_container_width=True)

    st.markdown("---")
    st.subheader("Dar de Alta un Nuevo Usuario Maestro")
    with st.form("form_user"):
        new_username = st.text_input("Nombre de Usuario (Login)")
        new_password = st.text_input("Contraseña", type="password")
        new_nombre = st.text_input("Nombre Completo del Usuario Maestro")

        if st.form_submit_button("Crear Usuario Maestro"):
            if new_username and new_password and new_nombre:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                try:
                    c.execute(
                        "INSERT INTO usuarios (username, password, nombre_completo, rol) VALUES (?, ?, ?, ?)",
                        (new_username, make_hashes(new_password), new_nombre, "Usuario Maestro")
                    )
                    conn.commit()
                    st.success(f"Usuario Maestro '{new_username}' dado de alta exitosamente.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al crear usuario: {e}")
                finally:
                    conn.close()
            else:
                st.error("Todos los campos son obligatorios.")
