import streamlit as st
import database.mock_db as db
from modules.proyectos import render_proyectos
from modules.requisiciones import render_requisiciones

st.set_page_config(page_title="Rattlesnake ERP", page_icon="🏗️", layout="wide")

# Inicializar base de datos SQLite local
db.init_db()

st.sidebar.title("Rattlesnake ERP")
st.sidebar.caption("Control de Obra & Gestión")

menu = st.sidebar.radio("Navegación", ["Proyectos", "Requisiciones de Campo"])

if menu == "Proyectos":
    render_proyectos()
elif menu == "Requisiciones de Campo":
    render_requisiciones()
