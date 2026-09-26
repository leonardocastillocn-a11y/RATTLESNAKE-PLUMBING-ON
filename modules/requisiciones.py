import streamlit as st
import database.mock_db as db

def render_requisiciones():
    st.title("📋 Requisiciones de Campo")

    proyectos_df = db.obtener_proyectos()

    if proyectos_df.empty:
        st.warning("Primero debes dar de alta al menos un proyecto en el menú 'Proyectos'.")
        return

    proyectos_dict = dict(zip(proyectos_df['nombre'], proyectos_df['id']))

    proyecto_sel = st.selectbox("Selecciona la Obra", list(proyectos_dict.keys()))
    proyecto_id = proyectos_dict[proyecto_sel]

    st.markdown("---")
    st.subheader("Solicitud de Insumos / Materiales")

    with st.form("form_requisicion"):
        insumo = st.text_input("Material o Insumo requerido")
        col1, col2 = st.columns(2)
        with col1:
            cantidad = st.number_input("Cantidad", min_value=0.01, step=1.0)
        with col2:
            unidad = st.text_input("Unidad de Medida (Ej: Ton, M3, Pza, Bulto)", value="Pza")

        observaciones = st.text_area("Uso destinado o notas de entrega")

        if st.form_submit_button("Enviar Requisición"):
            if insumo:
                db.guardar_requisicion(proyecto_id, insumo, cantidad, unidad, observaciones)
                st.success("Requisición registrada correctamente.")
            else:
                st.error("Escribe la descripción del insumo.")
