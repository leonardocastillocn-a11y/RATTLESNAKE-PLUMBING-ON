import streamlit as st
import database.mock_db as db

def render_proyectos():
    st.title("🏗️ Gestión de Proyectos / Obras")

    tab1, tab2 = st.tabs(["Listado de Obras", "Registrar Nueva Obra"])

    with tab1:
        df = db.obtener_proyectos()
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No hay proyectos registrados aún.")

    with tab2:
        with st.form("form_nuevo_proyecto"):
            codigo = st.text_input("Código de Obra (Ej: OBRA-2026-01)")
            nombre = st.text_input("Nombre / Ubicación de la Obra")
            presupuesto = st.number_input("Presupuesto Total ($)", min_value=0.0, step=1000.0)

            if st.form_submit_button("Guardar Proyecto"):
                if codigo and nombre:
                    try:
                        db.guardar_proyecto(codigo, nombre, presupuesto)
                        st.success(f"Proyecto {codigo} guardado exitosamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")
                else:
                    st.warning("El código y el nombre son obligatorios.")
