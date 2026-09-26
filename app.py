import hashlib
import json
import os
import secrets
import sqlite3
import urllib.parse
import urllib.request
from datetime import date, datetime

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
# DICCIONARIO BILINGÜE COMPLETO (i18n)
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
        "nav_payroll": "💵 Nómina & Control de Horas",
        "nav_estimates": "📐 Estimaciones & Cobro a Clientes",
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
        "metric_pending": "Cuentas por Pagar (CxP)",
        "metric_available": "Margen / Disponible",
        "chart_cat": "Desglose de Costos por Categoría",
        "chart_comp": "Presupuesto vs Costo Real por Proyecto",
        # Obras
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
        "obras_filter_status": "Filtrar por Estatus:",
        "obras_search": "🔎 Buscar Obra por Nombre, Cliente o Código:",
        "obras_edit_select": "Seleccionar Proyecto a Editar",
        "obras_edit_title": "✏️ Editar Datos de Obra & Actualizar Avance Físico",
        "obras_status": "Estatus de Obra",
        "obras_edit_save": "💾 Guardar Cambios",
        "obras_edit_success": "✅ ¡Obra y avances actualizados correctamente!",
        "obras_del_title": "🗑️ Eliminar Obra",
        "obras_del_select": "Seleccionar Proyecto a Borrar",
        "obras_del_warning": "⚠️ ATENCIÓN: Esta acción eliminará permanentemente la obra seleccionada y todos sus registros asociados.",
        "obras_del_confirm": "❌ Confirmar y Borrar Obra",
        "obras_del_success": "La obra se eliminó correctamente.",
        # Personal
        "workers_title": "👷 Control de Personal & Tarifas por Hora",
        "tab_workers_list": "📌 Lista & Asignación de Personal",
        "tab_new_worker": "➕ Registrar Nuevo Trabajador",
        "lbl_worker_name": "Nombre Completo del Trabajador",
        "lbl_position": "Puesto / Especialidad (ej. Albañil, Plomero, Residente)",
        "lbl_phone": "Teléfono de Contacto",
        "lbl_assign_obra": "Asignar a Obra",
        "btn_save_worker": "Registrar Trabajador",
        "msg_worker_success": "Trabajador registrado exitosamente.",
        "workers_filter_site": "Filtrar por Obra:",
        "workers_filter_status": "Estatus del Trabajador:",
        "workers_search": "🔎 Buscar Trabajador o Puesto:",
        "workers_reassign_title": "🔄 Reasignar Trabajador o Modificar Tarifas",
        "workers_select": "Seleccionar Trabajador",
        "workers_new_site": "Nueva Obra Asignada",
        "workers_hourly_rate": "Pago por Hora ($/hr)",
        "workers_daily_wage": "Salario Diario Referencia ($/día)",
        "workers_pay_mode": "Modalidad de Pago",
        "workers_save_changes": "Guardar Cambios de Ficha",
        "workers_updated_msg": "Ficha del trabajador actualizada correctamente.",
        "workers_del_title": "Eliminar Registro de Trabajador",
        "workers_del_select": "Selecciona el ID del Trabajador a borrar",
        "workers_del_btn": "Eliminar Trabajador",
        "workers_del_success": "Registro de trabajador eliminado.",
        # Nómina
        "payroll_title": "💵 Nómina, Pago por Hora & Control de Horas Extras",
        "tab_active_payroll": "📌 Historial de Nóminas & Aplicar Pagos",
        "tab_new_payroll": "➕ Calcular Nómina por Horas",
        "payroll_filter_status": "Estatus de Pago:",
        "payroll_filter_site": "Obra:",
        "payroll_search": "🔎 Buscar Trabajador:",
        "payroll_kpi_pending": "🔴 Saldo Pendiente por Pagar a Trabajadores",
        "payroll_kpi_paid": "🟢 Total Nómina Liquidada / Pagada",
        "payroll_pay_title": "💸 Liquidar Adeudo de Nómina a Trabajador",
        "payroll_select_id": "Seleccionar ID de Nómina a Liquidar",
        "payroll_pay_submit": "✅ Registrar Pago y Cargar a Costos de Mano de Obra",
        "payroll_pay_success": "🎉 Pago de nómina registrado correctamente y cargado a costos de obra.",
        "payroll_no_pending": "🎉 ¡No hay nóminas ni sueldos pendientes por liquidar!",
        "payroll_period_start": "Inicio de Periodo",
        "payroll_period_end": "Fin de Periodo",
        "payroll_hours_norm": "Horas Normales Trabajadas",
        "payroll_rate_norm": "Tarifa por Hora Normal ($/hr)",
        "payroll_hours_ext": "Horas Extras Trabajadas",
        "payroll_rate_ext": "Tarifa por Hora Extra ($/hr)",
        "payroll_deductions": "Descuentos / Deducciones / Anticipos ($)",
        "payroll_total_calc": "🧮 Total a Pagar:",
        "payroll_gen_submit": "💾 Generar Recibo de Nómina por Horas",
        "payroll_gen_success": "✅ Nómina por horas generada correctamente con estatus Pendiente.",
        "payroll_del_title": "Eliminar Registro de Nómina",
        "payroll_del_select": "Selecciona el ID de Nómina a borrar",
        "payroll_del_btn": "Eliminar Registro de Nómina",
        "payroll_del_success": "Registro de nómina eliminado.",
        # Estimaciones
        "estimates_title": "📐 Estimaciones de Obra & Control de Cobros a Clientes",
        "tab_active_estimates": "📌 Estimaciones Registradas & Cobros",
        "tab_new_estimate": "➕ Emitir Nueva Estimación",
        "estimates_filter_site": "Filtrar Obra:",
        "estimates_filter_status": "Estatus de Cobro:",
        "estimates_kpi_net": "📐 Total Neto Emitido",
        "estimates_kpi_collected": "🟢 Total Cobrado a Clientes",
        "estimates_kpi_pending": "🔴 Saldo Pendiente por Cobrar",
        "estimates_pay_title": "💵 Registrar Cobro / Abono de Cliente",
        "estimates_select_id": "Seleccionar ID de Estimación a Cobrar",
        "estimates_amount_input": "Monto Ingresado / Abonado ($)",
        "estimates_pay_submit": "✅ Registrar Cobro de Estimación",
        "estimates_pay_success": "🎉 ¡Ingreso de cobro a cliente registrado correctamente!",
        "estimates_num": "Número de Estimación (#)",
        "estimates_concept": "Concepto / Periodo de la Estimación",
        "estimates_gross": "Monto Bruto Estimado / Ejecutado ($)",
        "estimates_advance_pct": "% Amortización de Anticipo",
        "estimates_guarantee_pct": "% Retención de Fondo de Garantía",
        "estimates_net_calc": "🧮 Neto Facturable a Cobrar:",
        "estimates_issue_submit": "📐 Emitir Estimación de Obra",
        "estimates_issue_success": "✅ Estimación emitida exitosamente.",
        "estimates_del_title": "Eliminar Registro de Estimación",
        "estimates_del_select": "Selecciona el ID de la Estimación a borrar",
        "estimates_del_btn": "Eliminar Estimación",
        "estimates_del_success": "Registro de estimación eliminado.",
        # Costos
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
        "costos_categories_filter": "Categorías:",
        "costos_search": "🔎 Buscar Concepto / Usuario:",
        "costos_delete_title": "Eliminar Registro de Costo Erróneo",
        "costos_delete_select": "Selecciona el ID del costo a eliminar",
        "costos_delete_btn": "Eliminar Costo",
        "costos_deleted_msg": "Costo eliminado.",
        # CxP
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
        "cxp_filter_status": "Estatus:",
        "cxp_search": "🔎 Buscar Proveedor o Concepto:",
        "cxp_del_title": "Eliminar Registro de Cuenta por Pagar",
        "cxp_del_select": "Selecciona el ID de la CxP a borrar",
        "cxp_del_btn": "Eliminar Cuenta por Pagar",
        "cxp_del_success": "Registro de cuenta por pagar eliminado.",
        # Requisiciones
        "req_title": "📋 Requisiciones de Insumos & Materiales de Campo",
        "tab_active_req": "📌 Requisiciones Solicitadas",
        "tab_new_req": "➕ Nueva Requisición",
        "lbl_item": "Insumo / Material Requerido",
        "lbl_qty": "Cantidad",
        "lbl_unit": "Unidad",
        "lbl_priority": "Prioridad",
        "btn_send_req": "Enviar Requisición",
        "msg_req_success": "Requisición enviada con éxito.",
        "req_filter_priority": "Prioridad:",
        "req_filter_status": "Estatus:",
        "req_search": "🔎 Buscar Insumo o Solicitante:",
        "req_status_title": "🔄 Cambiar Estatus de Requisición",
        "req_status_select": "ID Requisición",
        "req_status_new": "Nuevo Estatus",
        "req_status_submit": "Actualizar Estatus",
        "req_status_success": "Estatus de la requisición actualizado.",
        "req_del_title": "Eliminar Requisición",
        "req_del_select": "Selecciona el ID de la Requisición a borrar",
        "req_del_btn": "Eliminar Requisición",
        "req_del_success": "Requisición eliminada.",
        # Usuarios
        "users_title": "👑 Control & Alta de Usuarios Maestros",
        "lbl_new_username": "Nombre de Usuario (Login)",
        "lbl_new_password": "Contraseña",
        "lbl_fullname": "Nombre Completo",
        "btn_create_user": "Dar de Alta Usuario Maestro",
        "msg_user_success": "Usuario Maestro creado con éxito.",
        "users_list": "Usuarios Registrados en el Sistema",
        "users_del_title": "Eliminar Usuario Maestro",
        "users_del_select": "Selecciona el Usuario a eliminar",
        "users_del_btn": "Eliminar Usuario",
        "users_del_success": "Usuario eliminado con éxito.",
        "users_del_self_err": "No puedes eliminar tu propio usuario en sesión activa.",
        "users_del_no_users": "No hay usuarios secundarios para eliminar.",
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
        "nav_payroll": "💵 Payroll & Hourly Control",
        "nav_estimates": "📐 Project Estimates & Client Billing",
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
        "metric_pending": "Accounts Payable (AP)",
        "metric_available": "Margin / Available",
        "chart_cat": "Cost Breakdown by Category",
        "chart_comp": "Budget vs Actual Cost per Project",
        # Obras
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
        "obras_filter_status": "Filter by Status:",
        "obras_search": "🔎 Search Project by Name, Client or Code:",
        "obras_edit_select": "Select Project to Edit",
        "obras_edit_title": "✏️ Edit Project Data & Update Progress",
        "obras_status": "Project Status",
        "obras_edit_save": "💾 Save Changes",
        "obras_edit_success": "✅ Project and progress updated successfully!",
        "obras_del_title": "🗑️ Delete Project",
        "obras_del_select": "Select Project to Delete",
        "obras_del_warning": "⚠️ WARNING: This action will permanently delete the selected project and all associated records.",
        "obras_del_confirm": "❌ Confirm and Delete Project",
        "obras_del_success": "Project deleted successfully.",
        # Personal
        "workers_title": "👷 Personnel Control & Hourly Rates",
        "tab_workers_list": "📌 Staff List & Assignment",
        "tab_new_worker": "➕ Register New Worker",
        "lbl_worker_name": "Worker Full Name",
        "lbl_position": "Role / Specialty (e.g. Mason, Plumber, Supervisor)",
        "lbl_phone": "Phone Number",
        "lbl_assign_obra": "Assign to Site",
        "btn_save_worker": "Register Worker",
        "msg_worker_success": "Worker registered successfully.",
        "workers_filter_site": "Filter by Project:",
        "workers_filter_status": "Worker Status:",
        "workers_search": "🔎 Search Worker or Position:",
        "workers_reassign_title": "🔄 Reassign Worker or Update Rates",
        "workers_select": "Select Worker",
        "workers_new_site": "New Assigned Project",
        "workers_hourly_rate": "Hourly Rate ($/hr)",
        "workers_daily_wage": "Daily Reference Wage ($/day)",
        "workers_pay_mode": "Payment Mode",
        "workers_save_changes": "Save Record Changes",
        "workers_updated_msg": "Worker record updated successfully.",
        "workers_del_title": "Delete Worker Record",
        "workers_del_select": "Select Worker ID to delete",
        "workers_del_btn": "Delete Worker",
        "workers_del_success": "Worker record deleted.",
        # Nómina
        "payroll_title": "💵 Payroll, Hourly Wages & Overtime Control",
        "tab_active_payroll": "📌 Payroll History & Apply Payments",
        "tab_new_payroll": "➕ Calculate Hourly Payroll",
        "payroll_filter_status": "Payment Status:",
        "payroll_filter_site": "Project:",
        "payroll_search": "🔎 Search Worker:",
        "payroll_kpi_pending": "🔴 Outstanding Wages Due",
        "payroll_kpi_paid": "🟢 Total Settled / Paid Payroll",
        "payroll_pay_title": "💸 Settle Worker Payroll Dues",
        "payroll_select_id": "Select Payroll ID to Settle",
        "payroll_pay_submit": "✅ Record Payment & Charge to Labor Cost",
        "payroll_pay_success": "🎉 Payroll payment recorded and loaded to site costs.",
        "payroll_no_pending": "🎉 No pending payroll or wages to settle!",
        "payroll_period_start": "Period Start Date",
        "payroll_period_end": "Period End Date",
        "payroll_hours_norm": "Regular Hours Worked",
        "payroll_rate_norm": "Regular Hourly Rate ($/hr)",
        "payroll_hours_ext": "Overtime Hours Worked",
        "payroll_rate_ext": "Overtime Hourly Rate ($/hr)",
        "payroll_deductions": "Deductions / Advances ($)",
        "payroll_total_calc": "🧮 Total Net Payable:",
        "payroll_gen_submit": "💾 Generate Hourly Payroll Stub",
        "payroll_gen_success": "✅ Hourly payroll stub generated with Pending status.",
        "payroll_del_title": "Delete Payroll Record",
        "payroll_del_select": "Select Payroll ID to delete",
        "payroll_del_btn": "Delete Payroll Record",
        "payroll_del_success": "Payroll record deleted.",
        # Estimaciones
        "estimates_title": "📐 Project Progress Estimates & Client Invoicing",
        "tab_active_estimates": "📌 Registered Estimates & Collections",
        "tab_new_estimate": "➕ Issue New Estimate",
        "estimates_filter_site": "Filter Project:",
        "estimates_filter_status": "Collection Status:",
        "estimates_kpi_net": "📐 Total Net Issued",
        "estimates_kpi_collected": "🟢 Total Collected from Clients",
        "estimates_kpi_pending": "🔴 Outstanding Balance to Collect",
        "estimates_pay_title": "💵 Record Client Collection / Partial Payment",
        "estimates_select_id": "Select Estimate ID to Collect",
        "estimates_amount_input": "Amount Collected / Paid ($)",
        "estimates_pay_submit": "✅ Record Estimate Collection",
        "estimates_pay_success": "🎉 Client payment recorded successfully!",
        "estimates_num": "Estimate Number (#)",
        "estimates_concept": "Estimate Concept / Period Description",
        "estimates_gross": "Gross Estimated Amount ($)",
        "estimates_advance_pct": "% Advance Downpayment Amortization",
        "estimates_guarantee_pct": "% Retainage / Guarantee Fund",
        "estimates_net_calc": "🧮 Net Collectible Invoice Amount:",
        "estimates_issue_submit": "📐 Issue Site Estimate",
        "estimates_issue_success": "✅ Estimate issued successfully.",
        "estimates_del_title": "Delete Estimate Record",
        "estimates_del_select": "Select Estimate ID to delete",
        "estimates_del_btn": "Delete Estimate",
        "estimates_del_success": "Estimate record deleted.",
        # Costos
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
        "costos_categories_filter": "Categories:",
        "costos_search": "🔎 Search Concept / User:",
        "costos_delete_title": "Delete Erroneous Expense Entry",
        "costos_delete_select": "Select Cost ID to Delete",
        "costos_delete_btn": "Delete Expense",
        "costos_deleted_msg": "Cost entry deleted.",
        # CxP
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
        "cxp_filter_status": "Status:",
        "cxp_search": "🔎 Search Vendor or Concept:",
        "cxp_del_title": "Delete Accounts Payable Entry",
        "cxp_del_select": "Select AP ID to delete",
        "cxp_del_btn": "Delete Accounts Payable",
        "cxp_del_success": "Accounts payable record deleted.",
        # Requisiciones
        "req_title": "📋 Field Materials & Supply Requisitions",
        "tab_active_req": "📌 Active Requisitions",
        "tab_new_req": "➕ New Requisition",
        "lbl_item": "Material / Supply Needed",
        "lbl_qty": "Quantity",
        "lbl_unit": "Unit",
        "lbl_priority": "Priority Level",
        "btn_send_req": "Submit Requisition",
        "msg_req_success": "Requisition submitted successfully.",
        "req_filter_priority": "Priority:",
        "req_filter_status": "Status:",
        "req_search": "🔎 Search Material or Requester:",
        "req_status_title": "🔄 Update Requisition Status",
        "req_status_select": "Requisition ID",
        "req_status_new": "New Status",
        "req_status_submit": "Update Status",
        "req_status_success": "Requisition status updated.",
        "req_del_title": "Delete Requisition",
        "req_del_select": "Select Requisition ID to delete",
        "req_del_btn": "Delete Requisition",
        "req_del_success": "Requisition deleted.",
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
        "users_del_success": "User deleted successfully.",
        "users_del_self_err": "You cannot delete your own active logged-in user.",
        "users_del_no_users": "No secondary users available to delete.",
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
                salario_diario REAL DEFAULT 0.0,
                tarifa_hora REAL DEFAULT 0.0,
                tipo_pago TEXT DEFAULT 'Por Hora',
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
                "salario_diario": "REAL DEFAULT 0.0",
                "tarifa_hora": "REAL DEFAULT 0.0",
                "tipo_pago": "TEXT DEFAULT 'Por Hora'",
                "estatus": "TEXT DEFAULT 'Activo'",
                "fecha_registro": "DATE DEFAULT CURRENT_DATE",
            },
        )

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
        ensure_columns(
            c,
            "nominas",
            {
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
            },
        )

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
        ensure_columns(
            c,
            "estimaciones",
            {
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
            },
        )

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
def get_nominas_df(proyecto_id=None):
    with sqlite3.connect(DB_PATH) as conn:
        if proyecto_id:
            return pd.read_sql_query(
                "SELECT n.*, t.nombre_completo as trabajador, t.puesto, p.nombre as proyecto FROM nominas n JOIN trabajadores t ON n.trabajador_id = t.id LEFT JOIN proyectos p ON n.proyecto_id = p.id WHERE n.proyecto_id = ? ORDER BY n.id DESC",
                conn, params=(proyecto_id,)
            )
        return pd.read_sql_query(
            "SELECT n.*, t.nombre_completo as trabajador, t.puesto, coalesce(p.nombre, 'Sin Asignar / Oficina') as proyecto FROM nominas n JOIN trabajadores t ON n.trabajador_id = t.id LEFT JOIN proyectos p ON n.proyecto_id = p.id ORDER BY n.id DESC",
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
    t["nav_payroll"],
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
# 1. BALANCE FINANCIERO
# ==========================================
elif menu_sel == t["nav_balance"]:
    st.markdown(f"<div class='main-header'>{t['bal_title']}</div>", unsafe_allow_html=True)

    proyectos_df = get_proyectos_df()
    
    if global_obra_sel != t["all_sites"]:
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
        st.subheader(t["obras_edit_title"])
        df_obras_edit = get_proyectos_df()

        if not df_obras_edit.empty:
            proyectos_dict_edit = dict(zip(df_obras_edit["nombre"] + " (" + df_obras_edit["cliente"] + ")", df_obras_edit["id"]))
            obra_sel_edit = st.selectbox(t["obras_edit_select"], list(proyectos_dict_edit.keys()))
            id_edit = proyectos_dict_edit[obra_sel_edit]
            row_edit = df_obras_edit[df_obras_edit["id"] == id_edit].iloc[0]

            with st.form("form_editar_obra"):
                c_e1, c_e2 = st.columns(2)
                with c_e1:
                    e_nombre = st.text_input(t["lbl_name"], value=str(row_edit["nombre"]))
                    e_cliente = st.text_input(t["lbl_client"], value=str(row_edit["cliente"]))
                    e_presupuesto = st.number_input(t["lbl_budget"], value=float(row_edit["presupuesto_total"]), step=10000.0)
                    e_estado = st.selectbox(
                        t["obras_status"],
                        ["En Proceso", "Pausado", "Concluido", "Cancelado"],
                        index=["En Proceso", "Pausado", "Concluido", "Cancelado"].index(row_edit["estado"]) if row_edit["estado"] in ["En Proceso", "Pausado", "Concluido", "Cancelado"] else 0,
                    )

                with c_e2:
                    e_calle = st.text_input(t["lbl_calle"], value=str(row_edit["calle"]))
                    e_cp = st.text_input(t["lbl_cp"], value=str(row_edit["codigo_postal"]))
                    e_ciudad = st.text_input(t["lbl_city"], value=str(row_edit["ciudad"]))
                    e_estado_prov = st.text_input(t["lbl_state"], value=str(row_edit["estado_provincia"]))

                st.markdown("---")
                st.markdown("### 📊 " + t["lbl_real_prog"])
                c_av1, c_av2 = st.columns(2)
                with c_av1:
                    e_avance_meta = st.number_input(t["lbl_target_prog"], min_value=0.0, max_value=100.0, value=float(row_edit["avance_meta"]), step=1.0)
                with c_av2:
                    e_avance_real = st.number_input(t["lbl_real_prog"], min_value=0.0, max_value=100.0, value=float(row_edit["avance_real"]), step=1.0)

                if st.form_submit_button(t["obras_edit_save"]):
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
                    st.success(t["obras_edit_success"])
                    st.rerun()
        else:
            st.info("No hay proyectos registrados para editar.")

    with tab4:
        st.subheader(t["obras_del_title"])
        df_obras_del = get_proyectos_df()

        if not df_obras_del.empty:
            proyectos_dict_del = dict(zip(df_obras_del["nombre"] + " (" + df_obras_del["cliente"] + ")", df_obras_del["id"]))
            obra_sel_del = st.selectbox(t["obras_del_select"], list(proyectos_dict_del.keys()))
            id_borrar = proyectos_dict_del[obra_sel_del]

            st.error(t["obras_del_warning"])

            if st.button(t["obras_del_confirm"], type="primary"):
                try:
                    with sqlite3.connect(DB_PATH) as conn:
                        c = conn.cursor()
                        c.execute("UPDATE trabajadores SET proyecto_id = NULL WHERE proyecto_id = ?", (id_borrar,))
                        c.execute("DELETE FROM costos WHERE proyecto_id = ?", (id_borrar,))
                        c.execute("DELETE FROM cuentas_por_pagar WHERE proyecto_id = ?", (id_borrar,))
                        c.execute("DELETE FROM requisiciones WHERE proyecto_id = ?", (id_borrar,))
                        c.execute("DELETE FROM estimaciones WHERE proyecto_id = ?", (id_borrar,))
                        c.execute("DELETE FROM nominas WHERE proyecto_id = ?", (id_borrar,))
                        c.execute("DELETE FROM proyectos WHERE id = ?", (id_borrar,))
                        conn.commit()
                    clear_data_cache()
                    st.success(t["obras_del_success"])
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

            st.dataframe(
                df_mostrar[["id", "nombre_completo", "puesto", "tarifa_hora", "salario_diario", "tipo_pago", "telefono", "proyecto", "estatus", "fecha_registro"]],
                column_config={
                    "id": "ID",
                    "nombre_completo": "Trabajador",
                    "puesto": "Puesto / Especialidad",
                    "tarifa_hora": st.column_config.NumberColumn("Pago por Hora ($/hr)", format="$%,.2f"),
                    "salario_diario": st.column_config.NumberColumn("Sueldo Diario ($/día)", format="$%,.2f"),
                    "tipo_pago": "Modalidad",
                    "telefono": "Teléfono",
                    "proyecto": "Obra Asignada",
                    "estatus": "Estatus",
                },
                use_container_width=True,
            )

            st.markdown("---")
            st.subheader(t["workers_reassign_title"])

            with st.form("form_reasignar_trabajador"):
                trabajador_dict = dict(zip(trabajadores_df["nombre_completo"] + " (" + trabajadores_df["puesto"] + ")", trabajadores_df["id"]))
                trabajador_sel = st.selectbox(t["workers_select"], list(trabajador_dict.keys()))
                trab_row = trabajadores_df[trabajadores_df['id'] == trabajador_dict[trabajador_sel]].iloc[0]
                
                c_re1, c_re2, c_re3, c_re4 = st.columns(4)
                with c_re1:
                    nueva_obra_sel = st.selectbox(t["workers_new_site"], [t["unassigned_office"]] + list(proyectos_dict.keys()))
                with c_re2:
                    nueva_tarifa_hora = st.number_input(t["workers_hourly_rate"], min_value=0.0, value=float(trab_row['tarifa_hora']), step=5.0)
                with c_re3:
                    nuevo_sueldo_val = st.number_input(t["workers_daily_wage"], min_value=0.0, value=float(trab_row['salario_diario']), step=50.0)
                with c_re4:
                    nuevo_tipo_pago = st.selectbox(t["workers_pay_mode"], ["Por Hora", "Semanal", "Diario", "Destajo / Proyecto", "Quincenal"], index=0)

                if st.form_submit_button(t["workers_save_changes"]):
                    trab_id = trabajador_dict[trabajador_sel]
                    nueva_obra_id = proyectos_dict[nueva_obra_sel] if nueva_obra_sel != t["unassigned_office"] else None

                    with sqlite3.connect(DB_PATH) as conn:
                        c = conn.cursor()
                        c.execute("UPDATE trabajadores SET proyecto_id = ?, tarifa_hora = ?, salario_diario = ?, tipo_pago = ? WHERE id = ?", (nueva_obra_id, nueva_tarifa_hora, nuevo_sueldo_val, nuevo_tipo_pago, trab_id))
                        conn.commit()
                    clear_data_cache()
                    st.success(t["workers_updated_msg"])
                    st.rerun()

            st.markdown("---")
            with st.expander("🗑️ " + t["workers_del_title"]):
                w_del_id = st.selectbox(t["workers_del_select"], trabajadores_df["id"].tolist(), key="del_w_sb")
                if st.button(t["workers_del_btn"], key="del_w_btn"):
                    with sqlite3.connect(DB_PATH) as conn:
                        c = conn.cursor()
                        c.execute("DELETE FROM nominas WHERE trabajador_id = ?", (w_del_id,))
                        c.execute("DELETE FROM trabajadores WHERE id = ?", (w_del_id,))
                        conn.commit()
                    clear_data_cache()
                    st.success(t["workers_del_success"])
                    st.rerun()
        else:
            st.info("No hay trabajadores registrados en la base de datos.")

    with tab2:
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
                        st.error(f"Error al guardar trabajador: {e}")

# ==========================================
# 3.1 CONTROL DE NÓMINA POR HORA
# ==========================================
elif menu_sel == t["nav_payroll"]:
    st.markdown(f"<div class='main-header'>{t['payroll_title']}</div>", unsafe_allow_html=True)

    proyectos_df = get_proyectos_df()
    proyectos_dict = dict(zip(proyectos_df["nombre"], proyectos_df["id"])) if not proyectos_df.empty else {}
    
    tab1, tab2 = st.tabs([t["tab_active_payroll"], t["tab_new_payroll"]])

    with tab1:
        st.subheader("🔍 " + t["payroll_filter_status"])
        np_f1, np_f2, np_f3 = st.columns([1, 1, 1.5])
        with np_f1:
            f_estatus_nom = st.multiselect(t["payroll_filter_status"], ["Pendiente", "Pagado"], default=["Pendiente", "Pagado"])
        with np_f2:
            f_obra_nom = st.selectbox(t["payroll_filter_site"], [t["all_sites"]] + list(proyectos_dict.keys()), index=0 if global_obra_sel == t["all_sites"] else (list(proyectos_dict.keys()).index(global_obra_sel) + 1 if global_obra_sel in proyectos_dict else 0))
        with np_f3:
            f_buscar_worker_nom = st.text_input(t["payroll_search"], "")

        nominas_df = get_nominas_df()

        if not nominas_df.empty:
            df_nom_filtrada = nominas_df.copy()
            if f_estatus_nom:
                df_nom_filtrada = df_nom_filtrada[df_nom_filtrada['estatus'].isin(f_estatus_nom)]
            if f_obra_nom != t["all_sites"]:
                df_nom_filtrada = df_nom_filtrada[df_nom_filtrada['proyecto'] == f_obra_nom]
            if f_buscar_worker_nom:
                df_nom_filtrada = df_nom_filtrada[df_nom_filtrada['trabajador'].str.lower().str.contains(f_buscar_worker_nom.lower())]

            total_adeudo_nomina = df_nom_filtrada[df_nom_filtrada['estatus'] == 'Pendiente']['monto_neto'].sum()
            total_pagado_nomina = df_nom_filtrada[df_nom_filtrada['estatus'] == 'Pagado']['monto_neto'].sum()

            nk1, nk2 = st.columns(2)
            nk1.metric(t["payroll_kpi_pending"], f"${total_adeudo_nomina:,.2f}")
            nk2.metric(t["payroll_kpi_paid"], f"${total_pagado_nomina:,.2f}")

            st.markdown("---")
            st.dataframe(
                df_nom_filtrada[["id", "trabajador", "puesto", "proyecto", "periodo_inicio", "periodo_fin", "horas_trabajadas", "tarifa_hora", "monto_base", "horas_extras", "bonos_extras", "descuentos", "monto_neto", "estatus", "fecha_pago"]],
                column_config={
                    "id": "ID",
                    "horas_trabajadas": st.column_config.NumberColumn("Horas Norm.", format="%.1f hrs"),
                    "tarifa_hora": st.column_config.NumberColumn("Tarifa/Hr", format="$%,.2f"),
                    "monto_base": st.column_config.NumberColumn("Sueldo Base", format="$%,.2f"),
                    "horas_extras": st.column_config.NumberColumn("Horas Ext.", format="%.1f hrs"),
                    "bonos_extras": st.column_config.NumberColumn("Extras / $", format="$%,.2f"),
                    "descuentos": st.column_config.NumberColumn("Deducciones", format="$%,.2f"),
                    "monto_neto": st.column_config.NumberColumn("Neto a Pagar", format="$%,.2f"),
                },
                use_container_width=True
            )

            st.markdown("---")
            st.subheader(t["payroll_pay_title"])
            pendientes_nom = df_nom_filtrada[df_nom_filtrada['estatus'] == 'Pendiente']

            if not pendientes_nom.empty:
                with st.form("form_pagar_nomina"):
                    nom_id_sel = st.selectbox(t["payroll_select_id"], pendientes_nom['id'].tolist())
                    row_nom = pendientes_nom[pendientes_nom['id'] == nom_id_sel].iloc[0]
                    st.info(f"💵 Trabajador: **{row_nom['trabajador']}** | Obra: **{row_nom['proyecto']}** | Neto a Pagar: **${row_nom['monto_neto']:,.2f}**")
                    
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
                                        f"Pago Nómina por Horas #{nom_id_sel}: {row_nom['trabajador']} ({row_nom['horas_trabajadas']} hrs normales + {row_nom['horas_extras']} hrs extras)",
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
            with st.expander("🗑️ " + t["payroll_del_title"]):
                nom_del_id = st.selectbox(t["payroll_del_select"], nominas_df["id"].tolist(), key="del_nom_sb")
                if st.button(t["payroll_del_btn"], key="del_nom_btn"):
                    with sqlite3.connect(DB_PATH) as conn:
                        c = conn.cursor()
                        c.execute("DELETE FROM nominas WHERE id = ?", (nom_del_id,))
                        conn.commit()
                    clear_data_cache()
                    st.success(t["payroll_del_success"])
                    st.rerun()
        else:
            st.info("Sin registros de nómina generados.")

    with tab2:
        trabajadores_df = get_trabajadores_df()
        if trabajadores_df.empty:
            st.warning("Registra trabajadores primero en el módulo de Personal.")
        else:
            with st.form("form_nueva_nomina"):
                trab_dict_nom = dict(zip(trabajadores_df['nombre_completo'] + " - " + trabajadores_df['puesto'], trabajadores_df['id']))
                w_sel_nom = st.selectbox(t["workers_select"], list(trab_dict_nom.keys()))
                trab_id_nom = trab_dict_nom[w_sel_nom]
                trab_row_nom = trabajadores_df[trabajadores_df['id'] == trab_id_nom].iloc[0]

                st.markdown(f"💡 **Tarifa Base:** `${trab_row_nom['tarifa_hora']:,.2f} / hr` | **Obra:** `{trab_row_nom['proyecto']}`")

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
                
                st.markdown(
                    f"### {t['payroll_total_calc']} **${monto_neto_calc:,.2f}** "
                    f"*(Base: ${monto_base_calc:,.2f} | Extras: ${monto_extras_calc:,.2f} | Deducción: -${descuentos_val:,.2f})*"
                )

                if st.form_submit_button(t["payroll_gen_submit"]):
                    try:
                        with sqlite3.connect(DB_PATH) as conn:
                            c = conn.cursor()
                            c.execute(
                                "INSERT INTO nominas (trabajador_id, proyecto_id, periodo_inicio, periodo_fin, horas_trabajadas, horas_extras, tarifa_hora, monto_base, bonos_extras, descuentos, monto_neto, registrado_por) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (
                                    trab_id_nom,
                                    trab_row_nom['proyecto_id'],
                                    p_inicio,
                                    p_fin,
                                    horas_trab,
                                    horas_ext,
                                    tarifa_hora_val,
                                    monto_base_calc,
                                    monto_extras_calc,
                                    descuentos_val,
                                    monto_neto_calc,
                                    user['nombre']
                                )
                            )
                            conn.commit()
                        clear_data_cache()
                        st.success(t["payroll_gen_success"])
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al generar nómina: {e}")

# ==========================================
# 3.2 ESTIMACIONES & COBRO A CLIENTES
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
            st.subheader("🔍 " + t["estimates_filter_site"])
            ef_1, ef_2 = st.columns([1, 1.5])
            with ef_1:
                f_obra_est = st.selectbox(t["estimates_filter_site"], [t["all_sites"]] + list(proyectos_dict.keys()), index=0 if global_obra_sel == t["all_sites"] else (list(proyectos_dict.keys()).index(global_obra_sel) + 1 if global_obra_sel in proyectos_dict else 0))
            with ef_2:
                f_estatus_est = st.multiselect(t["estimates_filter_status"], ["Pendiente", "Cobrado Parcial", "Cobrado"], default=["Pendiente", "Cobrado Parcial", "Cobrado"])

            estimaciones_df = get_estimaciones_df()

            if not estimaciones_df.empty:
                df_est_filtrada = estimaciones_df.copy()
                if f_obra_est != t["all_sites"]:
                    df_est_filtrada = df_est_filtrada[df_est_filtrada['proyecto'] == f_obra_est]
                if f_estatus_est:
                    df_est_filtrada = df_est_filtrada[df_est_filtrada['estatus'].isin(f_estatus_est)]

                total_estimado_bruto = df_est_filtrada['monto_estimado'].sum()
                total_cobrar_neto = df_est_filtrada['monto_neto_cobrar'].sum()
                total_cobrado_cliente = df_est_filtrada['monto_cobrado'].sum()
                saldo_pendiente_cliente = total_cobrar_neto - total_cobrado_cliente

                ek1, ek2, ek3 = st.columns(3)
                ek1.metric(t["estimates_kpi_net"], f"${total_cobrar_neto:,.2f}")
                ek2.metric(t["estimates_kpi_collected"], f"${total_cobrado_cliente:,.2f}")
                ek3.metric(t["estimates_kpi_pending"], f"${saldo_pendiente_cliente:,.2f}")

                st.markdown("---")
                st.dataframe(
                    df_est_filtrada[["id", "numero_estimacion", "proyecto", "cliente", "concepto_periodo", "monto_estimado", "amortizacion_anticipo", "retencion_garantia", "monto_neto_cobrar", "monto_cobrado", "estatus", "fecha_emision"]],
                    column_config={
                        "monto_estimado": st.column_config.NumberColumn("Monto Bruto", format="$%,.2f"),
                        "amortizacion_anticipo": st.column_config.NumberColumn("Anticipo Deducido", format="$%,.2f"),
                        "retencion_garantia": st.column_config.NumberColumn("Fondo Garantía", format="$%,.2f"),
                        "monto_neto_cobrar": st.column_config.NumberColumn("Neto a Cobrar", format="$%,.2f"),
                        "monto_cobrado": st.column_config.NumberColumn("Cobrado", format="$%,.2f"),
                    },
                    use_container_width=True
                )

                st.markdown("---")
                st.subheader(t["estimates_pay_title"])
                pendientes_cobro = df_est_filtrada[df_est_filtrada['monto_cobrado'] < df_est_filtrada['monto_neto_cobrar']]

                if not pendientes_cobro.empty:
                    with st.form("form_cobro_cliente"):
                        est_id_sel = st.selectbox(t["estimates_select_id"], pendientes_cobro['id'].tolist())
                        row_est = pendientes_cobro[pendientes_cobro['id'] == est_id_sel].iloc[0]
                        saldo_cobro_pen = row_est['monto_neto_cobrar'] - row_est['monto_cobrado']
                        
                        st.info(f"🏢 Obra: **{row_est['proyecto']}** | Cliente: **{row_est['cliente']}** | Saldo Pendiente de Cobro: **${saldo_cobro_pen:,.2f}**")
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
                    st.success("🎉 ¡Todas las estimaciones de los filtros seleccionados han sido cobradas al 100%!")

                st.markdown("---")
                with st.expander("🗑️ " + t["estimates_del_title"]):
                    est_del_id = st.selectbox(t["estimates_del_select"], estimaciones_df["id"].tolist(), key="del_est_sb")
                    if st.button(t["estimates_del_btn"], key="del_est_btn"):
                        with sqlite3.connect(DB_PATH) as conn:
                            c = conn.cursor()
                            c.execute("DELETE FROM estimaciones WHERE id = ?", (est_del_id,))
                            conn.commit()
                        clear_data_cache()
                        st.success(t["estimates_del_success"])
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

            st.markdown(f"### {t['estimates_net_calc']} **${m_neto_cobrar:,.2f}** *(Deducciones: Anticipo ${m_anticipo:,.2f} | Fondo Garantía ${m_garantia:,.2f})*")

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
                        st.error(f"Error al registrar estimación: {e}")

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
                st.markdown("##### 🔍 " + t["costos_categories_filter"])
                fc1, fc2 = st.columns(2)
                with fc1:
                    f_cats = st.multiselect(t["costos_categories_filter"], costos_df['categoria'].unique().tolist(), default=costos_df['categoria'].unique().tolist())
                with fc2:
                    f_busqueda_c = st.text_input(t["costos_search"], "")

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
                with st.expander("🗑️ " + t["costos_delete_title"]):
                    costo_del_id = st.selectbox(t["costos_delete_select"], costos_df["id"].tolist())
                    if st.button(t["costos_delete_btn"]):
                        with sqlite3.connect(DB_PATH) as conn:
                            c = conn.cursor()
                            c.execute("DELETE FROM costos WHERE id = ?", (costo_del_id,))
                            conn.commit()
                        clear_data_cache()
                        st.success(t["costos_deleted_msg"])
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
            st.subheader("🔍 " + t["cxp_filter_status"])
            c_f1, c_f2, c_f3 = st.columns([1, 1, 1.5])
            with c_f1:
                filtro_estatus_cxp = st.multiselect(t["cxp_filter_status"], ["Pendiente", "Parcial", "Pagado"], default=["Pendiente", "Parcial"])
            with c_f2:
                filtro_obra_cxp = st.selectbox(t["payroll_filter_site"], [t["all_sites"]] + list(proyectos_dict.keys()), index=0 if global_obra_sel == t["all_sites"] else (list(proyectos_dict.keys()).index(global_obra_sel) + 1 if global_obra_sel in proyectos_dict else 0))
            with c_f3:
                buscar_proveedor = st.text_input(t["cxp_search"], "")

            cxp_df = get_cxp_df()
            if not cxp_df.empty:
                cxp_df["saldo_pendiente"] = cxp_df["monto_total"] - cxp_df["monto_pagado"]
                
                df_cxp_filtrada = cxp_df.copy()
                if filtro_estatus_cxp:
                    df_cxp_filtrada = df_cxp_filtrada[df_cxp_filtrada["estatus"].isin(filtro_estatus_cxp)]
                if filtro_obra_cxp != t["all_sites"]:
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

                st.markdown("---")
                with st.expander("🗑️ " + t["cxp_del_title"]):
                    cxp_del_id = st.selectbox(t["cxp_del_select"], cxp_df["id"].tolist(), key="del_cxp_sb")
                    if st.button(t["cxp_del_btn"], key="del_cxp_btn"):
                        with sqlite3.connect(DB_PATH) as conn:
                            c = conn.cursor()
                            c.execute("DELETE FROM cuentas_por_pagar WHERE id = ?", (cxp_del_id,))
                            conn.commit()
                        clear_data_cache()
                        st.success(t["cxp_del_success"])
                        st.rerun()
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
            st.subheader("🔍 " + t["req_filter_priority"])
            rf_col1, rf_col2, rf_col3 = st.columns([1, 1, 1.5])
            with rf_col1:
                filtro_prio_req = st.multiselect(t["req_filter_priority"], ["Baja", "Normal", "Alta", "Urgente"], default=["Baja", "Normal", "Alta", "Urgente"])
            with rf_col2:
                filtro_estatus_req = st.multiselect(t["req_filter_status"], ["Pendiente", "Aprobado", "Entregado", "Rechazado"], default=["Pendiente", "Aprobado"])
            with rf_col3:
                buscar_req = st.text_input(t["req_search"], "")

            req_df = get_requisiciones_df()
            if not req_df.empty:
                df_req_filtrada = req_df.copy()
                if filtro_prio_req:
                    df_req_filtrada = df_req_filtrada[df_req_filtrada["prioridad"].isin(filtro_prio_req)]
                if filtro_estatus_req:
                    df_req_filtrada = df_req_filtrada[df_req_filtrada["estatus"].isin(filtro_estatus_req)]
                if global_obra_sel != t["all_sites"]:
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
                st.subheader(t["req_status_title"])
                with st.form("form_estatus_req"):
                    req_id_sel = st.selectbox(t["req_status_select"], df_req_filtrada["id"].tolist())
                    nuevo_estatus_req = st.selectbox(t["req_status_new"], ["Pendiente", "Aprobado", "Entregado", "Rechazado"])

                    if st.form_submit_button(t["req_status_submit"]):
                        with sqlite3.connect(DB_PATH) as conn:
                            c = conn.cursor()
                            c.execute("UPDATE requisiciones SET estatus = ? WHERE id = ?", (nuevo_estatus_req, req_id_sel))
                            conn.commit()
                        clear_data_cache()
                        st.success(t["req_status_success"])
                        st.rerun()

                st.markdown("---")
                with st.expander("🗑️ " + t["req_del_title"]):
                    req_del_id = st.selectbox(t["req_del_select"], req_df["id"].tolist(), key="del_req_sb")
                    if st.button(t["req_del_btn"], key="del_req_btn"):
                        with sqlite3.connect(DB_PATH) as conn:
                            c = conn.cursor()
                            c.execute("DELETE FROM requisiciones WHERE id = ?", (req_del_id,))
                            conn.commit()
                        clear_data_cache()
                        st.success(t["req_del_success"])
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

        st.markdown("---")
        with st.expander("🗑️ " + t["users_del_title"]):
            user_del_list = users_df[users_df['username'] != 'admin']['username'].tolist()
            if user_del_list:
                user_del_sel = st.selectbox(t["users_del_select"], user_del_list, key="del_user_sb")
                if st.button(t["users_del_btn"], key="del_user_btn"):
                    if user_del_sel == user['username']:
                        st.error(t["users_del_self_err"])
                    else:
                        with sqlite3.connect(DB_PATH) as conn:
                            c = conn.cursor()
                            c.execute("DELETE FROM usuarios WHERE username = ?", (user_del_sel,))
                            conn.commit()
                        clear_data_cache()
                        st.success(t["users_del_success"])
                        st.rerun()
            else:
                st.info(t["users_del_no_users"])
