import hashlib
import json
import os
import secrets
import sqlite3
import urllib.parse
import urllib.request
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import date, datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
import streamlit as st
from fpdf import FPDF

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
            font-size: 26px;
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
            font-size: 24px !important;
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
# GENERADOR DE PDFS (FPDF2)
# ==========================================
class PDFRecibo(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(2, 132, 199)
        self.cell(0, 10, 'RATTLESNAKE SYSTEM - CONTROL DE OBRA', ln=True, align='C')
        self.set_font('Helvetica', '', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, 'Comprobante Oficial de Pago de Nómina', ln=True, align='C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Página {self.page_no()}', align='C')

def generar_pdf_recibo_bytes(row):
    pdf = PDFRecibo()
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(15, 23, 42)
    
    pdf.cell(0, 8, f"RECIBO DE NÓMINA REFERENCIA #{row['id']}", ln=True)
    pdf.ln(2)
    
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(100, 6, f"Trabajador: {row['trabajador']}", ln=False)
    pdf.cell(0, 6, f"Puesto: {row['puesto']}", ln=True)
    pdf.cell(100, 6, f"Proyecto / Obra: {row['proyecto']}", ln=False)
    pdf.cell(0, 6, f"Fecha Emisión: {datetime.now().strftime('%Y-%m-%d')}", ln=True)
    pdf.cell(100, 6, f"Periodo: {row['periodo_inicio']} al {row['periodo_fin']}", ln=True)
    pdf.ln(5)
    
    pdf.set_fill_color(241, 245, 249)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(100, 8, 'Concepto', border=1, fill=True)
    pdf.cell(45, 8, 'Detalle / Horas', border=1, fill=True)
    pdf.cell(45, 8, 'Monto ($)', border=1, fill=True, ln=True)
    
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(100, 7, 'Sueldo Horas Normales', border=1)
    pdf.cell(45, 7, f"{row['horas_trabajadas']} hrs @ ${row['tarifa_hora']:.2f}", border=1)
    pdf.cell(45, 7, f"${row['monto_base']:,.2f}", border=1, ln=True)
    
    pdf.cell(100, 7, 'Horas Extras / Extras', border=1)
    pdf.cell(45, 7, f"{row['horas_extras']} hrs", border=1)
    pdf.cell(45, 7, f"${row['bonos_extras']:,.2f}", border=1, ln=True)
    
    pdf.cell(100, 7, 'Deducciones / Anticipos', border=1)
    pdf.cell(45, 7, '-', border=1)
    pdf.cell(45, 7, f"-${row['descuentos']:,.2f}", border=1, ln=True)
    
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(145, 8, 'NETO TOTAL A RECIBIR:', border=1)
    pdf.cell(45, 8, f"${row['monto_neto']:,.2f}", border=1, ln=True)
    
    pdf.ln(15)
    pdf.cell(90, 8, '________________________', align='C', ln=False)
    pdf.cell(90, 8, '________________________', align='C', ln=True)
    pdf.cell(90, 5, 'Firma del Trabajador', align='C', ln=False)
    pdf.cell(90, 5, 'Firma de Conformidad Empresa', align='C', ln=True)
    
    return bytes(pdf.output())

def generar_pdf_estimacion_bytes(row):
    pdf = PDFRecibo()
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(15, 23, 42)
    
    pdf.cell(0, 8, f"ESTIMACIÓN DE OBRA #{row['numero_estimacion']}", ln=True)
    pdf.ln(2)
    
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(100, 6, f"Proyecto: {row['proyecto']}", ln=False)
    pdf.cell(0, 6, f"Cliente: {row['cliente']}", ln=True)
    pdf.cell(100, 6, f"Fecha Emisión: {row['fecha_emision']}", ln=False)
    pdf.cell(0, 6, f"Estatus: {row['estatus']}", ln=True)
    pdf.cell(0, 6, f"Concepto / Periodo: {row['concepto_periodo']}", ln=True)
    pdf.ln(5)
    
    pdf.set_fill_color(241, 245, 249)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(120, 8, 'Descripción Financiera', border=1, fill=True)
    pdf.cell(70, 8, 'Monto ($)', border=1, fill=True, ln=True)
    
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(120, 7, 'Monto Bruto Estimado', border=1)
    pdf.cell(70, 7, f"${row['monto_estimado']:,.2f}", border=1, ln=True)
    
    pdf.cell(120, 7, 'Amortización de Anticipo (-)', border=1)
    pdf.cell(70, 7, f"-${row['amortizacion_anticipo']:,.2f}", border=1, ln=True)
    
    pdf.cell(120, 7, 'Retención Fondo de Garantía (-)', border=1)
    pdf.cell(70, 7, f"-${row['retencion_garantia']:,.2f}", border=1, ln=True)
    
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(120, 8, 'TOTAL NETO FACTURABLE / COBRABLE:', border=1)
    pdf.cell(70, 8, f"${row['monto_neto_cobrar']:,.2f}", border=1, ln=True)
    
    pdf.cell(120, 8, 'MONTO COBRADO A LA FECHA:', border=1)
    pdf.cell(70, 8, f"${row['monto_cobrado']:,.2f}", border=1, ln=True)
    
    return bytes(pdf.output())

# ==========================================
# ENVÍO DE CORREO SMTP
# ==========================================
def enviar_correo_con_pdf(destinatario, asunto, cuerpo, pdf_bytes, nombre_archivo):
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    
    if not smtp_user or not smtp_pass:
        return False, "⚠️ No se configuraron las credenciales SMTP en las variables de entorno."
        
    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = destinatario
        msg['Subject'] = asunto
        msg.attach(MIMEText(cuerpo, 'plain'))
        
        part = MIMEApplication(pdf_bytes, Name=nombre_archivo)
        part['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
        msg.attach(part)
        
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, destinatario, msg.as_string())
        server.quit()
        return True, "✅ Correo enviado con éxito."
    except Exception as e:
        return False, f"❌ Error enviando correo: {e}"

# ==========================================
# DICCIONARIO BILINGÜE Y SISTEMA SAFE-DICT
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
        "nav_workers": "👷 Personal & Nómina",
        "nav_estimates": "📐 Estimaciones & Clientes",
        "nav_costos": "💰 Registro de Costos",
        "nav_cxp": "💳 Cuentas por Pagar (CxP)",
        "nav_req": "📋 Requisiciones de Campo",
        "nav_users": "👑 Usuarios Maestros",
        "btn_logout": "Cerrar Sesión",
        "lang_selector": "🌐 Idioma / Language",
        "global_filter_title": "🎯 Filtro Global de Obra",
        "global_filter_label": "Seleccionar Obra para Filtrar Todo:",
        "all_sites": "Todas las Obras",
        "unassigned_office": "Sin Asignar / Oficina",
        # Director
        "dir_title": "🎯 Tablero Operativo Directivo - Resumen Ejecutivo",
        "dir_kpi_total_proj": "Proyectos Activos",
        "dir_kpi_goal_prog": "Meta Avance Físico Promedio",
        "dir_kpi_real_prog": "Avance Físico Real Promedio",
        "dir_kpi_efficiency": "Eficiencia Presupuestal Global",
        "dir_status_summary": "Estatus Operativo de Proyectos",
        "dir_scurve_title": "Curva S Acumulada de Ejecución Financiera",
        "dir_alerts_title": "⚠️ Alerta de Desvíos Presupuestales u Operativos",
        # Balance
        "bal_title": "📊 Dashboard Financiero & Rendimiento de Obra",
        "metric_budget": "Presupuesto Contratado",
        "metric_executed": "Costo Real Ejecutado",
        "metric_pending": "Compromisos & Pasivos Pendientes",
        "metric_available": "Margen / Disponible Real",
        "chart_cat": "Desglose de Costos por Categoría",
        "chart_comp": "Presupuesto vs Costo Real por Proyecto",
        # Obras
        "obras_title": "🏗️ Control de Obras & Ubicación GPS",
        "tab_map": "🗺️ Mapa & Editor Interactivo de Obras",
        "tab_new_obra": "➕ Registrar Nueva Obra",
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
        "obras_filter_status": "Filtrar por Estatus:",
        "obras_search": "🔎 Buscar Obra por Nombre, Cliente o Código:",
        "obras_edit_title": "✏️ Editor Directo de Obras & Avance Físico",
        "obras_edit_save": "Guardar Cambios",
        "obras_edit_success": "✅ ¡Obras actualizadas correctamente!",
        # Personal & Nómina
        "workers_title": "👷 Gestión Integrada de Personal & Nómina por Horas",
        "tab_workers_list": "📌 Directorio de Personal & Edición",
        "tab_new_worker": "➕ Registrar Trabajador",
        "tab_payroll": "💵 Control de Nómina & Horas Extras",
        "lbl_worker_name": "Nombre Completo del Trabajador",
        "lbl_position": "Puesto / Especialidad",
        "lbl_phone": "Teléfono",
        "lbl_assign_obra": "Asignar a Obra",
        "btn_save_worker": "Registrar Trabajador",
        "msg_worker_success": "Trabajador registrado exitosamente.",
        "workers_hourly_rate": "Pago por Hora ($/hr)",
        "workers_daily_wage": "Salario Diario ($/día)",
        "workers_pay_mode": "Modalidad de Pago",
        "workers_filter_site": "Filtrar por Obra:",
        "workers_filter_status": "Estatus del Trabajador:",
        "workers_search": "🔎 Buscar Trabajador o Puesto:",
        "workers_save_changes": "Guardar Cambios de Ficha",
        "workers_updated_msg": "Ficha del trabajador actualizada correctamente.",
        "workers_select": "Seleccionar Trabajador",
        "payroll_kpi_pending": "🔴 Adeudo Pendiente de Nómina",
        "payroll_kpi_paid": "🟢 Nómina Total Liquidada",
        "payroll_pay_title": "💸 Liquidar Adeudo de Nómina a Trabajador",
        "payroll_select_id": "Seleccionar ID de Nómina",
        "payroll_pay_submit": "✅ Pagar e Integrar a Costos de Mano de Obra",
        "payroll_pay_success": "🎉 Pago registrado e integrado al flujo financiero de la obra.",
        "payroll_no_pending": "🎉 ¡Sin sueldos ni nóminas pendientes por liquidar!",
        "payroll_period_start": "Inicio de Periodo",
        "payroll_period_end": "Fin de Periodo",
        "payroll_hours_norm": "Horas Normales",
        "payroll_rate_norm": "Tarifa/Hora ($/hr)",
        "payroll_hours_ext": "Horas Extras",
        "payroll_rate_ext": "Tarifa/Hora Extra ($/hr)",
        "payroll_deductions": "Deducciones / Anticipos ($)",
        "payroll_total_calc": "🧮 Total Neto a Pagar:",
        "payroll_gen_submit": "💾 Generar Recibo de Nómina",
        "payroll_gen_success": "✅ Recibo de nómina generado (registrado en compromisos).",
        # Estimaciones
        "estimates_title": "📐 Estimaciones de Obra & Cobro a Clientes",
        "tab_active_estimates": "📌 Estimaciones & Registro de Cobros",
        "tab_new_estimate": "➕ Emitir Nueva Estimación",
        "estimates_kpi_net": "📐 Total Neto Facturado",
        "estimates_kpi_collected": "🟢 Total Cobrado a Clientes",
        "estimates_kpi_pending": "🔴 Saldo Pendiente por Cobrar",
        "estimates_pay_title": "💵 Registrar Cobro / Abono de Cliente",
        "estimates_select_id": "Seleccionar ID de Estimación",
        "estimates_amount_input": "Monto Abonado por Cliente ($)",
        "estimates_pay_submit": "✅ Aplicar Cobro de Estimación",
        "estimates_pay_success": "🎉 Cobro ingresado exitosamente.",
        "estimates_num": "Número de Estimación (#)",
        "estimates_concept": "Concepto / Periodo de Avance",
        "estimates_gross": "Monto Bruto Estimado ($)",
        "estimates_advance_pct": "% Amortización de Anticipo",
        "estimates_guarantee_pct": "% Fondo de Garantía",
        "estimates_net_calc": "🧮 Neto Facturable:",
        "estimates_issue_submit": "📐 Emitir Estimación",
        "estimates_issue_success": "✅ Estimación emitida exitosamente.",
        # Costos
        "costos_title": "💰 Registro & Captura Metódica de Costos",
        "lbl_select_obra": "Seleccionar Obra",
        "lbl_cat": "Categoría de Costo",
        "lbl_concept": "Concepto / Descripción del Gasto",
        "lbl_amount": "Monto Total ($)",
        "lbl_date": "Fecha del Gasto",
        "lbl_obs": "Notas / Referencia",
        "btn_save_costo": "Registrar Costo Directo",
        "msg_costo_success": "Costo registrado y reflejado en balance.",
        "costos_history": "Historial de Costos Integrados",
        "costos_categories_filter": "Categorías:",
        "costos_search": "🔎 Buscar Concepto / Usuario:",
        "costos_deleted_msg": "Registros de costos actualizados.",
        # CxP
        "cxp_title": "💳 Cuentas por Pagar (CxP)",
        "tab_active_cxp": "📌 Cuentas Pendientes",
        "tab_new_cxp": "➕ Nueva Cuenta por Pagar",
        "lbl_provider": "Proveedor / Subcontratista",
        "lbl_due": "Fecha Límite de Pago",
        "btn_save_cxp": "Crear Cuenta por Pagar",
        "msg_cxp_success": "Cuenta por pagar registrada exitosamente.",
        "btn_pay": "Aplicar Pago / Abono a Proveedor",
        "lbl_cxp_id": "ID Cuenta por Pagar",
        "lbl_pay_amount": "Monto a Abonar ($)",
        "msg_pay_success": "Abono aplicado e integrado automáticamente a los Costos de Obra.",
        # Requisiciones
        "req_title": "📋 Requisiciones de Insumos & Materiales",
        "tab_active_req": "📌 Solicitudes de Campo",
        "tab_new_req": "➕ Nueva Requisición",
        "lbl_item": "Insumo / Material",
        "lbl_qty": "Cantidad",
        "lbl_unit": "Unidad",
        "lbl_priority": "Prioridad",
        "btn_send_req": "Enviar Requisición",
        "msg_req_success": "Requisición enviada con éxito.",
        "req_status_success": "Estatus de la requisición actualizado.",
        # Usuarios
        "users_title": "👑 Control de Usuarios Maestros",
        "lbl_new_username": "Nombre de Usuario (Login)",
        "lbl_new_password": "Contraseña",
        "lbl_fullname": "Nombre Completo",
        "btn_create_user": "Dar de Alta Usuario Maestro",
        "msg_user_success": "Usuario Maestro creado con éxito.",
        "users_list": "Usuarios Registrados en el Sistema",
        "users_del_title": "Eliminar Usuario Maestro",
        "users_del_select": "Selecciona el Usuario a eliminar",
        "users_del_btn": "Eliminar Usuario",
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
        "nav_workers": "👷 Staff & Payroll",
        "nav_estimates": "📐 Project Estimates & Billing",
        "nav_costos": "💰 Cost Tracking",
        "nav_cxp": "💳 Accounts Payable",
        "nav_req": "📋 Field Requisitions",
        "nav_users": "👑 Master Users",
        "btn_logout": "Sign Out",
        "lang_selector": "🌐 Language / Idioma",
        "global_filter_title": "🎯 Global Project Filter",
        "global_filter_label": "Select Project to Filter All:",
        "all_sites": "All Projects",
        "unassigned_office": "Unassigned / Office",
        # Director
        "dir_title": "🎯 Director Operational Dashboard - Executive Overview",
        "dir_kpi_total_proj": "Active Projects",
        "dir_kpi_goal_prog": "Target Physical Progress Avg",
        "dir_kpi_real_prog": "Actual Physical Progress Avg",
        "dir_kpi_efficiency": "Overall Budget Efficiency",
        "dir_status_summary": "Project Operational Status",
        "dir_scurve_title": "S-Curve Cumulative Financial Execution",
        "dir_alerts_title": "⚠️ Budget & Operational Variance Alerts",
        # Balance
        "bal_title": "📊 Financial Dashboard & Site Performance",
        "metric_budget": "Contracted Budget",
        "metric_executed": "Actual Cost Executed",
        "metric_pending": "Pending Liabilities & Dues",
        "metric_available": "Real Margin / Available",
        "chart_cat": "Cost Breakdown by Category",
        "chart_comp": "Budget vs Actual Cost per Project",
        # Obras
        "obras_title": "🏗️ Project Control & GPS Locations",
        "tab_map": "MAP & Interactive Editor",
        "tab_new_obra": "➕ Register New Project",
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
        "obras_filter_status": "Filter by Status:",
        "obras_search": "🔎 Search Project by Name, Client or Code:",
        "obras_edit_title": "✏️ Interactive Project & Progress Editor",
        "obras_edit_save": "Save Changes",
        "obras_edit_success": "✅ Projects updated successfully!",
        # Personal & Nómina
        "workers_title": "👷 Integrated Staff & Hourly Payroll Management",
        "tab_workers_list": "📌 Staff Directory & Editor",
        "tab_new_worker": "➕ Register Worker",
        "tab_payroll": "💵 Hourly Payroll & Overtime Control",
        "lbl_worker_name": "Worker Full Name",
        "lbl_position": "Role / Specialty",
        "lbl_phone": "Phone Number",
        "lbl_assign_obra": "Assign to Site",
        "btn_save_worker": "Register Worker",
        "msg_worker_success": "Worker registered successfully.",
        "workers_hourly_rate": "Hourly Rate ($/hr)",
        "workers_daily_wage": "Daily Wage ($/day)",
        "workers_pay_mode": "Payment Mode",
        "workers_filter_site": "Filter by Project:",
        "workers_filter_status": "Worker Status:",
        "workers_search": "🔎 Search Worker or Position:",
        "workers_save_changes": "Save Record Changes",
        "workers_updated_msg": "Worker record updated successfully.",
        "workers_select": "Select Worker",
        "payroll_kpi_pending": "🔴 Outstanding Wages Due",
        "payroll_kpi_paid": "🟢 Total Settled Payroll",
        "payroll_pay_title": "💸 Settle Worker Payroll Dues",
        "payroll_select_id": "Select Payroll ID",
        "payroll_pay_submit": "✅ Pay & Load to Site Labor Cost",
        "payroll_pay_success": "🎉 Payment recorded and loaded into site financial flow.",
        "payroll_no_pending": "🎉 No pending payroll or wages to settle!",
        "payroll_period_start": "Period Start Date",
        "payroll_period_end": "Period End Date",
        "payroll_hours_norm": "Regular Hours",
        "payroll_rate_norm": "Regular Rate ($/hr)",
        "payroll_hours_ext": "Overtime Hours",
        "payroll_rate_ext": "Overtime Rate ($/hr)",
        "payroll_deductions": "Deductions / Advances ($)",
        "payroll_total_calc": "🧮 Total Net Payable:",
        "payroll_gen_submit": "💾 Generate Payroll Stub",
        "payroll_gen_success": "✅ Payroll stub generated (recorded under liabilities).",
        # Estimaciones
        "estimates_title": "📐 Project Progress Estimates & Client Invoicing",
        "tab_active_estimates": "📌 Estimates & Collections",
        "tab_new_estimate": "➕ Issue New Estimate",
        "estimates_kpi_net": "📐 Total Net Billed",
        "estimates_kpi_collected": "🟢 Total Collected from Clients",
        "estimates_kpi_pending": "🔴 Outstanding Balance to Collect",
        "estimates_pay_title": "💵 Record Client Collection",
        "estimates_select_id": "Select Estimate ID",
        "estimates_amount_input": "Amount Paid by Client ($)",
        "estimates_pay_submit": "✅ Apply Collection",
        "estimates_pay_success": "🎉 Payment collected successfully.",
        "estimates_num": "Estimate Number (#)",
        "estimates_concept": "Estimate Concept / Period",
        "estimates_gross": "Gross Estimated Amount ($)",
        "estimates_advance_pct": "% Advance Downpayment Amortization",
        "estimates_guarantee_pct": "% Guarantee Retainage",
        "estimates_net_calc": "🧮 Net Collectible Invoice Amount:",
        "estimates_issue_submit": "📐 Issue Estimate",
        "estimates_issue_success": "✅ Estimate issued successfully.",
        # Costos
        "costos_title": "💰 Systematic Cost Tracking",
        "lbl_select_obra": "Select Project",
        "lbl_cat": "Cost Category",
        "lbl_concept": "Concept / Expense Description",
        "lbl_amount": "Total Amount ($)",
        "lbl_date": "Expense Date",
        "lbl_obs": "Notes / Ref",
        "btn_save_costo": "Register Direct Expense",
        "msg_costo_success": "Expense registered and updated on balance.",
        "costos_history": "Integrated Expense Log",
        "costos_categories_filter": "Categories:",
        "costos_search": "🔎 Search Concept / User:",
        "costos_deleted_msg": "Cost entries updated.",
        # CxP
        "cxp_title": "💳 Accounts Payable (AP)",
        "tab_active_cxp": "📌 Pending Accounts",
        "tab_new_cxp": "➕ New Payable Account",
        "lbl_provider": "Vendor / Subcontractor",
        "lbl_due": "Due Date",
        "btn_save_cxp": "Create Payable Account",
        "msg_cxp_success": "Payable account created successfully.",
        "btn_pay": "Apply Vendor Payment",
        "lbl_cxp_id": "AP Account ID",
        "lbl_pay_amount": "Amount to Pay ($)",
        "msg_pay_success": "Payment applied and automatically integrated into Site Costs.",
        # Requisiciones
        "req_title": "📋 Field Requisitions & Supplies",
        "tab_active_req": "📌 Field Requests",
        "tab_new_req": "➕ New Requisition",
        "lbl_item": "Material / Supply Needed",
        "lbl_qty": "Quantity",
        "lbl_unit": "Unit",
        "lbl_priority": "Priority Level",
        "btn_send_req": "Submit Requisition",
        "msg_req_success": "Requisition submitted successfully.",
        "req_status_success": "Requisition status updated.",
        # Usuarios
        "users_title": "👑 Master User Access Control",
        "lbl_new_username": "Username",
        "lbl_new_password": "Password",
        "lbl_fullname": "Full Name",
        "btn_create_user": "Register Master User",
        "msg_user_success": "Master User registered successfully.",
        "users_list": "Registered System Users",
        "users_del_title": "Delete Master User",
        "users_del_select": "Select User to delete",
        "users_del_btn": "Delete User",
    },
}

class SafeDict:
    def __init__(self, lang):
        self.lang = lang
    def __getitem__(self, key):
        lang_dict = TEXTS.get(self.lang, TEXTS["ES"])
        if key in lang_dict:
            return lang_dict[key]
        if key in TEXTS["ES"]:
            return TEXTS["ES"][key]
        return key

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
        ensure_columns(c, "usuarios", {
            "username": "TEXT DEFAULT ''",
            "password": "TEXT DEFAULT ''",
            "nombre_completo": "TEXT DEFAULT ''",
            "rol": "TEXT DEFAULT 'Usuario Maestro'",
        })

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
        ensure_columns(c, "proyectos", {
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
        })

        # 3. Trabajadores
        c.execute("""
            CREATE TABLE IF NOT EXISTS trabajadores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_completo TEXT NOT NULL,
                puesto TEXT NOT NULL,
                telefono TEXT,
                proyecto_id INTEGER,
                salario_diario REAL DEFAULT 0.0,
                tarifa_hora REAL DEFAULT 0.0,
                tipo_pago TEXT DEFAULT 'Por Hora',
                estatus TEXT DEFAULT 'Activo',
                fecha_registro DATE DEFAULT CURRENT_DATE,
                FOREIGN KEY (proyecto_id) REFERENCES proyectos (id)
            )
        """)
        ensure_columns(c, "trabajadores", {
            "nombre_completo": "TEXT DEFAULT ''",
            "puesto": "TEXT DEFAULT ''",
            "telefono": "TEXT DEFAULT ''",
            "proyecto_id": "INTEGER",
            "salario_diario": "REAL DEFAULT 0.0",
            "tarifa_hora": "REAL DEFAULT 0.0",
            "tipo_pago": "TEXT DEFAULT 'Por Hora'",
            "estatus": "TEXT DEFAULT 'Activo'",
            "fecha_registro": "DATE DEFAULT CURRENT_DATE",
        })

        # 4. Nóminas
        c.execute("""
            CREATE TABLE IF NOT EXISTS nominas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trabajador_id INTEGER,
                proyecto_id INTEGER,
                periodo_inicio DATE,
                periodo_fin DATE,
                horas_trabajadas REAL DEFAULT 0.0,
                horas_extras REAL DEFAULT 0.0,
                tarifa_hora REAL DEFAULT 0.0,
                monto_base REAL DEFAULT 0.0,
                bonos_extras REAL DEFAULT 0.0,
                descuentos REAL DEFAULT 0.0,
                monto_neto REAL DEFAULT 0.0,
                estatus TEXT DEFAULT 'Pendiente',
                fecha_pago DATE,
                registrado_por TEXT,
                FOREIGN KEY (trabajador_id) REFERENCES trabajadores (id),
                FOREIGN KEY (proyecto_id) REFERENCES proyectos (id)
            )
        """)
        ensure_columns(c, "nominas", {
            "trabajador_id": "INTEGER",
            "proyecto_id": "INTEGER",
            "periodo_inicio": "DATE",
            "periodo_fin": "DATE",
            "horas_trabajadas": "REAL DEFAULT 0.0",
            "horas_extras": "REAL DEFAULT 0.0",
            "tarifa_hora": "REAL DEFAULT 0.0",
            "monto_base": "REAL DEFAULT 0.0",
            "bonos_extras": "REAL DEFAULT 0.0",
            "descuentos": "REAL DEFAULT 0.0",
            "monto_neto": "REAL DEFAULT 0.0",
            "estatus": "TEXT DEFAULT 'Pendiente'",
            "fecha_pago": "DATE",
            "registrado_por": "TEXT DEFAULT ''",
        })

        # 5. Estimaciones
        c.execute("""
            CREATE TABLE IF NOT EXISTS estimaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proyecto_id INTEGER,
                numero_estimacion INTEGER NOT NULL,
                concepto_periodo TEXT NOT NULL,
                monto_estimado REAL NOT NULL,
                amortizacion_anticipo REAL DEFAULT 0.0,
                retencion_garantia REAL DEFAULT 0.0,
                monto_neto_cobrar REAL NOT NULL,
                monto_cobrado REAL DEFAULT 0.0,
                estatus TEXT DEFAULT 'Pendiente',
                fecha_emision DATE DEFAULT CURRENT_DATE,
                fecha_cobro DATE,
                registrado_por TEXT NOT NULL,
                FOREIGN KEY (proyecto_id) REFERENCES proyectos (id)
            )
        """)
        ensure_columns(c, "estimaciones", {
            "proyecto_id": "INTEGER",
            "numero_estimacion": "INTEGER DEFAULT 1",
            "concepto_periodo": "TEXT DEFAULT ''",
            "monto_estimado": "REAL DEFAULT 0.0",
            "amortizacion_anticipo": "REAL DEFAULT 0.0",
            "retencion_garantia": "REAL DEFAULT 0.0",
            "monto_neto_cobrar": "REAL DEFAULT 0.0",
            "monto_cobrado": "REAL DEFAULT 0.0",
            "estatus": "TEXT DEFAULT 'Pendiente'",
            "fecha_emision": "DATE DEFAULT CURRENT_DATE",
            "fecha_cobro": "DATE",
            "registrado_por": "TEXT DEFAULT ''",
        })

        # 6. Costos
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
        ensure_columns(c, "costos", {
            "proyecto_id": "INTEGER",
            "categoria": "TEXT DEFAULT ''",
            "concepto": "TEXT DEFAULT ''",
            "monto": "REAL DEFAULT 0.0",
            "fecha": "DATE DEFAULT CURRENT_DATE",
            "registrado_por": "TEXT DEFAULT ''",
            "observaciones": "TEXT DEFAULT ''",
        })

        # 7. Cuentas por pagar
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
        ensure_columns(c, "cuentas_por_pagar", {
            "proyecto_id": "INTEGER",
            "proveedor": "TEXT DEFAULT ''",
            "concepto": "TEXT DEFAULT ''",
            "monto_total": "REAL DEFAULT 0.0",
            "monto_pagado": "REAL DEFAULT 0.0",
            "estatus": "TEXT DEFAULT 'Pendiente'",
            "fecha_vencimiento": "DATE",
            "registrado_por": "TEXT DEFAULT ''",
        })

        # 8. Requisiciones
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
        ensure_columns(c, "requisiciones", {
            "proyecto_id": "INTEGER",
            "insumo": "TEXT DEFAULT ''",
            "cantidad": "REAL DEFAULT 0.0",
            "unidad": "TEXT DEFAULT ''",
            "prioridad": "TEXT DEFAULT 'Normal'",
            "solicitado_por": "TEXT DEFAULT ''",
            "estatus": "TEXT DEFAULT 'Pendiente'",
            "fecha": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        })

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
def get_nominas_df(proyecto_id=None):
    with sqlite3.connect(DB_PATH) as conn:
        if proyecto_id:
            return pd.read_sql_query(
                "SELECT n.*, t.nombre_completo as trabajador, t.puesto, t.telefono, p.nombre as proyecto FROM nominas n JOIN trabajadores t ON n.trabajador_id = t.id LEFT JOIN proyectos p ON n.proyecto_id = p.id WHERE n.proyecto_id = ? ORDER BY n.id DESC",
                conn, params=(proyecto_id,)
            )
        return pd.read_sql_query(
            "SELECT n.*, t.nombre_completo as trabajador, t.puesto, t.telefono, coalesce(p.nombre, 'Sin Asignar / Oficina') as proyecto FROM nominas n JOIN trabajadores t ON n.trabajador_id = t.id LEFT JOIN proyectos p ON n.proyecto_id = p.id ORDER BY n.id DESC",
            conn,
        )

@st.cache_data(ttl=60)
def get_estimaciones_df(proyecto_id=None):
    with sqlite3.connect(DB_PATH) as conn:
        if proyecto_id:
            return pd.read_sql_query(
                "SELECT e.*, p.nombre as proyecto, p.cliente FROM estimaciones e JOIN proyectos p ON e.proyecto_id = p.id WHERE e.proyecto_id = ? ORDER BY e.id DESC",
                conn, params=(proyecto_id,)
            )
        return pd.read_sql_query(
            "SELECT e.*, p.nombre as proyecto, p.cliente FROM estimaciones e JOIN proyectos p ON e.proyecto_id = p.id ORDER BY e.id DESC",
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

t = SafeDict(st.session_state["lang"])

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
    t["nav_estimates"],
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

st.sidebar.markdown(f"### {t['global_filter_title']}")
global_obra_sel = st.sidebar.selectbox(
    t["global_filter_label"],
    [t["all_sites"]] + list(proyectos_dict_global.keys()),
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
    
    if global_obra_sel != t["all_sites"]:
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
# 1. BALANCE FINANCIERO INTEGRADO
# ==========================================
elif menu_sel == t["nav_balance"]:
    st.markdown(f"<div class='main-header'>{t['bal_title']}</div>", unsafe_allow_html=True)

    proyectos_df = get_proyectos_df()
    
    if global_obra_sel != t["all_sites"]:
        proyectos_df = proyectos_df[proyectos_df['nombre'] == global_obra_sel]
        selected_p_id = proyectos_dict_global.get(global_obra_sel)
        costos_df = get_costos_df(selected_p_id)
        cxp_df = get_cxp_df(selected_p_id)
        nominas_df = get_nominas_df(selected_p_id)
    else:
        costos_df = get_costos_df()
        cxp_df = get_cxp_df()
        nominas_df = get_nominas_df()

    if proyectos_df.empty:
        st.info("Sin proyectos registrados aún en la base de datos o que coincidan con la búsqueda.")
    else:
        presupuesto_total = proyectos_df["presupuesto_total"].sum()
        costo_total_ejecutado = costos_df["monto"].sum() if not costos_df.empty else 0
        
        cxp_pendientes_val = (cxp_df["monto_total"] - cxp_df["monto_pagado"]).sum() if not cxp_df.empty else 0
        nominas_pendientes_val = nominas_df[nominas_df['estatus'] == 'Pendiente']['monto_neto'].sum() if not nominas_df.empty else 0
        
        pasivos_compromisos_total = cxp_pendientes_val + nominas_pendientes_val
        balance_disponible_real = presupuesto_total - costo_total_ejecutado - pasivos_compromisos_total

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(t["metric_budget"], f"${presupuesto_total:,.2f}")
        c2.metric(
            t["metric_executed"],
            f"${costo_total_ejecutado:,.2f}",
            delta=f"-{(costo_total_ejecutado/presupuesto_total*100) if presupuesto_total>0 else 0:.1f}%",
            delta_color="inverse",
        )
        c3.metric(t["metric_pending"], f"${pasivos_compromisos_total:,.2f}", help="Incluye Cuentas por Pagar a Proveedores + Nóminas Pendientes de Pago")
        c4.metric(
            t["metric_available"],
            f"${balance_disponible_real:,.2f}",
            delta=f"{(balance_disponible_real/presupuesto_total*100) if presupuesto_total>0 else 0:.1f}%",
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
                    go.Bar(name="Ejecutado Real", x=df_comp["nombre"], y=df_comp["monto"], marker_color="#EF4444"),
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
# 2. OBRAS & MAPA CON EDITOR DE TABLA
# ==========================================
elif menu_sel == t["nav_obras"]:
    st.markdown(f"<div class='main-header'>{t['obras_title']}</div>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs([
        t["tab_map"],
        t["tab_new_obra"],
    ])

    with tab1:
        st.subheader("🔍 " + t["obras_filter_status"])
        f_col1, f_col2 = st.columns([1, 2])
        with f_col1:
            filtro_estatus_obra = st.multiselect(
                t["obras_filter_status"],
                ["En Proceso", "Pausado", "Concluido", "Cancelado"],
                default=["En Proceso", "Pausado", "Concluido"]
            )
        with f_col2:
            buscar_obra = st.text_input(t["obras_search"], "")

        df_obras = get_proyectos_df()
        
        if not df_obras.empty:
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

            st.markdown("---")
            st.markdown("### 📝 " + t["obras_edit_title"])
            
            edited_obras = st.data_editor(
                df_obras[["id", "codigo", "nombre", "cliente", "presupuesto_total", "avance_meta", "avance_real", "estado", "calle", "ciudad"]],
                column_config={
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "codigo": st.column_config.TextColumn("Código"),
                    "presupuesto_total": st.column_config.NumberColumn("Presupuesto ($)", format="$%,.2f"),
                    "avance_meta": st.column_config.NumberColumn("Meta %", format="%.1f%%", min_value=0.0, max_value=100.0),
                    "avance_real": st.column_config.NumberColumn("Real %", format="%.1f%%", min_value=0.0, max_value=100.0),
                    "estado": st.column_config.SelectboxColumn("Estatus", options=["En Proceso", "Pausado", "Concluido", "Cancelado"]),
                },
                num_rows="dynamic",
                use_container_width=True,
                key="editor_obras_key"
            )

            if st.button("💾 " + t["obras_edit_save"]):
                with sqlite3.connect(DB_PATH) as conn:
                    c = conn.cursor()
                    ids_actuales = edited_obras['id'].dropna().tolist() if 'id' in edited_obras.columns else []
                    ids_originales = df_obras['id'].tolist()
                    ids_a_borrar = set(ids_originales) - set(ids_actuales)
                    
                    for id_b in ids_a_borrar:
                        c.execute("UPDATE trabajadores SET proyecto_id = NULL WHERE proyecto_id = ?", (id_b,))
                        c.execute("DELETE FROM costos WHERE proyecto_id = ?", (id_b,))
                        c.execute("DELETE FROM cuentas_por_pagar WHERE proyecto_id = ?", (id_b,))
                        c.execute("DELETE FROM requisiciones WHERE proyecto_id = ?", (id_b,))
                        c.execute("DELETE FROM estimaciones WHERE proyecto_id = ?", (id_b,))
                        c.execute("DELETE FROM nominas WHERE proyecto_id = ?", (id_b,))
                        c.execute("DELETE FROM proyectos WHERE id = ?", (id_b,))

                    for _, row in edited_obras.iterrows():
                        if pd.notna(row['id']):
                            c.execute(
                                "UPDATE proyectos SET codigo=?, nombre=?, cliente=?, presupuesto_total=?, avance_meta=?, avance_real=?, estado=?, calle=?, ciudad=? WHERE id=?",
                                (row['codigo'], row['nombre'], row['cliente'], row['presupuesto_total'], row['avance_meta'], row['avance_real'], row['estado'], row['calle'], row['ciudad'], int(row['id']))
                            )
                    conn.commit()
                clear_data_cache()
                st.success(t["obras_edit_success"])
                st.rerun()

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

# ==========================================
# 3. PERSONAL & NÓMINA INTEGRADA (CON EXPORTACIÓN)
# ==========================================
elif menu_sel == t["nav_workers"]:
    st.markdown(f"<div class='main-header'>{t['workers_title']}</div>", unsafe_allow_html=True)

    proyectos_df = get_proyectos_df()
    proyectos_dict = dict(zip(proyectos_df["nombre"], proyectos_df["id"])) if not proyectos_df.empty else {}

    tab1, tab2, tab3 = st.tabs([t["tab_workers_list"], t["tab_payroll"], t["tab_new_worker"]])

    # --- PESTAÑA 1: DIRECTORIO DE PERSONAL ---
    with tab1:
        st.subheader("🔍 " + t["workers_filter_site"])
        col_wf1, col_wf2, col_wf3 = st.columns([1, 1, 1.5])
        
        with col_wf1:
            filtro_obra_worker = st.selectbox(
                t["workers_filter_site"],
                [t["all_sites"]] + list(proyectos_dict.keys()),
                index=0 if global_obra_sel == t["all_sites"] else (list(proyectos_dict.keys()).index(global_obra_sel) + 1 if global_obra_sel in proyectos_dict else 0)
            )
        with col_wf2:
            filtro_estatus_worker = st.selectbox(t["workers_filter_status"], ["Todos", "Activo", "Inactivo"])
        with col_wf3:
            buscar_worker = st.text_input(t["workers_search"], "")

        trabajadores_df = get_trabajadores_df()

        if not trabajadores_df.empty:
            df_mostrar = trabajadores_df.copy()
            if filtro_obra_worker != t["all_sites"]:
                df_mostrar = df_mostrar[df_mostrar["proyecto"] == filtro_obra_worker]
            if filtro_estatus_worker != "Todos":
                df_mostrar = df_mostrar[df_mostrar["estatus"] == filtro_estatus_worker]
            if buscar_worker:
                term_w = buscar_worker.lower()
                df_mostrar = df_mostrar[
                    df_mostrar["nombre_completo"].str.lower().str.contains(term_w) |
                    df_mostrar["puesto"].str.lower().str.contains(term_w)
                ]

            st.markdown("### 📝 Editor Directo de Personal")
            edited_workers = st.data_editor(
                df_mostrar[["id", "nombre_completo", "puesto", "tarifa_hora", "salario_diario", "tipo_pago", "telefono", "estatus"]],
                column_config={
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "nombre_completo": st.column_config.TextColumn("Trabajador"),
                    "puesto": st.column_config.TextColumn("Puesto / Especialidad"),
                    "tarifa_hora": st.column_config.NumberColumn("Pago por Hora ($/hr)", format="$%,.2f"),
                    "salario_diario": st.column_config.NumberColumn("Sueldo Diario ($/día)", format="$%,.2f"),
                    "tipo_pago": st.column_config.SelectboxColumn("Modalidad", options=["Por Hora", "Semanal", "Diario", "Destajo / Proyecto", "Quincenal"]),
                    "estatus": st.column_config.SelectboxColumn("Estatus", options=["Activo", "Inactivo"]),
                },
                num_rows="dynamic",
                use_container_width=True,
                key="editor_workers_key"
            )

            if st.button("💾 " + t["workers_save_changes"]):
                with sqlite3.connect(DB_PATH) as conn:
                    c = conn.cursor()
                    ids_act = edited_workers['id'].dropna().tolist() if 'id' in edited_workers.columns else []
                    ids_orig = df_mostrar['id'].tolist()
                    ids_del = set(ids_orig) - set(ids_act)

                    for id_d in ids_del:
                        c.execute("DELETE FROM nominas WHERE trabajador_id = ?", (id_d,))
                        c.execute("DELETE FROM trabajadores WHERE id = ?", (id_d,))

                    for _, row in edited_workers.iterrows():
                        if pd.notna(row['id']):
                            c.execute(
                                "UPDATE trabajadores SET nombre_completo=?, puesto=?, tarifa_hora=?, salario_diario=?, tipo_pago=?, telefono=?, estatus=? WHERE id=?",
                                (row['nombre_completo'], row['puesto'], row['tarifa_hora'], row['salario_diario'], row['tipo_pago'], row['telefono'], row['estatus'], int(row['id']))
                            )
                    conn.commit()
                clear_data_cache()
                st.success(t["workers_updated_msg"])
                st.rerun()
        else:
            st.info("No hay trabajadores registrados en la base de datos.")

    # --- PESTAÑA 2: CONTROL DE NÓMINA & EXPORTACIÓN ---
    with tab2:
        st.subheader(t["payroll_title"])
        
        col_n1, col_n2 = st.columns([1.2, 1])

        with col_n1:
            st.markdown("### ➕ Calcular & Generar Recibo por Horas")
            if trabajadores_df.empty:
                st.warning("Registra trabajadores primero.")
            else:
                with st.form("form_nueva_nomina_int"):
                    trab_dict_nom = dict(zip(trabajadores_df['nombre_completo'] + " - " + trabajadores_df['puesto'], trabajadores_df['id']))
                    w_sel_nom = st.selectbox(t["workers_select"], list(trab_dict_nom.keys()))
                    trab_id_nom = trab_dict_nom[w_sel_nom]
                    trab_row_nom = trabajadores_df[trabajadores_df['id'] == trab_id_nom].iloc[0]

                    st.info(f"💡 **Tarifa Base:** `${trab_row_nom['tarifa_hora']:,.2f} / hr` | **Obra:** `{trab_row_nom['proyecto']}`")

                    c_n1, c_n2 = st.columns(2)
                    with c_n1:
                        p_inicio = st.date_input(t["payroll_period_start"], datetime.now())
                        p_fin = st.date_input(t["payroll_period_end"], datetime.now())
                        horas_trab = st.number_input(t["payroll_hours_norm"], min_value=0.0, value=40.0, step=1.0)
                        tarifa_hora_val = st.number_input(t["payroll_rate_norm"], min_value=0.0, value=float(trab_row_nom['tarifa_hora'] if trab_row_nom['tarifa_hora'] > 0 else 65.0), step=5.0)

                    with c_n2:
                        horas_ext = st.number_input(t["payroll_hours_ext"], min_value=0.0, value=0.0, step=0.5)
                        tarifa_extra_val = st.number_input(t["payroll_rate_ext"], min_value=0.0, value=float(tarifa_hora_val * 1.5), step=5.0)
                        descuentos_val = st.number_input(t["payroll_deductions"], min_value=0.0, value=0.0, step=50.0)

                    monto_base_calc = horas_trab * tarifa_hora_val
                    monto_extras_calc = horas_ext * tarifa_extra_val
                    monto_neto_calc = monto_base_calc + monto_extras_calc - descuentos_val
                    
                    st.markdown(f"#### {t['payroll_total_calc']} **${monto_neto_calc:,.2f}**")

                    if st.form_submit_button(t["payroll_gen_submit"]):
                        try:
                            with sqlite3.connect(DB_PATH) as conn:
                                c = conn.cursor()
                                c.execute(
                                    "INSERT INTO nominas (trabajador_id, proyecto_id, periodo_inicio, periodo_fin, horas_trabajadas, horas_extras, tarifa_hora, monto_base, bonos_extras, descuentos, monto_neto, registrado_por) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                    (trab_id_nom, trab_row_nom['proyecto_id'], p_inicio, p_fin, horas_trab, horas_ext, tarifa_hora_val, monto_base_calc, monto_extras_calc, descuentos_val, monto_neto_calc, user['nombre'])
                                )
                                conn.commit()
                            clear_data_cache()
                            st.success(t["payroll_gen_success"])
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

        with col_n2:
            st.markdown("### 📌 Adeudos & Liquidación de Nómina")
            nominas_df = get_nominas_df()

            if not nominas_df.empty:
                df_nom_filtrada = nominas_df.copy()
                if global_obra_sel != t["all_sites"]:
                    df_nom_filtrada = df_nom_filtrada[df_nom_filtrada['proyecto'] == global_obra_sel]

                pendientes_nom = df_nom_filtrada[df_nom_filtrada['estatus'] == 'Pendiente']

                if not pendientes_nom.empty:
                    with st.form("form_pagar_nomina_int"):
                        nom_id_sel = st.selectbox(t["payroll_select_id"], pendientes_nom['id'].tolist())
                        row_nom = pendientes_nom[pendientes_nom['id'] == nom_id_sel].iloc[0]
                        
                        st.warning(f"💵 **{row_nom['trabajador']}** | Obra: **{row_nom['proyecto']}**\n\nNeto a Liquidar: **${row_nom['monto_neto']:,.2f}**")
                        
                        if st.form_submit_button(t["payroll_pay_submit"]):
                            with sqlite3.connect(DB_PATH) as conn:
                                c = conn.cursor()
                                c.execute("UPDATE nominas SET estatus = 'Pagado', fecha_pago = CURRENT_DATE WHERE id = ?", (nom_id_sel,))
                                if row_nom['proyecto_id']:
                                    c.execute(
                                        "INSERT INTO costos (proyecto_id, categoria, concepto, monto, fecha, registrado_por, observaciones) VALUES (?, ?, ?, ?, CURRENT_DATE, ?, ?)",
                                        (
                                            row_nom['proyecto_id'],
                                            "Mano de Obra / Labor",
                                            f"Pago Nómina #{nom_id_sel}: {row_nom['trabajador']} ({row_nom['horas_trabajadas']} hrs)",
                                            row_nom['monto_neto'],
                                            user['nombre'],
                                            f"Pago Nómina Ref #{nom_id_sel}"
                                        )
                                    )
                                conn.commit()
                            clear_data_cache()
                            st.success(t["payroll_pay_success"])
                            st.rerun()
                else:
                    st.success(t["payroll_no_pending"])

                st.markdown("---")
                st.markdown("##### 📄 Exportar Recibo PDF / Enviar por WhatsApp")
                nom_pdf_sel = st.selectbox("Selecciona Recibo de Nómina", nominas_df['id'].tolist())
                row_pdf_nom = nominas_df[nominas_df['id'] == nom_pdf_sel].iloc[0]
                
                pdf_bytes_nom = generar_pdf_recibo_bytes(row_pdf_nom)
                
                c_e1, c_e2 = st.columns(2)
                with c_e1:
                    st.download_button(
                        label="📄 Descargar Recibo PDF",
                        data=pdf_bytes_nom,
                        file_name=f"Recibo_Nomina_{row_pdf_nom['trabajador']}_{row_pdf_nom['id']}.pdf",
                        mime="application/pdf"
                    )
                with c_e2:
                    msg_wa = urllib.parse.quote(f"Hola {row_pdf_nom['trabajador']}, tu recibo de nómina ID #{row_pdf_nom['id']} por un monto de ${row_pdf_nom['monto_neto']:,.2f} ha sido procesado.")
                    tel_clean = str(row_pdf_nom['telefono']).replace(" ", "").replace("-", "") if pd.notna(row_pdf_nom['telefono']) else ""
                    wa_url = f"https://api.whatsapp.com/send?phone={tel_clean}&text={msg_wa}"
                    st.markdown(f"[📱 Enviar por WhatsApp]({wa_url})", unsafe_allow_html=True)

            else:
                st.info("No hay registros de nómina.")

    # --- PESTAÑA 3: NUEVO TRABAJADOR ---
    with tab3:
        with st.form("form_nuevo_trabajador"):
            c_tw1, c_tw2 = st.columns(2)
            with c_tw1:
                w_nombre = st.text_input(t["lbl_worker_name"])
                w_puesto = st.text_input(t["lbl_position"])
                w_telefono = st.text_input(t["lbl_phone"])
            with c_tw2:
                w_tarifa_hora = st.number_input(t["workers_hourly_rate"], min_value=0.0, value=65.0, step=5.0)
                w_salario_diario = st.number_input(t["workers_daily_wage"], min_value=0.0, value=520.0, step=50.0)
                w_tipo_pago = st.selectbox(t["workers_pay_mode"], ["Por Hora", "Semanal", "Diario", "Destajo / Proyecto", "Quincenal"])
                opciones_obra = [t["unassigned_office"]] + list(proyectos_dict.keys())
                w_obra = st.selectbox(t["lbl_assign_obra"], opciones_obra)

            if st.form_submit_button(t["btn_save_worker"]):
                if w_nombre and w_puesto:
                    obra_id_val = proyectos_dict[w_obra] if w_obra != t["unassigned_office"] else None
                    try:
                        with sqlite3.connect(DB_PATH) as conn:
                            c = conn.cursor()
                            c.execute(
                                "INSERT INTO trabajadores (nombre_completo, puesto, telefono, proyecto_id, tarifa_hora, salario_diario, tipo_pago) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (w_nombre, w_puesto, w_telefono, obra_id_val, w_tarifa_hora, w_salario_diario, w_tipo_pago),
                            )
                            conn.commit()
                        clear_data_cache()
                        st.success(t["msg_worker_success"])
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

# ==========================================
# 4. ESTIMACIONES & CLIENTES (CON PDF & CORREO)
# ==========================================
elif menu_sel == t["nav_estimates"]:
    st.markdown(f"<div class='main-header'>{t['estimates_title']}</div>", unsafe_allow_html=True)

    proyectos_df = get_proyectos_df()
    if proyectos_df.empty:
        st.warning("Registra un proyecto u obra primero.")
    else:
        proyectos_dict = dict(zip(proyectos_df["nombre"], proyectos_df["id"]))
        tab1, tab2 = st.tabs([t["tab_active_estimates"], t["tab_new_estimate"]])

        with tab1:
            estimaciones_df = get_estimaciones_df()

            if not estimaciones_df.empty:
                df_est_filtrada = estimaciones_df.copy()
                if global_obra_sel != t["all_sites"]:
                    df_est_filtrada = df_est_filtrada[df_est_filtrada['proyecto'] == global_obra_sel]

                total_cobrar_neto = df_est_filtrada['monto_neto_cobrar'].sum()
                total_cobrado_cliente = df_est_filtrada['monto_cobrado'].sum()
                saldo_pendiente_cliente = total_cobrar_neto - total_cobrado_cliente

                ek1, ek2, ek3 = st.columns(3)
                ek1.metric(t["estimates_kpi_net"], f"${total_cobrar_neto:,.2f}")
                ek2.metric(t["estimates_kpi_collected"], f"${total_cobrado_cliente:,.2f}")
                ek3.metric(t["estimates_kpi_pending"], f"${saldo_pendiente_cliente:,.2f}")

                st.markdown("---")
                st.markdown("### 📝 Tabla Editora de Estimaciones")
                edited_est = st.data_editor(
                    df_est_filtrada[["id", "numero_estimacion", "proyecto", "cliente", "concepto_periodo", "monto_estimado", "monto_neto_cobrar", "monto_cobrado", "estatus"]],
                    column_config={
                        "id": st.column_config.NumberColumn("ID", disabled=True),
                        "monto_estimado": st.column_config.NumberColumn("Monto Bruto ($)", format="$%,.2f"),
                        "monto_neto_cobrar": st.column_config.NumberColumn("Neto a Cobrar ($)", format="$%,.2f"),
                        "monto_cobrado": st.column_config.NumberColumn("Cobrado ($)", format="$%,.2f"),
                        "estatus": st.column_config.SelectboxColumn("Estatus", options=["Pendiente", "Cobrado Parcial", "Cobrado"]),
                    },
                    num_rows="dynamic",
                    use_container_width=True,
                    key="editor_estimates_key"
                )

                if st.button("💾 " + t["obras_edit_save"], key="btn_save_est_editor"):
                    with sqlite3.connect(DB_PATH) as conn:
                        c = conn.cursor()
                        ids_act = edited_est['id'].dropna().tolist() if 'id' in edited_est.columns else []
                        ids_orig = df_est_filtrada['id'].tolist()
                        ids_del = set(ids_orig) - set(ids_act)

                        for id_d in ids_del:
                            c.execute("DELETE FROM estimaciones WHERE id = ?", (id_d,))

                        for _, row in edited_est.iterrows():
                            if pd.notna(row['id']):
                                c.execute(
                                    "UPDATE estimaciones SET numero_estimacion=?, concepto_periodo=?, monto_estimado=?, monto_neto_cobrar=?, monto_cobrado=?, estatus=? WHERE id=?",
                                    (row['numero_estimacion'], row['concepto_periodo'], row['monto_estimado'], row['monto_neto_cobrar'], row['monto_cobrado'], row['estatus'], int(row['id']))
                                )
                        conn.commit()
                    clear_data_cache()
                    st.success("✅ ¡Estimaciones actualizadas correctamente!")
                    st.rerun()

                st.markdown("---")
                st.markdown("##### 📄 Exportar Estimación PDF / Enviar por Correo a Cliente")
                est_pdf_sel = st.selectbox("Selecciona Estimación", estimaciones_df['id'].tolist())
                row_pdf_est = estimaciones_df[estimaciones_df['id'] == est_pdf_sel].iloc[0]
                
                pdf_bytes_est = generar_pdf_estimacion_bytes(row_pdf_est)
                
                ce_1, ce_2 = st.columns(2)
                with ce_1:
                    st.download_button(
                        label="📄 Descargar Estimación PDF",
                        data=pdf_bytes_est,
                        file_name=f"Estimacion_No{row_pdf_est['numero_estimacion']}_{row_pdf_est['proyecto']}.pdf",
                        mime="application/pdf"
                    )
                with ce_2:
                    email_dest = st.text_input("Correo del Cliente:", value="")
                    if st.button("📧 Enviar PDF por Correo"):
                        if email_dest:
                            asunto_mail = f"Estimación #{row_pdf_est['numero_estimacion']} - {row_pdf_est['proyecto']}"
                            cuerpo_mail = f"Estimado cliente {row_pdf_est['cliente']},\n\nAdjunto encontrará la estimación de obra #{row_pdf_est['numero_estimacion']} correspondiente a {row_pdf_est['concepto_periodo']} por un total neto de ${row_pdf_est['monto_neto_cobrar']:,.2f}.\n\nSaludos cordiales,\nRattlesnake System."
                            exito, msg_mail = enviar_correo_con_pdf(email_dest, asunto_mail, cuerpo_mail, pdf_bytes_est, f"Estimacion_{row_pdf_est['numero_estimacion']}.pdf")
                            if exito:
                                st.success(msg_mail)
                            else:
                                st.warning(msg_mail)
                        else:
                            st.warning("Escribe el correo del cliente.")

                st.markdown("---")
                st.subheader(t["estimates_pay_title"])
                pendientes_cobro = df_est_filtrada[df_est_filtrada['monto_cobrado'] < df_est_filtrada['monto_neto_cobrar']]

                if not pendientes_cobro.empty:
                    with st.form("form_cobro_cliente"):
                        est_id_sel = st.selectbox(t["estimates_select_id"], pendientes_cobro['id'].tolist())
                        row_est = pendientes_cobro[pendientes_cobro['id'] == est_id_sel].iloc[0]
                        saldo_cobro_pen = row_est['monto_neto_cobrar'] - row_est['monto_cobrado']
                        
                        st.info(f"🏢 Obra: **{row_est['proyecto']}** | Cliente: **{row_est['cliente']}** | Saldo Pendiente: **${saldo_cobro_pen:,.2f}**")
                        monto_abono_cliente = st.number_input(t["estimates_amount_input"], min_value=0.01, max_value=float(saldo_cobro_pen), step=5000.0)

                        if st.form_submit_button(t["estimates_pay_submit"]):
                            nuevo_cobrado = row_est['monto_cobrado'] + monto_abono_cliente
                            nuevo_est_status = "Cobrado" if nuevo_cobrado >= row_est['monto_neto_cobrar'] else "Cobrado Parcial"

                            with sqlite3.connect(DB_PATH) as conn:
                                c = conn.cursor()
                                c.execute(
                                    "UPDATE estimaciones SET monto_cobrado = ?, estatus = ?, fecha_cobro = CURRENT_DATE WHERE id = ?",
                                    (nuevo_cobrado, nuevo_est_status, est_id_sel)
                                )
                                conn.commit()
                            clear_data_cache()
                            st.success(t["estimates_pay_success"])
                            st.rerun()
            else:
                st.info("No hay estimaciones registradas actualmente.")

    with tab2:
        with st.form("form_nueva_estimacion"):
            obra_est_sel = st.selectbox(t["lbl_select_obra"], list(proyectos_dict.keys()))
            obra_id_est = proyectos_dict[obra_est_sel]

            c_es1, c_es2 = st.columns(2)
            with c_es1:
                num_est = st.number_input(t["estimates_num"], min_value=1, value=1, step=1)
                concepto_est = st.text_input(t["estimates_concept"])
                monto_bruto_est = st.number_input(t["estimates_gross"], min_value=0.01, step=10000.0)
            with c_es2:
                pct_anticipo = st.number_input(t["estimates_advance_pct"], min_value=0.0, max_value=100.0, value=0.0, step=5.0)
                pct_garantia = st.number_input(t["estimates_guarantee_pct"], min_value=0.0, max_value=50.0, value=5.0, step=1.0)

            m_anticipo = monto_bruto_est * (pct_anticipo / 100.0)
            m_garantia = monto_bruto_est * (pct_garantia / 100.0)
            m_neto_cobrar = monto_bruto_est - m_anticipo - m_garantia

            st.markdown(f"### {t['estimates_net_calc']} **${m_neto_cobrar:,.2f}**")

            if st.form_submit_button(t["estimates_issue_submit"]):
                if concepto_est and monto_bruto_est > 0:
                    try:
                        with sqlite3.connect(DB_PATH) as conn:
                            c = conn.cursor()
                            c.execute(
                                "INSERT INTO estimaciones (proyecto_id, numero_estimacion, concepto_periodo, monto_estimado, amortizacion_anticipo, retencion_garantia, monto_neto_cobrar, registrado_por) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                (obra_id_est, num_est, concepto_est, monto_bruto_est, m_anticipo, m_garantia, m_neto_cobrar, user['nombre'])
                            )
                            conn.commit()
                        clear_data_cache()
                        st.success(t["estimates_issue_success"])
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

# ==========================================
# 5. REGISTRO DE COSTOS
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
                st.markdown("### 📝 Editor Directo de Costos Registrados")
                edited_costos = st.data_editor(
                    costos_df[["id", "categoria", "concepto", "monto", "fecha", "registrado_por"]],
                    column_config={
                        "id": st.column_config.NumberColumn("ID", disabled=True),
                        "monto": st.column_config.NumberColumn("Monto ($)", format="$%,.2f"),
                        "categoria": st.column_config.SelectboxColumn("Categoría", options=["Materiales / Materials", "Mano de Obra / Labor", "Equipos / Equipment", "Subcontratos / Subcontracts", "Gastos Indirectos / Indirects"]),
                    },
                    num_rows="dynamic",
                    use_container_width=True,
                    key="editor_costos_key"
                )

                if st.button("💾 " + t["obras_edit_save"], key="btn_save_costos_editor"):
                    with sqlite3.connect(DB_PATH) as conn:
                        c = conn.cursor()
                        ids_act = edited_costos['id'].dropna().tolist() if 'id' in edited_costos.columns else []
                        ids_orig = costos_df['id'].tolist()
                        ids_del = set(ids_orig) - set(ids_act)

                        for id_d in ids_del:
                            c.execute("DELETE FROM costos WHERE id = ?", (id_d,))

                        for _, row in edited_costos.iterrows():
                            if pd.notna(row['id']):
                                c.execute(
                                    "UPDATE costos SET categoria=?, concepto=?, monto=?, fecha=? WHERE id=?",
                                    (row['categoria'], row['concepto'], row['monto'], row['fecha'], int(row['id']))
                                )
                        conn.commit()
                    clear_data_cache()
                    st.success(t["costos_deleted_msg"])
                    st.rerun()
            else:
                st.info("Sin registros de costos para esta obra.")

# ==========================================
# 6. CUENTAS POR PAGAR (CxP)
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
            cxp_df = get_cxp_df()
            if not cxp_df.empty:
                cxp_df["saldo_pendiente"] = cxp_df["monto_total"] - cxp_df["monto_pagado"]
                df_cxp_filtrada = cxp_df.copy()
                if global_obra_sel != t["all_sites"]:
                    df_cxp_filtrada = df_cxp_filtrada[df_cxp_filtrada["proyecto"] == global_obra_sel]

                st.markdown("### 📝 Editor Directo de Cuentas por Pagar")
                edited_cxp = st.data_editor(
                    df_cxp_filtrada[["id", "proyecto", "proveedor", "concepto", "monto_total", "monto_pagado", "saldo_pendiente", "estatus", "fecha_vencimiento"]],
                    column_config={
                        "id": st.column_config.NumberColumn("ID", disabled=True),
                        "monto_total": st.column_config.NumberColumn("Total ($)", format="$%,.2f"),
                        "monto_pagado": st.column_config.NumberColumn("Pagado ($)", format="$%,.2f"),
                        "saldo_pendiente": st.column_config.NumberColumn("Saldo ($)", format="$%,.2f", disabled=True),
                        "estatus": st.column_config.SelectboxColumn("Estatus", options=["Pendiente", "Parcial", "Pagado"]),
                    },
                    num_rows="dynamic",
                    use_container_width=True,
                    key="editor_cxp_key"
                )

                if st.button("💾 " + t["obras_edit_save"], key="btn_save_cxp_editor"):
                    with sqlite3.connect(DB_PATH) as conn:
                        c = conn.cursor()
                        ids_act = edited_cxp['id'].dropna().tolist() if 'id' in edited_cxp.columns else []
                        ids_orig = df_cxp_filtrada['id'].tolist()
                        ids_del = set(ids_orig) - set(ids_act)

                        for id_d in ids_del:
                            c.execute("DELETE FROM cuentas_por_pagar WHERE id = ?", (id_d,))

                        for _, row in edited_cxp.iterrows():
                            if pd.notna(row['id']):
                                c.execute(
                                    "UPDATE cuentas_por_pagar SET proveedor=?, concepto=?, monto_total=?, monto_pagado=?, estatus=?, fecha_vencimiento=? WHERE id=?",
                                    (row['proveedor'], row['concepto'], row['monto_total'], row['monto_pagado'], row['estatus'], row['fecha_vencimiento'], int(row['id']))
                                )
                        conn.commit()
                    clear_data_cache()
                    st.success("✅ ¡Cuentas por pagar actualizadas!")
                    st.rerun()

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
                    st.success("🎉 ¡No hay cuentas pendientes por pagar!")
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
# 7. REQUISICIONES DE CAMPO
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
            req_df = get_requisiciones_df()
            if not req_df.empty:
                df_req_filtrada = req_df.copy()
                if global_obra_sel != t["all_sites"]:
                    df_req_filtrada = df_req_filtrada[df_req_filtrada["proyecto"] == global_obra_sel]

                st.markdown("### 📝 Editor Directo de Requisiciones")
                edited_req = st.data_editor(
                    df_req_filtrada[["id", "proyecto", "insumo", "cantidad", "unidad", "prioridad", "solicitado_por", "estatus", "fecha"]],
                    column_config={
                        "id": st.column_config.NumberColumn("ID", disabled=True),
                        "prioridad": st.column_config.SelectboxColumn("Prioridad", options=["Baja", "Normal", "Alta", "Urgente"]),
                        "estatus": st.column_config.SelectboxColumn("Estatus", options=["Pendiente", "Aprobado", "Entregado", "Rechazado"]),
                    },
                    num_rows="dynamic",
                    use_container_width=True,
                    key="editor_req_key"
                )

                if st.button("💾 " + t["obras_edit_save"], key="btn_save_req_editor"):
                    with sqlite3.connect(DB_PATH) as conn:
                        c = conn.cursor()
                        ids_act = edited_req['id'].dropna().tolist() if 'id' in edited_req.columns else []
                        ids_orig = df_req_filtrada['id'].tolist()
                        ids_del = set(ids_orig) - set(ids_act)

                        for id_d in ids_del:
                            c.execute("DELETE FROM requisiciones WHERE id = ?", (id_d,))

                        for _, row in edited_req.iterrows():
                            if pd.notna(row['id']):
                                c.execute(
                                    "UPDATE requisiciones SET insumo=?, cantidad=?, unidad=?, prioridad=?, estatus=? WHERE id=?",
                                    (row['insumo'], row['cantidad'], row['unidad'], row['prioridad'], row['estatus'], int(row['id']))
                                )
                        conn.commit()
                    clear_data_cache()
                    st.success(t["req_status_success"])
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
# 8. USUARIOS MAESTROS
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

        st.markdown("---")
        with st.expander("🗑️ " + t["users_del_title"]):
            user_del_list = users_df[users_df['username'] != 'admin']['username'].tolist()
            if user_del_list:
                user_del_sel = st.selectbox(t["users_del_select"], user_del_list, key="del_user_sb")
                if st.button(t["users_del_btn"], key="del_user_btn"):
                    if user_del_sel == user['username']:
                        st.error("No puedes eliminar tu propio usuario en sesión.")
                    else:
                        with sqlite3.connect(DB_PATH) as conn:
                            c = conn.cursor()
                            c.execute("DELETE FROM usuarios WHERE username = ?", (user_del_sel,))
                            conn.commit()
                        clear_data_cache()
                        st.success("Usuario eliminado.")
                        st.rerun()
            else:
                st.info("No hay usuarios adicionales para eliminar.")
